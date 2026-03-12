# Cloudflare Tunnel 安装与配置指南

## 一、前置要求

### 1. Cloudflare 账号
- 注册免费 Cloudflare 账号：https://dash.cloudflare.com/sign-up
- 拥有一个已添加到 Cloudflare 的域名 (免费套餐必需)

### 2. 系统要求
- Windows 10/11
- 管理员权限 (可选，便于安装)

---

## 二、安装 cloudflared

### 方法 1: 直接下载 (推荐)

1. **访问 GitHub  releases 页面**
   ```
   https://github.com/cloudflare/cloudflared/releases/latest
   ```

2. **下载 Windows 版本**
   - 找到 `cloudflared-windows-amd64.exe`
   - 点击下载到本地

3. **安装到系统 PATH**
   
   **选项 A: 放到项目目录 (简单)**
   ```
   e:\1_CodeSpace\5_timu\one\tools\cloudflared.exe
   ```
   
   **选项 B: 放到系统 PATH (推荐)**
   - 在 `C:\Windows` 或 `C:\Users\<你的用户名>\AppData\Local\Microsoft\WindowsApps` 创建 `cloudflared.exe`
   - 或者添加到任意已在 PATH 中的目录

4. **验证安装**
   ```powershell
   cloudflared --version
   ```

### 方法 2: 使用 winget (Windows 包管理器)

```powershell
winget install cloudflare.cloudflared
```

### 方法 3: 使用 chocolatey

```powershell
choco install cloudflared
```

---

## 三、创建 Cloudflare Tunnel

### 方式 1: 通过 Dashboard 创建 (推荐新手)

1. **登录 Cloudflare Dashboard**
   ```
   https://dash.cloudflare.com/?to=/:account/zero-trust/tunnels
   ```

2. **创建 Tunnel**
   - 导航至：**Access** → **Tunnels**
   - 点击 **Create a tunnel**
   - 选择 **Cloudflared** 类型
   - 输入隧道名称：`knowledge-qa-tunnel`
   - 点击 **Add tunnel**

3. **安装 Connector**
   - 选择 **Windows** 作为操作系统
   - 复制 **credentials file** 的内容
   - 保存到本地，例如：`C:\Users\<你的用户名>\.cloudflared\<TUNNEL_ID>.json`

4. **配置 Public Hostname**
   - **Subdomain**: `knowledge-qa`
   - **Domain**: 选择你的域名
   - **Service**: `http://localhost:5001`
   - 点击 **Save tunnel**

5. **添加更多 Hostname (可选)**
   - 重复上述步骤添加 `api-knowledge-qa.yourdomain.com` → `http://localhost:8001`

### 方式 2: 通过命令行创建

1. **创建 Tunnel**
   ```powershell
   cloudflared tunnel create --name knowledge-qa-tunnel
   ```
   
   输出示例:
   ```
   Created tunnel knowledge-qa-tunnel with ID a1b2c3d4-e5f6-7890-abcd-ef1234567890
   Credentials written to C:\Users\<用户名>\.cloudflared\a1b2c3d4-e5f6-7890-abcd-ef1234567890.json
   ```

2. **保存 Tunnel ID**
   - 记录输出的 Tunnel ID (例如：`a1b2c3d4-e5f6-7890-abcd-ef1234567890`)

---

## 四、配置 Tunnel

### 1. 编辑配置文件

打开 `e:\1_CodeSpace\5_timu\one\cloudflared-config.yml`，修改以下内容:

```yaml
tunnel: knowledge-qa-tunnel

# 替换为你的 credentials 文件路径
credentials-file: C:\Users\<你的用户名>\.cloudflared\<TUNNEL_ID>.json

ingress:
  # 替换为你的域名
  - hostname: knowledge-qa.yourdomain.com
    service: http://localhost:5001
  
  # 可选：API 子域名
  - hostname: api-knowledge-qa.yourdomain.com
    service: http://localhost:8001
  
  - service: http_status:404
```

### 2. 配置 DNS 记录

**方式 1: 自动配置 (推荐)**
- 在 Tunnel Dashboard 中配置 Public Hostname 时会自动创建 DNS 记录

**方式 2: 手动配置**
1. 登录 Cloudflare Dashboard
2. 进入你的域名 → **DNS** → **DNS**
3. 添加 CNAME 记录:
   ```
   类型：CNAME
   名称：knowledge-qa
   目标：<TUNNEL_ID>.cfargotunnel.com
   Proxy status: Proxied (橙色云朵)
   TTL: Auto
   ```

