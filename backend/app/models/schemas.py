from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class UploadResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    chunks_count: int
    message: str

class SourceReference(BaseModel):
    content: str
    source: str
    page: Optional[int] = None
    chunk_index: Optional[int] = None  # 片段序号
    section: Optional[str] = None  # 所属章节（如 "第二章 休假制度 > 第一节 年假"）
    relevance_score: float

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceReference]

class DocumentInfo(BaseModel):
    id: str
    filename: str
    upload_time: str
    chunks_count: int
    file_size: int

class DocumentsResponse(BaseModel):
    documents: List[DocumentInfo]

class DeleteResponse(BaseModel):
    success: bool
    message: str
