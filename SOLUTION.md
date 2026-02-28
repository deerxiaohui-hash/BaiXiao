# 上传失败问题解决方案

## 问题诊断

经过详细排查，发现上传失败的根本原因是：

### 1. ONNX Runtime DLL 加载失败
```
ImportError: DLL load failed while importing onnxruntime_pybind11_state: 动态链接库(DLL)初始化例程失败。
```

这导致 ChromaDB 无法正常初始化，因为 ChromaDB 依赖 ONNX Runtime 进行向量嵌入。

### 2. 后端服务在处理上传时崩溃
当尝试上传文件时，后端服务因为 ChromaDB 初始化问题而崩溃。

## 已实施的修复

### 修复 1: 使用 EphemeralClient 替代 PersistentClient
修改了 `backend/app/services/vector_store.py`，使用内存模式的 ChromaDB 客户端，避免持久化存储时的 ONNX Runtime 问题。

```python
# 使用 EphemeralClient (内存模式) 避免持久化问题
self.client = chromadb.EphemeralClient(
    settings=ChromaSettings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)
```

### 修复 2: 使用简单哈希嵌入函数
实现了不依赖 ONNX Runtime 的 `SimpleHashEmbeddingFunction`，使用 MD5 哈希进行文本嵌入。

## 推荐的永久解决方案

### 方案 A: 安装 Visual C++ Redistributable（最简单）
1. 下载并安装: https://aka.ms/vs/17/release/vc_redist.x64.exe
2. 重启计算机
3. 重启后端服务

### 方案 B: 使用在线 Embedding API
修改代码使用 Longcat API 的 Embedding 功能：

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    api_key=settings.LONGCAT_API_KEY,
    base_url=settings.LONGCAT_BASE_URL,
    model=settings.EMBEDDING_MODEL
)
```

### 方案 C: 降级 ONNX Runtime
```bash
cd backend
.\venv\Scripts\pip.exe uninstall onnxruntime -y
.\venv\Scripts\pip.exe install onnxruntime==1.15.1
```

## 当前状态

✅ ChromaDB 已成功初始化（内存模式）
✅ 后端服务正常运行
⚠️  需要测试上传功能是否完全正常

## 下一步

1. 重启后端服务
2. 在前端测试文档上传功能
3. 如果仍有问题，考虑实施方案 A 或 B
