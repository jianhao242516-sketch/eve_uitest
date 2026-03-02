# 实时截图上传功能

## 功能说明

在driver启动到结束这段时间内，自动定时截图并上传到服务器，实现实时查看功能。使用后台线程定期截图，不影响测试执行。

## 启用方法

### 方法1: 在终端中临时设置（推荐，仅当前终端有效）

#### macOS/Linux:

```bash
# 启用实时截图上传
export REALTIME_SCREENSHOT_UPLOAD=true

# 可选：指定上传间隔（秒，默认2秒）
export REALTIME_SCREENSHOT_INTERVAL=2

# 可选：指定API服务器地址（默认: http://localhost:8005/api/upload）
export REALTIME_SCREENSHOT_API_URL=http://localhost:8005/api/upload

# 运行测试
python3 main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

#### Windows (PowerShell):

```powershell
# 启用实时截图上传
$env:REALTIME_SCREENSHOT_UPLOAD="true"

# 可选：指定上传间隔（秒，默认2秒）
$env:REALTIME_SCREENSHOT_INTERVAL="2"

# 可选：指定API服务器地址
$env:REALTIME_SCREENSHOT_API_URL="http://localhost:8005/api/upload"

# 运行测试
python main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

#### Windows (CMD):

```cmd
REM 启用实时截图上传
set REALTIME_SCREENSHOT_UPLOAD=true

REM 可选：指定上传间隔（秒，默认2秒）
set REALTIME_SCREENSHOT_INTERVAL=2

REM 可选：指定API服务器地址
set REALTIME_SCREENSHOT_API_URL=http://localhost:8005/api/upload

REM 运行测试
python main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

### 方法2: 在shell配置文件中永久设置（macOS/Linux）

如果您希望每次打开终端都自动设置，可以添加到shell配置文件中：

#### 对于 bash (默认shell):

```bash
# 编辑 ~/.bashrc 或 ~/.bash_profile
nano ~/.bashrc

# 添加以下内容：
export REALTIME_SCREENSHOT_UPLOAD=true
export REALTIME_SCREENSHOT_INTERVAL=2
export REALTIME_SCREENSHOT_API_URL=http://localhost:8005/api/upload

# 保存后，重新加载配置
source ~/.bashrc
```

#### 对于 zsh (macOS默认shell):

```bash
# 编辑 ~/.zshrc
nano ~/.zshrc

# 添加以下内容：
export REALTIME_SCREENSHOT_UPLOAD=true
export REALTIME_SCREENSHOT_INTERVAL=2
export REALTIME_SCREENSHOT_API_URL=http://localhost:8005/api/upload

# 保存后，重新加载配置
source ~/.zshrc
```

### 方法3: 在代码中设置

### 方法4: 在代码中设置

在测试脚本开始处添加：

```python
import os

# 启用实时截图上传
os.environ['REALTIME_SCREENSHOT_UPLOAD'] = 'true'
os.environ['REALTIME_SCREENSHOT_INTERVAL'] = '2'  # 2秒间隔
os.environ['REALTIME_SCREENSHOT_API_URL'] = 'http://localhost:8005/api/upload'

# 然后运行测试...
```

### 方法5: 在运行命令时设置（一行命令）

#### macOS/Linux:

```bash
REALTIME_SCREENSHOT_UPLOAD=true REALTIME_SCREENSHOT_INTERVAL=2 python3 main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

#### Windows (PowerShell):

```powershell
$env:REALTIME_SCREENSHOT_UPLOAD="true"; $env:REALTIME_SCREENSHOT_INTERVAL="2"; python main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

## 使用示例

### 完整示例（macOS/Linux）

```bash
# 1. 启动API服务器（终端1）
python3 main/api_server.py

# 2. 打开实时查看器（浏览器）
# 访问: http://localhost:8005/viewer

# 3. 启用实时截图上传并运行测试（终端2）
export REALTIME_SCREENSHOT_UPLOAD=true
export REALTIME_SCREENSHOT_INTERVAL=2  # 每2秒截图一次
python3 main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

### 完整示例（Windows PowerShell）

```powershell
# 1. 启动API服务器（PowerShell窗口1）
python main/api_server.py

# 2. 打开实时查看器（浏览器）
# 访问: http://localhost:8005/viewer

# 3. 启用实时截图上传并运行测试（PowerShell窗口2）
$env:REALTIME_SCREENSHOT_UPLOAD="true"
$env:REALTIME_SCREENSHOT_INTERVAL="2"
python main/run_ui.py --bundleId com.example.app --test tests/test_ui_flow.yaml
```

