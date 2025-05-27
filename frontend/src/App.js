import React, { useState } from 'react';
import { Layout, Menu, Typography, Space, Divider, Avatar, Dropdown, Button, Modal } from 'antd';
import { 
  BarChartOutlined, 
  UserOutlined, 
  GithubOutlined,
  ApiOutlined,
  DashboardOutlined,
  LineChartOutlined,
  RobotOutlined,
  LoginOutlined,
  LogoutOutlined,
  SettingOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import VideoAnalysis from './components/VideoAnalysis';
import UserAnalysis from './components/UserAnalysis';
import DataDashboard from './components/DataDashboard';
import InteractiveCharts from './components/InteractiveCharts';
import MachineLearning from './components/MachineLearning';
import AIChat from './components/AIChat';
import ReportCenter from './components/ReportCenter';
import Auth, { AuthProvider, useAuth } from './components/Auth';
import 'antd/dist/reset.css';

const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;

const AppContent = () => {
  const [selectedKey, setSelectedKey] = useState('video');
  const [authModalVisible, setAuthModalVisible] = useState(false);
  const { user, logout, isAuthenticated } = useAuth();

  const menuItems = [
    {
      key: 'video',
      icon: <BarChartOutlined />,
      label: '热门视频分析',
    },
    {
      key: 'user',
      icon: <UserOutlined />,
      label: '用户数据分析',
    },
    {
      key: 'dashboard',
      icon: <DashboardOutlined />,
      label: '实时数据大屏',
    },
    {
      key: 'interactive',
      icon: <LineChartOutlined />,
      label: '交互式图表',
    },
    {
      key: 'ml',
      icon: <RobotOutlined />,
      label: '智能推荐',
    },
    {
      key: 'ai-chat',
      icon: <ApiOutlined />,
      label: 'DeepSeek V3 助手',
    },
    {
      key: 'reports',
      icon: <FileTextOutlined />,
      label: '自动化报告',
    },
  ];

  // 用户菜单
  const userMenuItems = [
    {
      key: 'profile',
      icon: <SettingOutlined />,
      label: '个人设置',
      onClick: () => setAuthModalVisible(true)
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: logout
    }
  ];

  const renderContent = () => {
    switch (selectedKey) {
      case 'video':
        return <VideoAnalysis />;
      case 'user':
        return <UserAnalysis />;
      case 'dashboard':
        return <DataDashboard />;
      case 'interactive':
        return <InteractiveCharts />;
      case 'ml':
        return <MachineLearning />;
      case 'ai-chat':
        return <AIChat />;
      case 'reports':
        return <ReportCenter />;
      default:
        return <VideoAnalysis />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center', 
        background: '#001529',
        padding: '0 24px'
      }}>
        <div style={{ 
          color: 'white', 
          fontSize: '20px', 
          fontWeight: 'bold',
          marginRight: '40px',
          display: 'flex',
          alignItems: 'center'
        }}>
          <ApiOutlined style={{ marginRight: '8px', fontSize: '24px' }} />
          B站数据分析系统
        </div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
          style={{ 
            flex: 1, 
            minWidth: 0,
            background: 'transparent',
            borderBottom: 'none'
          }}
        />
        
        {/* 用户登录/头像区域 */}
        <div style={{ marginLeft: 'auto' }}>
          {isAuthenticated ? (
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              trigger={['click']}
            >
              <Space style={{ cursor: 'pointer', color: 'white' }}>
                <Avatar 
                  size="small" 
                  icon={<UserOutlined />} 
                  style={{ backgroundColor: '#1890ff' }}
                />
                <span>{user?.username}</span>
              </Space>
            </Dropdown>
          ) : (
            <Button 
              type="primary" 
              icon={<LoginOutlined />}
              onClick={() => setAuthModalVisible(true)}
            >
              登录
            </Button>
          )}
        </div>
      </Header>

      <Content style={{ 
        background: '#f0f2f5',
        minHeight: 'calc(100vh - 134px)'
      }}>
        {renderContent()}
      </Content>

      {/* 认证模态框 */}
      <Modal
        title={null}
        open={authModalVisible}
        onCancel={() => setAuthModalVisible(false)}
        footer={null}
        width={500}
        centered
      >
        <Auth onClose={() => setAuthModalVisible(false)} />
      </Modal>

      <Footer style={{ 
        textAlign: 'center', 
        background: '#fafafa',
        borderTop: '1px solid #e8e8e8'
      }}>
        <Space split={<Divider type="vertical" />}>
          <Text type="secondary">
            B站数据分析系统 ©2025
          </Text>
          <Text type="secondary">
            基于 FastAPI + React 构建
          </Text>
          <Space>
            <GithubOutlined />
            <Text type="secondary">Monvine</Text>
          </Space>
        </Space>
      </Footer>
    </Layout>
  );
};

const App = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App; 