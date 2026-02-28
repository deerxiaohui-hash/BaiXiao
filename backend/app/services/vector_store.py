import json
import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
from langchain_core.documents import Document
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import EmbeddingFunction

from app.config import settings


class SimpleHashEmbeddingFunction(EmbeddingFunction):
    """简单的哈希嵌入函数，不依赖 ONNX Runtime"""
    def __init__(self, dim: int = 384):
        self.dim = dim
    
    def _text_to_embedding(self, text: str) -> List[float]:
        words = text.lower().split()
        embedding = [0.0] * self.dim
        
        for i, word in enumerate(words):
            hash_val = int(hashlib.md5(word.encode()).hexdigest(), 16)
            idx = hash_val % self.dim
            embedding[idx] += 1.0
        
        norm = sum(x * x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x / norm for x in embedding]
        
        return embedding
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        return [self._text_to_embedding(text) for text in input]


class VectorStore:
    def __init__(self):
        # 使用简单哈希嵌入，避免 ONNX Runtime 问题
        self.embedding_function = SimpleHashEmbeddingFunction()
        
        try:
            # 使用 EphemeralClient (内存模式) 避免持久化问题
            self.client = chromadb.EphemeralClient(
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            self.collection = self.client.get_or_create_collection(
                name="enterprise_knowledge",
                embedding_function=self.embedding_function,
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ ChromaDB 初始化成功 (内存模式)")
        except Exception as e:
            print(f"❌ ChromaDB 初始化错误: {e}")
            raise
        
        self.metadata_file = settings.DATA_DIR / "document_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"documents": {}}
    
    def _save_metadata(self):
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def add_documents(self, documents: List[Document], document_id: str, filename: str, file_size: int):
        try:
            print(f"[DEBUG] 开始添加文档: {filename}, 分块数: {len(documents)}")
            ids = [f"{document_id}_{i}" for i in range(len(documents))]
            texts = [doc.page_content for doc in documents]
            metadatas = [{"document_id": document_id, "filename": filename, **doc.metadata} for doc in documents]
            
            print(f"[DEBUG] 准备调用 collection.add()")
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            print(f"[DEBUG] collection.add() 完成")
            
            from datetime import datetime
            self.metadata["documents"][document_id] = {
                "filename": filename,
                "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "chunks_count": len(documents),
                "file_size": file_size
            }
            self._save_metadata()
            print(f"[DEBUG] 元数据保存完成")
        except Exception as e:
            print(f"[ERROR] add_documents 失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        documents = []
        if results['documents'] and results['documents'][0]:
            for i, text in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                documents.append(Document(page_content=text, metadata=metadata))
        
        return documents
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        documents_with_scores = []
        if results['documents'] and results['documents'][0]:
            for i, text in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                documents_with_scores.append((
                    Document(page_content=text, metadata=metadata),
                    distance
                ))
        
        return documents_with_scores
    
    def delete_document(self, document_id: str) -> bool:
        if document_id not in self.metadata["documents"]:
            return False
        
        try:
            all_docs = self.collection.get()
            ids_to_delete = []
            
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata.get('document_id') == document_id:
                    ids_to_delete.append(all_docs['ids'][i])
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
            
            del self.metadata["documents"][document_id]
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"删除文档失败: {e}")
            return False
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
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
        return len(self.metadata["documents"])


vector_store = VectorStore()
