# 部署指南：本地 Appium + 服务器代码

本指南说明如何将代码部署到服务器，同时使用本地（开发机器）的 Appium 服务。

## 架构说明

```
┌─────────────────┐         HTTP API         ┌─────────────────┐
│   客户端/调用方  │ ───────────────────────> │  服务器 (代码)   │
└─────────────────┘                           └─────────────────┘
                                                      │
                                                      │ Appium 协议
                                                      │ (HTTP/WebSocket)
                                                      ▼
                                              ┌─────────────────┐
                                              │ 本地 Appium 服务 │
                                              │  (开发机器)      │
                                              └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │   真实设备       │
                                              │  (USB/网络连接)   │
                                              └─────────────────┘
```

## 步骤 1: 配置本地 Appium 服务

### 1.1 启动 Appium 并监听所有网络接口

默认情况下，Appium 只监听 `127.0.0.1`，需要改为监听所有接口：

```bash
# 方式1: 使用 --address 参数
appium --address 0.0.0.0 --port 4723

# 方式2: 使用环境变量
export APPIUM_ADDRESS=0.0.0.0
appium --port 4723

# 方式3: 多设备多端口（推荐）
appium --address 0.0.0.0 --port 4723 &
appium --address 0.0.0.0 --port 4724 &
appium --address 0.0.0.0 --port 4725 &
```

### 1.2 配置防火墙

确保本地防火墙允许服务器访问 Appium 端口：

**macOS:**
```bash
# 查看防火墙状态
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 允许特定端口（需要管理员权限）
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/node
```

**Linux:**
```bash
# 使用 ufw
sudo ufw allow 4723/tcp
sudo ufw allow 4724/tcp
sudo ufw allow 4725/tcp

# 或使用 iptables
sudo iptables -A INPUT -p tcp --dport 4723 -j ACCEPT
```

**Windows:**
- 在 Windows 防火墙中添加入站规则，允许端口 4723-4730

### 1.3 获取本地 IP 地址

```bash
# macOS/Linux
ifconfig | grep "inet " | grep -v 127.0.0.1

# 或使用
ipconfig getifaddr en0  # macOS
hostname -I             # Linux

# Windows
ipconfig
```

记录下你的本地 IP 地址，例如：`192.168.1.100`

## 步骤 2: 配置服务器代码

### 2.1 修改设备配置文件

编辑 `utils/devices.yaml`，为每个设备指定 Appium 服务器地址：

```yaml
devices:
  - name: "25iPad"
    udid: "00008120-0004086930214032"
    platformName: "iOS"
    appium_server: "http://192.168.1.100:4723"  # 本地 Appium 地址

  - name: "23M4"
    udid: "00008132-000C28E63C39001C"
    platformName: "iOS"
    appium_server: "http://192.168.1.100:4724"  # 第二个设备使用不同端口

  - name: "iPad_03"
    udid: "00008130-001A2B3C0D987654"
    platformName: "iOS"
    appium_server: "http://192.168.1.100:4725"
```

### 2.2 通过 API 参数指定（推荐）

如果不想修改配置文件，可以在 API 请求中指定 `appium_host`：

```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml",
  "appium_host": "192.168.1.100",
  "base_port": 4723
}
```

## 步骤 3: 部署服务器代码

### 3.1 将代码上传到服务器

```bash
# 使用 scp
scp -r ruby_eve_uitest user@server:/path/to/

# 或使用 git
git clone <your-repo> /path/to/ruby_eve_uitest
```

### 3.2 安装依赖

```bash
cd /path/to/ruby_eve_uitest
pip3 install flask appium-python-client pyyaml selenium
```

### 3.3 启动 API 服务

```bash
# 直接运行
python3 main/api_server.py --host 0.0.0.0 --port 5000

# 或使用 nohup 后台运行
nohup python3 main/api_server.py --host 0.0.0.0 --port 5000 > api.log 2>&1 &

# 或使用 systemd 服务（推荐）
```

