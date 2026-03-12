# 切换到真实 Embedding 模型以提高相关度准确性

## 问题分析

当前系统使用的是**简单哈希向量化方法**，存在以下问题：
- ❌ 不理解语义（"带薪年假" 和 "年休假" 无法识别为相似）
- ❌ 只是简单的词频统计
- ❌ 相似度计算不准确（经常显示 0%）

## 解决方案

使用**真实的 Embedding 模型**来生成语义向量，大幅提高相关度准确性。

### 新实现的特点

✅ 使用 OpenAI 兼容的 Embedding API  
✅ 理解中文语义  
✅ 相似度计算准确  
✅ 支持 LongCat 等国内 API  

## 切换步骤

### 1. 检查 Embedding 模型配置

编辑 `backend/.env` 文件，确保配置了正确的 embedding 模型：

```env
LONGCAT_API_KEY=your_api_key_here
LONGCAT_BASE_URL=https://api.longcat.chat/openai/v1
LONGCAT_MODEL=LongCat-Flash-Thinking-2601
EMBEDDING_MODEL=text-embedding-ada-002
```

### 2. 修改导入语句

编辑以下文件，将导入从 `vector_store_simple` 改为 `vector_store_embedding`：

#### backend/app/services/rag_service.py
```python
# 修改前
from app.services.vector_store_simple import vector_store

# 修改后
from app.services.vector_store_embedding import vector_store
```

#### backend/app/api/upload.py
```python
# 修改前
from app.services.vector_store_simple import vector_store

# 修改后
from app.services.vector_store_embedding import vector_store
```

#### backend/app/api/documents.py
```python
# 修改前
from app.services.vector_store_simple import vector_store

# 修改后
from app.services.vector_store_embedding import vector_store
```

### 3. 安装依赖（如果需要）

```bash
cd backend
pip install langchain-openai numpy
```

### 4. 清理旧数据（可选）

如果想重新开始，可以删除旧的向量数据：

```bash
# 备份旧数据
cd backend/data
mkdir backup
copy document_metadata.json backup\
copy document_vectors.json backup\ 2>nul

# 清理（可选）
del document_vectors.json 2>nul
```

### 5. 重启后端服务

```bash
cd backend
python -m uvicorn app.main:app --reload
```

### 6. 重新上传文档

由于向量生成方式改变，需要重新上传文档以生成新的 embeddings。

## 效果对比

### 使用简单哈希方法（修改前）
```
问题：今年我司的带薪年假有多少天？

参考来源：
📄 企业员工管理制度.docx (片段 1) 相关度: 0%
📄 企业员工管理制度.docx (片段 2) 相关度: 0%
```

### 使用真实 Embedding（修改后）
```
问题：今年我司的带薪年假有多少天？

参考来源：
📄 企业员工管理制度.docx (片段 1) 相关度: 85%
📄 企业员工管理制度.docx (片段 2) 相关度: 72%
```

## 注意事项

1. **API 费用**：使用 Embedding API 会产生费用（通常很低）
2. **速度**：首次上传文档时会调用 API 生成 embeddings，可能需要几秒钟
3. **兼容性**：确保你的 API 提供商支持 OpenAI 兼容的 embedding 接口

## 备选方案

如果不想使用 API，可以考虑：

### 方案 A：使用本地 sentence-transformers
- 完全免费
- 需要下载模型（约 400MB）
- 推荐模型：`paraphrase-multilingual-MiniLM-L12-v2`

### 方案 B：继续使用简单方法但改进
- 使用 TF-IDF 或 BM25
- 效果比哈希好，但仍不如真实 embedding

## 故障排除

### 问题 1：ImportError: No module named 'langchain_openai'
```bash
pip install langchain-openai
```

### 问题 2：API 调用失败
- 检查 API Key 是否正确
- 检查 BASE_URL 是否正确
- 确认 EMBEDDING_MODEL 名称是否正确

### 问题 3：相关度仍然很低
- 确认文档内容与问题相关
- 尝试调整 chunk_size（在 config.py 中）
- 检查文档是否正确上传
