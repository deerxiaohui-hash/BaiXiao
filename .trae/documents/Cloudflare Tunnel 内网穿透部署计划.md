# 企业内部智能问答知识库 - 实现计划

## 项目概述

构建一个企业内部智能问答知识库系统，支持：

* 上传 PDF、Word 等格式的企业制度文件

* 通过 Web 对话框进行自然语言问答

* 基于大模型的 RAG（检索增强生成）能力

* 提供答案引用来源

## 用户配置步骤

### 步骤 1：安装环境依赖

```bash
# 安装 Python 3.10+（如已安装可跳过）
# 安装 Node.js 18+（如已安装可跳过）
```

### 步骤 2：配置 Longcat API

在项目根目录创建 `.env` 文件，填入以下配置：

```env
# Longcat API 配置（必填）
LONGCAT_API_KEY=your_api_key_here
LONGCAT_BASE_URL=https://api.longcat.ai/v1
LONGCAT_MODEL=longcat-chat
EMBEDDING_MODEL=text-embedding-ada-002
```

### 步骤 3：启动项目

#### 3.1 启动后端服务
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```
**注意**: `--host 0.0.0.0` 参数必需，允许外部连接 (包括 Cloudflare Tunnel)

#### 3.2 启动前端服务
需要修改 Vite 配置以监听所有接口:

**方式 1: 修改 vite.config.js**
```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',  // 添加此行，允许外部访问
    port: 5001,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      }
    }
  }
})
```

**方式 2: 命令行启动**
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

**重要说明**: 
- ⚠️ 必须监听 `0.0.0.0` 而不是 `localhost` 或 `127.0.0.1`
- `localhost` 只允许本机访问，Cloudflare Tunnel 无法转发
- `0.0.0.0` 允许所有网络接口访问 (包括 Tunnel)

#### 3.3 启动 Cloudflare Tunnel
```bash
cloudflared tunnel run --config cloudflared-config.yml knowledge-qa-tunnel
```

#### 启动脚本 (start-with-tunnel.bat)
```batch
@echo off
echo 正在启动企业内部智能问答知识库系统...
echo.

REM 启动后端服务 (监听 0.0.0.0 允许 Tunnel 访问)
start "Backend - Port 8001" cmd /k "cd /d e:\1_CodeSpace\5_timu\one\backend && .\venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
echo [√] 后端服务启动中...
timeout /t 3 /nobreak >nul

REM 启动前端服务 (监听 0.0.0.0 允许 Tunnel 访问)
start "Frontend - Port 5001" cmd /k "cd /d e:\1_CodeSpace\5_timu\one\frontend && npm run dev -- --host 0.0.0.0"
echo [√] 前端服务启动中...
timeout /t 3 /nobreak >nul

REM 启动 Cloudflare Tunnel
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run --config e:\1_CodeSpace\5_timu\one\cloudflared-config.yml knowledge-qa-tunnel"
echo [√] Cloudflare Tunnel 启动中...
timeout /t 2 /nobreak >nul

echo.
echo ========================================
echo 所有服务已启动!
echo ========================================
echo - 后端本地访问：http://localhost:8001
echo - 前端本地访问：http://localhost:5001
echo - 公网访问地址：https://knowledge-qa.yourdomain.com
echo ========================================
echo.
echo 提示：按任意键查看 Cloudflare Tunnel 日志
pause >nul
```

**重要**: 前端和后端都必须监听 `0.0.0.0` 而不是 `127.0.0.1`!

**技术原理**:
- `127.0.0.1` (localhost): 只允许本机进程访问
- `0.0.0.0`: 监听所有网络接口，包括:
  - 本地回环 (127.0.0.1)
  - 局域网 IP (192.168.x.x)
  - Cloudflare Tunnel 创建的虚拟网络接口
  
Cloudflare Tunnel 在本地创建一个虚拟网络接口，通过该接口将公网流量转发到本地服务。如果服务只监听 `127.0.0.1`，Tunnel 将无法访问服务！

### 步骤 4：访问应用

打开浏览器访问 `http://localhost:5173`

