"""
简单的向量存储实现，不依赖 ChromaDB
使用内存存储和简单的余弦相似度计算
"""
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
import numpy as np

from app.config import settings


class SimpleVectorStore:
    def __init__(self):
        self.documents_store: List[Dict[str, Any]] = []
        self.metadata_file = settings.DATA_DIR / "document_metadata.json"
        self.metadata = self._load_metadata()
        print("✅ SimpleVectorStore 初始化成功 (内存模式)")
    
    def _load_metadata(self) -> Dict[str, Any]:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"documents": {}}
    
    def _save_metadata(self):
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def _text_to_vector(self, text: str, dim: int = 384) -> List[float]:
        """将文本转换为向量"""
        words = text.lower().split()
        vector = [0.0] * dim
        
        for word in words:
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = hash_val % dim
            vector[idx] += 1.0
        
        # 归一化
        norm = sum(x * x for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return vector
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return dot_product
    
    def add_documents(self, documents: List[Document], document_id: str, filename: str, file_size: int):
        """添加文档到存储"""
        try:
            print(f"[DEBUG] 开始添加文档: {filename}, 分块数: {len(documents)}")
            
            for i, doc in enumerate(documents):
                vector = self._text_to_vector(doc.page_content)
                self.documents_store.append({
                    "id": f"{document_id}_{i}",
                    "document_id": document_id,
                    "filename": filename,
                    "content": doc.page_content,
                    "vector": vector,
                    "metadata": doc.metadata
                })
            
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
        query_vector = self._text_to_vector(query)
        
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
            results.append(Document(
                page_content=doc_data["content"],
                metadata=doc_data["metadata"]
            ))
        
        return results
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """带分数的相似度搜索"""
        query_vector = self._text_to_vector(query)
        
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


vector_store = SimpleVectorStore()
