import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# 模型下载走国内镜像，必须在 huggingface_hub 首次 import 前设置
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

class Settings(BaseSettings):
    LONGCAT_API_KEY: str = os.getenv("LONGCAT_API_KEY", "")
    LONGCAT_BASE_URL: str = os.getenv("LONGCAT_BASE_URL", "https://api.longcat.ai/v1")
    LONGCAT_MODEL: str = os.getenv("LONGCAT_MODEL", "longcat-chat")

    # 检索配置：hybrid = 语义向量+BM25 混合；tfidf = 纯词面（无重依赖，回退用）
    RETRIEVAL_BACKEND: str = os.getenv("RETRIEVAL_BACKEND", "hybrid")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    EMBEDDING_DEVICE: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    EMBEDDING_BATCH_SIZE: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "16"))
    RETRIEVAL_TOP_K: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    RETRIEVAL_CANDIDATES: int = int(os.getenv("RETRIEVAL_CANDIDATES", "10"))
    RRF_K: int = int(os.getenv("RRF_K", "60"))
    # 相关度阈值（余弦相似度），低于该值的片段不进入 prompt
    MIN_SIMILARITY_HYBRID: float = float(os.getenv("MIN_SIMILARITY_HYBRID", "0.35"))
    MIN_SIMILARITY_TFIDF: float = float(os.getenv("MIN_SIMILARITY_TFIDF", "0.05"))

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DOCUMENTS_DIR: Path = DATA_DIR / "documents"
    INDEX_DIR: Path = DATA_DIR / "index"

    MAX_FILE_SIZE: int = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".doc"}
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 80
    # 分块逻辑版本号：变更分块实现时 +1，触发已索引文档自动重建
    CHUNKER_VERSION: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self.INDEX_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
