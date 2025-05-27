#!/bin/bash

echo "🚀 启动 DeepAnalytics Pro"
echo "========================"

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "❌ .env 文件不存在，请先运行 ./install.sh"
    exit 1
fi

# 启动后端服务
echo "🔧 启动后端服务..."
cd backend
python3 main.py &
BACKEND_PID=$!
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"
cd ..

# 等待后端启动
sleep 3

# 启动前端服务
echo "🎨 启动前端服务..."
cd frontend
npm start &
FRONTEND_PID=$!
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"
cd ..

echo ""
echo "🎉 DeepAnalytics Pro 启动完成！"
echo ""
echo "📖 访问地址:"
echo "   前端应用: http://localhost:3000"
echo "   后端API: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "🛑 停止服务:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📝 进程ID已保存到 .pids 文件"
echo "$BACKEND_PID $FRONTEND_PID" > .pids

# 等待用户输入停止
echo "按 Ctrl+C 停止所有服务..."
trap "kill $BACKEND_PID $FRONTEND_PID; echo '🛑 服务已停止'; exit" INT
wait 