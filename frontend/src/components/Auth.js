import React, { useState, useContext, createContext } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Tabs, 
  message, 
  Space, 
  Typography,
  Alert,
  Modal,
  Divider
} from 'antd';
import { 
  UserOutlined, 
  LockOutlined, 
  MailOutlined,
  LoginOutlined,
  UserAddOutlined,
  BilibiliOutlined,
  CookieOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

// API配置
const API_BASE_URL = 'http://localhost:8000';

// 认证上下文
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(false);

  // 设置axios默认header
  React.useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // 验证token有效性
      checkTokenValidity();
    } else {
      delete axios.defaults.headers.common['Authorization'];
    }
  }, [token]);

  const checkTokenValidity = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/auth/me`);
      setUser(response.data.user);
    } catch (error) {
      // Token无效，清除本地存储
      logout();
    }
  };

  const login = async (username, password) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/login`, {
        username,
        password
      });
      
      const { token: newToken, user: userData } = response.data;
      
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      message.success('登录成功！');
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '登录失败';
      message.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const register = async (username, email, password) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/register`, {
        username,
        email,
        password
      });
      
      const { token: newToken, user: userData } = response.data;
      
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
      
      message.success('注册成功！');
      return { success: true };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '注册失败';
      message.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await axios.post(`${API_BASE_URL}/api/auth/logout`);
      }
    } catch (error) {
      // 忽略登出错误
    } finally {
      setToken(null);
      setUser(null);
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      message.success('已登出');
    }
  };

  const updateBilibiliInfo = async (cookie) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/auth/update-bilibili`, {
        cookie
      });
      
      // 更新用户信息
      const updatedUser = {
        ...user,
        bilibili_mid: response.data.bilibili_info.mid,
        bilibili_name: response.data.bilibili_info.name
      };
      setUser(updatedUser);
      
      message.success('B站信息更新成功！');
      return { success: true, data: response.data };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'B站信息更新失败';
      message.error(errorMsg);
      return { success: false, error: errorMsg };
    } finally {
      setLoading(false);
    }
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateBilibiliInfo,
    isAuthenticated: !!token && !!user
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

const Auth = ({ onClose }) => {
  const [activeTab, setActiveTab] = useState('login');
  const [cookieModalVisible, setCookieModalVisible] = useState(false);
  const { login, register, updateBilibiliInfo, loading, user, isAuthenticated } = useAuth();
  
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();
  const [cookieForm] = Form.useForm();

  const handleLogin = async (values) => {
    const result = await login(values.username, values.password);
    if (result.success) {
      loginForm.resetFields();
      if (onClose) onClose();
    }
  };

  const handleRegister = async (values) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }
    
    const result = await register(values.username, values.email, values.password);
    if (result.success) {
      registerForm.resetFields();
      if (onClose) onClose();
    }
  };

  const handleUpdateCookie = async (values) => {
    const result = await updateBilibiliInfo(values.cookie);
    if (result.success) {
      cookieForm.resetFields();
      setCookieModalVisible(false);
      message.success('B站数据同步中，请稍候...');
    }
  };

  if (isAuthenticated) {
    return (
      <Card title="用户信息" style={{ maxWidth: 500, margin: '0 auto' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>用户名：</Text>
            <Text>{user.username}</Text>
          </div>
          <div>
            <Text strong>邮箱：</Text>
            <Text>{user.email}</Text>
          </div>
          {user.bilibili_name && (
            <div>
              <Text strong>B站昵称：</Text>
              <Text>{user.bilibili_name}</Text>
            </div>
          )}
          {user.bilibili_mid && (
            <div>
              <Text strong>B站UID：</Text>
              <Text>{user.bilibili_mid}</Text>
            </div>
          )}
          
          <Divider />
          
          <Space>
            <Button 
              type="primary" 
              icon={<BilibiliOutlined />}
              onClick={() => setCookieModalVisible(true)}
            >
              {user.bilibili_mid ? '更新B站Cookie' : '绑定B站账号'}
            </Button>
          </Space>
          
          {!user.bilibili_mid && (
            <Alert
              message="提示"
              description="绑定B站账号后，系统将获取您的观看历史等数据，为您提供个性化推荐和分析。"
              type="info"
              showIcon
            />
          )}
        </Space>

        <Modal
          title="绑定B站账号"
          open={cookieModalVisible}
          onCancel={() => setCookieModalVisible(false)}
          footer={null}
          width={600}
        >
          <Form form={cookieForm} onFinish={handleUpdateCookie} layout="vertical">
            <Alert
              message="如何获取Cookie？"
              description={
                <div>
                  <p>1. 打开浏览器，登录B站</p>
                  <p>2. 按F12打开开发者工具</p>
                  <p>3. 切换到Network标签页</p>
                  <p>4. 刷新页面，找到任意请求</p>
                  <p>5. 在Request Headers中找到Cookie字段，复制完整内容</p>
                </div>
              }
              type="info"
              style={{ marginBottom: 16 }}
            />
            
            <Form.Item
              name="cookie"
              label="B站Cookie"
              rules={[
                { required: true, message: '请输入Cookie' },
                { min: 50, message: 'Cookie长度不足，请检查是否完整' }
              ]}
            >
              <TextArea
                rows={6}
                placeholder="请粘贴完整的Cookie内容..."
                style={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
            </Form.Item>
            
            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading} block>
                绑定并同步数据
              </Button>
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    );
  }

  return (
    <Card title="用户登录" style={{ maxWidth: 400, margin: '0 auto' }}>
      <Tabs activeKey={activeTab} onChange={setActiveTab} centered>
        <TabPane tab={<span><LoginOutlined />登录</span>} key="login">
          <Form form={loginForm} onFinish={handleLogin} layout="vertical">
            <Form.Item
              name="username"
              rules={[{ required: true, message: '请输入用户名' }]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                size="large"
              />
            </Form.Item>
            
            <Form.Item
              name="password"
              rules={[{ required: true, message: '请输入密码' }]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                size="large"
              />
            </Form.Item>
            
            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                size="large"
                block
              >
                登录
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
        
        <TabPane tab={<span><UserAddOutlined />注册</span>} key="register">
          <Form form={registerForm} onFinish={handleRegister} layout="vertical">
            <Form.Item
              name="username"
              rules={[
                { required: true, message: '请输入用户名' },
                { min: 3, message: '用户名至少3个字符' },
                { max: 20, message: '用户名最多20个字符' }
              ]}
            >
              <Input
                prefix={<UserOutlined />}
                placeholder="用户名"
                size="large"
              />
            </Form.Item>
            
            <Form.Item
              name="email"
              rules={[
                { required: true, message: '请输入邮箱' },
                { type: 'email', message: '请输入有效的邮箱地址' }
              ]}
            >
              <Input
                prefix={<MailOutlined />}
                placeholder="邮箱"
                size="large"
              />
            </Form.Item>
            
            <Form.Item
              name="password"
              rules={[
                { required: true, message: '请输入密码' },
                { min: 6, message: '密码至少6个字符' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="密码"
                size="large"
              />
            </Form.Item>
            
            <Form.Item
              name="confirmPassword"
              rules={[
                { required: true, message: '请确认密码' }
              ]}
            >
              <Input.Password
                prefix={<LockOutlined />}
                placeholder="确认密码"
                size="large"
              />
            </Form.Item>
            
            <Form.Item>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                size="large"
                block
              >
                注册
              </Button>
            </Form.Item>
          </Form>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default Auth; 