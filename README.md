# Ruby Eve UI Test Framework

基于 Appium + Python + YAML 的移动端UI自动化测试框架，支持多设备并行测试。

## 🚀 功能特性

### ✨ 核心功能
- **多设备并行测试**: 支持同时运行多个设备进行测试
- **YAML驱动**: 测试用例使用YAML格式，易于编写和维护
- **页面对象模式**: 完整的POM架构，代码结构清晰
- **智能弹窗处理**: 自动检测和处理常见弹窗
- **截图功能**: 每次运行独立文件夹，支持时间戳命名
- **简化操作**: 提供简化的元素点击方法

### 📱 支持平台
- **iOS**: 支持真机和模拟器
- **Android**: 支持真机和模拟器

## 📁 项目结构

```
ruby_eve_uitest/
├── main/                    # 主程序入口
│   ├── run_ui.py           # 测试执行主程序
│   └── device_executor.py  # 单设备执行器
├── pages/                   # 页面对象
│   ├── base_page.py        # 基础页面类
│   ├── cj_search_xm_page.py    # 项目搜索页面
│   ├── cj_search_user_page.py  # 用户搜索页面
│   ├── cj_user_page.py         # 用户页面
│   ├── detect_page.py          # 检测页面
│   └── video_detect_page.py    # 视频检测页面
├── tests/                   # 测试用例
│   ├── test_cj_collect_flow.yaml  # 采集流程测试
│   └── test_ui_flow.yaml         # UI流程测试
├── utils/                   # 工具类
│   ├── devices.yaml         # 设备配置
│   ├── elements.yaml        # 元素定位配置
│   ├── popups.yaml          # 弹窗配置
│   ├── driver.py            # 驱动配置
│   └── logger.py            # 日志工具
└── screenshots/             # 截图目录
    └── run_X_YYYYMMDD_HHMMSS/  # 按运行次数分文件夹
```

## 🛠️ 安装配置

### 环境要求
- Python 3.7+
- Appium Server
- iOS: Xcode + WebDriverAgent
- Android: Android SDK + UiAutomator2

### 依赖安装
```bash
pip install appium-python-client
pip install pyyaml
pip install selenium
```

## 📋 配置说明

### 1. 设备配置 (`utils/devices.yaml`)
```yaml
devices:
  - name: "23M4"
    udid: "00008132-000C28E63C39001C"
    platformName: "iOS"
    appium_port: 4724
    appium_server: "http://127.0.0.1:4724"
```

### 2. 元素配置 (`utils/elements.yaml`)
```yaml
CjSearchXmPage:
  project_search_input: ['xpath', "//XCUIElementTypeStaticText[@name='请输入科研项目编号']"]
  first_project_result: ['xpath', "//XCUIElementTypeCollectionView/XCUIElementTypeCell[1]"]
```

### 3. 弹窗配置 (`utils/popups.yaml`)
```yaml
popups:
  - xpath: "//XCUIElementTypeButton[@name='以后']"
    description: "Apple账号验证-以后按钮"
```

## 🚀 使用方法

### 基本用法
```bash
# 单次执行
python3 main/run_ui.py --bundleId com.meitu.MTKingEnterprise --test tests/test_cj_collect_flow.yaml --base_port 4723 --device 23M4

# 多次执行
python3 main/run_ui.py --bundleId com.meitu.MTKingEnterprise --test tests/test_cj_collect_flow.yaml --base_port 4723 --device 23M4 --times 5

# 多设备并行
python3 main/run_ui.py --bundleId com.meitu.MTKingEnterprise --test tests/test_cj_collect_flow.yaml --base_port 4723 --device 23M4,iPad_01
```

### 参数说明
- `--bundleId`: 应用包名
- `--test`: 测试用例文件路径
- `--base_port`: Appium服务基础端口
- `--device`: 设备名称（支持多个，逗号分隔）
- `--times`: 执行次数（默认1次）

## 📝 测试用例编写

### YAML格式示例
```yaml
- name: '采集流程测试 - 项目11到用户11'
  steps:
    - page: 'CjSearchXmPage'
      actions:
        - method: 'check_and_handle_popups'
          params: 3
        - method: 'input_project_search'
          params: '11'
        - method: 'wait'
          params: 2
        - method: 'click_first_project'
        - method: 'take_screenshot'
          params: 'project_search_result'
    - page: 'CjSearchUserPage'
      actions:
        - method: 'input_user_search'
          params: '11'
        - method: 'click_only_one_user'
```

### 支持的操作方法
- `wait`: 强制等待
- `click_element`: 简化点击（支持跨页面元素）
- `take_screenshot`: 截图
- `wait_for_element_to_appear`: 等待元素出现
- `wait_for_element_to_disappear`: 等待元素消失
- `check_and_handle_popups`: 主动检查弹窗

## 🔧 高级功能

### 1. 简化元素点击
```yaml
# 当前页面元素
- method: 'click_element'
  params: 'first_project_result'

# 其他页面元素
- method: 'click_element'
  params: 'CjSearchUserPage.only_one_user'
```

### 2. 智能弹窗处理
```yaml
# 主动检查弹窗
- method: 'check_and_handle_popups'
  params: 3  # 最多检查3次
```

### 3. 截图功能
- 每次运行创建独立文件夹：`run_X_YYYYMMDD_HHMMSS/`
- 支持自定义截图名称
- 自动添加时间戳

### 4. 等待机制
```yaml
# 等待元素出现
- method: 'wait_for_element_to_appear'
  params: ['element_name', 30]  # 元素名，超时时间

# 等待元素消失
- method: 'wait_for_element_to_disappear'
  params: ['element_name', 30]
```

## 📊 测试报告

### 执行结果汇总
```
================================================================================
🎯 测试执行完成汇总
================================================================================
📊 执行统计:
   🔢 总执行次数: 3
   📱 测试设备: 23M4
   📄 测试用例: tests/test_cj_collect_flow.yaml
   ✅ 成功次数: 3
   ❌ 失败次数: 0
   📈 成功率: 100.0%
================================================================================
```

### 日志文件
- 详细执行日志保存在日志文件中
- 支持多设备并行日志记录
- 包含错误信息和调试信息

## 🐛 常见问题

### 1. WebDriverAgent 连接失败
- 检查 Xcode 和 WebDriverAgent 配置
- 确保设备已信任开发者证书
- 重启 Appium 服务

### 2. 端口冲突
- 使用不同的 `--base_port` 参数
- 检查端口占用情况：`lsof -i :端口号`

### 3. 元素定位失败
- 检查 `elements.yaml` 中的定位器
- 使用 `take_screenshot` 查看当前页面状态
- 添加 `wait` 等待页面加载

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

MIT License

---

**注意**: 使用前请确保已正确配置 Appium 环境和设备连接。