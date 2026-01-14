# API 参数文档

本文档列出了 `main/api_server.py` 中所有 API 端点及其支持的参数。

## 1. POST /api/test/run - 执行测试任务

### 必需参数
- `bundleId` 或 `bundle_id` (string): Bundle ID，应用标识符
- `device` (string): 设备名称，必须在 `devices.yaml` 中配置

### 可选参数
- `test` (string): 测试文件路径，默认 `tests/test_ui_flow.yaml`
- `app` (string): 应用安装包路径
  - 支持绝对路径或相对路径（本地部署时）
  - 支持自动下载：`auto_v`、`auto_m`、`auto_lp`（需要下载模块支持）
- `reinstall` (boolean): 是否重新安装应用，默认 `false`
- `times` (integer): 执行次数，默认 `1`
- `device_name` (string): 用于 `check_connected`、`connect` 等方法的设备名称
- `cases` 或 `case` (string|array): 用例名过滤
  - 支持字符串（逗号分隔）或数组格式
- `base_port` (integer): Appium 基础端口，默认 `4723`
- `devices` (string): 设备配置文件路径，默认 `utils/devices.yaml`
- `appium_host` (string): Appium 服务器地址，默认 `127.0.0.1`
  - 支持远程 IP 地址（分布式部署）
  - 支持 URL 格式，会自动提取主机名
- `realtime_screenshot_upload` (boolean): 是否启用实时截图上传，默认 `false` 【0108新增】
- `realtime_screenshot_interval` (integer): 截图间隔（秒），默认 `2` 【0108新增】
- `realtime_screenshot_api_url` (string): 上传API地址，默认 `http://localhost:8005/api/upload` 【0108新增】

### 返回
```json
{
  "success": true,
  "task_id": "uuid",
  "message": "测试任务已创建，正在执行中（将执行 N 次）",
  "status_url": "/api/test/status/{task_id}"
}
```

---

## 2. GET /api/test/status/<task_id> - 查询任务状态

### 路径参数
- `task_id` (string): 任务 ID

### 查询参数
- `include_log` (boolean): 是否包含日志内容，默认 `false`
  - 设置为 `true` 时，返回结果中包含 `log_content` 字段

### 返回
任务状态信息，包括：
- `status`: 任务状态（pending, downloading, running, completed, failed, cancelled）
- `bundle_id`: Bundle ID
- `device`: 设备名称
- `test_file`: 测试文件路径
- `app_path`: 应用路径
- `times`: 执行次数
- `create_time`: 创建时间
- `start_time`: 开始时间
- `end_time`: 结束时间
- `log_file`: 日志文件路径
- `result`: 执行结果（如果已完成）
- `log_content`: 日志内容（如果 `include_log=true`）

---

## 3. GET /api/test/list - 列出任务

### 查询参数
- `status` (string): 过滤任务状态，可选值：
  - 不传或 `running`: 只返回正在执行的任务（pending, downloading, running）
  - `all`: 返回所有任务（包括历史任务，限制最近50个）
  - `completed`: 只返回已完成的任务
  - `failed`: 只返回失败的任务
  - `active`: 返回所有非终态任务（pending, downloading, running）

### 返回
```json
{
  "total": 10,
  "tasks": [...],
  "filter": "running"
}
```

---

## 4. GET /api/test/log/<task_id> - 获取任务日志内容

### 路径参数
- `task_id` (string): 任务 ID

### 返回
```json
{
  "task_id": "uuid",
  "log_file": "/path/to/log/file.log",
  "log_content": "日志内容..."
}
```

如果日志文件尚未创建，返回：
```json
{
  "task_id": "uuid",
  "log_content": "",
  "note": "日志文件尚未创建（任务可能还未开始执行）"
}
```

---

## 5. GET /api/test/result/<task_id> - 获取任务执行结果汇总

### 路径参数
- `task_id` (string): 任务 ID

