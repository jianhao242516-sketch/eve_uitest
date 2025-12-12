# Ruby Eve UI Test Framework

基于 Appium + Python + YAML 的移动端UI自动化测试框架，支持多设备并行测试。

## 🌐 HTTP API 服务

本框架提供 HTTP API 服务，支持通过 RESTful 接口远程执行自动化测试。

### 快速启动服务

```bash
# 启动 API 服务（默认端口 8005）
python3 main/api_server.py

# 指定端口
python3 main/api_server.py --host 0.0.0.0 --port 8005
```

### API 使用示例

```bash
# 执行测试任务
curl -X POST http://localhost:8005/api/test/run \
  -H "Content-Type: application/json" \
  -d '{
    "bundleId": "com.evelabinsight.MTEveEnterprise",
    "device": "25iPad",
    "test": "tests/test_ui_flow_m.yaml",
    "app": "apps",
    "reinstall": true
  }'

# 查询任务状态
curl http://localhost:8005/api/test/status/<task_id>
```

**详细 API 文档**: 请查看 [API_README.md](API_README.md)  
**部署指南**: 请查看 [DEPLOYMENT.md](DEPLOYMENT.md)  
**服务介绍**: 请查看 [SERVICE_INTRO.md](SERVICE_INTRO.md)

## 🚀 功能特性

### ✨ 核心功能
- **多设备并行测试**: 支持同时运行多个设备进行测试
- **YAML驱动**: 测试用例使用YAML格式，易于编写和维护
- **页面对象模式**: 完整的POM架构，代码结构清晰
- **动态页面类创建**: 无需手动创建页面类文件，系统自动创建
- **多文件元素管理**: 元素配置支持多文件管理，按模块组织
- **智能弹窗处理**: 自动检测和处理常见弹窗
- **截图功能**: 按运行时间戳、执行次数、用例序号自动组织
- **简化操作**: 提供统一的元素操作方法（click_element, send_keys_element）
- **坐标操作**: 支持坐标点击和滑动操作
- **用例串行执行**: 每个用例自动重启APP，确保环境干净
- **前置和清理方法**: 支持在用例执行前后自动执行配置和清理方法
- **运行时参数传递**: 支持通过命令行参数动态传入设备名称等参数

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
│   ├── base_page.py        # 基础页面类（所有页面继承此类）
│   ├── home_page.py        # 首页（可选，支持动态创建）
│   ├── login_page.py       # 登录页（可选，支持动态创建）
│   └── ...                 # 其他页面类（可选）
├── tests/                   # 测试用例
│   ├── test_cj_collect_flow_element.yaml  # 采集流程测试
│   ├── test_chanel_flow.yaml              # Chanel流程测试
│   └── test_ui_flow.yaml                  # UI流程测试
├── utils/                   # 工具类
│   ├── devices.yaml         # 设备配置
│   ├── elements/            # 元素定位配置目录
│   │   ├── EveV_pages.yaml  # EveV页面元素
│   │   ├── cj_pages.yaml    # 采集相关页面元素
│   │   └── chanel_page.yaml # Chanel页面元素
│   ├── popups.yaml          # 弹窗配置
│   ├── driver.py            # 驱动配置
│   └── logger.py            # 日志工具
└── screenshots/             # 截图目录
    └── run_YYYYMMDD_HHMMSS/ # 运行时间戳目录
        └── times_X/          # 第X次执行
            └── case_Y/       # 第Y个用例
                └── *.png     # 截图文件
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

### 2. 元素配置 (`utils/elements/`)

元素配置支持多文件管理，系统会自动加载 `utils/elements/` 目录下所有 `.yaml` 文件。

**文件组织方式：**
- `EveV_pages.yaml` - 通用页面元素（HomePage, UserProfilePage, DetectPage, LoginPage, Reportpage）
- `cj_pages.yaml` - 采集相关页面元素（CjSearchXmPage, CjSearchUserPage, CjUserPage, VideoDetectPage）
- `chanel_page.yaml` - Chanel页面元素

