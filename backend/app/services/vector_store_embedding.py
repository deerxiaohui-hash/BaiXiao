"""
使用真实 Embedding 模型的向量存储实现
支持 OpenAI 兼容的 Embedding API
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from app.config import settings


class EmbeddingVectorStore:
    def __init__(self):
        self.documents_store: List[Dict[str, Any]] = []
        self.metadata_file = settings.DATA_DIR / "document_metadata.json"
        self.vectors_file = settings.DATA_DIR / "document_vectors.json"
        self.metadata = self._load_metadata()
        
        # 初始化 Embedding 模型
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.LONGCAT_API_KEY,
            base_url=settings.LONGCAT_BASE_URL,
            model=settings.EMBEDDING_MODEL
        )
        
        # 加载已存储的向量
        self._load_vectors()
        print(f"✅ EmbeddingVectorStore 初始化成功 (使用模型: {settings.EMBEDDING_MODEL})")
    
    def _load_metadata(self) -> Dict[str, Any]:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"documents": {}}
    
    def _save_metadata(self):
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def _load_vectors(self):
        """加载已保存的向量数据"""
        if self.vectors_file.exists():
            try:
                with open(self.vectors_file, 'r', encoding='utf-8') as f:
                    self.documents_store = json.load(f)
                print(f"[DEBUG] 加载了 {len(self.documents_store)} 个文档片段")
            except Exception as e:
                print(f"[WARNING] 加载向量数据失败: {e}")
                self.documents_store = []
    
    def _save_vectors(self):
        """保存向量数据到文件"""
        try:
            with open(self.vectors_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents_store, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] 保存向量数据失败: {e}")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def add_documents(self, documents: List[Document], document_id: str, filename: str, file_size: int):
        """添加文档到存储"""
        try:
            print(f"[DEBUG] 开始添加文档: {filename}, 分块数: {len(documents)}")
            
            # 提取所有文本内容
            texts = [doc.page_content for doc in documents]
            
            # 批量生成 embeddings
            print(f"[DEBUG] 正在生成 embeddings...")
            vectors = self.embeddings.embed_documents(texts)
            print(f"[DEBUG] Embeddings 生成完成")
            
            # 存储文档和向量
            for i, (doc, vector) in enumerate(zip(documents, vectors)):
                self.documents_store.append({
                    "id": f"{document_id}_{i}",
                    "document_id": document_id,
                    "filename": filename,
                    "content": doc.page_content,
                    "vector": vector,
                    "metadata": doc.metadata
                })
            
            # 保存向量数据
            self._save_vectors()
            
            # 更新元数据
            from datetime import datetime
            self.metadata["documents"][document_id] = {
                "filename": filename,
                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "chunks_count": len(documents),
                "file_size": file_size
            }
            self._save_metadata()
            print(f"[DEBUG] 文档添加完成")
        except Exception as e:
            print(f"[ERROR] add_documents 失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """相似度搜索"""
        results = self.similarity_search_with_score(query, k)
        return [doc for doc, _ in results]
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """带分数的相似度搜索"""
        if not self.documents_store:
            return []
        
        try:
            # 生成查询向量
            query_vector = self.embeddings.embed_query(query)
            
            # 计算所有文档的相似度
            similarities = []
            for doc_data in self.documents_store:
                similarity = self._cosine_similarity(query_vector, doc_data["vector"])
                similarities.append((similarity, doc_data))
            
            # 排序并返回 top-k
            similarities.sort(reverse=True, key=lambda x: x[0])
            top_k = similarities[:k]
            
            results = []
            for similarity, doc_data in top_k:
                doc = Document(
                    page_content=doc_data["content"],
                    metadata=doc_data["metadata"]
                )
                # 将相似度转换为距离（1 - similarity）
                distance = 1.0 - similarity
                results.append((doc, distance))
            
            return results
        except Exception as e:
            print(f"[ERROR] similarity_search_with_score 失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def delete_document(self, document_id: str) -> bool:
        """删除文档"""
        if document_id not in self.metadata["documents"]:
            return False
        
        try:
            # 从存储中删除所有相关文档
            self.documents_store = [
                doc for doc in self.documents_store 
                if doc["document_id"] != document_id
            ]
            
            # 保存更新后的向量数据
            self._save_vectors()
            
            # 删除元数据
            del self.metadata["documents"][document_id]
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """获取所有文档列表"""
        documents = []
        for doc_id, info in self.metadata["documents"].items():
            documents.append({
                "id": doc_id,
                "filename": info["filename"],
                "upload_time": info["upload_time"],
                "chunks_count": info["chunks_count"],
                "file_size": info["file_size"]
            })
        return documents
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        return len(self.metadata["documents"])


# 创建全局实例
vector_store = EmbeddingVectorStore()
