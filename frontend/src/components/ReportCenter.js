import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Table,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  DatePicker,
  Select,
  Modal,
  message,
  Tag,
  Tooltip,
  Spin,
  Empty,
  Popconfirm
} from 'antd';
import {
  FileTextOutlined,
  DownloadOutlined,
  EyeOutlined,
  DeleteOutlined,
  CalendarOutlined,
  ReloadOutlined,
  PlusOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import api, { reportAPI } from '../services/api';
import moment from 'moment';
import './ReportCenter.css';

const { Title, Text } = Typography;
const { Option } = Select;

const ReportCenter = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [currentReport, setCurrentReport] = useState(null);
  const [generateModalVisible, setGenerateModalVisible] = useState(false);
  const [reportType, setReportType] = useState('daily');
  const [selectedDate, setSelectedDate] = useState(moment().subtract(1, 'day'));

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    setLoading(true);
    try {
      const response = await reportAPI.getList();
      if (response.success) {
        setReports(response.reports);
      } else {
        message.error('获取报告列表失败');
      }
    } catch (error) {
      console.error('获取报告列表失败:', error);
      message.error('获取报告列表失败');
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    try {
      let response;
      let requestData = {};

      if (reportType === 'daily') {
        requestData = {
          target_date: selectedDate.format('YYYY-MM-DD')
        };
        response = await reportAPI.generateDaily(requestData);
      } else if (reportType === 'weekly') {
        // 获取周开始日期（周一）
        const weekStart = selectedDate.clone().startOf('week').add(1, 'day');
        requestData = {
          week_start: weekStart.format('YYYY-MM-DD')
        };
        response = await reportAPI.generateWeekly(requestData);
      }
      
      if (response.success) {
        message.success('报告生成成功！');
        setGenerateModalVisible(false);
        loadReports(); // 刷新报告列表
      } else {
        message.error(response.message || '报告生成失败');
      }
    } catch (error) {
      console.error('生成报告失败:', error);
      message.error('生成报告失败');
    } finally {
      setGenerating(false);
    }
  };

  const viewReport = async (filename) => {
    try {
      const response = await reportAPI.view(filename);
      if (response.success) {
        setCurrentReport({
          filename: response.filename,
          content: response.content
        });
        setViewModalVisible(true);
      } else {
        message.error('查看报告失败');
      }
    } catch (error) {
      console.error('查看报告失败:', error);
      message.error('查看报告失败');
    }
  };

  const downloadReport = async (filename) => {
    try {
      const blob = await reportAPI.download(filename);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      message.success('报告下载成功');
    } catch (error) {
      console.error('下载报告失败:', error);
      message.error('下载报告失败');
    }
  };

  const deleteReport = async (filename) => {
    try {
      const response = await reportAPI.delete(filename);
      if (response.success) {
        message.success('报告删除成功');
        loadReports(); // 刷新列表
      } else {
        message.error('删除报告失败');
      }
    } catch (error) {
      console.error('删除报告失败:', error);
      message.error('删除报告失败');
    }
  };

  const getReportTypeTag = (filename) => {
    if (filename.includes('daily')) {
      return <Tag color="blue">日报</Tag>;
    } else if (filename.includes('weekly')) {
      return <Tag color="green">周报</Tag>;
    } else if (filename.includes('monthly')) {
      return <Tag color="purple">月报</Tag>;
    }
    return <Tag color="default">报告</Tag>;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const columns = [
    {
      title: '报告名称',
      dataIndex: 'filename',
      key: 'filename',
      render: (filename) => (
        <Space>
          <FileTextOutlined />
          <Text strong>{filename}</Text>
          {getReportTypeTag(filename)}
        </Space>
      ),
    },
    {
      title: '文件大小',
      dataIndex: 'size',
      key: 'size',
      render: (size) => formatFileSize(size),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => moment(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '修改时间',
      dataIndex: 'modified_at',
      key: 'modified_at',
      render: (time) => moment(time).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看报告">
            <Button
              type="primary"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => viewReport(record.filename)}
            />
          </Tooltip>
          <Tooltip title="下载报告">
            <Button
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => downloadReport(record.filename)}
            />
          </Tooltip>
          <Tooltip title="删除报告">
            <Popconfirm
              title="确定要删除这个报告吗？"
              onConfirm={() => deleteReport(record.filename)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="report-center">
      <Card
        title={
          <Space>
            <BarChartOutlined />
            <Title level={4} style={{ margin: 0 }}>自动化分析报告中心</Title>
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setGenerateModalVisible(true)}
            >
              生成报告
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadReports}
              loading={loading}
            >
              刷新
            </Button>
          </Space>
        }
      >
        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small" className="stat-card">
              <div className="stat-content">
                <div className="stat-value">{reports.length}</div>
                <div className="stat-label">总报告数</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small" className="stat-card">
              <div className="stat-content">
                <div className="stat-value">
                  {reports.filter(r => r.filename.includes('daily')).length}
                </div>
                <div className="stat-label">日报数量</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small" className="stat-card">
              <div className="stat-content">
                <div className="stat-value">
                  {reports.filter(r => r.filename.includes('weekly')).length}
                </div>
                <div className="stat-label">周报数量</div>
              </div>
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small" className="stat-card">
              <div className="stat-content">
                <div className="stat-value">
                  {formatFileSize(reports.reduce((sum, r) => sum + r.size, 0))}
                </div>
                <div className="stat-label">总文件大小</div>
              </div>
            </Card>
          </Col>
        </Row>

        <Divider />

        {/* 报告列表 */}
        <Table
          columns={columns}
          dataSource={reports}
          rowKey="filename"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个报告`,
          }}
          locale={{
            emptyText: (
              <Empty
                description="暂无报告"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
        />
      </Card>

      {/* 生成报告模态框 */}
      <Modal
        title="生成新报告"
        open={generateModalVisible}
        onOk={generateReport}
        onCancel={() => setGenerateModalVisible(false)}
        confirmLoading={generating}
        okText="生成报告"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text strong>报告类型：</Text>
            <Select
              value={reportType}
              onChange={setReportType}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Option value="daily">日报</Option>
              <Option value="weekly">周报</Option>
            </Select>
          </div>
          
          <div>
            <Text strong>
              {reportType === 'daily' ? '目标日期：' : '目标周：'}
            </Text>
            <DatePicker
              value={selectedDate}
              onChange={setSelectedDate}
              style={{ width: '100%', marginTop: 8 }}
              format="YYYY-MM-DD"
              placeholder={reportType === 'daily' ? '选择日期' : '选择周内任意日期'}
            />
          </div>
          
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">
              {reportType === 'daily' 
                ? '将生成指定日期的数据分析日报' 
                : '将生成指定日期所在周的数据分析周报'
              }
            </Text>
          </div>
        </Space>
      </Modal>

      {/* 查看报告模态框 */}
      <Modal
        title={
          <Space>
            <FileTextOutlined />
            <span>查看报告 - {currentReport?.filename}</span>
          </Space>
        }
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={() => downloadReport(currentReport?.filename)}>
            下载
          </Button>,
          <Button key="close" onClick={() => setViewModalVisible(false)}>
            关闭
          </Button>,
        ]}
        width={1000}
        style={{ top: 20 }}
      >
        <div className="report-content">
          {currentReport && (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
              components={{
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
                table: ({children}) => (
                  <table className="markdown-table">{children}</table>
                ),
                a: ({href, children}) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                )
              }}
            >
              {currentReport.content}
            </ReactMarkdown>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default ReportCenter; 