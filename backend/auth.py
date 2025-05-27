import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
import bcrypt

JWT_SECRET_KEY = "bilibili_analytics_secret_key_2024"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7

class AuthService:
    """用户认证服务"""

    def __init__(self, engine):
        self.engine = engine
        self._init_auth_tables()

    def _init_auth_tables(self):
        """初始化认证相关表"""
        with self.engine.begin() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                bilibili_cookie TEXT,
                bilibili_mid VARCHAR(20),
                bilibili_name VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_bilibili_mid (bilibili_mid)
            )
            """))
            
            # 用户会话表
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                token_hash VARCHAR(255) NOT NULL,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                INDEX idx_token_hash (token_hash),
                INDEX idx_user_id (user_id)
            )
            """))
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def generate_token(self, user_id: int, username: str) -> str:
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def register_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """用户注册"""
        try:
            password_hash = self.hash_password(password)

            with self.engine.begin() as conn:
                result = conn.execute(text("""
                INSERT INTO users (username, email, password_hash)
                VALUES (:username, :email, :password_hash)
                """), {
                    'username': username,
                    'email': email,
                    'password_hash': password_hash
                })
                
                user_id = result.lastrowid
                
                # 生成令牌
                token = self.generate_token(user_id, username)
                
                # 保存会话
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                conn.execute(text("""
                INSERT INTO user_sessions (user_id, token_hash, expires_at)
                VALUES (:user_id, :token_hash, :expires_at)
                """), {
                    'user_id': user_id,
                    'token_hash': token_hash,
                    'expires_at': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
                })
                
                return {
                    'success': True,
                    'user_id': user_id,
                    'username': username,
                    'email': email,
                    'token': token
                }
                
        except IntegrityError as e:
            if 'username' in str(e):
                return {'success': False, 'error': '用户名已存在'}
            elif 'email' in str(e):
                return {'success': False, 'error': '邮箱已被注册'}
            else:
                return {'success': False, 'error': '注册失败'}
        except Exception as e:
            return {'success': False, 'error': f'注册失败: {str(e)}'}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """用户登录"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                SELECT id, username, email, password_hash, bilibili_mid, bilibili_name
                FROM users 
                WHERE username = :username AND is_active = TRUE
                """), {'username': username})
                
                user = result.fetchone()
                
                if not user:
                    return {'success': False, 'error': '用户名或密码错误'}
                
                if not self.verify_password(password, user[3]):  # password_hash
                    return {'success': False, 'error': '用户名或密码错误'}
                
                # 生成新令牌
                token = self.generate_token(user[0], user[1])
                
                # 保存会话
                token_hash = hashlib.sha256(token.encode()).hexdigest()
                with self.engine.begin() as conn:
                    conn.execute(text("""
                    INSERT INTO user_sessions (user_id, token_hash, expires_at)
                    VALUES (:user_id, :token_hash, :expires_at)
                    """), {
                        'user_id': user[0],
                        'token_hash': token_hash,
                        'expires_at': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
                    })
                    
                    # 更新最后登录时间
                    conn.execute(text("""
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :user_id
                    """), {'user_id': user[0]})
                
                return {
                    'success': True,
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'bilibili_mid': user[4],
                    'bilibili_name': user[5],
                    'token': token
                }
                
        except Exception as e:
            return {'success': False, 'error': f'登录失败: {str(e)}'}
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """通过令牌获取用户信息"""
        payload = self.verify_token(token)
        if not payload:
            return None

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                SELECT u.id, u.username, u.email, u.bilibili_mid, u.bilibili_name, u.bilibili_cookie
                FROM users u
                JOIN user_sessions s ON u.id = s.user_id
                WHERE u.id = :user_id AND s.token_hash = :token_hash 
                AND s.expires_at > NOW() AND s.is_active = TRUE
                """), {
                    'user_id': payload['user_id'],
                    'token_hash': hashlib.sha256(token.encode()).hexdigest()
                })
                
                user = result.fetchone()
                if user:
                    return {
                        'user_id': user[0],
                        'username': user[1],
                        'email': user[2],
                        'bilibili_mid': user[3],
                        'bilibili_name': user[4],
                        'bilibili_cookie': user[5]
                    }
                return None
                
        except Exception:
            return None
    
    def update_bilibili_info(self, user_id: int, cookie: str, mid: str, name: str) -> bool:
        """更新用户的B站信息"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                UPDATE users 
                SET bilibili_cookie = :cookie, bilibili_mid = :mid, bilibili_name = :name,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :user_id
                """), {
                    'user_id': user_id,
                    'cookie': cookie,
                    'mid': mid,
                    'name': name
                })
                return True
        except Exception:
            return False
    
    def logout_user(self, token: str) -> bool:
        """用户登出"""
        try:
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            with self.engine.begin() as conn:
                conn.execute(text("""
                UPDATE user_sessions 
                SET is_active = FALSE 
                WHERE token_hash = :token_hash
                """), {'token_hash': token_hash})
                return True
        except Exception:
            return False
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            with self.engine.begin() as conn:
                conn.execute(text("""
                DELETE FROM user_sessions 
                WHERE expires_at < NOW() OR is_active = FALSE
                """))
        except Exception:
            pass 