**元素定义格式：**
```yaml
# utils/elements/cj_pages.yaml
CjSearchXmPage:
  project_search_input: ['xpath', "//XCUIElementTypeStaticText[@name='请输入科研项目编号']"]
  first_project_result: ['xpath', "//XCUIElementTypeCollectionView/XCUIElementTypeCell[1]"]
```

**添加新页面元素：**
只需在 `utils/elements/` 目录下创建新的 YAML 文件，系统会自动加载。

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
python3 main/run_ui.py --bundleId com.meitu.MTKingEnterprise --test tests/test_cj_collect_flow_element.yaml --base_port 4723 --device 23M4

# 多次执行
python3 main/run_ui.py --bundleId com.meitu.MTKingEnterprise --test tests/test_cj_collect_flow_element.yaml --base_port 4723 --device 23M4 --times 5

# 多设备并行
python3 main/run_ui.py --bundleId com.meitu.MTKingEnterprise --test tests/test_cj_collect_flow_element.yaml --base_port 4723 --device 23M4,iPad_01

# 运行时传入设备名称（用于 check_connected、connect 等方法）
python3 main/run_ui.py --bundleId com.evelabinsight.MTEveEnterprise --test tests/test_press_flow_m.yaml --base_port 4723 --device ipad1 --device_name 200018
```

### 参数说明
- `--bundleId`: 应用包名
- `--test`: 测试用例文件路径
- `--base_port`: Appium服务基础端口
- `--device`: 设备名称（支持多个，逗号分隔）
- `--times`: 执行次数（默认1次）
- `--device_name`: 设备名称（用于 `check_connected`、`connect` 等方法），如果不传则使用 YAML 中的值或方法默认值

### 执行流程说明
- **用例串行执行**: 多个用例会按顺序串行执行，每个用例开始前会自动重启APP
- **环境隔离**: 每个用例都在干净的环境中执行，互不干扰
- **自动等待**: 用例之间会自动等待，确保执行稳定
- **前置方法（setup_method）**: 在启动 app 之前执行，用于配置环境（如开启功能开关、配置登录方式等）
- **清理方法（teardown_method）**: 在每个用例执行完成后执行，用于清理环境（如恢复默认配置）

## 📝 测试用例编写

### YAML格式示例
```yaml
- name: '检测流程'
  setup_method: 'setup_method_1'  # 可选：指定前置方法名，在启动app前会先调用该方法
  teardown_method: 'teardown_method_1'  # 可选：指定清理方法名，在用例执行完成后会调用该方法
  steps:
    - page: 'CjSearchXmPage'
      actions:
        # 检查弹窗
        - method: 'check_and_handle_popups'
          params: 3
        # 点击元素
        - method: 'click_element'
          params: 'project_search_input'
        # 输入文本
        - method: 'send_keys_element'
          params: ['project_search_input', '11']
        # 等待
        - method: 'wait'
          params: 2
        # 点击元素
        - method: 'click_element'
          params: 'first_project_result'
        # 截图
        - method: 'take_screenshot'
          params: 'project_search_result'
    - page: 'CjSearchUserPage'
      actions:
        - method: 'click_element'
          params: 'user_search_input'
        - method: 'send_keys_element'
          params: ['user_search_input', '11']
        - method: 'click_element'
          params: 'only_one_user'
```

### 支持的操作方法

#### 元素操作
- `click_element`: 点击元素（支持跨页面元素）
- `send_keys_element`: 向元素输入文本
- `click_by_coordinates`: 通过坐标点击
- `tap`: 轻触坐标

#### 等待方法
- `wait`: 强制等待
- `wait_for_element_to_appear`: 等待元素出现
- `wait_for_element_to_disappear`: 等待元素消失

#### 滑动操作
- `swipe`: 自定义滑动
- `swipe_up`: 向上滑动
- `swipe_down`: 向下滑动
- `swipe_left`: 向左滑动
- `swipe_right`: 向右滑动

#### 其他功能
- `take_screenshot`: 截图
- `check_and_handle_popups`: 主动检查弹窗
- `assert_element_exists`: 断言元素存在
- `assert_text_equals`: 断言文本等于

## 🔧 高级功能

### 1. 简化元素操作
```yaml
# 点击当前页面元素
- method: 'click_element'
  params: 'first_project_result'

