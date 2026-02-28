import os
import uuid
import hashlib
import re
from pathlib import Path
from typing import List, Tuple
from langchain_core.documents import Document

from app.config import settings


class SimpleTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
    
    def split_text(self, text: str) -> List[str]:
        if not text:
            return []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            if end >= len(text):
                chunks.append(text[start:].strip())
                break
            
            best_split = end
            for sep in self.separators:
                idx = text.rfind(sep, start, end)
                if idx > start:
                    best_split = idx + len(sep)
                    break
            
            chunk = text[start:best_split].strip()
            if chunk:
                chunks.append(chunk)
            
            start = best_split - self.chunk_overlap
            if start < 0:
                start = 0
        
        return chunks
    
    def create_documents(self, texts: List[str], metadatas: List[dict] = None) -> List[Document]:
        documents = []
        for i, text in enumerate(texts):
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            chunks = self.split_text(text)
            for chunk in chunks:
                documents.append(Document(page_content=chunk, metadata=metadata.copy()))
        return documents


class DocumentProcessor:
    def __init__(self):
        self.text_splitter = SimpleTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
    
    def get_file_hash(self, file_path: Path) -> str:
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def generate_document_id(self) -> str:
        return f"doc_{uuid.uuid4().hex[:12]}"
    
    def extract_text_from_pdf(self, file_path: Path) -> Tuple[str, List[dict]]:
        import pdfplumber
        
        full_text = ""
        page_info = []
        
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                if text.strip():
                    full_text += text + "\n"
                    page_info.append({
                        "page": page_num,
                        "text": text
                    })
        
        return full_text, page_info
    
    def extract_text_from_docx(self, file_path: Path) -> Tuple[str, List[dict]]:
        from docx import Document as DocxDocument
        
        doc = DocxDocument(file_path)
        full_text = ""
        page_info = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                full_text += para.text + "\n"
        
        page_info.append({
            "page": 1,
            "text": full_text
        })
        
        return full_text, page_info
    
    def extract_text(self, file_path: Path) -> Tuple[str, List[dict]]:
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            return self.extract_text_from_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            return self.extract_text_from_docx(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")
    
    def split_text(self, text: str, metadata: dict) -> List[Document]:
        chunks = self.text_splitter.create_documents(
            texts=[text],
            metadatas=[metadata]
        )
        return chunks
    
    def process_document(self, file_path: Path, filename: str) -> Tuple[str, List[Document]]:
        document_id = self.generate_document_id()
        full_text, page_info = self.extract_text(file_path)
        
        if not full_text.strip():
            raise ValueError("文档内容为空，无法处理")
        
        base_metadata = {
            "document_id": document_id,
            "filename": filename,
            "source": filename
        }
        
        chunks = self.split_text(full_text, base_metadata)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_id"] = f"{document_id}_chunk_{i}"
            chunk.metadata["chunk_index"] = i  # 添加片段序号
        
        return document_id, chunks
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> Path:
        safe_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = settings.DOCUMENTS_DIR / safe_filename
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        return file_path
    
    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, str]:
        ext = Path(filename).suffix.lower()
        
        if ext not in settings.ALLOWED_EXTENSIONS:
            return False, f"不支持的文件格式: {ext}。支持的格式: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        
        if file_size > settings.MAX_FILE_SIZE:
            return False, f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB (最大 {settings.MAX_FILE_SIZE / 1024 / 1024}MB)"
        
        return True, "文件验证通过"


document_processor = DocumentProcessor()
