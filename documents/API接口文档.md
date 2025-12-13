# Python脚本批量执行工具 - API接口文档

## 文档信息
- **版本**: v1.0
- **创建日期**: 2024-12-11
- **文档类型**: API接口规范
- **目标读者**: 开发团队、集成人员

---

## 目录
1. [API概述](#1-api概述)
2. [认证授权](#2-认证授权)
3. [接口列表](#3-接口列表)
4. [数据模型](#4-数据模型)
5. [错误处理](#5-错误处理)
6. [使用示例](#6-使用示例)

---

## 1. API概述

### 1.1 基本信息
- **协议**: HTTP/HTTPS
- **格式**: JSON
- **编码**: UTF-8
- **基础URL**: `http://localhost:5000/api/v1`
- **版本**: v1.0

### 1.2 设计原则
- RESTful风格
- 统一的响应格式
- 完善的错误处理
- 支持分页和过滤
- 版本化管理

### 1.3 通用响应格式

**成功响应**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        // 具体数据
    },
    "timestamp": "2024-12-11T15:30:00Z"
}
```

**错误响应**:
```json
{
    "code": 400,
    "message": "Bad Request",
    "error": {
        "type": "ValidationError",
        "details": "Invalid parameter: script_id"
    },
    "timestamp": "2024-12-11T15:30:00Z"
}
```

---

## 2. 认证授权

### 2.1 认证方式

**Token认证**:
```http
Authorization: Bearer <access_token>
```

### 2.2 获取Token

**接口**: `POST /api/v1/auth/login`

**请求**:
```json
{
    "username": "admin",
    "password": "password123"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "Login successful",
    "data": {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "Bearer",
        "expires_in": 3600,
        "user": {
            "user_id": "user_001",
            "username": "admin",
            "role": "admin"
        }
    }
}
```

### 2.3 刷新Token

**接口**: `POST /api/v1/auth/refresh`

**请求头**:
```http
Authorization: Bearer <access_token>
```

**响应**:
```json
{
    "code": 200,
    "data": {
        "access_token": "new_token_here",
        "expires_in": 3600
    }
}
```

---

## 3. 接口列表

### 3.1 脚本管理

#### 3.1.1 获取脚本列表

**接口**: `GET /api/v1/scripts`

**查询参数**:
- `keyword` (string, optional): 搜索关键字
- `module` (string, optional): 模块名
- `status` (string, optional): 状态
- `page` (int, optional): 页码，默认1
- `page_size` (int, optional): 每页数量，默认20

**请求示例**:
```http
GET /api/v1/scripts?module=Demo&page=1&page_size=20
Authorization: Bearer <token>
```

**响应**:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "script_id": "script_001",
                "file_path": "TestScripts/Demo/test.py",
                "file_name": "test.py",
                "module_name": "Demo",
                "status": "idle",
                "last_result": "PASS",
                "execution_count": 10,
                "success_rate": 90.0
            }
        ],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5
    }
}
```

#### 3.1.2 获取脚本详情

**接口**: `GET /api/v1/scripts/{script_id}`

**响应**:
```json
{
    "code": 200,
    "data": {
        "script_id": "script_001",
        "file_path": "TestScripts/Demo/test.py",
        "file_name": "test.py",
        "module_name": "Demo",
        "description": "测试脚本",
        "status": "idle",
        "last_result": "PASS",
        "last_execution_time": "2024-12-11T14:30:00Z",
        "execution_count": 10,
        "success_count": 9,
        "failed_count": 1,
        "avg_duration": 5.2,
        "file_size": 1024,
        "last_modified": "2024-12-10T10:00:00Z"
    }
}
```

#### 3.1.3 刷新脚本列表

**接口**: `POST /api/v1/scripts/refresh`

**响应**:
```json
{
    "code": 200,
    "message": "Scripts refreshed successfully",
    "data": {
        "total_scripts": 150,
        "new_scripts": 5,
        "updated_scripts": 3
    }
}
```

### 3.2 脚本执行

#### 3.2.1 执行脚本

**接口**: `POST /api/v1/execute`

**请求**:
```json
{
    "script_ids": ["script_001", "script_002"],
    "mode": "parallel",
    "max_parallel": 5,
    "timeout": 300,
    "batch_name": "测试批次"
}
```

**响应**:
```json
{
    "code": 200,
    "message": "Execution started",
    "data": {
        "batch_id": "batch_20241211_001",
        "total_scripts": 2,
        "execution_mode": "parallel",
        "start_time": "2024-12-11T15:30:00Z"
    }
}
```

#### 3.2.2 停止执行

**接口**: `POST /api/v1/execute/{batch_id}/stop`

**响应**:
```json
{
    "code": 200,
    "message": "Execution stopped",
    "data": {
        "batch_id": "batch_20241211_001",
        "stopped_count": 3
    }
}
```

#### 3.2.3 获取执行状态

**接口**: `GET /api/v1/execute/{batch_id}/status`

**响应**:
```json
{
    "code": 200,
    "data": {
        "batch_id": "batch_20241211_001",
        "status": "running",
        "total_scripts": 10,
        "completed_count": 7,
        "success_count": 6,
        "failed_count": 1,
        "running_count": 3,
        "progress": 70.0,
        "start_time": "2024-12-11T15:30:00Z",
        "estimated_remaining": 120
    }
}
```

### 3.3 执行历史

#### 3.3.1 获取执行历史

**接口**: `GET /api/v1/history`

**查询参数**:
- `script_path` (string, optional): 脚本路径
- `batch_id` (string, optional): 批次ID
- `status` (string, optional): 状态
- `start_date` (string, optional): 开始日期
- `end_date` (string, optional): 结束日期
- `page` (int, optional): 页码
- `page_size` (int, optional): 每页数量

**响应**:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "record_id": "record_001",
                "script_path": "TestScripts/Demo/test.py",
                "batch_id": "batch_20241211_001",
                "status": "SUCCESS",
                "result": "PASS",
                "start_time": "2024-12-11T15:30:00Z",
                "end_time": "2024-12-11T15:30:05Z",
                "duration": 5.2,
                "memory_usage": 50.5,
                "cpu_usage": 25.3
            }
        ],
        "total": 500,
        "page": 1,
        "page_size": 20
    }
}
```

#### 3.3.2 获取执行详情

**接口**: `GET /api/v1/history/{record_id}`

**响应**:
```json
{
    "code": 200,
    "data": {
        "record_id": "record_001",
        "script_path": "TestScripts/Demo/test.py",
        "script_name": "test.py",
        "batch_id": "batch_20241211_001",
        "status": "SUCCESS",
        "result": "PASS",
        "start_time": "2024-12-11T15:30:00Z",
        "end_time": "2024-12-11T15:30:05Z",
        "duration": 5.2,
        "output": "Test passed successfully",
        "error_message": null,
        "memory_usage": 50.5,
        "cpu_usage": 25.3,
        "exit_code": 0
    }
}
```

### 3.4 统计分析

#### 3.4.1 获取统计信息

**接口**: `GET /api/v1/statistics`

**查询参数**:
- `start_date` (string, optional): 开始日期
- `end_date` (string, optional): 结束日期
- `group_by` (string, optional): 分组方式 (day/week/month)

**响应**:
```json
{
    "code": 200,
    "data": {
        "total_executions": 1000,
        "success_count": 850,
        "failed_count": 100,
        "error_count": 50,
        "success_rate": 85.0,
        "avg_duration": 5.5,
        "total_duration": 5500.0,
        "by_date": [
            {
                "date": "2024-12-11",
                "executions": 100,
                "success_count": 85,
                "failed_count": 15
            }
        ]
    }
}
```

#### 3.4.2 生成报告

**接口**: `POST /api/v1/reports/generate`

**请求**:
```json
{
    "batch_id": "batch_20241211_001",
    "format": "html",
    "include_details": true
}
```

**响应**:
```json
{
    "code": 200,
    "message": "Report generated successfully",
    "data": {
        "report_id": "report_001",
        "download_url": "/api/v1/reports/report_001/download",
        "format": "html",
        "size": 102400
    }
}
```

### 3.5 用户管理

#### 3.5.1 获取用户列表

**接口**: `GET /api/v1/users`

**权限**: admin

**响应**:
```json
{
    "code": 200,
    "data": {
        "items": [
            {
                "user_id": "user_001",
                "username": "admin",
                "role": "admin",
                "email": "admin@example.com",
                "is_active": true,
                "last_login": "2024-12-11T15:00:00Z"
            }
        ],
        "total": 10
    }
}
```

#### 3.5.2 创建用户

**接口**: `POST /api/v1/users`

**权限**: admin

**请求**:
```json
{
    "username": "newuser",
    "password": "password123",
    "role": "user",
    "email": "newuser@example.com",
    "full_name": "New User"
}
```

**响应**:
```json
{
    "code": 201,
    "message": "User created successfully",
    "data": {
        "user_id": "user_002",
        "username": "newuser",
        "role": "user"
    }
}
```

---

## 4. 数据模型

### 4.1 ScriptInfo

```typescript
interface ScriptInfo {
    script_id: string;
    file_path: string;
    file_name: string;
    module_name: string;
    description?: string;
    status: 'idle' | 'running' | 'success' | 'failed' | 'error';
    last_result?: 'PASS' | 'FAIL' | 'UNKNOWN';
    last_execution_time?: string;
    execution_count: number;
    success_count: number;
    failed_count: number;
    success_rate: number;
    avg_duration: number;
}
```

### 4.2 ExecutionRecord

```typescript
interface ExecutionRecord {
    record_id: string;
    script_path: string;
    script_name: string;
    batch_id?: string;
    status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'ERROR' | 'TIMEOUT';
    result?: 'PASS' | 'FAIL' | 'UNKNOWN';
    start_time: string;
    end_time?: string;
    duration: number;
    output?: string;
    error_message?: string;
    memory_usage: number;
    cpu_usage: number;
    exit_code?: number;
}
```

### 4.3 BatchExecution

```typescript
interface BatchExecution {
    batch_id: string;
    batch_name?: string;
    total_scripts: number;
    completed_count: number;
    success_count: number;
    failed_count: number;
    error_count: number;
    start_time: string;
    end_time?: string;
    duration: number;
    execution_mode: 'sequential' | 'parallel';
    status: 'pending' | 'running' | 'completed' | 'cancelled';
}
```

---

## 5. 错误处理

### 5.1 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

### 5.2 错误类型

```json
{
    "code": 400,
    "message": "Validation Error",
    "error": {
        "type": "ValidationError",
        "details": "Invalid script_id format",
        "field": "script_id"
    }
}
```

**错误类型**:
- `ValidationError`: 参数验证错误
- `AuthenticationError`: 认证失败
- `PermissionError`: 权限不足
- `ResourceNotFoundError`: 资源不存在
- `ExecutionError`: 执行错误
- `InternalError`: 内部错误

---

## 6. 使用示例

### 6.1 Python示例

```python
import requests

