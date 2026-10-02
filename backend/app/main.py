import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import upload, chat, documents
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="百晓 BaiXiao",
    description="企业内部智能问答知识库 - 基于 RAG 的企业制度文档问答系统",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    return {
        "message": "百晓 BaiXiao API",
        "version": "1.0.0",
        "documents_count": settings.DOCUMENTS_DIR.exists() and len(list(settings.DOCUMENTS_DIR.iterdir())) or 0
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
