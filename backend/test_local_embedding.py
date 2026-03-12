"""
测试本地 Embedding 模型
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_local_embedding():
    print("=" * 60)
    print("测试本地 Embedding 模型")
    print("=" * 60)
    
    try:
        print("\n正在加载 sentence-transformers...")
        from sentence_transformers import SentenceTransformer
        
        print("正在加载模型 'paraphrase-multilingual-MiniLM-L12-v2'...")
        print("(首次运行会自动下载模型，约 400MB，请耐心等待)")
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        print("\n✅ 模型加载成功!")
        
        # 测试中文文本
        print("\n正在测试中文文本 embedding...")
        test_texts = [
            "今年我司的带薪年假有多少天？",
            "员工出差需要提前填写申请表",
            "带薪年假根据工作年限确定"
        ]
        
        vectors = model.encode(test_texts, show_progress_bar=True)
        
        print(f"\n✅ 成功生成 {len(vectors)} 个向量")
        print(f"  向量维度: {vectors[0].shape}")
        print(f"  向量类型: {type(vectors[0])}")
        
        # 测试相似度
        print("\n正在测试相似度计算...")
        import numpy as np
        
        query = "年假有几天"
        query_vector = model.encode(query)
        
        print(f"\n查询: {query}")
        print("\n相似度排名:")
        for i, text in enumerate(test_texts):
            similarity = np.dot(query_vector, vectors[i]) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vectors[i])
            )
            print(f"  {i+1}. [{similarity:.2%}] {text}")
        
        print("\n✅ 所有测试通过!")
        return True
        
    except ImportError as e:
        print(f"\n❌ 错误: 缺少依赖")
        print(f"  {e}")
        print("\n请运行以下命令安装:")
        print("  pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_local_embedding()
    sys.exit(0 if success else 1)
