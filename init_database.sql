-- B站数据分析系统数据库初始化脚本
-- 请在MySQL中执行此脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS bilibili_analysis 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE bilibili_analysis;

-- 创建视频表
CREATE TABLE IF NOT EXISTS videos (
    bvid VARCHAR(20) PRIMARY KEY COMMENT '视频BV号',
    title TEXT COMMENT '视频标题',
    aid VARCHAR(20) COMMENT '视频AV号',
    author VARCHAR(100) COMMENT '作者名称',
    mid VARCHAR(20) COMMENT '作者UID',
    view INT DEFAULT 0 COMMENT '播放量',
    danmaku INT DEFAULT 0 COMMENT '弹幕数',
    reply INT DEFAULT 0 COMMENT '评论数',
    favorite INT DEFAULT 0 COMMENT '收藏数',
    coin INT DEFAULT 0 COMMENT '投币数',
    share INT DEFAULT 0 COMMENT '分享数',
    `like` INT DEFAULT 0 COMMENT '点赞数',
    duration INT DEFAULT 0 COMMENT '视频时长(秒)',
    pubdate DATETIME COMMENT '发布时间',
    tid INT COMMENT '分区ID',
    tname VARCHAR(50) COMMENT '分区名称',
    copyright TINYINT DEFAULT 0 COMMENT '版权标识',
    tags TEXT COMMENT '标签(逗号分隔)',
    `desc` TEXT COMMENT '视频描述',
    ctime DATETIME COMMENT '创建时间',
    collected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    
    INDEX idx_mid (mid),
    INDEX idx_pubdate (pubdate),
    INDEX idx_tid (tid),
    INDEX idx_view (view),
    INDEX idx_collected_at (collected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='视频数据表';

-- 创建用户数据表
CREATE TABLE IF NOT EXISTS user_data (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    user_mid VARCHAR(20) NOT NULL COMMENT '用户UID',
    data_type VARCHAR(50) NOT NULL COMMENT '数据类型(watch_history/favorites)',
    data_content JSON COMMENT '数据内容(JSON格式)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_user_mid (user_mid),
    INDEX idx_data_type (data_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户数据表';

-- 创建系统日志表(可选)
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增ID',
    log_type VARCHAR(50) NOT NULL COMMENT '日志类型',
    log_level VARCHAR(20) DEFAULT 'INFO' COMMENT '日志级别',
    message TEXT COMMENT '日志消息',
    details JSON COMMENT '详细信息',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    INDEX idx_log_type (log_type),
    INDEX idx_log_level (log_level),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';

-- 插入一些示例数据(可选)
-- INSERT INTO videos (bvid, title, author, view, `like`, pubdate, tname, collected_at) VALUES
-- ('BV1234567890', '示例视频标题', '示例UP主', 10000, 500, NOW(), '生活', NOW());

-- 显示创建的表
SHOW TABLES;

-- 显示表结构
DESCRIBE videos;
DESCRIBE user_data;

SELECT 'Database initialization completed successfully!' AS status; 