# 点击其他页面元素（跨页面引用）
- method: 'click_element'
  params: 'DetectPage.confirm_button'

# 输入文本
- method: 'send_keys_element'
  params: ['project_search_input', '11']
```

### 2. 坐标操作
```yaml
# 点击坐标
- method: 'click_by_coordinates'
  params: [200, 300]

# 轻触坐标
- method: 'tap'
  params: [200, 300, 100]  # x, y, duration(ms)
```

### 3. 滑动操作
```yaml
# 向上滑动（默认从屏幕中部，滑动500像素）
- method: 'swipe_up'
  params: 500

# 向下滑动
- method: 'swipe_down'
  params: 500

# 向左滑动
- method: 'swipe_left'
  params: 300

# 向右滑动
- method: 'swipe_right'
  params: 300

# 自定义滑动（从起点到终点）
- method: 'swipe'
  params: [100, 200, 400, 600, 1000]  # start_x, start_y, end_x, end_y, duration(ms)
```

### 4. 智能弹窗处理
```yaml
# 主动检查弹窗
- method: 'check_and_handle_popups'
  params: 3  # 最多检查3次
```

### 5. 截图功能
截图会自动保存到以下目录结构：
```
screenshots/
  └── run_20251024_173000/    # 运行时间戳
      └── times_1/             # 第1次执行
          └── case_1/          # 第1个用例
              └── screenshot_xxx.png
```

```yaml
# 截图（自动命名）
- method: 'take_screenshot'

# 自定义截图名称
- method: 'take_screenshot'
  params: 'search_result'
```

### 6. 等待机制
```yaml
# 等待元素出现
- method: 'wait_for_element_to_appear'
  params: ['element_name', 30]  # 元素名，超时时间(秒)

# 等待元素消失
- method: 'wait_for_element_to_disappear'
  params: ['element_name', 30]
```

### 7. 动态页面类创建
**无需手动创建页面类文件！** 在 YAML 中直接使用页面名称，系统会自动创建：

```yaml
- page: 'NewPage'  # 即使没有对应的 Python 文件，也能正常工作
  actions:
    - method: 'click_element'
      params: 'some_button'
```

系统会自动：
- 动态创建继承自 `BasePage` 的页面类
- 自动设置 `page_name`
- 可以使用 `utils/elements/` 目录中定义的元素

### 8. 前置方法和清理方法（setup_method / teardown_method）
**支持在用例执行前后自动执行配置和清理方法，用于环境准备和恢复。**

#### 前置方法（setup_method）
在启动 app **之前**执行，用于配置测试环境，例如：
- 开启/关闭功能开关
- 配置登录方式（扫码登录、账号密码登录等）
- 配置检测维度
- 配置报告页功能等

**执行时机**：
- 在创建 driver 之前执行
- 所有用例的前置方法会在启动 app 前统一执行（去重）
- 如果前置方法执行失败，会记录警告但继续执行测试

**使用示例**：
```yaml
- name: '检测流程'
  setup_method: 'setup_method_1'  # 指定前置方法名
  steps:
    - page: 'M_HomePage'
      actions:
        - method: 'check_connected'
          params: '200018'
```

**定义前置方法**：
在 `api_scripts/test_setup_methods.py` 中定义并注册：

```python
def setup_method_1():
    """示例：开启扫码登录"""
    logger.log("执行前置方法: setup_method_login_qr_code")
    update_login_qr_code(1)  # 开启扫码登录
    logger.log("✅ setup_method_login_qr_code 执行完成")

# 注册到方法表
SETUP_METHODS = {
    'setup_method_1': setup_method_1,
    # 可以继续添加更多方法...
}
```

#### 清理方法（teardown_method）
在每个用例执行**完成后**执行，用于清理测试环境，例如：
- 恢复默认配置
- 关闭临时开启的功能
- 清理测试数据等

**执行时机**：
- 在用例的所有步骤执行完成后执行
- 无论用例成功还是失败，都会执行清理方法
- 如果清理方法执行失败，会记录警告但不影响后续用例

**使用示例**：
```yaml
- name: '检测流程'
  setup_method: 'setup_method_1'
  teardown_method: 'teardown_method_1'  # 指定清理方法名
  steps:
    - page: 'M_HomePage'
      actions:
        - method: 'check_connected'
          params: '200018'
