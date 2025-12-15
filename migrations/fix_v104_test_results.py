"""修复v1.0.4数据库中的test_result字段

从output字段中重新提取正确的测试结果，修正错误的test_result值
"""

import sqlite3
import os
import sys
from datetime import datetime
import shutil


def extract_test_result_from_output(output: str) -> str:
    """从输出中提取测试结果
    
    Args:
        output: 执行输出文本
        
    Returns:
        测试结果：'pass'、'fail'、'pending'等（使用英文，与数据库一致）
    """
    if not output:
        return 'pending'
    
    # 从后往前查找，最后的结果最准确
    lines = output.split('\n')
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        
        line_lower = line.lower()
        
        # 检查合格标识（排除"不合格"中的"合格"）
        if '合格' in line and '不合格' not in line:
            return 'pass'
        elif 'pass' in line_lower and 'fail' not in line_lower:
            return 'pass'
        
        # 检查不合格标识
        elif '不合格' in line:
            return 'fail'
        elif 'fail' in line_lower:
            return 'fail'
        
        # 检查待判定标识
        elif '待判定' in line or '需要确认' in line:
            return 'pending'
        elif 'pending' in line_lower:
            return 'pending'
    
    # 如果没有找到明确的结果标识，返回待判定
    return 'pending'


def fix_test_results(db_path='data/script_executor.db'):
    """修复test_result字段
    
    Args:
        db_path: 数据库文件路径
    """
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        # 备份数据库
        backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(db_path, backup_path)
        print(f"✅ 已备份数据库到: {backup_path}")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查test_result字段是否存在
        cursor.execute("PRAGMA table_info(execution_history)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'test_result' not in columns:
            print("⚠️  test_result字段不存在，跳过修复")
            conn.close()
            return True
        
        # 查询所有有output的记录
        cursor.execute("""
            SELECT id, test_result, output, status
            FROM execution_history
            WHERE output IS NOT NULL AND output != ''
        """)
        
        records = cursor.fetchall()
        print(f"\n📊 找到 {len(records)} 条有输出的记录")
        
        if len(records) == 0:
            print("✅ 没有需要修复的记录")
            conn.close()
            return True
        
        # 统计修复情况
        fix_stats = {
            'pass': 0,
            'fail': 0,
            'pending': 0,
            '未变更': 0
        }
        
        # 逐条检查并修复
        fixed_count = 0
        for record_id, old_result, output, status in records:
            # 从output中提取正确的结果
            correct_result = extract_test_result_from_output(output)
            
            # 如果结果不同，则更新
            if old_result != correct_result:
                cursor.execute("""
                    UPDATE execution_history
                    SET test_result = ?
                    WHERE id = ?
                """, (correct_result, record_id))
                
                fix_stats[correct_result] += 1
                fixed_count += 1
                
                if fixed_count <= 10:  # 只显示前10条
                    print(f"  修复: {record_id[:20]}... | {old_result} → {correct_result}")
            else:
                fix_stats['未变更'] += 1
        
        # 提交更改
        conn.commit()
        
        print(f"\n✅ 成功修复 {fixed_count} 条记录:")
        print(f"   - 修正为pass(合格): {fix_stats['pass']}")
        print(f"   - 修正为fail(不合格): {fix_stats['fail']}")
        print(f"   - 保持pending(待判定): {fix_stats['pending']}")
        print(f"   - 无需变更: {fix_stats['未变更']}")
        
        # 验证修复结果
        cursor.execute("""
            SELECT test_result, COUNT(*)
            FROM execution_history
            GROUP BY test_result
        """)
        
        print(f"\n📊 修复后的数据分布:")
        for result, count in cursor.fetchall():
            print(f"   - {result}: {count}")
        
        conn.close()
        
        print(f"\n✅ 数据修复完成！")
        print(f"💡 如果遇到问题，可以从备份恢复: {backup_path}")
        
        return True
    
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # 支持命令行参数指定数据库路径
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'data/script_executor.db'
    
    print("=" * 60)
    print("🔧 v1.0.4数据库test_result字段修复工具")
    print("=" * 60)
    print(f"数据库路径: {db_path}")
    print()
    print("功能说明:")
    print("  - 从output字段中重新提取测试结果")
    print("  - 修正错误的test_result值")
    print("  - 自动备份数据库")
    print()
    
    success = fix_test_results(db_path)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ 修复成功！现在可以正确显示历史测试结果了")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ 修复失败，请检查错误信息")
        print("=" * 60)
        sys.exit(1)