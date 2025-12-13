-- 数据库迁移脚本 v1.1
-- 功能：扩展执行结果状态 + 添加测试方案管理
-- 日期：2025-12-12
-- 作者：开发团队

-- ============================================
-- 第一部分：扩展执行结果状态（需求6）
-- ============================================

-- 1. 为 execution_history 表添加 test_result 字段
ALTER TABLE execution_history ADD COLUMN test_result VARCHAR(20) DEFAULT '-';

-- 2. 为 batch_executions 表添加新的统计字段
ALTER TABLE batch_executions ADD COLUMN pending_scripts INTEGER DEFAULT 0;
ALTER TABLE batch_executions ADD COLUMN error_scripts INTEGER DEFAULT 0;
ALTER TABLE batch_executions ADD COLUMN timeout_scripts INTEGER DEFAULT 0;

-- 3. 更新现有数据的 test_result（基于 status 字段推断）
UPDATE execution_history 
SET test_result = CASE 
    WHEN status = 'SUCCESS' THEN '合格'
    WHEN status = 'FAILED' THEN '不合格'
    WHEN status = 'ERROR' THEN '执行错误'
    WHEN status = 'TIMEOUT' THEN '超时'
    WHEN status = 'PENDING' THEN '待判定'
    ELSE '-'
END
WHERE test_result = '-';

-- ============================================
-- 第二部分：测试方案管理（需求3）
-- ============================================

-- 4. 创建测试方案表
CREATE TABLE IF NOT EXISTS test_suites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    script_paths TEXT NOT NULL,
    script_count INTEGER DEFAULT 0,
    created_by VARCHAR(50),
    created_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_executed_time DATETIME,
    execution_count INTEGER DEFAULT 0
);

-- 5. 为 batch_executions 表添加 suite_id 字段
ALTER TABLE batch_executions ADD COLUMN suite_id INTEGER;
ALTER TABLE batch_executions ADD COLUMN suite_name VARCHAR(100);

-- 6. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_execution_history_test_result ON execution_history(test_result);
CREATE INDEX IF NOT EXISTS idx_execution_history_batch_id ON execution_history(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_executions_suite_id ON batch_executions(suite_id);
CREATE INDEX IF NOT EXISTS idx_batch_executions_status ON batch_executions(status);
CREATE INDEX IF NOT EXISTS idx_test_suites_name ON test_suites(name);

-- ============================================
-- 第三部分：数据验证
-- ============================================

-- 验证表结构
SELECT 'execution_history columns:' as info;
PRAGMA table_info(execution_history);

SELECT 'batch_executions columns:' as info;
PRAGMA table_info(batch_executions);

SELECT 'test_suites columns:' as info;
PRAGMA table_info(test_suites);

-- 统计信息
SELECT 'Migration completed successfully!' as status;
SELECT COUNT(*) as total_executions FROM execution_history;
SELECT COUNT(*) as total_batches FROM batch_executions;
SELECT COUNT(*) as total_suites FROM test_suites;