# Ruby Eve UI Test API 接口文档

## 概述

Ruby Eve UI Test API 是一个基于 Flask 的 RESTful API 服务，用于执行 iOS UI 自动化测试任务。支持任务管理、状态查询、日志查看等功能。

**默认服务地址**: `http://0.0.0.0:8005`

**启动命令**:
```bash
python main/api_server.py [--host 0.0.0.0] [--port 8005] [--debug]
```

---

## 目录

- [测试任务管理](#测试任务管理)
  - [执行测试任务](#1-执行测试任务)
  - [查询任务状态](#2-查询任务状态)
  - [列出任务](#3-列出任务)
  - [获取任务日志](#4-获取任务日志)
  - [获取任务结果](#5-获取任务结果)
  - [取消任务](#6-取消任务)
- [设备管理](#设备管理)
  - [列出所有设备](#7-列出所有设备)
- [系统管理](#系统管理)
  - [健康检查](#8-健康检查)

---

## 测试任务管理

### 1. 执行测试任务

创建并启动一个新的测试任务。

**接口**: `POST /api/test/run`

**请求头**:
```
Content-Type: application/json
```

**请求参数** (JSON Body):

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `bundleId` 或 `bundle_id` | string | ✅ | - | 应用的 Bundle ID |
| `device` | string | ✅ | - | 设备名称（需在 `utils/devices.yaml` 中配置） |
| `test` | string | ❌ | `tests/test_ui_flow.yaml` | 测试用例文件路径 |
| `app` | string | ❌ | - | 应用安装包路径。支持：<br>- 绝对路径<br>- 相对路径（仅本地部署）<br>- `auto_v`：自动下载最新 V 版本包<br>- `auto_m`：自动下载最新 M 版本包 |
| `reinstall` | boolean | ❌ | `false` | 是否重新安装应用 |
| `times` | integer | ❌ | `1` | 执行次数 |
| `device_name` | string | ❌ | - | 用于 `check_connected`、`connect` 等方法的设备名称 |
| `cases` 或 `case` | string/array | ❌ | - | 用例名过滤，支持：<br>- 字符串（逗号分隔）：`"case1,case2"`<br>- 数组：`["case1", "case2"]` |
| `appium_host` | string | ❌ | `127.0.0.1` | Appium 服务器地址（支持远程连接） |
| `base_port` | integer | ❌ | `4723` | Appium 基础端口号 |
| `devices` | string | ❌ | `utils/devices.yaml` | 设备配置文件路径 |

**请求示例**:

```json
{
  "bundleId": "com.example.app",
  "device": "iPad-Pro",
  "test": "tests/test_ui_flow.yaml",
  "app": "auto_v",
  "reinstall": true,
  "times": 3,
  "cases": ["test_login", "test_home"],
  "appium_host": "127.0.0.1"
}
```

**响应示例** (HTTP 202):

```json
{
  "success": true,
  "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
  "message": "测试任务已创建，正在下载最新包并执行测试（将执行 3 次）",
  "status_url": "/api/test/status/0580fdab-9ff3-4ff2-ab98-4a4d665ac956"
}
```

**错误响应**:

- `400 Bad Request`: 缺少必需参数或参数错误
  ```json
  {
    "error": "缺少必需参数: bundleId"
  }
  ```

- `500 Internal Server Error`: 服务器内部错误
  ```json
  {
    "error": "创建测试任务失败: ..."
  }
  ```

**注意事项**:

1. **自动下载功能**: 当 `app` 为 `auto_v` 或 `auto_m` 时，系统会自动下载最新包。需要确保：
   - `utils/ci_download/download_New_ipa.py` 存在
   - 已安装 `protobuf` 库：`pip install protobuf`
   - 已编译 proto 文件：`cd utils/ci_download && protoc --python_out=. omnibus_connect_builds.proto`

2. **分布式部署**: 当 `appium_host` 为远程 IP 时：
   - `app` 必须是 Appium 机器上的绝对路径
   - 不支持相对路径
   - 自动下载的文件在服务器端，Appium 无法访问（需要手动传输或使用共享存储）

3. **任务执行**: 任务在后台异步执行，立即返回 `task_id`，可通过状态查询接口获取执行进度。

---

### 2. 查询任务状态

查询指定任务的当前状态和详细信息。

**接口**: `GET /api/test/status/<task_id>`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `task_id` | string | ✅ | 任务 ID（UUID） |

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `include_log` | boolean | ❌ | `false` | 是否包含日志内容 |

**请求示例**:

```
GET /api/test/status/0580fdab-9ff3-4ff2-ab98-4a4d665ac956
GET /api/test/status/0580fdab-9ff3-4ff2-ab98-4a4d665ac956?include_log=true
```

**响应示例** (HTTP 200):

```json
{
  "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
  "status": "running",
  "bundle_id": "com.example.app",
  "device": "iPad-Pro",
  "test_file": "tests/test_ui_flow.yaml",
  "app_path": "/path/to/app.ipa",
  "reinstall": true,
  "times": 3,
  "create_time": "2026-01-06T10:00:00",
  "start_time": "2026-01-06T10:00:05",
  "log_file": "logs/0580fdab-9ff3-4ff2-ab98-4a4d665ac956.log",
  "message": "正在执行测试..."
}
```

**包含日志的响应示例**:

```json
{
  "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
  "status": "running",
  "log_content": "[2026-01-06 10:00:05] 开始执行测试任务...\n...",
  ...
}
```

**任务状态说明**:

| 状态 | 说明 |
|------|------|
| `pending` | 等待执行 |
| `downloading` | 正在下载应用包（仅自动下载时） |
| `running` | 正在执行测试 |
| `completed` | 执行完成 |
| `failed` | 执行失败 |
| `cancelled` | 已取消 |

**错误响应**:

- `404 Not Found`: 任务不存在
  ```json
  {
    "error": "任务不存在"
  }
  ```

---

### 3. 列出任务

列出所有任务或按状态过滤任务。

**接口**: `GET /api/test/list`

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `status` | string | ❌ | `running` | 过滤条件：<br>- `running` 或不传：只返回正在执行的任务（pending, downloading, running）<br>- `all`：返回所有任务（限制最近50个）<br>- `completed`：只返回已完成的任务<br>- `failed`：只返回失败的任务<br>- `active`：返回所有非终态任务（pending, downloading, running） |

**请求示例**:

```
GET /api/test/list
GET /api/test/list?status=all
GET /api/test/list?status=completed
GET /api/test/list?status=failed
GET /api/test/list?status=active
```

**响应示例** (HTTP 200):

```json
{
  "total": 5,
  "filter": "running",
  "tasks": [
    {
      "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
      "status": "running",
      "bundle_id": "com.example.app",
      "device": "iPad-Pro",
      "create_time": "2026-01-06T10:00:00",
      ...
    },
    ...
  ]
}
```

**说明**:

- 任务列表按创建时间倒序排列
- `status=all` 时限制返回最近 50 个任务
- 默认只返回正在执行的任务，不包括历史任务

---

### 4. 获取任务日志

获取指定任务的完整日志内容。

**接口**: `GET /api/test/log/<task_id>`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `task_id` | string | ✅ | 任务 ID（UUID） |

**请求示例**:

```
GET /api/test/log/0580fdab-9ff3-4ff2-ab98-4a4d665ac956
```

**响应示例** (HTTP 200):

```json
{
  "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
  "log_file": "logs/0580fdab-9ff3-4ff2-ab98-4a4d665ac956.log",
  "log_content": "[2026-01-06 10:00:05] 开始执行测试任务...\n[2026-01-06 10:00:10] 第 1/3 次执行开始\n..."
}
```

**如果日志文件尚未创建**:

```json
{
  "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
  "log_content": "",
  "note": "日志文件尚未创建（任务可能还未开始执行）"
}
```

**错误响应**:

- `404 Not Found`: 任务不存在或日志文件路径不存在
  ```json
  {
    "error": "任务不存在"
  }
  ```

- `500 Internal Server Error`: 读取日志文件失败
  ```json
  {
    "error": "读取日志文件失败: ..."
  }
  ```

---

### 5. 获取任务结果

获取已完成任务的执行结果汇总。

**接口**: `GET /api/test/result/<task_id>`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `task_id` | string | ✅ | 任务 ID（UUID） |

**请求示例**:

```
GET /api/test/result/0580fdab-9ff3-4ff2-ab98-4a4d665ac956
```

**响应示例** (HTTP 200):

```json
{
  "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956",
  "status": "completed",
  "summary_text": "================================================================================\n🎯 测试执行完成汇总\n================================================================================\n📊 执行统计:\n   🔢 总执行次数: 3\n   📱 测试设备: iPad-Pro\n   📄 测试用例: tests/test_ui_flow.yaml\n   ✅ 成功次数: 8\n   ❌ 失败次数: 1\n   📈 成功率: 88.9%\n================================================================================\n💡 提示: 详细的执行日志请查看日志文件\n================================================================================",
  "statistics": {
    "total_runs": 3,
    "device": "iPad-Pro",
    "test_file": "tests/test_ui_flow.yaml",
    "total_passed": 8,
    "total_failed": 1,
    "total": 9,
    "success_rate": 88.89
  },
  "timeline": {
    "create_time": "2026-01-06T10:00:00",
    "start_time": "2026-01-06T10:00:05",
    "end_time": "2026-01-06T10:15:30"
  },
  "screenshot_dir": "screenshots/run_20260106_100005/",
  "error": null
}
```

**错误响应**:

- `404 Not Found`: 任务不存在
  ```json
  {
    "error": "任务不存在"
  }
  ```

- `400 Bad Request`: 任务尚未完成
  ```json
  {
    "error": "任务尚未完成",
    "status": "running",
    "message": "任务仍在执行中，请等待完成后查询结果"
  }
  ```

**说明**:

- 只有状态为 `completed`、`failed` 或 `cancelled` 的任务才能查询结果
- `summary_text` 提供格式化的文本摘要
- `statistics` 提供结构化的统计数据
- `screenshot_dir` 为截图保存目录（相对路径）

---

### 6. 取消任务

取消正在执行的任务。

**接口**: `POST /api/test/cancel/<task_id>`

**路径参数**:

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `task_id` | string | ✅ | 任务 ID（UUID） |

**请求示例**:

```
POST /api/test/cancel/0580fdab-9ff3-4ff2-ab98-4a4d665ac956
```

**响应示例** (HTTP 200):

```json
{
  "success": true,
  "message": "任务已标记为取消"
}
```

**错误响应**:

- `404 Not Found`: 任务不存在
  ```json
  {
    "error": "任务不存在"
  }
  ```

- `400 Bad Request`: 任务已完成，无法取消
  ```json
  {
    "error": "任务已完成，无法取消"
  }
  ```

**说明**:

- 取消操作会标记任务为 `cancelled` 状态
- 正在执行的测试会继续运行，但会在下次检查取消状态时停止
- 已完成的任务无法取消

---

## 设备管理

### 7. 列出所有设备

获取所有可用的测试设备列表。

**接口**: `GET /api/devices`

**查询参数**:

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `devices` | string | ❌ | `utils/devices.yaml` | 设备配置文件路径 |

**请求示例**:

```
GET /api/devices
GET /api/devices?devices=utils/devices.yaml
```

**响应示例** (HTTP 200):

```json
{
  "devices": [
    {
      "name": "iPad-Pro",
      "udid": "00008030-001A4D1E3A38802E",
      "platformName": "iOS",
      "appium_server": "http://127.0.0.1:4723"
    },
    {
      "name": "iPhone-14",
      "udid": "00008030-001A4D1E3A38802F",
      "platformName": "iOS",
      "appium_server": "http://127.0.0.1:4724"
    }
  ],
  "total": 2
}
```

**错误响应**:

- `500 Internal Server Error`: 加载设备列表失败
  ```json
  {
    "error": "加载设备列表失败: ..."
  }
  ```

**说明**:

- 设备配置从 `utils/devices.yaml` 文件读取
- 设备列表包含设备名称、UDID、平台类型和 Appium 服务器地址等信息

---

## 系统管理

### 8. 健康检查

检查 API 服务是否正常运行。

**接口**: `GET /api/health`

**请求示例**:

```
GET /api/health
```

**响应示例** (HTTP 200):

```json
{
  "status": "ok",
  "service": "Ruby Eve UI Test API",
  "timestamp": "2026-01-06T10:00:00"
}
```

---

## 任务状态说明

### 状态流转

```
pending → downloading → running → completed
                              ↓
                           failed
                              ↓
                         cancelled (可随时取消)
```

### 状态详情

| 状态 | 说明 | 可执行操作 |
|------|------|-----------|
| `pending` | 任务已创建，等待执行 | 查询状态、取消 |
| `downloading` | 正在下载应用包（仅自动下载时） | 查询状态、取消 |
| `running` | 正在执行测试 | 查询状态、取消 |
| `completed` | 测试执行完成 | 查询状态、查看结果、查看日志 |
| `failed` | 测试执行失败 | 查询状态、查看结果、查看日志 |
| `cancelled` | 任务已取消 | 查询状态、查看结果（如果有） |

---

## 错误码说明

| HTTP 状态码 | 说明 | 常见原因 |
|------------|------|---------|
| `200` | 成功 | 请求处理成功 |
| `202` | 已接受 | 任务已创建，正在后台执行 |
| `400` | 请求错误 | 参数缺失、参数格式错误、业务逻辑错误 |
| `404` | 资源不存在 | 任务不存在、文件不存在 |
| `500` | 服务器错误 | 内部错误、依赖缺失、文件读取失败 |

---

## 使用示例

### 完整流程示例

```bash
# 1. 健康检查
curl http://localhost:8005/api/health

# 2. 查看可用设备
curl http://localhost:8005/api/devices

# 3. 创建测试任务
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.example.app",
    "device": "iPad-Pro",
    "test": "tests/test_ui_flow.yaml",
    "app": "auto_v",
    "times": 3
  }'

# 返回: {"success": true, "task_id": "0580fdab-9ff3-4ff2-ab98-4a4d665ac956", ...}

# 4. 查询任务状态
curl http://localhost:8005/api/test/status/0580fdab-9ff3-4ff2-ab98-4a4d665ac956

# 5. 查看任务日志
curl http://localhost:8005/api/test/log/0580fdab-9ff3-4ff2-ab98-4a4d665ac956

# 6. 查看任务结果（完成后）
curl http://localhost:8005/api/test/result/0580fdab-9ff3-4ff2-ab98-4a4d665ac956

# 7. 列出所有任务
curl http://localhost:8005/api/test/list?status=all
```

### Python 客户端示例

```python
import requests
import time

BASE_URL = "http://localhost:8005"

# 创建测试任务
response = requests.post(f"{BASE_URL}/api/test/run", json={
    "bundleId": "com.example.app",
    "device": "iPad-Pro",
    "test": "tests/test_ui_flow.yaml",
    "app": "auto_v",
    "times": 3
})
task_id = response.json()["task_id"]
print(f"任务已创建: {task_id}")

# 轮询任务状态
while True:
    status_response = requests.get(f"{BASE_URL}/api/test/status/{task_id}")
    status = status_response.json()
    
    print(f"当前状态: {status['status']}")
    
    if status['status'] in ['completed', 'failed', 'cancelled']:
        # 获取最终结果
        result_response = requests.get(f"{BASE_URL}/api/test/result/{task_id}")
        result = result_response.json()
        print(result['summary_text'])
        break
    
    time.sleep(5)  # 等待 5 秒后再次查询
```

---

## 注意事项

1. **自动下载功能**:
   - 需要安装 `protobuf` 库并编译 proto 文件
   - 自动下载的文件会在测试完成后自动清理
   - 分布式部署时，下载的文件在服务器端，Appium 无法直接访问

2. **分布式部署**:
   - 当 `appium_host` 为远程 IP 时，`app` 路径必须是 Appium 机器上的绝对路径
   - 不支持相对路径（除非 Appium 在本地）

3. **任务持久化**:
   - 已完成或失败的任务会保存到 `logs/tasks.json`
   - 服务重启后会自动加载历史任务
   - 正在执行的任务不会持久化（避免频繁写入）

4. **日志文件**:
   - 每个任务的日志保存在 `logs/{task_id}.log`
   - 日志文件在任务创建时就会创建，即使任务还未开始执行

5. **任务取消**:
   - 取消操作是异步的，正在执行的测试会在下次检查时停止
   - 已完成的任务无法取消

---

## 更新日志

- **2026-01-06**: 新增自动下载功能（`auto_v`、`auto_m`）
- **2026-01-06**: 支持分布式部署（远程 Appium 服务器）
- **2026-01-06**: 支持任务取消功能
- **2026-01-06**: 支持多次执行（`times` 参数）
- **2026-01-06**: 支持用例过滤（`cases` 参数）

---

## 技术支持

如有问题或建议，请联系开发团队。