### 3.4 创建 systemd 服务（可选）

创建 `/etc/systemd/system/ruby-eve-api.service`:

```ini
[Unit]
Description=Ruby Eve UI Test API Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/ruby_eve_uitest
ExecStart=/usr/bin/python3 main/api_server.py --host 0.0.0.0 --port 5000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable ruby-eve-api
sudo systemctl start ruby-eve-api
sudo systemctl status ruby-eve-api
```

## 步骤 4: 测试连接

### 4.1 测试 Appium 连接

在服务器上测试能否连接到本地 Appium：

```bash
# 测试连接
curl http://192.168.1.100:4723/status

# 应该返回 Appium 状态信息
```

### 4.2 测试 API 服务

```bash
# 健康检查
curl http://server-ip:5000/api/health

# 列出设备
curl http://server-ip:5000/api/devices

# 执行测试
curl -X POST http://server-ip:5000/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.evelabinsight.MTEveEnterprise",
    "device": "25iPad",
    "test": "tests/test_ui_flow_m.yaml",
    "appium_host": "192.168.1.100"
  }'
```

## 网络要求

### 端口映射

确保以下端口可访问：

- **服务器 → 本地 Appium**: 
  - 4723, 4724, 4725... (Appium 端口)
  
- **客户端 → 服务器 API**:
  - 5000 (API 服务端口，可自定义)

### 网络连接检查

```bash
# 在服务器上测试
telnet 192.168.1.100 4723

# 或使用 nc
nc -zv 192.168.1.100 4723
```

## 常见问题

### 1. 连接被拒绝

**问题**: `Connection refused` 或 `无法连接到 Appium`

**解决**:
- 检查 Appium 是否启动并监听 `0.0.0.0`
- 检查防火墙设置
- 检查网络连通性（ping、telnet）

### 2. 超时

**问题**: 请求超时

**解决**:
- 检查网络延迟
- 增加超时时间
- 检查 Appium 服务是否正常

### 3. 设备未找到

**问题**: `未找到设备: xxx`

**解决**:
- 检查设备配置文件
- 确认设备名称拼写正确
- 检查设备是否已连接

### 4. 权限问题

**问题**: 无法访问设备或文件

**解决**:
- 确保服务器用户有权限访问设备
- 检查文件权限
- 检查 Appium 权限设置

## 安全建议

1. **使用 VPN**: 如果服务器和本地不在同一网络，建议使用 VPN
2. **限制访问**: 使用防火墙限制 Appium 端口的访问来源
3. **使用 HTTPS**: 生产环境建议使用 HTTPS（需要配置 SSL 证书）
4. **认证机制**: 考虑为 API 添加认证（API Key、Token 等）

## 示例配置

### 完整示例：devices.yaml

```yaml
devices:
  - name: "25iPad"
    udid: "00008120-0004086930214032"
    platformName: "iOS"
    appium_server: "http://192.168.1.100:4723"  # 本地开发机器 IP

  - name: "23M4"
    udid: "00008132-000C28E63C39001C"
    platformName: "iOS"
    appium_server: "http://192.168.1.100:4724"
```

### 完整示例：API 请求

```json
{
  "bundleId": "com.evelabinsight.MTEveEnterprise",
  "device": "25iPad",
  "test": "tests/test_ui_flow_m.yaml",
  "app": "/path/to/app.ipa",
  "reinstall": true,
  "appium_host": "192.168.1.100",
  "base_port": 4723
}
```

## 监控和维护

### 查看日志

```bash
# API 服务日志
tail -f api.log

# Appium 日志
tail -f ~/.appium/logs/appium.log
```

### 重启服务

```bash
# 重启 API 服务
sudo systemctl restart ruby-eve-api

# 重启 Appium（本地）
pkill -f appium
appium --address 0.0.0.0 --port 4723 &
```

