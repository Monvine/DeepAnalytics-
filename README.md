# 🚀 DeepAnalytics Pro

> 基于 DeepSeek AI 驱动的智能数据分析平台

一个集成了**人工智能**、**机器学习**和**实时数据分析**的现代化B站内容分析系统。采用 FastAPI + React + DeepSeek V3 技术栈，提供智能问答、预测分析和自动化报告生成。

## ✨ 核心特性

### 🤖 AI 智能分析
- **DeepSeek V3 驱动**：基于最新大语言模型的智能问答
- **自然语言查询**：用自然语言提问，获得专业数据分析
- **智能洞察**：AI 自动发现数据趋势和异常

### 📊 机器学习引擎
- **智能推荐系统**：基于协同过滤和内容分析的视频推荐
- **用户行为聚类**：深度学习用户偏好模式
- **趋势预测模型**：预测视频播放量和热度走势
- **情感分析**：分析评论和弹幕情感倾向

### 📈 实时数据分析
- **多维度可视化**：交互式图表和数据大屏
- **实时监控**：热门视频和用户行为实时追踪
- **自动化报告**：定时生成日报、周报和月报
- **数据导出**：支持多种格式的数据导出

### 🔐 企业级安全
- **JWT 认证**：安全的用户身份验证
- **权限管理**：细粒度的访问控制
- **数据加密**：敏感信息安全存储
- **API 限流**：防止恶意请求

## 🏗️ 技术架构

```
  
   React 前端              FastAPI 后端          DeepSeek AI    
                                                       
 • Ant Design    ◄──►    • RESTful API   ◄──►   • GPT-4 级别     
 • Recharts              • WebSocket            • 智能问答        
 • Axios                 • 异步处理               • 数据洞察      
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
  
   数据可视化                  机器学习                数据存储        
                               
 • 实时图表                • scikit-learn        • MySQL 8.0     
 • 交互式大屏              • 推荐算法              • Redis 缓存     
 • 响应式设计              • 聚类分析              • 数据备份        
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 📋 系统要求

- **Python** 3.8+
- **Node.js** 16+
- **MySQL** 8.0+
- **Redis** 6.0+ (可选)

### ⚡ 一键安装

```bash
# 克隆项目
git clone https://github.com/your-username/DeepAnalytics-Pro.git
cd DeepAnalytics-Pro

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，填入你的配置

# 安装依赖
./install.bat  # Windows
# 或
chmod +x install.sh && ./install.sh  # Linux/Mac

# 启动服务
./start.bat  # Windows
# 或
./start.sh  # Linux/Mac
```

### 🔧 手动安装

1. **环境配置**
   ```bash
   # 复制环境变量模板
   cp env.example .env
   ```

2. **编辑配置文件**
   ```bash
   # 必填配置项
   DEEPSEEK_API_KEY=sk-your-deepseek-api-key
   DEFAULT_COOKIE=your-bilibili-cookie
   DB_PASSWORD=your-mysql-password
   JWT_SECRET_KEY=your-jwt-secret
   ```

3. **后端安装**
   ```bash
   cd backend
   pip install -r requirements.txt
   python main.py
   ```

4. **前端安装**
   ```bash
   cd frontend
   npm install
   npm start
   ```

5. **数据库初始化**
   ```bash
   mysql -u root -p < init_database.sql
   ```

## 📖 使用指南

### 🎯 基础功能

#### 1. 数据爬取与分析
- 访问 `http://localhost:3000`
- 点击"开始分析"自动爬取热门视频
- 查看实时数据可视化图表

#### 2. AI 智能问答
- 在聊天界面输入问题：
  - "最近一周哪个分区表现最好？"
  - "给我分析一下播放量趋势"
  - "推荐一些提高视频热度的策略"

#### 3. 机器学习功能
- **视频推荐**：基于用户行为的个性化推荐
- **用户聚类**：发现相似用户群体
- **趋势预测**：预测未来数据走势

### 🔐 用户系统

#### 注册与登录
```bash
# 注册新用户
POST /api/auth/register
{
  "username": "your_username",
  "email": "your_email@example.com",
  "password": "your_password"
}

# 用户登录
POST /api/auth/login
{
  "username": "your_username",
  "password": "your_password"
}
```

#### Cookie 配置
1. 登录 B站网页版
2. 打开开发者工具 (F12)
3. 复制 Cookie 值
4. 在设置中更新 Cookie

### 📊 API 接口

#### 数据分析接口
```bash
# 获取视频分析
GET /api/analysis/videos

# 获取用户分析
GET /api/user/analysis/{user_id}

# 机器学习推荐
GET /api/ml/recommendations?limit=10
```

#### AI 问答接口
```bash
# AI 聊天
POST /api/ai/chat
{
  "query": "你的问题",
  "conversation_history": []
}

# 获取智能建议
GET /api/ai/suggestions
```

## 🛠️ 高级配置

### 🐳 Docker 部署

```dockerfile
# 使用 Docker Compose
docker-compose up -d

# 或单独构建
docker build -t deepanalytics-pro .
docker run -p 8000:8000 -p 3000:3000 deepanalytics-pro
```

### ☁️ 云端部署

支持部署到：
- **AWS EC2** + RDS
- **阿里云 ECS** + RDS
- **腾讯云 CVM** + TencentDB
- **Vercel** (前端) + **Railway** (后端)

### 📈 性能优化

- **Redis 缓存**：缓存热点数据
- **数据库索引**：优化查询性能
- **CDN 加速**：静态资源加速
- **负载均衡**：支持集群部署

## 🔍 故障排除

### 常见问题

1. **AI 功能无法使用**
   - 检查 DeepSeek API Key 是否正确
   - 确认网络可以访问 `api.deepseek.com`

2. **数据爬取失败**
   - 更新 B站 Cookie
   - 检查网络连接

3. **数据库连接错误**
   - 确认 MySQL 服务运行正常
   - 检查数据库配置信息

### 日志查看

```bash
# 后端日志
tail -f backend/logs/app.log

# 前端日志
npm run dev  # 开发模式查看控制台
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！

### 开发流程
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- **Python**: 遵循 PEP 8
- **JavaScript**: 使用 ESLint + Prettier
- **提交信息**: 使用 Conventional Commits

## 📄 开源协议

本项目采用 [CC BY-NC-SA 4.0](LICENSE) 开源协议。

**📋 协议说明**：
- ✅ **允许**: 学习、研究、分享、修改
- ❌ **禁止**: 商业用途
- 📤 **要求**: 署名、相同协议分享

**详细说明**: 查看 [LICENSE.md](LICENSE.md) 了解完整的协议条款和使用场景。

## 🙏 致谢

- [DeepSeek](https://deepseek.com/) - 提供强大的 AI 能力
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Python Web 框架
- [React](https://reactjs.org/) - 用户界面构建库
- [Ant Design](https://ant.design/) - 企业级 UI 设计语言

## 📞 联系我们

- **项目主页**: https://github.com/your-username/DeepAnalytics-Pro
- **问题反馈**: https://github.com/your-username/DeepAnalytics-Pro/issues
- **邮箱**: your-email@example.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给我们一个 Star！**

Made with ❤️ by DeepAnalytics Team

</div> 