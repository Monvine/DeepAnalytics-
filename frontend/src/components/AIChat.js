import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Space, 
  Typography, 
  List, 
  Avatar, 
  Spin, 
  Alert, 
  Tag, 
  Divider,
  Row,
  Col,
  Empty,
  Tooltip
} from 'antd';
import { 
  SendOutlined, 
  RobotOutlined, 
  UserOutlined, 
  BulbOutlined,
  ReloadOutlined,
  ExperimentOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import axios from 'axios';
import './AIChat.css';
import 'highlight.js/styles/github.css'; // 代码高亮样式

const { TextArea } = Input;
const { Text, Title } = Typography;

// DeepSeek头像组件
const DeepSeekAvatar = ({ size = "small", style = {} }) => {
  return (
    <Avatar 
      size={size}
      className="deepseek-avatar"
      style={{ 
        color: 'white',
        fontSize: size === 'small' ? '10px' : '14px',
        ...style
      }}
    >
      DS
    </Avatar>
  );
};

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [aiStatus, setAiStatus] = useState({ service_available: false });
  const messagesEndRef = useRef(null);

  // 初始化
  useEffect(() => {
    loadSuggestions();
    checkAIStatus();
    
    // 添加欢迎消息
    setMessages([{
      id: Date.now(),
      type: 'assistant',
      content: '你好！我是 **DeepSeek V3** 智能助手，专门为B站数据分析而生。我可以帮你：\n\n- 📊 分析视频播放量趋势\n- 🔥 识别热门分区和内容\n- 📈 评估视频表现指标\n- 💡 提供数据洞察建议\n\n有什么问题尽管问我吧！',
      timestamp: new Date().toISOString(),
      intent: null
    }]);
  }, []);

  // 自动滚动到底部
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadSuggestions = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/ai/suggestions');
      setSuggestions(response.data.suggestions || []);
    } catch (error) {
      console.error('获取建议失败:', error);
    }
  };

  const checkAIStatus = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/ai/status');
      setAiStatus(response.data);
    } catch (error) {
      console.error('检查AI状态失败:', error);
      setAiStatus({ service_available: false, error: error.message });
    }
  };

  const sendMessage = async (messageText = null) => {
    const text = messageText || inputMessage.trim();
    if (!text) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      // 准备对话历史（最近5轮）
      const conversationHistory = messages.slice(-5).map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const response = await axios.post('http://localhost:8000/api/ai/chat', {
        query: text,
        conversation_history: conversationHistory
      });

      const aiResponse = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response,
        timestamp: response.data.timestamp,
        intent: response.data.intent,
        data_context_available: response.data.data_context_available,
        model: response.data.model
      };

      setMessages(prev => [...prev, aiResponse]);

    } catch (error) {
      console.error('发送消息失败:', error);
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: '抱歉，我暂时无法回答你的问题。请稍后再试。',
        timestamp: new Date().toISOString(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([{
      id: Date.now(),
      type: 'assistant',
      content: '✨ 聊天记录已清空！我是 **DeepSeek V3** 助手，随时为你的B站数据分析提供帮助。',
      timestamp: new Date().toISOString()
    }]);
  };

  const renderMessage = (message) => {
    const isUser = message.type === 'user';
    
    return (
      <div className={`message-wrapper ${isUser ? 'user-message' : 'ai-message'}`} key={message.id}>
        <div className="message-content">
          {isUser ? (
            <Avatar 
              size="small"
              icon={<UserOutlined />}
              style={{ 
                backgroundColor: '#1890ff',
                marginRight: '8px'
              }}
            />
          ) : (
            <DeepSeekAvatar size="small" style={{ marginRight: '8px' }} />
          )}
          <div className="message-text">
            <div className="message-body">
              {(message.type === 'ai' || message.type === 'assistant') ? (
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    // 自定义代码块样式
                    code: ({node, inline, className, children, ...props}) => {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <pre className={className} {...props}>
                          <code>{children}</code>
                        </pre>
                      ) : (
                        <code className="inline-code" {...props}>
                          {children}
                        </code>
                      );
                    },
                    // 自定义表格样式
                    table: ({children}) => (
                      <table className="markdown-table">{children}</table>
                    ),
                    // 自定义链接样式
                    a: ({href, children}) => (
                      <a href={href} target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    )
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              ) : (
                message.content
              )}
            </div>
            <div className="message-meta">
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </Text>
              {message.intent && (
                <Tag color="blue" style={{ marginLeft: '8px', fontSize: '10px' }}>
                  {message.intent.type}
                </Tag>
              )}
              {message.data_context_available && (
                <Tag color="green" style={{ marginLeft: '4px', fontSize: '10px' }}>
                  数据支持
                </Tag>
              )}
              {message.model && (
                <Tag color="purple" style={{ marginLeft: '4px', fontSize: '10px' }}>
                  {message.model}
                </Tag>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="ai-chat-container">
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={18}>
          <Card 
            title={
              <Space>
                <DeepSeekAvatar size="small" />
                <span>DeepSeek V3 助手</span>
                <Tag color={aiStatus.service_available ? 'green' : 'red'}>
                  {aiStatus.service_available ? '在线' : '离线'}
                </Tag>
              </Space>
            }
            extra={
              <Space>
                <Tooltip title="刷新状态">
                  <Button 
                    icon={<ReloadOutlined />} 
                    size="small"
                    onClick={checkAIStatus}
                  />
                </Tooltip>
                <Button 
                  size="small" 
                  onClick={clearChat}
                >
                  清空聊天
                </Button>
              </Space>
            }
            className="chat-card"
          >
            {!aiStatus.service_available && (
              <Alert
                message="AI服务暂时不可用"
                description={aiStatus.error || "请检查网络连接或稍后重试"}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <div className="messages-container">
              {messages.length === 0 ? (
                <Empty 
                  description="开始你的第一个问题吧！"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ) : (
                messages.map(renderMessage)
              )}
              
              {loading && (
                <div className="message-wrapper ai-message">
                  <div className="message-content">
                    <DeepSeekAvatar size="small" style={{ marginRight: '8px' }} />
                    <div className="message-text">
                      <Spin size="small" />
                      <Text type="secondary" style={{ marginLeft: '8px' }}>
                        AI正在思考中...
                      </Text>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <Divider style={{ margin: '16px 0' }} />

            <div className="input-area">
              <Space.Compact style={{ width: '100%' }}>
                <TextArea
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="输入你的问题...（按Enter发送，Shift+Enter换行）"
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  style={{ resize: 'none' }}
                />
                <Button 
                  type="primary" 
                  icon={<SendOutlined />}
                  onClick={() => sendMessage()}
                  loading={loading}
                  disabled={!inputMessage.trim() || !aiStatus.service_available}
                >
                  发送
                </Button>
              </Space.Compact>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={6}>
          <Card 
            title={
              <Space>
                <BulbOutlined />
                <span>智能建议</span>
              </Space>
            }
            size="small"
            className="suggestions-card"
          >
            <List
              size="small"
              dataSource={suggestions}
              renderItem={(suggestion, index) => (
                <List.Item 
                  className="suggestion-item"
                  onClick={() => sendMessage(suggestion)}
                >
                  <Text>{suggestion}</Text>
                </List.Item>
              )}
            />
          </Card>

          <Card 
            title={
              <Space>
                <ExperimentOutlined />
                <span>使用说明</span>
              </Space>
            }
            size="small"
            style={{ marginTop: 16 }}
          >
            <div className="help-content">
              <Text type="secondary" style={{ fontSize: '12px' }}>
                <p>💡 你可以问我：</p>
                <ul>
                  <li>数据统计问题</li>
                  <li>趋势分析问题</li>
                  <li>热门内容分析</li>
                  <li>创作建议</li>
                </ul>
                
                <p>🔍 支持的查询类型：</p>
                <ul>
                  <li>播放量、点赞数等指标</li>
                  <li>不同分区的表现</li>
                  <li>时间趋势分析</li>
                  <li>内容策略建议</li>
                </ul>
              </Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AIChat; 