```

**定义清理方法**：
在 `api_scripts/test_setup_methods.py` 中定义并注册：

```python
def teardown_method_1():
    """示例：恢复默认配置"""
    logger.log("执行清理方法: teardown_method_1")
    update_login_qr_code(2)  # 恢复扫码登录为默认状态
    logger.log("✅ teardown_method_1 执行完成")

# 注册到方法表
TEARDOWN_METHODS = {
    'teardown_method_1': teardown_method_1,
    # 可以继续添加更多方法...
}
```

#### 完整示例
```yaml
- name: '检测流程'
  setup_method: 'setup_method_1'  # 前置：开启扫码登录
  teardown_method: 'teardown_method_1'  # 清理：恢复默认配置
  steps:
    - page: 'M_HomePage'
      actions:
        - method: 'check_connected'
          params: '200018'
        - method: 'searchuser'
          params: 'ruby'
    - page: 'M_UserProfilePage'
      actions:
        - method: 'click_element'
          params: 'start_detect_button'
```

#### 可用方法
查看 `api_scripts/test_setup_methods.py` 文件中的 `SETUP_METHODS` 和 `TEARDOWN_METHODS` 字典，可以看到所有已注册的方法。

#### 注意事项
- 前置方法和清理方法都是**可选的**，不指定也不会影响测试执行
- 前置方法执行失败不会阻止测试继续执行，只会记录警告
- 清理方法执行失败也不会影响后续用例，只会记录警告
- 可以在多个用例中复用同一个前置或清理方法

### 9. 运行时参数传递（device_name）
**支持运行时传入设备名称，自动应用到所有需要 `device_name` 参数的方法。**

#### 优先级顺序
1. **运行时传入的值**（`--device_name`）- 最高优先级
2. YAML 中的值（`params`）
3. 方法的默认值（如果方法有默认参数）
4. 全局默认值 `'200018'`（如果方法没有默认值）

#### 使用示例

**方式1：运行时传入 device_name（覆盖 YAML 中的值）**
```bash
python3 main/run_ui.py \
  --bundleId com.evelabinsight.MTEveEnterprise \
  --test tests/test_press_flow_m.yaml \
  --base_port 4723 \
  --device ipad1 \
  --device_name 200018
```

YAML 文件：
```yaml
- page: 'M_HomePage'
  actions:
    - method: 'check_connected'
      params: '200018'  # 这个值会被运行时传入的值覆盖
```

**方式2：YAML 中不传 params，使用运行时传入的值**
```yaml
- page: 'M_HomePage'
  actions:
    - method: 'check_connected'
      # 不传 params，使用运行时传入的 --device_name
```

**方式3：都不传，使用方法的默认值**
```yaml
- page: 'M_HomePage'
  actions:
    - method: 'check_connected'
      # 不传 params，运行时也不传 --device_name，使用方法默认值
```

#### 支持的方法
所有需要 `device_name` 参数的方法都会自动支持，包括：
- `check_connected(device_name='200018')` - 检查连接状态
- `connect(device_name)` - 连接设备
- 其他将来添加的需要 `device_name` 的方法

系统会自动检测方法签名，如果方法需要 `device_name` 参数，会自动应用运行时传入的值。

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
- 检查 `utils/elements/` 目录下对应文件中的定位器
- 使用 `take_screenshot` 查看当前页面状态
- 添加 `wait` 或 `wait_for_element_to_appear` 等待页面加载
- 确认页面名称和元素名称是否正确

### 4. 页面类不存在
- **无需担心！** 系统支持动态创建页面类
- 只需在 `utils/elements/` 中定义元素即可
- 在 YAML 中直接使用页面名称，系统会自动创建类

### 5. 截图目录结构
- 截图按运行时间戳、执行次数、用例序号自动组织
- 每次运行都会创建新的时间戳目录
- 每个用例的截图保存在独立的子目录中

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