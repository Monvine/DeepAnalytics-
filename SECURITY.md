# 🔒 安全配置指南

## 🚨 敏感信息

本项目需要配置以下敏感信息：
- **DeepSeek API Key**: AI功能必需
- **B站Cookie**: 获取用户数据必需
- **数据库密码**: MySQL连接密码
- **JWT密钥**: 用户认证密钥

## 🛡️ 配置步骤

### 1. 环境变量配置

```bash
# 复制模板文件
cp env.example .env

# 编辑配置文件
nano .env
```

填入真实配置：
```bash
DEEPSEEK_API_KEY=sk-your-actual-api-key
DEFAULT_COOKIE=your-bilibili-cookie
DB_PASSWORD=your-database-password
JWT_SECRET_KEY=your-jwt-secret
```

### 2. 获取配置信息

**DeepSeek API Key**:
1. 访问 [DeepSeek官网](https://platform.deepseek.com/)
2. 注册并获取API Key

**B站Cookie**:
1. 登录B站网页版
2. 按F12打开开发者工具
3. Network标签中复制任意请求的Cookie

## ⚠️ 安全注意事项

- ❌ 永远不要提交 `.env` 文件到Git
- ❌ 永远不要在代码中硬编码敏感信息
- ✅ 定期更换API密钥和Cookie
- ✅ 使用强密码作为JWT密钥

## 🚀 部署

生产环境建议使用系统环境变量或密钥管理服务。

Docker部署时通过环境变量传递：
```bash
docker run -e DEEPSEEK_API_KEY=xxx -e DEFAULT_COOKIE=xxx app
``` 