### 快速验证环境变量是否设置成功

#### macOS/Linux:

```bash
# 检查环境变量
echo $REALTIME_SCREENSHOT_UPLOAD
echo $REALTIME_SCREENSHOT_INTERVAL
echo $REALTIME_SCREENSHOT_API_URL

# 应该输出：
# true
# 2
# http://localhost:8005/api/upload
```

#### Windows (PowerShell):

```powershell
# 检查环境变量
echo $env:REALTIME_SCREENSHOT_UPLOAD
echo $env:REALTIME_SCREENSHOT_INTERVAL
echo $env:REALTIME_SCREENSHOT_API_URL
```

## 环境变量说明

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `REALTIME_SCREENSHOT_UPLOAD` | 是否启用实时截图上传 | `false` | `true` / `false` |
| `REALTIME_SCREENSHOT_INTERVAL` | 截图上传间隔（秒） | `2` | `1`, `2`, `5` |
| `REALTIME_SCREENSHOT_API_URL` | 上传API地址 | `http://localhost:8005/api/upload` | `http://192.168.1.100:8005/api/upload` |

## 功能特性

1. **后台线程执行**: 使用独立线程定期截图，不影响测试执行
2. **自动启动和停止**: driver创建后自动启动，driver关闭前自动停止
3. **可配置间隔**: 通过环境变量控制截图频率
4. **失败不影响测试**: 截图或上传失败只打印警告，不影响测试执行
5. **优雅停止**: 测试结束时自动停止线程

## 工作原理

1. **线程启动**: driver创建成功后，自动启动后台线程
2. **定期截图**: 线程每隔指定时间（默认2秒）截图一次
3. **自动上传**: 截图后立即上传到服务器
4. **线程停止**: driver关闭前，自动停止线程

## 查看实时截图

启用后，可以通过以下方式查看：

1. **Web界面**: 访问 `http://localhost:8005/viewer`
   - 自动刷新显示最新截图
   - 可调整刷新间隔
   - 显示截图更新时间

2. **API接口**: 
   - `GET /api/screenshot/latest` - 获取最新截图
   - `GET /api/screenshot/info` - 获取截图信息

## 性能考虑

- **截图频率**: 建议间隔设置为2-5秒，过于频繁可能影响测试性能
- **网络影响**: 上传截图会有轻微的网络开销，但通常可以忽略
- **线程开销**: 后台线程开销很小，不影响测试执行

## 注意事项

1. **API服务器必须运行**: 确保API服务器正在运行，否则上传会失败
2. **需要requests库**: 如果未安装，请运行 `pip install requests`
3. **网络连接**: 如果API服务器在远程机器，确保网络可达
4. **失败处理**: 上传失败不会影响测试执行，只会打印警告信息

## 故障排查

### 问题1: 实时截图没有上传

**检查项**:
- 环境变量`REALTIME_SCREENSHOT_UPLOAD`是否设置为`true`
- API服务器是否正在运行
- 查看日志是否有错误信息

**解决方法**:

#### macOS/Linux:

```bash
# 检查环境变量
echo $REALTIME_SCREENSHOT_UPLOAD
# 如果输出为空或不是"true"，需要设置：
export REALTIME_SCREENSHOT_UPLOAD=true

# 检查API服务器
curl http://localhost:8005/api/health
```

#### Windows (PowerShell):

```powershell
# 检查环境变量
echo $env:REALTIME_SCREENSHOT_UPLOAD
# 如果输出为空或不是"true"，需要设置：
$env:REALTIME_SCREENSHOT_UPLOAD="true"

# 检查API服务器
curl http://localhost:8005/api/health
```

### 问题2: 上传失败

**可能原因**:
- API服务器未启动
- 网络连接问题
- requests库未安装

**解决方法**:
```bash
# 安装requests库
pip install requests

# 检查API服务器状态
curl http://localhost:8005/api/health
```

### 问题3: 截图频率不合适

**解决方法**:
- 调整`REALTIME_SCREENSHOT_INTERVAL`环境变量
- 值越小，截图越频繁，但可能影响性能
- 建议值：1-5秒

## 与现有功能的兼容性

- ✅ 不影响现有的截图保存功能
- ✅ 不影响测试执行
- ✅ 可以同时使用本地保存和服务器上传
- ✅ 上传失败不会影响测试执行

## 更多信息

- 实时查看器使用说明: 查看API服务器启动时的提示信息
- API文档: `API_DOCUMENTATION.md`
- 上传示例代码: `example_upload.py`

