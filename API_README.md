# Ruby Eve UI Test API 服务

HTTP API 服务，用于接收外部请求并执行 UI 测试。

## 启动服务

```bash
# 基本启动（默认端口 8005）
python3 main/api_server.py

# 指定端口和地址
python3 main/api_server.py --host 0.0.0.0 --port 8005

# 调试模式
python3 main/api_server.py --debug
```

## API 接口

### 1. 执行测试任务

**POST** `/api/test/run`

**请求体 (JSON):**
```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml",
  "app": "/path/to/app.ipa",
  "reinstall": true,
  "base_port": 4723
}
```

**参数说明:**
- `bundleId` (必需): App 的 bundleId 或 appPackage
- `device` (必需): 设备名称
- `test` (可选): 测试用例文件路径，默认 `tests/test_ui_flow.yaml`
- `app` (可选): App 安装包路径或目录路径
  - 如果指定文件路径（如 `/path/to/app.ipa`），则安装该文件
  - 如果指定目录路径（如 `/path/to/apps`），则自动查找目录下最新的 `.ipa` (iOS) 或 `.apk` (Android) 文件并安装
- `reinstall` (可选): 是否重新安装 app，默认 `false`
  - `false`: 仅安装（如果已安装则跳过）
  - `true`: 先卸载再安装（强制重新安装）
- `base_port` (可选): Appium 起始端口，默认 `4723`
- `appium_host` (可选): Appium 服务器地址，默认 `127.0.0.1`。如果 Appium 在远程机器，设置为远程 IP，例如 `192.168.1.100`
- `devices` (可选): 设备配置文件路径，默认 `utils/devices.yaml`

**注意**: 如果 `devices.yaml` 中设备已配置 `appium_server`，将优先使用配置文件中的地址。

**App 安装场景示例:**

1. **仅安装（不卸载）:**
```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml",
  "app": "/path/to/app.ipa"
}
```

2. **重新安装（先卸载再安装）:**
```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml",
  "app": "/path/to/app.ipa",
  "reinstall": true
}
```

3. **从目录自动选择最新 app 并重新安装:**
```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml",
  "app": "/Users/meitu/Downloads/ruby_eve_uitest/apps",
  "reinstall": true
}
```

4. **不安装 app（仅运行测试）:**
```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml"
}
```
（不传 `app` 参数即可）

**响应示例:**
```json
{
  "success": true,
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "测试任务已创建，正在执行中",
  "status_url": "/api/test/status/550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. 查询任务状态

**GET** `/api/test/status/<task_id>`

**响应示例:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "bundle_id": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test_file": "tests/test_ui_flow_m.yaml",
  "create_time": "2025-11-28T15:00:00",
  "start_time": "2025-11-28T15:00:01",
  "end_time": "2025-11-28T15:05:30",
  "result": {
    "passed": 1,
    "failed": 0,
    "total": 1,
    "success_rate": 100.0
  },
  "screenshot_dir": "screenshots/run_20251128_150001/"
}
```

**状态值:**
- `pending`: 等待执行
- `running`: 正在执行
- `completed`: 执行完成
- `failed`: 执行失败
- `cancelled`: 已取消

### 3. 列出所有任务

**GET** `/api/test/list`

返回最近 50 个任务。

### 4. 取消任务

**POST** `/api/test/cancel/<task_id>`

取消指定的任务（仅标记，无法真正停止正在运行的任务）。

### 5. 列出所有设备

**GET** `/api/devices`

返回所有可用的设备列表。

### 6. 健康检查

**GET** `/api/health`

检查服务是否正常运行。

## 使用示例

### Python 示例

```python
import requests
import time

# 示例1: 重新安装 app 并执行测试
response = requests.post('http://localhost:8005/api/test/run', json={
    'bundleId': 'com.evelabinsight.MTEveEnterprise',
    'device': '25iPad',
    'test': 'tests/test_ui_flow_m.yaml',
    'app': '/path/to/app.ipa',  # 指定 app 文件路径
    'reinstall': True  # 重新安装（先卸载再安装）
})

# 示例2: 从目录自动选择最新 app 并重新安装
response = requests.post('http://localhost:8005/api/test/run', json={
    'bundleId': 'com.evelabinsight.MTEveEnterprise',
    'device': '25iPad',
    'test': 'tests/test_ui_flow_m.yaml',
    'app': '/Users/meitu/Downloads/ruby_eve_uitest/apps',  # 目录路径
    'reinstall': True
})

# 示例3: 仅安装（不卸载）
response = requests.post('http://localhost:8005/api/test/run', json={
    'bundleId': 'com.evelabinsight.MTEveEnterprise',
    'device': '25iPad',
    'test': 'tests/test_ui_flow_m.yaml',
    'app': '/path/to/app.ipa',
    'reinstall': False  # 或省略此参数
})

# 示例4: 不安装 app，仅运行测试
response = requests.post('http://localhost:8005/api/test/run', json={
    'bundleId': 'com.evelabinsight.MTEveEnterprise',
    'device': '25iPad',
    'test': 'tests/test_ui_flow_m.yaml'
    # 不传 app 参数
})

task_id = response.json()['task_id']
print(f'任务 ID: {task_id}')

# 轮询任务状态
while True:
    status_response = requests.get(f'http://localhost:8005/api/test/status/{task_id}')
    status = status_response.json()
    
    print(f'状态: {status["status"]}')
    
    if status['status'] in ['completed', 'failed', 'cancelled']:
        if 'result' in status:
            print(f'结果: {status["result"]}')
        break
    
    time.sleep(2)
```

### cURL 示例

```bash
# 示例1: 重新安装 app 并执行测试
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.evelabinsight.MTEveEnterprise",
    "device": "25iPad",
    "test": "tests/test_ui_flow_m.yaml",
    "app": "/path/to/app.ipa",
    "reinstall": true
  }'

# 示例2: 从目录自动选择最新 app 并重新安装
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.evelabinsight.MTEveEnterprise",
    "device": "25iPad",
    "test": "tests/test_ui_flow_m.yaml",
    "app": "/Users/meitu/Downloads/ruby_eve_uitest/apps",
    "reinstall": true
  }'

# 示例3: 仅安装（不卸载）
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.evelabinsight.MTEveEnterprise",
    "device": "25iPad",
    "test": "tests/test_ui_flow_m.yaml",
    "app": "/path/to/app.ipa",
    "reinstall": false
  }'

# 示例4: 不安装 app，仅运行测试
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.evelabinsight.MTEveEnterprise",
    "device": "25iPad",
    "test": "tests/test_ui_flow_m.yaml"
  }'

# 查询任务状态
curl http://localhost:8005/api/test/status/<task_id>

# 列出所有任务
curl http://localhost:8005/api/test/list

# 列出所有设备
curl http://localhost:8005/api/devices
```

## 依赖安装

```bash
pip install flask
```

## 注意事项

1. 服务启动后，测试任务会在后台线程中执行
2. 任务状态存储在内存中，服务重启后会丢失
3. 如果需要持久化任务状态，可以考虑使用数据库
4. 确保 Appium 服务已启动并运行在正确的端口