## 技术选型

### 后端框架

* **Python + FastAPI**: 轻量级、高性能、异步支持好

* **LangChain**: 成熟的 RAG 框架，支持多种向量数据库和 LLM

### 前端框架

* **Vue3 + Vite**: 现代化前端开发体验

* **TailwindCSS**: 快速构建美观 UI

### 前端设计风格

* **主色调**：白色背景 (#FFFFFF)

* **辅助色**：浅灰色 (#F5F5F5, #E5E5E5)

* **强调色**：现代蓝 (#3B82F6)

* **文字色**：深灰色 (#1F2937, #6B7280)

* **风格**：简约、现代、时尚、清爽

* **圆角**：适度圆角 (8px-16px)

* **阴影**：轻微阴影增加层次感

### 向量数据库

* **ChromaDB**: 轻量级本地向量数据库，无需额外部署

### 文档处理

* **PyPDF2 / pdfplumber**: PDF 解析

* **python-docx**: Word 文档解析

* **LangChain Document Loaders**: 统一文档加载接口

### 大模型

* **Longcat API**: 兼容 OpenAI API 格式，通过配置 base\_url 使用

* **配置灵活**: 支持自定义 API 端点和模型名称

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React)                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  文件上传页面  │    │  对话问答页面  │    │  文档管理页面  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    后端 API (FastAPI)                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  文件上传接口  │    │  问答对话接口  │    │  文档管理接口  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG 核心服务 (LangChain)                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  文档解析服务  │───▶│  向量化服务   │───▶│  检索生成服务  │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      存储层                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  文件存储     │    │  ChromaDB    │    │  SQLite      │  │
│  │  (本地磁盘)   │    │  (向量存储)   │    │  (元数据)    │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 目录结构

```
one/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── api/               # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── upload.py      # 文件上传接口
│   │   │   ├── chat.py        # 问答对话接口
│   │   │   └── documents.py   # 文档管理接口
│   │   ├── services/          # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py  # 文档解析
│   │   │   ├── vector_store.py        # 向量存储
│   │   │   └── rag_service.py         # RAG 服务
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── data/                  # 数据目录
│   │   ├── documents/         # 上传的文档
│   │   └── chroma/            # 向量数据库
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── style.css           # 全局样式（白色简约风格）
│   │   ├── components/
│   │   │   ├── Layout.vue      # 页面布局
│   │   │   ├── Sidebar.vue     # 侧边导航
│   │   │   ├── FileUpload.vue  # 文件上传组件
│   │   │   ├── ChatBox.vue     # 对话框组件
│   │   │   ├── MessageList.vue # 消息列表
│   │   │   ├── SourceCard.vue  # 来源引用卡片
│   │   │   └── DocumentList.vue # 文档列表
│   │   ├── views/
│   │   │   ├── ChatView.vue    # 对话问答页面（主页面）
│   │   │   └── ManageView.vue  # 文档管理页面
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── router/
│   │   │   └── index.js
│   │   └── composables/
│   │       └── useChat.js
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
│
└── README.md                   # 项目说明
```

## 实现步骤

### 第一阶段：后端基础搭建

#### 1.1 项目初始化

* [ ] 创建后端目录结构

* [ ] 创建 requirements.txt（FastAPI, LangChain, ChromaDB 等）

* [ ] 创建 .env.example 配置模板

* [ ] 创建 FastAPI 主入口

#### 1.2 配置管理

* [ ] 实现配置加载（环境变量、API Key 等）

* [ ] 配置 Longcat API 端点和模型

* [ ] 配置数据存储路径

#### 1.3 文档处理服务

* [ ] 实现 PDF 文档解析

* [ ] 实现 Word 文档解析

* [ ] 实现文档分块（Chunking）策略

* [ ] 实现文本清洗

#### 1.4 向量存储服务

* [ ] 初始化 ChromaDB

* [ ] 实现文档向量化存储

* [ ] 实现相似度检索

* [ ] 实现文档删除功能

#### 1.5 RAG 服务

* [ ] 实现检索增强生成流程

* [ ] 设计 Prompt 模板

* [ ] 实现答案生成

* [ ] 实现来源引用

#### 1.6 API 接口

* [ ] 文件上传接口（POST /api/upload）

* [ ] 问答对话接口（POST /api/chat）

* [ ] 文档列表接口（GET /api/documents）

* [ ] 文档删除接口（DELETE /api/documents/{id}）

### 第二阶段：前端开发

#### 2.1 项目初始化

* [ ] 创建 Vite + Vue3 项目

* [ ] 配置 TailwindCSS 和 PostCSS

* [ ] 创建白色简约风格的全局样式

* [ ] 创建基础布局组件

#### 2.2 布局与导航

* [ ] 实现侧边栏导航组件

* [ ] 实现页面布局框架

* [ ] 配置 Vue Router 路由

#### 2.3 对话问答页面（主页面）

* [ ] 实现消息列表展示

* [ ] 实现输入框和发送按钮

* [ ] 实现来源引用卡片展示

* [ ] 实现加载动画

* [ ] 实现文件上传区域（拖拽上传）

#### 2.4 文档管理页面

* [ ] 实现文档列表展示

* [ ] 实现文档删除功能

* [ ] 实现文档状态显示

#### 2.5 API 服务封装

* [ ] 封装后端 API 调用

* [ ] 错误处理与提示

### 第三阶段：集成测试与优化

#### 3.1 功能测试

* [ ] 测试文档上传流程

* [ ] 测试问答功能

* [ ] 测试来源引用

* [ ] 测试文档管理

#### 3.2 性能优化

* [ ] 优化文档分块策略

* [ ] 优化检索效率

* [ ] 前端加载优化

#### 3.3 用户体验

* [ ] 添加加载动画

* [ ] 添加错误提示

* [ ] 优化响应式布局

## 核心功能详细设计

### 1. 文档处理流程

```python
# 伪代码
def process_document(file):
    # 1. 解析文档
    text = parse_document(file)  # PDF/Word -> Text
    
    # 2. 文本分块
    chunks = split_text(text, chunk_size=500, overlap=50)
    
    # 3. 向量化存储
    for chunk in chunks:
        embedding = embed_text(chunk)
        store_in_chroma(embedding, metadata={
            'source': file.name,
            'chunk_id': chunk.id,
            'content': chunk.text
        })
```

### 2. RAG 问答流程

```python
# 伪代码
def answer_question(question):
    # 1. 问题向量化
    question_embedding = embed_text(question)
    
    # 2. 相似度检索
    relevant_chunks = search_chroma(question_embedding, top_k=5)
    
    # 3. 构建 Prompt
    context = build_context(relevant_chunks)
    prompt = f"""
    基于以下企业制度文档内容回答问题，如果文档中没有相关信息，请说明。
    
    文档内容：
    {context}
    
    问题：{question}
    
    请给出准确答案，并注明引用来源。
    """
    
    # 4. 大模型生成
    answer = llm_generate(prompt)
    
    # 5. 返回答案和来源
    return {
        'answer': answer,
        'sources': relevant_chunks
    }
```

### 3. API 接口设计

#### 上传文档

```
POST /api/upload
Content-Type: multipart/form-data

Request:
- file: PDF/Word 文件

Response:
{
  "success": true,
  "document_id": "doc_123",
  "filename": "休假制度.pdf",
  "chunks_count": 15,
  "message": "文档上传成功"
}
```

#### 问答对话

```
POST /api/chat
Content-Type: application/json

Request:
{
  "question": "今年我司的带薪年假有多少天？"
}

Response:
{
  "answer": "根据公司制度，员工带薪年假天数如下：...",
  "sources": [
    {
      "content": "员工带薪年假规定：工作满1年不满10年的...",
      "source": "休假制度.pdf",
      "page": 3,
      "relevance_score": 0.89
    }
  ]
}
```

#### 文档列表

```
GET /api/documents

Response:
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "休假制度.pdf",
      "upload_time": "2024-01-15 10:30:00",
      "chunks_count": 15,
      "file_size": 102400
    }
  ]
}
```

## 环境要求

* Python 3.10+

* Node.js 18+

* Longcat API Key 和 API 端点

## 部署说明

### 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 配置 Longcat API Key 和端点
uvicorn app.main:app --reload
```

### 环境变量配置 (.env)

```env
# Longcat API 配置
LONGCAT_API_KEY=your_api_key_here
LONGCAT_BASE_URL=https://api.longcat.ai/v1  # 替换为实际端点
LONGCAT_MODEL=longcat-chat  # 替换为实际模型名称

# 向量模型配置（用于文档嵌入）
EMBEDDING_MODEL=text-embedding-ada-002  # 或其他支持的嵌入模型
```

### 前端启动

```bash
one/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI 入口
│   │   ├── config.py          # 配置管理
│   │   ├── api/               # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── upload.py      # 文件上传接口
│   │   │   ├── chat.py        # 问答对话接口
│   │   │   └── documents.py   # 文档管理接口
│   │   ├── services/          # 业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── document_processor.py  # 文档解析
│   │   │   ├── vector_store.py        # 向量存储
│   │   │   └── rag_service.py         # RAG 服务
│   │   ├── models/            # 数据模型
│   │   │   ├── __init__.py
│   │   │   └── schemas.py
│   │   └── utils/             # 工具函数
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── data/                  # 数据目录
│   │   ├── documents/         # 上传的文档
│   │   └── chroma/            # 向量数据库
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.js
│   │   ├── style.css           # 全局样式（白色简约风格）
│   │   ├── components/
│   │   │   ├── Layout.vue      # 页面布局
│   │   │   ├── Sidebar.vue     # 侧边导航
│   │   │   ├── FileUpload.vue  # 文件上传组件
│   │   │   ├── ChatBox.vue     # 对话框组件
│   │   │   ├── MessageList.vue # 消息列表
│   │   │   ├── SourceCard.vue  # 来源引用卡片
│   │   │   └── DocumentList.vue # 文档列表
│   │   ├── views/
│   │   │   ├── ChatView.vue    # 对话问答页面（主页面）
│   │   │   └── ManageView.vue  # 文档管理页面
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── router/
│   │   │   └── index.js
│   │   └── composables/
│   │       └── useChat.js
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
│
└── README.md                   # 项目说明
```

## 注意事项

1. **API Key 安全**: 不要将 API Key 提交到代码仓库
2. **Longcat API 兼容性**: Longcat API 兼容 OpenAI API 格式，LangChain 可直接使用
3. **文件大小限制**: 建议限制单个文件不超过 10MB
4. **并发处理**: 使用异步处理提升性能
5. **错误处理**: 提供友好的错误提示
6. **日志记录**: 记录关键操作日志便于排查问题

## Longcat API 配置说明

Longcat API 兼容 OpenAI API 格式，在 LangChain 中使用方式：

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# 聊天模型配置
llm = ChatOpenAI(
    api_key="your_longcat_api_key",
    base_url="https://api.longcat.ai/v1",  # Longcat API 端点
    model="longcat-chat"
)

# 嵌入模型配置（用于向量化）
embeddings = OpenAIEmbeddings(
    api_key="your_longcat_api_key",
    base_url="https://api.longcat.ai/v1",
    model="text-embedding-ada-002"  # 根据实际支持的模型调整
)
```