---

## 五、运行 Tunnel

### 方式 1: 使用一键启动脚本 (推荐)

```powershell
cd e:\1_CodeSpace\5_timu\one
.\start-with-tunnel.bat
```

### 方式 2: 手动运行

```powershell
cloudflared tunnel run --config e:\1_CodeSpace\5_timu\one\cloudflared-config.yml knowledge-qa-tunnel
```

### 方式 3: 作为 Windows 服务安装 (长期运行)

1. **安装服务**
   ```powershell
   cloudflared service install --config e:\1_CodeSpace\5_timu\one\cloudflared-config.yml knowledge-qa-tunnel
   ```

2. **启动服务**
   ```powershell
   net start cloudflared
   ```

3. **停止服务**
   ```powershell
   net stop cloudflared
   ```

4. **卸载服务**
   ```powershell
   cloudflared service uninstall
   ```

---

## 六、验证访问

### 1. 本地验证
```powershell
# 测试后端
curl http://localhost:8001/health

# 测试前端
curl http://localhost:5001
```

### 2. 公网验证
```powershell
# 测试公网访问
curl https://knowledge-qa.yourdomain.com/health

# 或在浏览器中访问
https://knowledge-qa.yourdomain.com
```

### 3. 检查 Tunnel 状态
```powershell
cloudflared tunnel list
```

---

## 七、快速测试 (临时方案)

如果只需要临时暴露进行测试，可以使用快速隧道:

```powershell
# 启动后端和前端后
cloudflared tunnel --url http://localhost:5001
```

**优点**:
- 无需配置
- 立即生成公网 URL
- 适合快速演示

**缺点**:
- 每次生成随机 URL
- 不适合长期稳定访问
- 无法自定义域名

---

## 八、故障排查

### 问题 1: cloudflared 命令未找到

**解决方案**:
```powershell
# 验证 cloudflared 是否在 PATH 中
where cloudflared

# 如果未找到，手动添加到 PATH
$env:Path += ";C:\path\to\cloudflared"
```

### 问题 2: Tunnel 无法连接

**检查项**:
1. 确认 credentials 文件路径正确
2. 确认 Tunnel ID 正确
3. 检查网络连接
4. 查看详细日志:
   ```powershell
   cloudflared tunnel run --config cloudflared-config.yml knowledge-qa-tunnel --verbose
   ```

### 问题 3: 502 Bad Gateway

**原因**: 本地服务未启动或监听地址错误

**解决方案**:
1. 确认后端服务正在运行: `http://localhost:8001`
2. 确认前端服务正在运行: `http://localhost:5001`
3. 确认服务监听 `0.0.0.0` 而非 `127.0.0.1`

### 问题 4: DNS 解析失败

**解决方案**:
1. 等待 DNS 传播 (通常几分钟，最长 24 小时)
2. 检查 DNS 记录配置
3. 使用 `nslookup knowledge-qa.yourdomain.com` 验证
4. 清除本地 DNS 缓存: `ipconfig /flushdns`

---

## 九、安全建议

### 1. 添加访问控制 (推荐)

在 Cloudflare Dashboard → Access → Applications 中配置:
- 允许特定邮箱域名访问
- 需要登录才能访问
- IP 白名单

### 2. 限制文件上传

在应用层添加:
- 文件大小限制 (建议 < 10MB)
- 文件类型限制 (仅允许 PDF, DOCX)
- 上传频率限制

### 3. 启用日志记录

```yaml
# 在 cloudflared-config.yml 中添加
logging:
  level: info
  output: e:\1_CodeSpace\5_timu\one\logs\cloudflared.log
```

---

## 十、相关资源

- **官方文档**: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/
- **GitHub**: https://github.com/cloudflare/cloudflared
- **定价**: https://www.cloudflare.com/plans/zero-trust/

---

## 总结

完成以上步骤后，你的企业内部智能问答知识库系统应该可以通过公网访问:

- **前端**: https://knowledge-qa.yourdomain.com
- **后端**: https://api-knowledge-qa.yourdomain.com (可选)
- **本地**: http://localhost:5001 / http://localhost:8001

**关键配置**:
✅ 前端和后端都监听 `0.0.0.0`  
✅ cloudflared-config.yml 正确配置  
✅ DNS 记录已添加  
✅ Tunnel 正在运行
