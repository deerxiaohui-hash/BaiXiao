"""
统一检索模块：hybrid（语义向量 + BM25 混合）与 tfidf（纯词面）双后端。

设计要点：
- search() 返回余弦相似度（0~1，越大越相关），不再向调用方暴露"距离"
- 索引持久化到 data/index/（chunks.json + vectors.npz），带 schema/模型/分块版本戳，
  版本不匹配时自动重建或重编码，无需手动重新上传
- 语义模型惰性加载（首次使用才 import torch），加载失败自动降级为 BM25 词面检索，
  不阻断服务启动
- 任何持久化/检索异常都记录完整日志，绝不静默吞掉返回空结果
"""
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import jieba
import numpy as np
from langchain_core.documents import Document
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings

logger = logging.getLogger(__name__)

SCHEMA_VERSION = 2

# bge 中文模型官方建议：短查询检索长文本时给查询加指令前缀
BGE_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："

# 加权 RRF：语义路为主、词面路为辅，只影响排序，相似度/阈值始终取语义余弦
RRF_DENSE_WEIGHT = 0.7
RRF_BM25_WEIGHT = 0.3

# 首次启动迁移：旧实现（vector_store_tfidf 等）遗留的数据文件
LEGACY_VECTORS_FILE = settings.DATA_DIR / "document_vectors.json"


def _tokenize(text: str) -> List[str]:
    return [t for t in jieba.lcut(text) if t.strip() and t not in _STOPWORDS]


# 中文功能词停用表：这些词在长文档中零散出现会让 BM25 产生虚高匹配
_STOPWORDS = {
    "的", "了", "在", "是", "有", "和", "与", "及", "或", "等", "对", "被", "把",
    "从", "向", "而", "且", "并", "但", "还", "又", "再", "则", "如", "若", "就",
    "都", "也", "很", "你", "我", "他", "她", "它", "这", "那", "为", "以", "于",
    "个", "们", "吗", "呢", "吧", "啊", "么", "中", "内", "外", "下", "上", "里",
    "该", "此", "本", "其", "之", "所", "各", "每", "要", "会", "能",
    "什么", "怎么", "怎样", "多少", "哪", "哪些",
}


