# Cloudflare Tunnel 部署 - 快速使用指南

## ✅ 已完成的配置

以下文件已为你创建并配置好:

1. **vite.config.js** - 已添加 `host: '0.0.0.0'` 配置
2. **cloudflared-config.yml** - Tunnel 配置文件模板
3. **start-with-tunnel.bat** - 一键启动脚本
4. **CLOUDFLARE_SETUP.md** - 详细安装配置指南
5. **README.md** - 项目说明文档

---

## 🚀 快速开始 (3 步部署)

### 步骤 1: 安装 cloudflared

**最简单方式** (使用 winget):
```powershell
winget install cloudflare.cloudflared
```

**或手动下载**:
1. 访问：https://github.com/cloudflare/cloudflared/releases/latest
2. 下载 `cloudflared-windows-amd64.exe`
3. 重命名为 `cloudflared.exe`
4. 放到 `C:\Windows` 或项目 `tools` 目录

**验证安装**:
```powershell
cloudflared --version
```

---

### 步骤 2: 创建 Cloudflare Tunnel

1. **访问 Cloudflare Zero Trust Dashboard**
   ```
   https://dash.cloudflare.com/?to=/:account/zero-trust/tunnels
   ```

2. **创建 Tunnel**
   - 点击 **Create a tunnel**
   - 选择 **Cloudflared**
   - 名称：`knowledge-qa-tunnel`
   - 点击 **Add tunnel**

3. **保存 Credentials**
   - 选择 **Windows** 作为操作系统
   - 复制 credentials file 内容
   - 保存到：`C:\Users\<你的用户名>\.cloudflared\<TUNNEL_ID>.json`

4. **配置 Public Hostname**
   - **Subdomain**: `knowledge-qa`
   - **Domain**: 选择你的域名
   - **Service**: `http://localhost:5001`
   - 点击 **Save tunnel**

---

### 步骤 3: 配置并启动

1. **编辑 cloudflared-config.yml**
   
   打开 `e:\1_CodeSpace\5_timu\one\cloudflared-config.yml`,修改:
   
   ```yaml
   tunnel: knowledge-qa-tunnel
   
   # 替换为你的实际路径和 Tunnel ID
   credentials-file: C:\Users\<你的用户名>\.cloudflared\<TUNNEL_ID>.json
   
   ingress:
     # 替换为你的域名
     - hostname: knowledge-qa.yourdomain.com
       service: http://localhost:5001
     
     - hostname: api-knowledge-qa.yourdomain.com
       service: http://localhost:8001
     
     - service: http_status:404
   ```

2. **运行一键启动脚本**
   ```powershell
   cd e:\1_CodeSpace\5_timu\one
   .\start-with-tunnel.bat
   ```

3. **访问应用**
   - 本地：http://localhost:5001
   - 公网：https://knowledge-qa.yourdomain.com

---

## 📋 关键配置说明

### 为什么必须监听 0.0.0.0？

```
❌ 127.0.0.1 (localhost) - 只允许本机进程访问
✅ 0.0.0.0 - 允许所有网络接口访问

Cloudflare Tunnel 通过虚拟网络接口转发流量，
如果服务只监听 127.0.0.1，Tunnel 将无法访问！
```

### 已自动配置的监听地址

**前端 (vite.config.js)**:
```javascript
server: {
  host: '0.0.0.0',  // ✅ 已配置
  port: 5001,
  // ...
}
```

**后端 (启动命令)**:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
#                                    ^^^^^^^^^^ 已配置
```

---

## 🔧 故障排查

### 问题：cloudflared 命令未找到

```powershell
# 检查是否安装
where cloudflared

# 如果未找到，重新安装或手动添加到 PATH
```

### 问题：502 Bad Gateway

**原因**: 本地服务未启动

**解决**:
1. 检查后端是否运行：http://localhost:8001
2. 检查前端是否运行：http://localhost:5001
3. 查看启动脚本输出的日志

### 问题：DNS 解析失败

**解决**:
1. 等待 DNS 传播 (几分钟到 24 小时)
2. 检查 Cloudflare DNS 记录
3. 运行：`nslookup knowledge-qa.yourdomain.com`

---

## 🎯 临时快速测试

如果只需要临时暴露 (无需配置域名):

```powershell
# 启动后端和前端后
cloudflared tunnel --url http://localhost:5001
```

会生成一个随机公网 URL，适合快速演示。

---

## 📚 详细文档

- **完整安装配置指南**: [CLOUDFLARE_SETUP.md](./CLOUDFLARE_SETUP.md)
- **项目说明**: [README.md](./README.md)
- **部署计划**: [.trae/documents/Cloudflare Tunnel 内网穿透部署计划.md](./.trae/documents/Cloudflare Tunnel 内网穿透部署计划.md)

---

## ✅ 检查清单

部署前请确认:

- [ ] cloudflared 已安装并可执行
- [ ] Cloudflare 账号已注册
- [ ] 域名已添加到 Cloudflare
- [ ] Tunnel 已创建并获取 credentials
- [ ] cloudflared-config.yml 已正确配置
- [ ] 运行 `.\start-with-tunnel.bat`
- [ ] 公网访问正常

---

## 💡 下一步建议

1. **配置访问控制** (推荐)
   - Cloudflare Dashboard → Access → Applications
   - 添加邮箱白名单或登录要求

2. **测试公网访问**
   - 使用其他设备访问公网 URL
   - 测试文件上传和问答功能

3. **监控和日志**
   - 查看 Cloudflare Dashboard 流量统计
   - 定期检查应用日志

---

**祝你部署顺利！** 🎉

如有问题，请查看详细文档或检查故障排查部分。
