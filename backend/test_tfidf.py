"""
测试 TF-IDF 向量存储
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_tfidf():
    print("=" * 60)
    print("测试 TF-IDF 向量存储")
    print("=" * 60)
    
    try:
        print("\n正在导入依赖...")
        import jieba
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np
        
        print("✅ 依赖导入成功")
        
        # 测试中文分词
        print("\n正在测试中文分词...")
        test_text = "今年我司的带薪年假有多少天？"
        words = list(jieba.cut(test_text))
        print(f"  原文: {test_text}")
        print(f"  分词: {' / '.join(words)}")
        
        # 测试 TF-IDF
        print("\n正在测试 TF-IDF...")
        texts = [
            "今年我司的带薪年假有多少天？",
            "员工出差需要提前填写申请表",
            "带薪年假根据工作年限确定",
            "年假应在当年内使用完毕"
        ]
        
        vectorizer = TfidfVectorizer(
            tokenizer=lambda x: list(jieba.cut(x)),
            max_features=1000,
            ngram_range=(1, 2)
        )
        
        vectors = vectorizer.fit_transform(texts).toarray()
        print(f"✅ TF-IDF 向量生成成功")
        print(f"  文档数量: {len(texts)}")
        print(f"  向量维度: {vectors.shape[1]}")
        
        # 测试相似度
        print("\n正在测试相似度计算...")
        query = "年假有几天"
        query_vector = vectorizer.transform([query]).toarray()[0]
        
        print(f"\n查询: {query}")
        print("\n相似度排名:")
        
        similarities = []
        for i, text in enumerate(texts):
            similarity = np.dot(query_vector, vectors[i]) / (
                np.linalg.norm(query_vector) * np.linalg.norm(vectors[i]) + 1e-10
            )
            similarities.append((similarity, text))
        
        similarities.sort(reverse=True)
        for i, (sim, text) in enumerate(similarities, 1):
            print(f"  {i}. [{sim:.2%}] {text}")
        
        print("\n✅ 所有测试通过!")
        print("\n说明:")
        print("  - TF-IDF 方法比简单哈希好很多")
        print("  - 使用 jieba 进行中文分词")
        print("  - 相关度计算更准确")
        print("  - 不需要额外的大型模型")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_tfidf()
    sys.exit(0 if success else 1)
