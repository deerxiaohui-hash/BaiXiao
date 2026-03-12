@echo off
chcp 65001 >nul
echo.
echo ========================================
echo   企业内部智能问答知识库系统
echo   Cloudflare Tunnel 部署启动脚本
echo ========================================
echo.

REM 检查 cloudflared 是否存在
where cloudflared >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [错误] 未找到 cloudflared 命令
    echo.
    echo 请先安装 cloudflared:
    echo 1. 访问 https://github.com/cloudflare/cloudflared/releases/latest
    echo 2. 下载 cloudflared-windows-amd64.exe
    echo 3. 重命名为 cloudflared.exe 并放置到系统 PATH 或项目 tools 目录
    echo.
    pause
    exit /b 1
)

echo [提示] 正在启动后端服务...
echo [提示] 监听地址：0.0.0.0:8001 (允许 Tunnel 访问)
start "Backend - Port 8001" cmd /k "cd /d e:\1_CodeSpace\5_timu\one\backend && .\venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload"
timeout /t 3 /nobreak >nul
echo [√] 后端服务已启动

echo.
echo [提示] 正在启动前端服务...
echo [提示] 监听地址：0.0.0.0:5001 (允许 Tunnel 访问)
start "Frontend - Port 5001" cmd /k "cd /d e:\1_CodeSpace\5_timu\one\frontend && npm run dev -- --host 0.0.0.0"
timeout /t 3 /nobreak >nul
echo [√] 前端服务已启动

echo.
echo [提示] 正在启动 Cloudflare Tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared tunnel run --config e:\1_CodeSpace\5_timu\one\cloudflared-config.yml knowledge-qa-tunnel"
timeout /t 2 /nobreak >nul
echo [√] Cloudflare Tunnel 已启动

echo.
echo ========================================
echo   所有服务已启动!
echo ========================================
echo.
echo 本地访问:
echo   - 前端：http://localhost:5001
echo   - 后端：http://localhost:8001
echo.
echo 公网访问:
echo   - 前端：https://knowledge-qa.yourdomain.com
echo   - 后端：https://api-knowledge-qa.yourdomain.com (可选)
echo.
echo ========================================
echo.
echo [重要] 请确保:
echo 1. cloudflared-config.yml 已正确配置 (隧道 ID、域名、credentials 路径)
echo 2. Cloudflare DNS 已配置 CNAME 记录
echo 3. 前端和后端都监听 0.0.0.0 (而非 127.0.0.1)
echo.
echo 提示：按任意键查看 Cloudflare Tunnel 日志窗口
pause >nul
