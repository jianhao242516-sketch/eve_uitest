# API接口启用实时截图上传

## 功能说明

通过API接口运行测试时，可以在请求参数中直接启用实时截图上传功能，无需手动设置环境变量。

## API请求参数

在 `POST /api/test/run` 接口中添加以下可选参数：

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `realtime_screenshot_upload` | boolean | `false` | 是否启用实时截图上传 |
| `realtime_screenshot_interval` | number | `2` | 截图上传间隔（秒） |
| `realtime_screenshot_api_url` | string | `http://localhost:8005/api/upload` | 上传API地址 |

## 使用示例

### 示例1: 基本使用（启用实时截图上传）

```bash
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.example.app",
    "device": "iPad7",
    "test": "tests/test_ui_flow.yaml",
    "app": "/path/to/app.ipa",
    "reinstall": true,
    "realtime_screenshot_upload": true,
    "realtime_screenshot_interval": 2
  }'
```

### 示例2: 自定义上传间隔

```bash
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.example.app",
    "device": "iPad7",
    "test": "tests/test_ui_flow.yaml",
    "realtime_screenshot_upload": true,
    "realtime_screenshot_interval": 5
  }'
```

### 示例3: 自定义API服务器地址

```bash
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.example.app",
    "device": "iPad7",
    "test": "tests/test_ui_flow.yaml",
    "realtime_screenshot_upload": true,
    "realtime_screenshot_interval": 2,
    "realtime_screenshot_api_url": "http://192.168.1.100:8005/api/upload"
  }'
```

### 示例4: Python requests库

```python
import requests

url = "http://localhost:8005/api/test/run"
data = {
    "bundleId": "com.example.app",
    "device": "iPad7",
    "test": "tests/test_ui_flow.yaml",
    "app": "/path/to/app.ipa",
    "reinstall": True,
    "realtime_screenshot_upload": True,  # 启用实时截图上传
    "realtime_screenshot_interval": 2,    # 每2秒截图一次
    "realtime_screenshot_api_url": "http://localhost:8005/api/upload"
}

response = requests.post(url, json=data)
result = response.json()
print(f"任务ID: {result.get('task_id')}")
```

### 示例5: 完整请求示例

```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "iPad7",
  "test": "tests/test_ui_flow.yaml",
  "device_name": "V_500348",
  "appium_host": "127.0.0.1",
  "app": "/path/to/app.ipa",
  "reinstall": true,
  "times": 1,
  "realtime_screenshot_upload": true,
  "realtime_screenshot_interval": 2,
  "realtime_screenshot_api_url": "http://localhost:8005/api/upload"
}
```

## 查看实时截图

启用实时截图上传后，可以通过以下方式查看：

1. **Web界面**: 访问 `http://localhost:8005/viewer`
2. **API接口**: 
   - `GET /api/screenshot/latest` - 获取最新截图
   - `GET /api/screenshot/info` - 获取截图信息

## 完整使用流程

```bash
# 1. 启动API服务器
python3 main/api_server.py

# 2. 打开实时查看器（浏览器）
# 访问: http://localhost:8005/viewer

# 3. 通过API运行测试并启用实时截图上传
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.example.app",
    "device": "iPad7",
    "test": "tests/test_ui_flow.yaml",
    "realtime_screenshot_upload": true,
    "realtime_screenshot_interval": 2
  }'
```

## 参数说明

### realtime_screenshot_upload

- **类型**: boolean
- **默认值**: `false`
- **说明**: 是否启用实时截图上传功能
- **示例**: `true` 或 `false`

### realtime_screenshot_interval

- **类型**: number
- **默认值**: `2`
- **说明**: 截图上传间隔（秒），建议值：1-5秒
- **示例**: `1`, `2`, `5`

### realtime_screenshot_api_url

- **类型**: string
- **默认值**: `http://localhost:8005/api/upload`
- **说明**: 上传API地址，如果API服务器在其他机器，需要修改此地址
- **示例**: `http://192.168.1.100:8005/api/upload`

## 注意事项

1. **API服务器必须运行**: 确保API服务器正在运行，否则上传会失败
2. **网络连接**: 如果API服务器在远程机器，确保网络可达
3. **性能影响**: 截图频率过高可能影响测试性能，建议间隔设置为2-5秒
4. **失败不影响测试**: 上传失败不会影响测试执行，只会打印警告信息

## 与直接运行的区别

### 直接运行（命令行）

```bash
# 需要设置环境变量
export REALTIME_SCREENSHOT_UPLOAD=true
export REALTIME_SCREENSHOT_INTERVAL=2
python3 main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

### API调用

```bash
# 直接在请求参数中设置
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.example.app",
    "device": "iPad7",
    "test": "tests/test_ui_flow.yaml",
    "realtime_screenshot_upload": true,
    "realtime_screenshot_interval": 2
  }'
```

## 更多信息

- 实时截图功能说明: `REALTIME_SCREENSHOT.md`
- API完整文档: `API_DOCUMENTATION.md`

