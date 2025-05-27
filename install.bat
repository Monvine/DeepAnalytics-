@echo off
chcp 65001 >nul
echo.
echo ========================================
echo    DeepAnalytics Pro - 自动安装脚本
echo ========================================
echo.

REM 检查Python是否安装
echo [1/6] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或未添加到PATH
    echo 请先安装Python 3.8+并添加到系统PATH
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python环境检查通过

REM 检查Node.js是否安装
echo.
echo [2/6] 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js未安装或未添加到PATH
    echo 请先安装Node.js 16+并添加到系统PATH
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js环境检查通过

REM 检查MySQL是否安装
echo.
echo [3/6] 检查MySQL环境...
mysql --version >nul 2>&1
if errorlevel 1 (
    echo ⚠️ MySQL未安装或未添加到PATH
    echo 请确保MySQL 8.0+已安装并正在运行
) else (
    echo ✅ MySQL环境检查通过
)

REM 配置环境变量
echo.
echo [4/6] 配置环境变量...
if not exist .env (
    copy env.example .env >nul
    echo ✅ 已创建 .env 文件
    echo ⚠️ 请编辑 .env 文件，填入真实配置
) else (
    echo ✅ .env 文件已存在
)

REM 安装后端依赖
echo.
echo [5/6] 安装后端Python依赖...
cd backend
if not exist requirements.txt (
    echo ❌ requirements.txt文件不存在
    pause
    exit /b 1
)
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ 后端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 后端依赖安装完成
cd ..

REM 安装前端依赖
echo.
echo [6/6] 安装前端Node.js依赖...
cd frontend
if not exist package.json (
    echo ❌ package.json文件不存在
    pause
    exit /b 1
)
npm install
if errorlevel 1 (
    echo ❌ 前端依赖安装失败
    pause
    exit /b 1
)
echo ✅ 前端依赖安装完成
cd ..

REM 完成安装
echo.
echo ========================================
echo        DeepAnalytics Pro 安装完成！
echo ========================================
echo.
echo 📋 下一步操作：
echo 1. 编辑 .env 文件，配置API密钥和数据库
echo 2. 初始化数据库：mysql -u root -p ^< init_database.sql
echo 3. 启动系统：运行 start.bat
echo.
echo 🌐 访问地址：
echo    前端应用：http://localhost:3000
echo    后端API：http://localhost:8000
echo    API文档：http://localhost:8000/docs
echo.
pause 