class DenseEncoder:
    """bge 语义编码器。模型惰性加载；加载失败后标记失败，重启服务才会重试。"""

    def __init__(self):
        self._model = None
        self._failed = False
        self._lock = threading.Lock()

    def _load(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            logger.info(f"加载语义模型 {settings.EMBEDDING_MODEL} (device={settings.EMBEDDING_DEVICE}) ...")
            t0 = time.time()
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL, device=settings.EMBEDDING_DEVICE
            )
            logger.info(f"语义模型加载完成，耗时 {time.time() - t0:.1f}s")
        return self._model

    def try_get_model(self):
        if self._failed:
            return None
        try:
            return self._load()
        except Exception as e:
            logger.error(f"语义模型加载失败，混合检索降级为 BM25 词面检索: {e}", exc_info=True)
            self._failed = True
            return None

    def encode_passages(self, texts: List[str]) -> np.ndarray:
        model = self._load()
        return model.encode(
            texts,
            batch_size=settings.EMBEDDING_BATCH_SIZE,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def encode_query(self, query: str) -> np.ndarray:
        model = self._load()
        return model.encode(
            [BGE_QUERY_INSTRUCTION + query],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]


class VectorStore:
    def __init__(
        self,
        index_dir: Path = None,
        metadata_file: Path = None,
        documents_dir: Path = None,
    ):
        self.index_dir = index_dir or settings.INDEX_DIR
        self.metadata_file = metadata_file or (settings.DATA_DIR / "document_metadata.json")
        self.documents_dir = documents_dir or settings.DOCUMENTS_DIR
        self.chunks_file = self.index_dir / "chunks.json"
        self.vectors_file = self.index_dir / "vectors.npz"
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # 文档注册表（沿用原路径，文档列表接口不变）
        self.metadata: Dict[str, Any] = self._read_json(
            self.metadata_file, default={"documents": {}}
        )
        self.chunks: List[Dict[str, Any]] = []
        self.dense_matrix: Optional[np.ndarray] = None  # 与 self.chunks 行对齐

        self.encoder = DenseEncoder()
        self._index_lock = threading.Lock()

        # 词面检索状态（从 chunks 现算，不持久化）
        self._tfidf = None
        self._tfidf_matrix = None
        self._bm25 = None

        self._load_or_rebuild()

    # ---------- 持久化 ----------

    @staticmethod
    def _read_json(path: Path, default):
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"读取 {path} 失败: {e}", exc_info=True)
            return default

    def _save_metadata(self):
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def _save_chunks(self, embedding_model: str, chunker_version: int):
        state = {
            "schema_version": SCHEMA_VERSION,
            "embedding_model": embedding_model,
            "chunker_version": chunker_version,
            "chunks": self.chunks,
        }
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _save_matrix(self):
        if self.dense_matrix is None:
            if self.vectors_file.exists():
                self.vectors_file.unlink()
            return
        np.savez_compressed(self.vectors_file, vectors=self.dense_matrix.astype(np.float32))

    # ---------- 启动加载 / 自动重建 ----------

    def _load_or_rebuild(self):
        state = None
        if self.chunks_file.exists():
            state = self._read_json(self.chunks_file, default=None)
            if state is None:
                logger.warning("chunks.json 损坏，将重建索引")

        if state is not None and state.get("schema_version") == SCHEMA_VERSION:
            self.chunks = state.get("chunks", [])
            self._ensure_lexical()

            if state.get("chunker_version") != settings.CHUNKER_VERSION and self.chunks:
                logger.warning(
                    f"分块逻辑已更新 ({state.get('chunker_version')} -> {settings.CHUNKER_VERSION})，"
                    f"用原始文件重建分块 ..."
                )
                with self._index_lock:
                    if self._rechunk_from_sources():
                        self._ensure_lexical()
                        if settings.RETRIEVAL_BACKEND == "hybrid":
                            self._reencode_all()
                        self._save_chunks(settings.EMBEDDING_MODEL, settings.CHUNKER_VERSION)
                        self._save_matrix()
                        self._save_metadata()

            if settings.RETRIEVAL_BACKEND == "hybrid" and self.chunks:
                if state.get("embedding_model") != settings.EMBEDDING_MODEL:
                    logger.warning(
                        f"embedding 模型已变更 ({state.get('embedding_model')} -> {settings.EMBEDDING_MODEL})，"
                        f"重新编码 {len(self.chunks)} 个片段 ..."
                    )
                    self._reencode_all()
                else:
                    self._load_matrix()
            return

        # 首次升级：从旧版 document_vectors.json 迁移文本，向量重新编码
        legacy = self._read_json(LEGACY_VECTORS_FILE, default=None)
        legacy_chunks = (legacy or {}).get("documents", [])
        if legacy_chunks:
            logger.info(f"检测到旧版索引，迁移 {len(legacy_chunks)} 个片段到新格式 ...")
            self.chunks = [
                {
                    "id": c.get("id"),
                    "document_id": c.get("document_id"),
                    "filename": c.get("filename"),
                    "content": c.get("content", ""),
                    "chunk_index": (c.get("metadata") or {}).get("chunk_index"),
                    "section": (c.get("metadata") or {}).get("section"),
                    "page": (c.get("metadata") or {}).get("page"),
                }
                for c in legacy_chunks
            ]
            self._ensure_lexical()
            if settings.RETRIEVAL_BACKEND == "hybrid":
                self._reencode_all()
            self._save_chunks(settings.EMBEDDING_MODEL, settings.CHUNKER_VERSION)
            self._save_matrix()
            LEGACY_VECTORS_FILE.rename(LEGACY_VECTORS_FILE.with_suffix(".json.migrated"))
            logger.info("旧版索引迁移完成，原文件已重命名为 .migrated")
        else:
            logger.info("索引为空，等待文档上传")

    def _load_matrix(self):
        if not self.vectors_file.exists():
            logger.warning("语义向量文件缺失，重新编码 ...")
            self._reencode_all()
            return
        try:
            matrix = np.load(self.vectors_file, allow_pickle=False)["vectors"]
            if matrix.shape[0] != len(self.chunks):
                logger.warning(
                    f"语义向量行数({matrix.shape[0]})与片段数({len(self.chunks)})不一致，重新编码 ..."
                )
                self._reencode_all()
                return
            self.dense_matrix = matrix
        except Exception as e:
            logger.error(f"加载语义向量失败: {e}", exc_info=True)
            self._reencode_all()

    def _reencode_all(self):
        """用当前 embedding 模型重编码全部片段文本；失败则降级为词面检索。"""
        if self.encoder.try_get_model() is None:
            self.dense_matrix = None
            return
        try:
            texts = [c["content"] for c in self.chunks]
            self.dense_matrix = self.encoder.encode_passages(texts) if texts else None
            self._save_matrix()
            logger.info(f"语义向量编码完成: {len(texts)} 个片段")
        except Exception as e:
            logger.error(f"语义向量编码失败，混合检索降级为 BM25: {e}", exc_info=True)
            self.dense_matrix = None

    def _rechunk_from_sources(self):
        """分块逻辑变更时，用已保存的原始文件重建全部分块。"""
        from app.services.document_processor import document_processor

        rebuilt_any = False
        for doc_id, info in list(self.metadata["documents"].items()):
            stored = info.get("stored_file")
            src = self.documents_dir / stored if stored else None
            if not src or not src.exists():
                logger.warning(
                    f"文档 {doc_id}({info.get('filename')}) 缺少原始文件，保留旧分块；"
                    f"重新上传后即可使用新分块逻辑"
                )
                continue
            try:
                chunks = document_processor.build_chunks(src, info["filename"], doc_id)
                self._replace_doc_chunks(doc_id, chunks)
                info["chunks_count"] = len(chunks)
                rebuilt_any = True
                logger.info(f"文档 {doc_id} 已按新分块逻辑重建: {len(chunks)} 个片段")
            except Exception as e:
                logger.error(f"重建文档 {doc_id} 分块失败: {e}", exc_info=True)
        return rebuilt_any

    def _replace_doc_chunks(self, document_id: str, documents: List[Document]):
        self.chunks = [c for c in self.chunks if c["document_id"] != document_id] + [
            {
                "id": d.metadata.get("chunk_id"),
                "document_id": document_id,
                "filename": d.metadata["filename"],
                "content": d.page_content,
                "chunk_index": d.metadata.get("chunk_index"),
                "section": d.metadata.get("section"),
                "page": d.metadata.get("page"),
            }
            for d in documents
        ]

    # ---------- 词面检索状态 ----------

    def _ensure_lexical(self):
        texts = [c["content"] for c in self.chunks]
        if not texts:
            self._tfidf = None
            self._tfidf_matrix = None
            self._bm25 = None
            return
        try:
            self._tfidf = TfidfVectorizer(
                tokenizer=_tokenize,
                max_features=20000,
                ngram_range=(1, 2),
                min_df=1,
            )
            self._tfidf_matrix = self._tfidf.fit_transform(texts)
        except Exception as e:
            logger.error(f"TF-IDF 索引构建失败: {e}", exc_info=True)
            self._tfidf = None
            self._tfidf_matrix = None
        try:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi([_tokenize(t) for t in texts])
        except Exception as e:
            logger.error(f"BM25 索引构建失败: {e}", exc_info=True)
            self._bm25 = None

    def _tfidf_scores(self, query: str) -> Optional[np.ndarray]:
        if self._tfidf is None:
            return None
        q = self._tfidf.transform([query])
        return (self._tfidf_matrix @ q.T).toarray().ravel()

    def _bm25_scores(self, query: str) -> Optional[np.ndarray]:
        if self._bm25 is None:
            return None
        return np.asarray(self._bm25.get_scores(_tokenize(query)), dtype=np.float32)

    def _dense_scores(self, query: str) -> Optional[np.ndarray]:
        if self.dense_matrix is None or self.encoder.try_get_model() is None:
            return None
        try:
            qv = self.encoder.encode_query(query)
            return self.dense_matrix @ qv  # 均已归一化，点积即余弦
        except Exception as e:
            logger.error(f"查询编码失败，本次跳过语义召回: {e}", exc_info=True)
            return None

    # ---------- 公开接口 ----------

    def add_documents(
        self,
        documents: List[Document],
        document_id: str,
        filename: str,
        file_size: int,
        stored_file: str = None,
    ):
        with self._index_lock:
            logger.info(f"添加文档: {filename}, 分块数: {len(documents)}")
            self._replace_doc_chunks(document_id, documents)

            try:
                self._ensure_lexical()
                if settings.RETRIEVAL_BACKEND == "hybrid":
                    self._reencode_all()
                self._save_chunks(settings.EMBEDDING_MODEL, settings.CHUNKER_VERSION)
                self._save_matrix()
            except Exception as e:
                logger.error(f"索引持久化失败: {e}", exc_info=True)
                raise

            self.metadata["documents"][document_id] = {
                "filename": filename,
                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "chunks_count": len(documents),
                "file_size": file_size,
                "stored_file": stored_file,
            }
            self._save_metadata()

    def delete_document(self, document_id: str) -> bool:
        if document_id not in self.metadata["documents"]:
            return False
        with self._index_lock:
            self.chunks = [c for c in self.chunks if c["document_id"] != document_id]
            self._ensure_lexical()
            if settings.RETRIEVAL_BACKEND == "hybrid" and self.chunks:
                self._reencode_all()
            else:
                self.dense_matrix = None
            try:
                self._save_chunks(settings.EMBEDDING_MODEL, settings.CHUNKER_VERSION)
                self._save_matrix()
            except Exception as e:
                logger.error(f"删除后索引持久化失败: {e}", exc_info=True)
                raise
            del self.metadata["documents"][document_id]
            self._save_metadata()
            return True

    def search(
        self,
        query: str,
        k: int = None,
        min_similarity: float = None,
        backend: str = None,
    ) -> List[Tuple[Document, float]]:
        """返回 [(Document, 余弦相似度)]，相似度降序；低于阈值的片段被过滤。"""
        k = k or settings.RETRIEVAL_TOP_K
        backend = backend or settings.RETRIEVAL_BACKEND
        if backend == "hybrid":
            min_similarity = (
                settings.MIN_SIMILARITY_HYBRID if min_similarity is None else min_similarity
            )
            pairs = self._hybrid_search(query, k)
        else:
            min_similarity = (
                settings.MIN_SIMILARITY_TFIDF if min_similarity is None else min_similarity
            )
            pairs = self._tfidf_search(query, k)

        results = []
        for idx, sim in pairs:
            if sim < min_similarity:
                continue
            results.append((self._to_document(self.chunks[idx]), float(sim)))
        return results[:k]

    def _top_indices(self, scores: np.ndarray, n: int) -> List[Tuple[int, float]]:
        order = np.argsort(scores)[::-1][:n]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]

    def _tfidf_search(self, query, k) -> List[Tuple[int, float]]:
        scores = self._tfidf_scores(query)
        if scores is None:
            return []
        return self._top_indices(scores, k)

    def _hybrid_search(self, query, k) -> List[Tuple[int, float]]:
        lex_scores = self._bm25_scores(query)
        dense_scores = self._dense_scores(query)

        if dense_scores is None and lex_scores is None:
            return []
        if dense_scores is None:
            logger.warning("语义向量不可用，本次查询仅使用 BM25 词面召回")
            return self._top_indices(lex_scores, k)

        dense_list = self._top_indices(dense_scores, settings.RETRIEVAL_CANDIDATES)
        # 展示相似度/阈值都基于语义余弦；BM25 只参与排序
        if lex_scores is None:
            return dense_list

        rrf: Dict[int, float] = {}
        for weight, ranked in (
            (RRF_DENSE_WEIGHT, dense_list),
            (RRF_BM25_WEIGHT, self._top_indices(lex_scores, settings.RETRIEVAL_CANDIDATES)),
        ):
            for rank, (idx, _) in enumerate(ranked, start=1):
                rrf[idx] = rrf.get(idx, 0.0) + weight / (settings.RRF_K + rank)
        fused_order = sorted(rrf, key=rrf.get, reverse=True)[:k]
        return [(idx, float(dense_scores[idx])) for idx in fused_order]

    @staticmethod
    def _to_document(chunk: Dict[str, Any]) -> Document:
        return Document(
            page_content=chunk["content"],
            metadata={
                "document_id": chunk.get("document_id"),
                "filename": chunk.get("filename"),
                "source": chunk.get("filename"),
                "chunk_id": chunk.get("id"),
                "chunk_index": chunk.get("chunk_index"),
                "section": chunk.get("section"),
                "page": chunk.get("page"),
            },
        )

    # ---------- 文档列表 ----------

    def get_all_documents(self) -> List[Dict[str, Any]]:
        documents = []
        for doc_id, info in self.metadata["documents"].items():
            documents.append(
                {
                    "id": doc_id,
                    "filename": info["filename"],
                    "upload_time": info["upload_time"],
                    "chunks_count": info["chunks_count"],
                    "file_size": info["file_size"],
                }
            )
        return documents

    def get_document_count(self) -> int:
        return len(self.metadata["documents"])


# 全局单例（模型惰性加载，import 时不会加载 torch）
vector_store = VectorStore()