# 基础配置
BASE_URL = "http://localhost:5000/api/v1"
token = None

# 登录获取token
def login(username, password):
    global token
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": username, "password": password}
    )
    data = response.json()
    token = data['data']['access_token']
    return token

# 获取脚本列表
def get_scripts():
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/scripts", headers=headers)
    return response.json()

# 执行脚本
def execute_scripts(script_ids, mode="parallel"):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{BASE_URL}/execute",
        headers=headers,
        json={
            "script_ids": script_ids,
            "mode": mode,
            "batch_name": "API测试批次"
        }
    )
    return response.json()

# 查询执行状态
def get_execution_status(batch_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/execute/{batch_id}/status",
        headers=headers
    )
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 1. 登录
    login("admin", "password123")
    
    # 2. 获取脚本列表
    scripts = get_scripts()
    print(f"Total scripts: {scripts['data']['total']}")
    
    # 3. 执行脚本
    script_ids = [item['script_id'] for item in scripts['data']['items'][:5]]
    result = execute_scripts(script_ids)
    batch_id = result['data']['batch_id']
    print(f"Batch ID: {batch_id}")
    
    # 4. 查询状态
    status = get_execution_status(batch_id)
    print(f"Progress: {status['data']['progress']}%")
```

### 6.2 cURL示例

```bash
# 登录
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'

# 获取脚本列表
curl -X GET http://localhost:5000/api/v1/scripts \
  -H "Authorization: Bearer <token>"

# 执行脚本
curl -X POST http://localhost:5000/api/v1/execute \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "script_ids": ["script_001", "script_002"],
    "mode": "parallel",
    "batch_name": "测试批次"
  }'

# 查询执行状态
curl -X GET http://localhost:5000/api/v1/execute/batch_001/status \
  -H "Authorization: Bearer <token>"
```

---

## 附录

### A. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2024-12-11 | 初始版本 |

### B. 联系方式

- **技术支持**: support@example.com
- **API问题**: api@example.com

---

**文档维护**: 开发团队  
**最后更新**: 2024-12-11