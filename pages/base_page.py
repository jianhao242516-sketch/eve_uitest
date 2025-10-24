from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import yaml
import os

# 所有页面类都继承自 BasePage，负责提供：
# 元素定位封装（find, click, send_keys）
# 等待机制
# 通用操作（截图、滑动等）
class BasePage:
    _elements = None  # 类变量，缓存元素配置
    _popups = None    # 类变量，缓存弹窗配置
    
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self._load_elements()
        self._load_popups()
    
    def _load_elements(self):
        """加载元素配置文件"""
        if BasePage._elements is None:
            elements_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'elements.yaml')
            with open(elements_file, 'r', encoding='utf-8') as f:
                BasePage._elements = yaml.safe_load(f)
    
    def _load_popups(self):
        """加载弹窗配置文件"""
        if BasePage._popups is None:
            popups_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'popups.yaml')
            with open(popups_file, 'r', encoding='utf-8') as f:
                BasePage._popups = yaml.safe_load(f)
    
    def _get_locator(self, page_name, element_name):
        """根据页面名和元素名获取定位器"""
        try:
            element_info = BasePage._elements[page_name][element_name]
            by_type = element_info[0].lower()
            locator = element_info[1]
            
            # 转换定位方式
            by_mapping = {
                'xpath': AppiumBy.XPATH,
                'id': AppiumBy.ID,
                'name': AppiumBy.NAME,
                'class': AppiumBy.CLASS_NAME,
                'tag': AppiumBy.TAG_NAME,
                'accessibility_id': AppiumBy.ACCESSIBILITY_ID
            }
            
            return (by_mapping.get(by_type, AppiumBy.XPATH), locator)
        except KeyError:
            raise ValueError(f"元素 '{element_name}' 在页面 '{page_name}' 中未找到")
    
    def find_element_by_name(self, page_name, element_name):
        """通过元素名称查找元素"""
        by, locator = self._get_locator(page_name, element_name)
        return self.find(by, locator)

    def find(self, by, locator):
        """查找单个元素"""
        try:
            return self.wait.until(EC.presence_of_element_located((by, locator)))
        except Exception as e:
            # 查找元素失败时，尝试处理可能的弹窗
            if self._handle_popups():
                # 弹窗处理后重试查找
                return self.wait.until(EC.presence_of_element_located((by, locator)))
            else:
                # 没有弹窗或弹窗处理失败，抛出原始异常
                raise e

    def click_element(self, element_name):
        """直接点击元素 - 简化方法
        
        Args:
            element_name: 元素名称，格式为 "页面名.元素名" 或直接元素名
        """
        try:
            if '.' in element_name:
                # 格式: "页面名.元素名"
                page_name, element = element_name.split('.', 1)
                by, locator = self._get_locator(page_name, element)
            else:
                # 直接元素名，使用当前页面
                by, locator = self._get_locator(self.page_name, element_name)
            
            self.click(by, locator)
            print(f"✅ 已点击元素: {element_name}")
            return True
        except Exception as e:
            print(f"❌ 点击元素失败: {element_name} - {e}")
            return False

    def click(self, by, locator):
        """点击元素"""
        el = self.find(by, locator)
        el.click()

    def send_keys(self, by, locator, value):
        """输入文本"""
        el = self.find(by, locator)
        el.clear()
        el.send_keys(value)

    def get_text(self, by, locator):
        """获取元素文本"""
        el = self.find(by, locator)
        return el.text

    def screenshot(self, name=None, timestamp=True):
        """截图方法
        
        Args:
            name: 截图文件名，如果不指定则自动生成
            timestamp: 是否在文件名中添加时间戳
        """
        import os
        import time
        from datetime import datetime
        
        # 创建截图目录 - 每次运行一个文件夹
        base_screenshot_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
        
        # 获取运行次数信息（从环境变量或默认值）
        run_number = os.environ.get('CURRENT_RUN_NUMBER', '1')
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_dir = os.path.join(base_screenshot_dir, f"run_{run_number}_{run_timestamp}")
        
        # 如果文件夹已存在，添加序号
        counter = 1
        original_dir = screenshot_dir
        while os.path.exists(screenshot_dir):
            screenshot_dir = f"{original_dir}_{counter}"
            counter += 1
        
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
        
        # 生成文件名
        if name is None:
            name = f"screenshot_{self.page_name}"
        
        # 添加时间戳到文件名
        if timestamp:
            current_time = datetime.now().strftime("%H%M%S")
            name = f"{name}_{current_time}"
        
        # 确保文件扩展名
        if not name.endswith('.png'):
            name += '.png'
        
        # 完整路径
        file_path = os.path.join(screenshot_dir, name)
        
        try:
            self.driver.save_screenshot(file_path)
            print(f"📸 截图已保存: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ 截图失败: {e}")
            return None

    def is_element_present(self, by, locator, timeout=3):
        """检查元素是否存在（不抛出异常）"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, locator)))
            return True
        except:
            return False

    def wait_for_element_to_appear(self, element_name, timeout=30):
        """等待指定元素出现"""
        import time
        try:
            by, locator = self._get_locator(self.page_name, element_name)
            print("等待元素出现,超时时间", timeout, "元素", by, locator)
        except ValueError as e:
            print(f"❌ 错误: {e}")
            print(f"💡 提示: 请检查 elements.yaml 中 {self.page_name} 页面是否定义了 '{element_name}' 元素")
            return False
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_element_present(by, locator, timeout=1):
                return True
            time.sleep(0.5)  # 每0.5秒检查一次
        
        return False  # 超时

    def wait_for_element_to_disappear(self, element_name, timeout=30):
        """等待指定元素消失"""
        import time
        try:
            by, locator = self._get_locator(self.page_name, element_name)
            print("等待元素消失,超时时间", timeout, "元素", by, locator)
        except ValueError as e:
            print(f"❌ 错误: {e}")
            print(f"💡 提示: 请检查 elements.yaml 中 {self.page_name} 页面是否定义了 '{element_name}' 元素")
            return False
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not self.is_element_present(by, locator, timeout=1):
                return True
            time.sleep(0.5)  # 每0.5秒检查一次
        
        return False  # 超时

    def _handle_popups(self):
        """处理可能的弹窗"""
        popup_handled = False
        
        print("🔍 开始检查弹窗...")
        
        for popup in BasePage._popups.get('popups', []):
            try:
                # 检查弹窗是否存在
                if self.is_element_present(AppiumBy.XPATH, popup['xpath'], timeout=1):
                    print(f"🚨 发现弹窗: {popup['description']}")
                    print(f"📍 弹窗XPath: {popup['xpath']}")
                    
                    # 先截图记录弹窗状态
                    self.screenshot(f"popup_{popup['description'].replace(' ', '_')}")
                    
                    # 点击弹窗按钮
                    self.click(AppiumBy.XPATH, popup['xpath'])
                    print(f"✅ 已点击弹窗: {popup['description']}")
                    popup_handled = True
                    
                    # 等待一下让弹窗消失
                    import time
                    time.sleep(1)
                    break  # 处理一个弹窗后退出
            except Exception as e:
                # 弹窗处理失败，继续检查下一个
                print(f"⚠️ 处理弹窗失败: {popup['description']} - {e}")
                continue
        
        if not popup_handled:
            print("ℹ️ 未发现需要处理的弹窗")
        
        return popup_handled

    def handle_popups_manually(self):
        """手动处理弹窗（主动调用）"""
        return self._handle_popups()
    
    def check_and_handle_popups(self, max_attempts=3):
        """主动检查并处理弹窗，最多尝试max_attempts次"""
        print("🔍 主动检查弹窗...")
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            print(f"🔄 第 {attempts} 次检查弹窗...")
            
            if self._handle_popups():
                print(f"✅ 第 {attempts} 次检查发现并处理了弹窗")
                # 继续检查是否还有其他弹窗
                continue
            else:
                print(f"ℹ️ 第 {attempts} 次检查未发现弹窗")
                break
        
        print(f"🏁 弹窗检查完成，共检查了 {attempts} 次")

    def assert_element_exists(self, element_or_by, locator_or_page=None, message=None):
        """断言元素存在 - 支持元素名称或定位器"""
        if locator_or_page is None:
            # 使用元素名称: assert_element_exists('HomePage.searchuser')
            page_name, element_name = element_or_by.split('.')
            by, locator = self._get_locator(page_name, element_name)
        else:
            # 使用定位器: assert_element_exists(by, locator)
            by, locator = element_or_by, locator_or_page
            
        if not self.is_element_present(by, locator):
            error_msg = message or f"元素不存在: {by}={locator}"
            raise AssertionError(error_msg)
        return True

    def assert_element_not_exists(self, element_or_by, locator_or_page=None, message=None):
        """断言元素不存在 - 支持元素名称或定位器"""
        if locator_or_page is None:
            # 使用元素名称
            page_name, element_name = element_or_by.split('.')
            by, locator = self._get_locator(page_name, element_name)
        else:
            # 使用定位器
            by, locator = element_or_by, locator_or_page
            
        if self.is_element_present(by, locator):
            error_msg = message or f"元素应该不存在但实际存在: {by}={locator}"
            raise AssertionError(error_msg)
        return True

    def assert_text_equals(self, element_or_by, locator_or_page=None, expected_text=None, message=None):
        """断言元素文本等于预期值 - 支持元素名称或定位器"""
        if expected_text is None:
            # 使用元素名称: assert_text_equals('HomePage.searchuser', 'expected_text')
            page_name, element_name = element_or_by.split('.')
            by, locator = self._get_locator(page_name, element_name)
            expected_text = locator_or_page
        else:
            # 使用定位器: assert_text_equals(by, locator, expected_text)
            by, locator = element_or_by, locator_or_page
            
        actual_text = self.get_text(by, locator)
        if actual_text != expected_text:
            error_msg = message or f"文本不匹配: 期望'{expected_text}', 实际'{actual_text}'"
            raise AssertionError(error_msg)
        return True

    def assert_text_contains(self, element_or_by, locator_or_page=None, expected_text=None, message=None):
        """断言元素文本包含预期值 - 支持元素名称或定位器"""
        if expected_text is None:
            # 使用元素名称
            page_name, element_name = element_or_by.split('.')
            by, locator = self._get_locator(page_name, element_name)
            expected_text = locator_or_page
        else:
            # 使用定位器
            by, locator = element_or_by, locator_or_page
            
        actual_text = self.get_text(by, locator)
        if expected_text not in actual_text:
            error_msg = message or f"文本不包含: 期望包含'{expected_text}', 实际'{actual_text}'"
            raise AssertionError(error_msg)
        return True
