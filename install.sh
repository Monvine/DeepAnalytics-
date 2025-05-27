#!/bin/bash

echo "🚀 DeepAnalytics Pro - 自动安装脚本"
echo "=================================="

# 检查Python版本
echo "📋 检查系统环境..."
python3 --version
if [ $? -ne 0 ]; then
    echo "❌ Python 3.8+ 未安装，请先安装Python"
    exit 1
fi

# 检查Node.js版本
node --version
if [ $? -ne 0 ]; then
    echo "❌ Node.js 16+ 未安装，请先安装Node.js"
    exit 1
fi

# 检查MySQL
mysql --version
if [ $? -ne 0 ]; then
    echo "⚠️  MySQL未安装，请确保MySQL 8.0+已安装并运行"
fi

echo "✅ 环境检查完成"

# 配置环境变量
echo "🔧 配置环境变量..."
if [ ! -f .env ]; then
    cp env.example .env
    echo "📝 已创建 .env 文件，请编辑填入真实配置"
    echo "⚠️  必须配置: DEEPSEEK_API_KEY, DEFAULT_COOKIE, DB_PASSWORD"
fi

# 安装后端依赖
echo "📦 安装后端依赖..."
cd backend
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ 后端依赖安装失败"
    exit 1
fi
cd ..

# 安装前端依赖
echo "📦 安装前端依赖..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ 前端依赖安装失败"
    exit 1
fi
cd ..

# 初始化数据库
echo "🗄️  初始化数据库..."
echo "请手动执行: mysql -u root -p < init_database.sql"

echo "✅ 安装完成！"
echo ""
echo "🚀 启动命令:"
echo "   ./start.sh"
echo ""
echo "📖 访问地址:"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs" 