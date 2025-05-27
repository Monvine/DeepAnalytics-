@echo off
chcp 65001 >nul
echo.
echo ========================================
echo      启动 DeepAnalytics Pro
echo ========================================
echo.

REM 检查环境变量文件
if not exist .env (
    echo ❌ .env 文件不存在，请先运行 install.bat
    pause
    exit /b 1
)

echo 🔧 正在检查环境...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.

REM 启动后端
echo 🔧 启动后端服务...
cd backend
start "DeepAnalytics Pro - 后端服务" cmd /k "python main.py"
cd ..

REM 等待后端启动
echo ⏳ 等待后端服务启动...
timeout /t 5 /nobreak >nul

REM 启动前端
echo 🎨 启动前端服务...
cd frontend
start "DeepAnalytics Pro - 前端服务" cmd /k "npm start"
cd ..

echo.
echo ========================================
echo      DeepAnalytics Pro 启动完成！
echo ========================================
echo.
echo 🌐 访问地址：
echo    前端应用：http://localhost:3000
echo    后端API：http://localhost:8000
echo    API文档：http://localhost:8000/docs
echo.
echo 💡 提示：
echo    - 前端和后端服务将在新窗口中运行
echo    - 关闭对应窗口即可停止服务
echo    - 首次启动可能需要较长时间
echo.
echo 按任意键关闭此窗口...
pause >nul 