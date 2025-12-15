"""测试日期查询逻辑"""

import sqlite3
from datetime import datetime
import os

# 数据库路径
db_path = os.path.join('data', 'script_executor.db')

if not os.path.exists(db_path):
    print(f"❌ 数据库文件不存在: {db_path}")
    exit(1)

# 连接数据库
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# 获取今天的日期
today = datetime.now().strftime('%Y-%m-%d')
print(f"今天的日期: {today}\n")

# 模拟 ResultViewer 的查询逻辑
start_date = today  # 今天
end_date = today    # 今天

print(f"查询日期范围: {start_date} 到 {end_date}\n")

# 添加时间部分（模拟 get_by_date_range 的逻辑）
start_datetime = f"{start_date} 00:00:00"
end_datetime = f"{end_date} 23:59:59"

print(f"实际查询范围: {start_datetime} 到 {end_datetime}\n")

# 查询所有今天的记录
cursor.execute("""
    SELECT id, script_path, status, test_result, start_time
    FROM execution_history
    WHERE start_time LIKE ?
    ORDER BY start_time DESC
""", (f"{today}%",))

all_today_records = cursor.fetchall()
print(f"=== 数据库中今天的所有记录（{len(all_today_records)}条）===\n")

for record in all_today_records[:10]:  # 只显示前10条
    start_time = record['start_time']
    # 提取时间部分
    record_datetime = start_time.replace('T', ' ').split('.')[0]
    if len(record_datetime) == 10:
        record_datetime = f"{record_datetime} 00:00:00"
    
    # 检查是否在范围内
    in_range = start_datetime <= record_datetime <= end_datetime
    
    print(f"ID: {record['id'][:20]}...")
    print(f"  start_time: {start_time}")
    print(f"  处理后: {record_datetime}")
    print(f"  在范围内: {in_range}")
    print(f"  状态: {record['status']}, 结果: {record['test_result']}")
    print()

# 测试字符串比较
print("=== 字符串比较测试 ===\n")
test_times = [
    "2025-12-15T13:46:00",
    "2025-12-15 13:46:00",
    "2025-12-15T13:46:00.123456",
    "2025-12-15",
]

for test_time in test_times:
    record_datetime = test_time.replace('T', ' ').split('.')[0]
    if len(record_datetime) == 10:
        record_datetime = f"{record_datetime} 00:00:00"
    
    in_range = start_datetime <= record_datetime <= end_datetime
    print(f"原始: {test_time}")
    print(f"处理后: {record_datetime}")
    print(f"在范围内: {in_range}")
    print()

conn.close()

print("✅ 测试完成")