"""
测试 Embedding 模型是否配置正确
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from langchain_openai import OpenAIEmbeddings


def test_embedding():
    print("=" * 60)
    print("测试 Embedding 模型配置")
    print("=" * 60)
    
    print(f"\n配置信息:")
    print(f"  API Key: {settings.LONGCAT_API_KEY[:10]}..." if settings.LONGCAT_API_KEY else "  API Key: 未配置")
    print(f"  Base URL: {settings.LONGCAT_BASE_URL}")
    print(f"  Embedding Model: {settings.EMBEDDING_MODEL}")
    
    if not settings.LONGCAT_API_KEY:
        print("\n❌ 错误: LONGCAT_API_KEY 未配置")
        print("请在 .env 文件中配置 LONGCAT_API_KEY")
        return False
    
    try:
        print("\n正在初始化 Embedding 模型...")
        embeddings = OpenAIEmbeddings(
            api_key=settings.LONGCAT_API_KEY,
            base_url=settings.LONGCAT_BASE_URL,
            model=settings.EMBEDDING_MODEL
        )
        
        print("正在测试 embedding 生成...")
        test_text = "今年我司的带薪年假有多少天？"
        vector = embeddings.embed_query(test_text)
        
        print(f"\n✅ 成功!")
        print(f"  测试文本: {test_text}")
        print(f"  向量维度: {len(vector)}")
        print(f"  向量前5个值: {vector[:5]}")
        
        # 测试批量生成
        print("\n正在测试批量 embedding 生成...")
        test_texts = [
            "员工出差需要提前填写申请表",
            "带薪年假根据工作年限确定"
        ]
        vectors = embeddings.embed_documents(test_texts)
        print(f"✅ 批量生成成功! 生成了 {len(vectors)} 个向量")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_embedding()
    sys.exit(0 if success else 1)
