# ✅ 502 Bad Gateway 错误已解决!

## 🔍 问题原因

**502 Bad Gateway - Unable to reach the origin service**

这个错误的原因是:

1. **前端服务已停止**: Vite 开发服务器意外停止运行
2. **IPv6/IPv4 问题**: Cloudflare Tunnel 尝试连接 IPv6 地址 `[::1]:5001`，但服务只监听 IPv4

---

## ✅ 解决方案

### 1. 重新启动前端服务
```bash
cd frontend
npm run dev
```
✅ 前端已在 http://localhost:5001 正常运行

### 2. 使用明确的 IPv4 地址启动 Tunnel
```bash
.\tools\cloudflared.exe tunnel --url http://127.0.0.1:5001
```
✅ 明确指定使用 `127.0.0.1` (IPv4) 而不是 `localhost` (可能解析为 IPv6)

---

## 📊 当前服务状态

| 服务 | 状态 | 地址 |
|------|------|------|
| **后端 API** | ✅ 运行中 | http://0.0.0.0:8001 |
| **前端** | ✅ 运行中 | http://localhost:5001 |
| **Cloudflare Tunnel** | ✅ 运行中 | 见下方新 URL |

---

## 🌐 新的访问地址

### ✨ 公网访问 (任何设备)
```
https://felt-camps-horse-non.trycloudflare.com
```

### 🏠 本地访问
- **前端**: http://localhost:5001
- **后端**: http://localhost:8001
- **局域网**: http://192.168.10.52:5001

---

## 💡 技术要点

### 为什么使用 127.0.0.1 而不是 localhost?

在 Windows 上，`localhost` 可能解析为:
- `127.0.0.1` (IPv4)
- `::1` (IPv6)

**问题**:
- Vite 开发服务器可能只监听 IPv4
- Cloudflare Tunnel 使用 `localhost` 可能解析为 IPv6
- 导致连接失败: `dial tcp [::1]:5001: connectex: No connection`

**解决方案**:
- 明确使用 `127.0.0.1` (IPv4)
- 或者修改 Vite 配置同时监听 IPv4 和 IPv6

### vite.config.js 配置

```javascript
export default defineConfig({
  plugins: [vue()],
  server: {
    host: '0.0.0.0',  // 监听所有网络接口 (包括 IPv4)
    port: 5001,
    allowedHosts: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true
      }
    }
  }
})
```

---

## 🔄 问题排查流程

### 遇到 502 Bad Gateway 时的检查步骤:

1. **检查前端服务**
   ```powershell
   # 查看端口 5001 是否有服务监听
   netstat -ano | findstr :5001
   ```

2. **检查后端服务**
   ```powershell
   # 查看端口 8001 是否有服务监听
   netstat -ano | findstr :8001
   ```

3. **检查 Tunnel 日志**
   - 查看 Cloudflare Tunnel 终端输出
   - 寻找 `ERR` 开头的错误信息
   - 确认连接的目标地址

4. **重启服务**
   ```powershell
   # 停止所有服务
   Ctrl+C (在各个终端)
   
   # 重启后端
   cd backend
   .\venv\Scripts\activate
   uvicorn app.main:app --host 0.0.0.0 --port 8001
   
   # 重启前端
   cd frontend
   npm run dev
   
   # 重启 Tunnel (使用 IPv4)
   .\tools\cloudflared.exe tunnel --url http://127.0.0.1:5001
   ```

---

## 📝 避免此问题的最佳实践

### 1. 使用明确的 IP 地址
```bash
# ✅ 推荐：使用明确的 IPv4 地址
.\tools\cloudflared.exe tunnel --url http://127.0.0.1:5001

# ⚠️ 可能有问题：使用 localhost
.\tools\cloudflared.exe tunnel --url http://localhost:5001
```

### 2. 配置服务监听所有接口
```javascript
// vite.config.js
server: {
  host: '0.0.0.0',  // 监听所有 IPv4 接口
  // 或者
  host: '::',       // 监听所有 IPv6 接口
}
```

### 3. 定期检查服务状态
```powershell
# 查看 Node.js 进程
Get-Process node

# 查看 Python 进程
Get-Process python

# 查看端口占用
netstat -ano | findstr :5001
```

---

## 🧪 验证连接

### 1. 本地测试
```
访问：http://localhost:5001
预期：页面正常加载
```

### 2. 公网测试
```
访问：https://felt-camps-horse-non.trycloudflare.com
预期：页面正常加载，无 502 错误
```

### 3. 功能测试
- ✅ 上传文件
- ✅ 智能问答
- ✅ 查看引用

---

## ⚠️ 注意事项

### 服务停止
- 前端服务可能因为内存不足、错误等原因意外停止
- 定期检查服务是否仍在运行
- 使用脚本或工具监控服务状态

### URL 变更
- 每次重启 Tunnel 都会生成新的 URL
- 本次 URL: `https://felt-camps-horse-non.trycloudflare.com`
- 下次重启会变化

### 端口冲突
- 如果端口 5001 被占用，Vite 会自动使用其他端口
- 检查终端输出确认实际使用的端口

---

## ✅ 当前状态总结

- ✅ 后端服务正常运行在端口 8001
- ✅ 前端服务正常运行在端口 5001
- ✅ Cloudflare Tunnel 使用 IPv4 连接到前端
- ✅ 新的公网 URL 已生成
- ✅ 502 Bad Gateway 错误已解决

**当前公网访问地址**: 
```
https://felt-camps-horse-non.trycloudflare.com
```

---

**问题已完全解决！现在可以正常访问了!** 🎉
