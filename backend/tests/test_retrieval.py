"""检索链路冒烟测试：不依赖语义模型的部分全部可跑。

运行：cd backend && ./venv/Scripts/python.exe -m pytest tests/ -v
"""
import sys
from pathlib import Path

import pytest
from langchain_core.documents import Document

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.vector_store import VectorStore


DOC = "员工手册"


def make_store(tmp_path, contents):
    store = VectorStore(
        index_dir=tmp_path / "index",
        metadata_file=tmp_path / "metadata.json",
        documents_dir=tmp_path / "docs",
    )
    docs = [
        Document(
            page_content=text,
            metadata={
                "document_id": "doc_test",
                "filename": DOC,
                "source": DOC,
                "chunk_id": f"doc_test_chunk_{i}",
                "chunk_index": i,
                "section": None,
                "page": None,
            },
        )
        for i, text in enumerate(contents)
    ]
    store.add_documents(docs, "doc_test", DOC, 100)
    return store


SAMPLE_CHUNKS = [
    "第一条 带薪年假规定：员工累计工作已满1年不满10年的，年休假5天；已满10年不满20年的，年休假10天。",
    "第九条 住宿费用标准：一线城市普通员工500元每天，部门经理800元每天。",
    "第十二条 员工报销应在费用发生后30天内完成，逾期不予受理，发票抬头应与公司名称一致。",
]


def test_search_returns_similarity_sorted(tmp_path):
    store = make_store(tmp_path, SAMPLE_CHUNKS)
    results = store.search("年假有几天", backend="tfidf", min_similarity=0.0)

    assert len(results) > 0
    scores = [s for _, s in results]
    assert scores == sorted(scores, reverse=True), "结果必须按相似度降序"
    assert all(0.0 <= s <= 1.0 for s in scores), "相似度必须在 0~1 之间（不再返回距离）"
    assert "年假" in results[0][0].page_content, "最相关结果应命中年假条款"


def test_threshold_filters_irrelevant(tmp_path):
    store = make_store(tmp_path, SAMPLE_CHUNKS)
    results = store.search("量子物理的黑体辐射", backend="tfidf", min_similarity=0.2)
    assert results == [], "完全不相关的查询应被阈值过滤为空"


def test_delete_document(tmp_path):
    store = make_store(tmp_path, SAMPLE_CHUNKS)
    assert store.delete_document("doc_test") is True
    assert store.delete_document("doc_test") is False
    assert store.search("年假", backend="tfidf") == []
    assert store.get_all_documents() == []


def test_metadata_section_roundtrip(tmp_path):
    store = make_store(tmp_path, SAMPLE_CHUNKS)
    results = store.search("报销时间", backend="tfidf", min_similarity=0.0)
    assert results
    doc = results[0][0]
    assert doc.metadata["filename"] == DOC
    assert doc.metadata["chunk_index"] is not None


def test_hybrid_backend_available(tmp_path):
    """混合后端：语义召回命中相关条款，无关条款被阈值过滤。"""
    store = make_store(tmp_path, SAMPLE_CHUNKS)
    if store.encoder.try_get_model() is None:
        pytest.skip("语义模型未就绪（未下载或加载失败），跳过 hybrid 测试")

    results = store.search("出差的住宿报销额度", backend="hybrid")
    assert results, "相关查询不应返回空"
    contents = [d.page_content for d, _ in results]
    assert any("住宿" in c for c in contents), "语义相关的住宿条款应被召回"
    assert all("年假" not in c for c in contents), "不相关的年假条款应被阈值过滤"
    # 注意：hybrid 结果按融合排序，相似度不保证单调
    assert all(s >= 0.35 for s in (s for _, s in results)), "结果相似度不得低于阈值"
