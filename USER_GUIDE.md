# Ruby Eve UI Test 用户指南

## 📖 目录

1. [快速开始](#快速开始)
2. [测试用例编写](#测试用例编写)
3. [可用方法列表](#可用方法列表)
4. [最佳实践](#最佳实践)
5. [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 运行单个测试用例

```bash
python3 main/run_ui.py \
  --bundleId com.meitu.MTKingEnterprise \
  --test tests/test_cj_collect_flow_element.yaml \
  --base_port 4723 \
  --device 23M4 \
  --times 1
```

### 2. 运行多次测试

```bash
python3 main/run_ui.py \
  --bundleId com.meitu.MTKingEnterprise \
  --test tests/test_cj_collect_flow_element.yaml \
  --base_port 4723 \
  --device 23M4 \
  --times 10
```

### 3. 多设备并行测试

```bash
python3 main/run_ui.py \
  --bundleId com.meitu.MTKingEnterprise \
  --test tests/test_cj_collect_flow.yaml \
  --base_port 4723 \
  --device 23M4,iPad_01
```

---

## 📝 测试用例编写

### 基本结构

测试用例使用 YAML 格式，基本结构如下：

```yaml
- name: '用例名称'
  steps:
    - page: '页面名称'
      actions:
        - method: '方法名'
          params: '参数值'
```

### 完整示例

```yaml
- name: '采集流程测试'
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
        
        # 截图
        - method: 'take_screenshot'
          params: 'search_result'
        
        # 点击下一个元素
        - method: 'click_element'
          params: 'first_project_result'
    
    - page: 'CjUserPage'
      actions:
        # 等待元素出现
        - method: 'wait_for_element_to_appear'
          params: ['start_collect_button', 10]
        
        # 点击元素
        - method: 'click_element'
          params: 'start_collect_button'
```

### 多个用例

```yaml
# 第一个用例
- name: '完整采集流程'
  steps:
    - page: 'CjSearchXmPage'
      actions:
        - method: 'click_element'
          params: 'project_search_input'

# 第二个用例（会自动重启APP）
- name: '采集流程-视频不采集'
  steps:
    - page: 'CjSearchXmPage'
      actions:
        - method: 'click_element'
          params: 'project_search_input'
```

---

## 🛠️ 可用方法列表

### 1. 元素操作

#### `click_element(element_name)`
点击元素

**参数:**
- `element_name`: 元素名称（当前页面元素）或 `'页面名.元素名'`（跨页面元素）

**示例:**
```yaml
# 点击当前页面的元素
- method: 'click_element'
  params: 'start_collect_button'

# 点击其他页面的元素
- method: 'click_element'
  params: 'DetectPage.confirm_button'
```

#### `send_keys_element(element_name, value)`
向元素输入文本

**参数:**
- `element_name`: 元素名称
- `value`: 要输入的文本

**示例:**
```yaml
- method: 'send_keys_element'
  params: ['project_search_input', '11']
```

#### `click_by_coordinates(x, y)`
通过坐标点击

**参数:**
- `x`: X坐标
- `y`: Y坐标

**示例:**
```yaml
- method: 'click_by_coordinates'
  params: [200, 300]
```

#### `tap(x, y, duration=100)`
轻触坐标

**参数:**
- `x`: X坐标
- `y`: Y坐标
- `duration`: 持续时间（毫秒），默认100ms

**示例:**
```yaml
- method: 'tap'
  params: [200, 300, 100]
```

---

### 2. 等待方法

#### `wait(seconds)`
强制等待

**参数:**
- `seconds`: 等待秒数

**示例:**
```yaml
- method: 'wait'
  params: 3
```

#### `wait_for_element_to_appear(element_name, timeout=30)`
等待元素出现

**参数:**
- `element_name`: 元素名称
- `timeout`: 超时时间（秒），默认30秒

**示例:**
```yaml
- method: 'wait_for_element_to_appear'
  params: ['start_video_button', 10]
```

#### `wait_for_element_to_disappear(element_name, timeout=30)`
等待元素消失

**参数:**
- `element_name`: 元素名称
- `timeout`: 超时时间（秒），默认30秒

**示例:**
```yaml
- method: 'wait_for_element_to_disappear'
  params: ['shooting_button', 30]
```

---

### 3. 截图

#### `take_screenshot(name)`
截图

**参数:**
- `name`: 截图文件名（可选）

**示例:**
```yaml
- method: 'take_screenshot'
  params: 'end'

# 或使用默认名称
- method: 'take_screenshot'
```

**注意:** 截图会自动保存在 `screenshots/run_{运行次数}_{时间戳}/` 目录下

---

### 4. 弹窗处理

#### `check_and_handle_popups(max_attempts)`
主动检查并处理弹窗

**参数:**
- `max_attempts`: 最多检查次数

**示例:**
```yaml
- method: 'check_and_handle_popups'
  params: 3
```

**说明:** 
- 自动检测 `popups.yaml` 中配置的弹窗
- 最多尝试 `max_attempts` 次
- 处理弹窗时会自动截图

---

### 5. 断言

#### `assert_element_exists(element_name)`
断言元素存在

**参数:**
- `element_name`: 元素名称（格式：`'页面名.元素名'`）

**示例:**
```yaml
- method: 'assert_element_exists'
  params: 'CjUserPage.is_CjUserPage'
```

#### `assert_element_not_exists(element_name)`
断言元素不存在

**示例:**
```yaml
- method: 'assert_element_not_exists'
  params: 'DetectPage.shooting_button'
```

#### `assert_text_equals(element_name, expected_text)`
断言元素文本等于期望值

**参数:**
- `element_name`: 元素名称
- `expected_text`: 期望的文本

**示例:**
```yaml
- method: 'assert_text_equals'
  params: ['username_label', '张三']
```

#### `assert_text_contains(element_name, expected_text)`
断言元素文本包含期望值

**示例:**
```yaml
- method: 'assert_text_contains'
  params: ['result_label', '成功']
```

---

## 💡 最佳实践

### 1. 用例结构

```yaml
- name: '清晰的用例名称'
  steps:
    - page: '页面名称'
      actions:
        # 1. 先检查弹窗
        - method: 'check_and_handle_popups'
          params: 3
        
        # 2. 执行操作
        - method: 'click_element'
          params: 'button'
        
        # 3. 等待加载
        - method: 'wait'
          params: 2
        
        # 4. 验证结果
        - method: 'assert_element_exists'
          params: 'ResultPage.success_message'
```

### 2. 等待元素的最佳实践

```yaml
# ❌ 不好的做法：盲目等待很长时间
- method: 'wait'
  params: 30

# ✅ 好的做法：等待特定元素
- method: 'wait_for_element_to_appear'
  params: ['next_page_element', 10]
```

### 3. 截图的位置

```yaml
# 在关键操作后截图
- method: 'click_element'
  params: 'submit_button'
- method: 'take_screenshot'
  params: 'after_submit'
- method: 'wait'
  params: 3
```

### 4. 元素命名的技巧

**在 `utils/elements.yaml` 中定义元素:**

```yaml
DetectPage:
  # 使用有意义的名称
  still_button: ['xpath', "//XCUIElementTypeStaticText[@name='仍旧拍摄']"]
  shooting_button: ['xpath', "//XCUIElementTypeStaticText[@name='拍摄中...']"]
  back_button: ['xpath', "//XCUIElementTypeImage[@name='icon_nav_back']"]
  
  # 特殊元素使用清晰的标识
  is_DetectPage: ['xpath', "//XCUIElementTypeStaticText[@name='检测页面']"]
```

### 5. 跨页面元素的引用

```yaml
# 可以在任何页面的用例中引用任何页面的元素
- method: 'click_element'
  params: 'DetectPage.confirm_button'  # 在CjUserPage中点击DetectPage的元素
```

---

## ❓ 常见问题

### Q1: 如何判断元素是否真的被点击了？

A: 可以使用以下方法：

```yaml
# 点击后等待特定元素出现
- method: 'click_element'
  params: 'submit_button'
- method: 'wait_for_element_to_appear'
  params: ['success_message', 10]
```

### Q2: 元素点击没有反应怎么办？

A: 尝试使用坐标点击：

```yaml
# 先使用元素点击
- method: 'click_element'
  params: 'button'

# 如果不行，使用坐标点击
- method: 'click_by_coordinates'
  params: [200, 300]
```

### Q3: 多个用例是否需要重启APP？

A: **会自动重启！** 每个用例开始前都会自动重启APP，确保环境干净。

### Q4: 如何调试测试用例？

A: 使用截图功能：

```yaml
# 在关键步骤前后截图
- method: 'take_screenshot'
  params: 'before_action'
- method: 'click_element'
  params: 'button'
- method: 'take_screenshot'
  params: 'after_action'
```

### Q5: 元素找不到怎么办？

A: 检查以下几点：

1. **检查元素定义**：确认 `elements.yaml` 中有定义
2. **添加等待**：使用 `wait_for_element_to_appear`
3. **截图查看**：使用 `take_screenshot` 查看当前页面
4. **处理弹窗**：使用 `check_and_handle_popups`

### Q6: 如何传递更复杂的参数？

```yaml
# 单参数
- method: 'click_element'
  params: 'button_name'

# 多个参数使用列表
- method: 'send_keys_element'
  params: ['input_field', 'text_value']

# 三元组
- method: 'wait_for_element_to_appear'
  params: ['element_name', 10]
```

---

## 📚 更多信息

- **元素配置**: `utils/elements.yaml`
- **设备配置**: `utils/devices.yaml`
- **弹窗配置**: `utils/popups.yaml`
- **日志查看**: 查看运行日志文件获取详细执行信息

---

## 🎯 快速参考

### 常用方法速查

| 方法 | 用途 | 示例 |
|------|------|------|
| `click_element` | 点击元素 | `params: 'button_name'` |
| `send_keys_element` | 输入文本 | `params: ['input_name', 'text']` |
| `click_by_coordinates` | 点击坐标 | `params: [200, 300]` |
| `wait` | 强制等待 | `params: 2` |
| `wait_for_element_to_appear` | 等待元素出现 | `params: ['element', 10]` |
| `wait_for_element_to_disappear` | 等待元素消失 | `params: ['element', 30]` |
| `take_screenshot` | 截图 | `params: 'screenshot_name'` |
| `check_and_handle_popups` | 处理弹窗 | `params: 3` |
| `assert_element_exists` | 断言存在 | `params: 'Page.element'` |
| `assert_text_equals` | 断言文本等于 | `params: ['Page.element', 'text']` |

---

**祝你测试顺利！🎉**