### 返回
```json
{
  "task_id": "uuid",
  "status": "completed",
  "summary_text": "格式化的文本汇总",
  "statistics": {
    "total_runs": 1,
    "device": "设备名称",
    "test_file": "测试文件路径",
    "total_passed": 5,
    "total_failed": 2,
    "total": 7,
    "success_rate": 71.43
  },
  "timeline": {
    "create_time": "2026-01-13T10:00:00",
    "start_time": "2026-01-13T10:00:01",
    "end_time": "2026-01-13T10:05:00"
  },
  "screenshot_dir": "screenshots/run_20260113_100000/",
  "error": null
}
```

**注意**: 只有已完成、失败或已取消的任务才能查询结果。

---

## 6. POST /api/test/cancel/<task_id> - 取消任务

### 路径参数
- `task_id` (string): 任务 ID

### 返回
```json
{
  "success": true,
  "message": "任务已标记为取消"
}
```

**注意**: 
- 只能取消未完成的任务（pending, downloading, running）
- 已完成或失败的任务无法取消
- 取消操作仅标记任务状态，无法真正停止正在运行的任务

---

## 7. GET /api/health - 健康检查

### 无参数

### 返回
```json
{
  "status": "ok",
  "service": "Ruby Eve UI Test API",
  "timestamp": "2026-01-13T10:00:00"
}
```

---

## 8. GET /api/devices - 列出所有可用设备

### 查询参数
- `devices` (string): 设备配置文件路径，默认 `utils/devices.yaml`

### 返回
```json
{
  "devices": [
    {
      "name": "设备名称",
      "udid": "设备UDID",
      "platformName": "iOS",
      ...
    }
  ],
  "total": 5
}
```

---

## 9. POST /api/upload - 上传实时截图 【0108新增】

### 请求头
- `Content-Type`: `image/jpeg` 或 `image/png`

### 请求体
- 图片的二进制数据

### 返回
```json
{
  "success": true,
  "message": "Screenshot uploaded successfully",
  "path": "/path/to/screenshot.jpg",
  "timestamp": "2026-01-08T10:30:00"
}
```

---

## 10. GET /api/screenshot/latest - 获取最新截图 【0108新增】

### 无参数

### 返回
- 如果存在最新截图，返回图片文件（Content-Type: image/jpeg）
- 如果不存在，返回 404 错误

---

## 11. GET /api/screenshot/info - 获取最新截图信息 【0108新增】

### 无参数

### 返回
```json
{
  "path": "/path/to/screenshot.jpg",
  "timestamp": "2026-01-08T10:30:00",
  "exists": true
}
```

---

## 12. GET /viewer 或 /realtime - 实时截图查看器（Web界面）【0108新增】

### 无参数

### 返回
HTML 页面，用于实时查看上传的截图

---

## 启动参数

服务器启动时支持以下命令行参数：

- `--host` (string): 服务器地址，默认 `0.0.0.0`
- `--port` (integer): 服务器端口，默认 `8005`
- `--debug` (flag): 启用调试模式

### 示例
```bash
python main/api_server.py --host 0.0.0.0 --port 8005 --debug
```

---

## 特殊功能说明

### 自动下载功能
- 当 `app` 参数为 `auto_v`、`auto_m` 或 `auto_lp` 时，系统会自动下载最新包
- 需要 `utils/ci_download/download_New_ipa.py` 模块可用
- 需要 `protobuf` 库支持
- **限制**: 在分布式部署（远程 Appium）中无法使用自动下载功能

### 分布式部署
- 当 `appium_host` 不是本地地址（127.0.0.1/localhost）时，视为分布式部署
- 在分布式部署中，`app` 参数必须是 Appium 机器上的绝对路径
- 相对路径无法在分布式部署中使用

### 实时截图功能 【0108新增】
- 通过 `realtime_screenshot_upload` 参数启用
- 支持自定义截图间隔和上传 API 地址
- 可通过 Web 界面 `/viewer` 实时查看截图

