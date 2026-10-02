# 百晓 BaiXiao

企业内部智能问答知识库 —— 基于 RAG (检索增强生成) 技术的企业制度文档智能问答系统。

## 功能特性

- 📁 **文档上传**: 支持 PDF、Word 等企业制度文件上传
- 🤖 **智能问答**: 通过自然语言提问，获取精准答案
- 🔍 **引用溯源**: 答案自动标注原文引用来源
- 💼 **企业应用**: 适用于 HR 制度、财务流程、行政规范等场景

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- Longcat API Key

### 安装步骤

#### 1. 后端配置

```bash
cd backend

# 创建虚拟环境 (如已有可跳过)
python -m venv venv
.\venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 Longcat API Key
```

#### 2. 前端配置

```bash
cd frontend

# 安装依赖
npm install
```

### 本地开发启动

#### 方式 1: 分别启动

**启动后端:**
```bash
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

**启动前端 (新终端):**
```bash
cd frontend
npm run dev
```

访问 `http://localhost:5001` 即可使用。

#### 方式 2: 一键启动 (带 Cloudflare Tunnel)

如需对外暴露供他人访问，使用一键启动脚本:

```bash
.\start-with-tunnel.bat
```

**注意**: 使用前需配置 Cloudflare Tunnel，详见 [Cloudflare 部署指南](./CLOUDFLARE_SETUP.md)

---

## 公网部署 (Cloudflare Tunnel)

### 快速部署步骤

#### 1. 安装 cloudflared

**方法 A - 直接下载:**
```
访问：https://github.com/cloudflare/cloudflared/releases/latest
下载：cloudflared-windows-amd64.exe
重命名：cloudflared.exe
放置到：C:\Windows 或 项目 tools 目录
```

**方法 B - 使用 winget:**
```powershell
winget install cloudflare.cloudflared
```

#### 2. 创建 Tunnel

访问 Cloudflare Dashboard:
```
https://dash.cloudflare.com/?to=/:account/zero-trust/tunnels
```

创建 Tunnel 并获取 credentials 文件。

#### 3. 配置项目

编辑 `cloudflared-config.yml`:
```yaml
tunnel: knowledge-qa-tunnel
credentials-file: C:\Users\<你的用户名>\.cloudflared\<TUNNEL_ID>.json

ingress:
  - hostname: knowledge-qa.yourdomain.com
    service: http://localhost:5001
  
  - hostname: api-knowledge-qa.yourdomain.com
    service: http://localhost:8001
  
  - service: http_status:404
```

#### 4. 启动服务

```bash
.\start-with-tunnel.bat
```

访问 `https://knowledge-qa.yourdomain.com` 即可使用。

详细配置请参考：[Cloudflare Tunnel 部署指南](./CLOUDFLARE_SETUP.md)

---

## 项目结构

```
one/
├── backend/                    # 后端服务 (FastAPI + LangChain)
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── services/          # RAG 核心服务
│   │   ├── models/            # 数据模型
│   │   └── main.py            # FastAPI 入口
│   ├── data/                  # 文档和向量数据库存储
│   ├── requirements.txt
│   └── .env
│
├── frontend/                   # 前端应用 (Vue 3 + Vite)
│   ├── src/
│   │   ├── views/             # 页面组件
│   │   ├── components/        # 通用组件
│   │   └── services/          # API 服务
│   ├── vite.config.js
│   └── package.json
│
├── cloudflared-config.yml      # Cloudflare Tunnel 配置
├── start-with-tunnel.bat       # 一键启动脚本
├── CLOUDFLARE_SETUP.md         # Cloudflare 部署指南
└── README.md                   # 项目说明
```

## API 接口

### 上传文档
```http
POST /api/upload
Content-Type: multipart/form-data

参数：file (PDF/Word 文件)
```

### 智能问答
```http
POST /api/chat
Content-Type: application/json

{
  "question": "今年我司的带薪年假有多少天？"
}
```

### 文档列表
```http
GET /api/documents
```

### 删除文档
```http
DELETE /api/documents/{id}
```

## 技术栈

**后端:**
- FastAPI - 高性能 Web 框架
- LangChain - RAG 框架
- ChromaDB - 向量数据库
- PyPDF2 / python-docx - 文档解析

**前端:**
- Vue 3 - 渐进式框架
- Vite - 下一代构建工具
- TailwindCSS - 原子化 CSS
- Axios - HTTP 客户端

**部署:**
- Cloudflare Tunnel - 内网穿透
- Zero Trust - 访问控制 (可选)

## 配置说明

### 环境变量 (.env)

```env
# Longcat API 配置
LONGCAT_API_KEY=your_api_key_here
LONGCAT_BASE_URL=https://api.longcat.ai/v1
LONGCAT_MODEL=longcat-chat

# 向量模型配置
EMBEDDING_MODEL=text-embedding-ada-002
```

### Vite 配置 (vite.config.js)

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',  // 允许外部访问 (Cloudflare Tunnel 必需)
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

## 常见问题

### Q: 为什么需要监听 0.0.0.0？

A: Cloudflare Tunnel 通过虚拟网络接口转发流量。如果服务只监听 `127.0.0.1` (localhost)，Tunnel 将无法访问服务。必须监听 `0.0.0.0` 以允许所有网络接口访问。

### Q: 公网访问速度慢？

A: 检查:
1. 本地网络连接
2. Cloudflare Tunnel 状态
3. 考虑使用 Cloudflare Zero Trust 付费套餐

### Q: 如何限制访问权限？

A: 在 Cloudflare Dashboard → Access → Applications 中配置访问策略:
- 邮箱白名单
- 需要登录
- IP 限制

### Q: 文件上传失败？

A: 检查:
1. 文件大小是否超过限制 (建议 < 10MB)
2. 文件格式是否支持 (PDF, DOCX)
3. 后端日志查看具体错误

## 安全建议

1. **API Key 保护**: 不要将 `.env` 文件提交到代码仓库
2. **访问控制**: 配置 Cloudflare Access 限制访问
3. **文件限制**: 限制上传文件大小和类型
4. **日志记录**: 启用操作日志便于审计

## 成本说明

**Cloudflare 免费套餐包含:**
- ✅ 1 个域名
- ✅ 无限流量
- ✅ 基础 Tunnel 功能
- ✅ SSL/TLS 证书

**付费升级 (可选):**
- Zero Trust 团队功能 ($7/用户/月)
- 高级路由规则

## 开发计划

- [ ] 支持更多文档格式 (Excel, PPT)
- [ ] 批量上传功能
- [ ] 对话历史记录
- [ ] 多租户支持
- [ ] 答案反馈机制
- [ ] 管理后台

## 相关资源

- [Cloudflare Tunnel 官方文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [LangChain 文档](https://python.langchain.com/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Vue 3 文档](https://vuejs.org/)

## License

MIT

---

**注意**: 本项目仅供学习和内部使用。生产环境部署请做好安全措施和权限控制。
