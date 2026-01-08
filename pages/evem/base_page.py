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
        """加载元素配置文件
        支持两种方式：
        1. 从 utils/elements/ 目录加载所有 .yaml 文件（推荐）
        2. 从 utils/elements.yaml 加载（向后兼容）
        """
        if BasePage._elements is None:
            # 现在 base_page.py 在 pages/evev/ 或 pages/evem/ 子目录中，需要多一层 dirname
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            elements_dir = os.path.join(base_dir, 'utils', 'elements')
            elements_file = os.path.join(base_dir, 'utils', 'elements.yaml')
            
            BasePage._elements = {}
            
            # 优先从 elements 目录加载
            if os.path.exists(elements_dir) and os.path.isdir(elements_dir):
                print(f"📂 从目录加载元素: {elements_dir}")
                # 扫描目录下所有 .yaml 文件
                yaml_files = [f for f in os.listdir(elements_dir) if f.endswith('.yaml') or f.endswith('.yml')]
                
                if yaml_files:
                    for yaml_file in sorted(yaml_files):
                        file_path = os.path.join(elements_dir, yaml_file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                file_elements = yaml.safe_load(f)
                                if file_elements:
                                    # 合并元素定义（如果同一个页面在多个文件中定义，后面的会覆盖前面的）
                                    for page_name, page_elements in file_elements.items():
                                        if page_name in BasePage._elements:
                                            # 合并同一页面的元素
                                            BasePage._elements[page_name].update(page_elements)
                                        else:
                                            BasePage._elements[page_name] = page_elements
                                    print(f"  ✅ 已加载: {yaml_file}")
                        except Exception as e:
                            print(f"  ⚠️ 加载文件失败 {yaml_file}: {e}")
                    
                    if BasePage._elements:
                        print(f"📊 共加载 {len(BasePage._elements)} 个页面的元素定义")
                        return
            
            # 如果目录不存在或为空，尝试加载单个文件（向后兼容）
            if os.path.exists(elements_file):
                print(f"📄 从文件加载元素: {elements_file}")
                try:
                    with open(elements_file, 'r', encoding='utf-8') as f:
                        BasePage._elements = yaml.safe_load(f) or {}
                        print(f"✅ 已加载元素文件")
                except Exception as e:
                    print(f"❌ 加载元素文件失败: {e}")
                    BasePage._elements = {}
            else:
                print(f"⚠️ 未找到元素配置文件: {elements_file} 或目录: {elements_dir}")
                BasePage._elements = {}
    
    def _load_popups(self):
        """加载弹窗配置文件"""
        if BasePage._popups is None:
            # 现在 base_page.py 在 pages/evev/ 或 pages/evem/ 子目录中，需要多一层 dirname
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            popups_file = os.path.join(base_dir, 'utils', 'popups.yaml')
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
                'accessibility_id': AppiumBy.ACCESSIBILITY_ID,
                'ios_predicate': AppiumBy.IOS_PREDICATE
            }
            
            return (by_mapping.get(by_type, AppiumBy.XPATH), locator)
        except KeyError:
            raise ValueError(f"元素 '{element_name}' 在页面 '{page_name}' 中未找到")
    
    def find_element_by_name(self, page_name, element_name):
        """通过元素名称查找元素"""
        by, locator = self._get_locator(page_name, element_name)
        return self.find(by, locator)

    def find(self, by, locator):
        """查找单个元素
        
        注意：如果元素找不到，会直接抛出异常，不会自动处理弹窗或重试
        """
        return self.wait.until(EC.presence_of_element_located((by, locator)))

    def click_element(self, element_name):
        """直接点击元素 - 简化方法
        
        Args:
            element_name: 元素名称，格式为 "页面名.元素名" 或直接元素名
        
        注意：如果元素找不到或点击失败，会抛出异常，不会返回 False
        """
        if '.' in element_name:
            # 格式: "页面名.元素名"
            page_name, element = element_name.split('.', 1)
            by, locator = self._get_locator(page_name, element)
        else:
            # 直接元素名，使用当前页面
            by, locator = self._get_locator(self.page_name, element_name)
        
        self.click(by, locator)
        print(f"✅ 已点击元素: {element_name}")

    def send_keys_element(self, element_name, value):
        """直接向元素输入文本 - 简化方法
        
        Args:
            element_name: 元素名称，格式为 "页面名.元素名" 或直接元素名
            value: 要输入的文本
        
        注意：如果元素找不到或输入失败，会抛出异常，不会返回 False
        """
        if '.' in element_name:
            # 格式: "页面名.元素名"
            page_name, element = element_name.split('.', 1)
            by, locator = self._get_locator(page_name, element)
        else:
            # 直接元素名，使用当前页面
            by, locator = self._get_locator(self.page_name, element_name)
        
        self.send_keys(by, locator, value)
        print(f"✅ 已向元素 {element_name} 输入文本: {value}")

    def click(self, by, locator):
        """点击元素
        
        对于 StaticText 等可能不可直接点击的元素，会：
        1. 先检查元素是否可点击，如果可点击则直接点击
        2. 如果不可点击或点击失败，使用坐标点击（点击元素中心）
        3. 如果还失败，尝试点击父元素
        """
        el = self.find(by, locator)
        
        # 检查元素是否可点击
        try:
            # 尝试等待元素可点击（最多等待1秒）
            wait_clickable = WebDriverWait(self.driver, 1)
            clickable_el = wait_clickable.until(EC.element_to_be_clickable((by, locator)))
            clickable_el.click()
            print(f"✅ 元素可点击，已直接点击")
        except Exception:
            # 如果元素不可点击或等待超时，使用坐标点击
            print(f"⚠️ 元素可能不可直接点击，使用坐标点击")
            try:
                location = el.location
                size = el.size
                center_x = location['x'] + size['width'] / 2
                center_y = location['y'] + size['height'] / 2
                print(f"📍 使用元素中心坐标点击: ({int(center_x)}, {int(center_y)})")
                self.driver.tap([(int(center_x), int(center_y))])
                print(f"✅ 已通过坐标点击元素")
            except Exception as coord_error:
                # 如果坐标点击也失败，尝试点击父元素
                print(f"⚠️ 坐标点击也失败，尝试点击父元素: {coord_error}")
                try:
                    # 获取父元素并点击
                    parent = el.find_element(AppiumBy.XPATH, "..")
                    parent_location = parent.location
                    parent_size = parent.size
                    parent_center_x = parent_location['x'] + parent_size['width'] / 2
                    parent_center_y = parent_location['y'] + parent_size['height'] / 2
                    print(f"📍 使用父元素中心坐标点击: ({int(parent_center_x)}, {int(parent_center_y)})")
                    self.driver.tap([(int(parent_center_x), int(parent_center_y))])
                    print(f"✅ 已通过父元素坐标点击")
                except Exception as parent_error:
                    # 所有方法都失败，抛出异常
                    error_msg = f"❌ 所有点击方法都失败: 直接点击失败，坐标点击失败({coord_error})，父元素点击失败({parent_error})"
                    print(error_msg)
                    raise Exception(error_msg) from parent_error

    def click_by_coordinates(self, x, y):
        """通过坐标点击
        
        Args:
            x: X坐标
            y: Y坐标
        """
        try:
            x, y = int(x), int(y)
            print(f"🎯 点击坐标: ({x}, {y})")
            
            self.driver.tap([(x, y)])
            
            print(f"✅ 已点击坐标: ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ 点击坐标失败: ({x}, {y}) - {e}")
            return False

    def tap(self, x, y, duration=100):
        """轻触坐标（tap）
        
        Args:
            x: X坐标
            y: Y坐标
            duration: 持续时间（毫秒），默认100ms
        """
        try:
            x, y = int(x), int(y)
            duration = int(duration)
            print(f"🎯 轻触坐标: ({x}, {y}), 持续时间: {duration}ms")
            
            self.driver.tap([(x, y)], duration)
            
            print(f"✅ 已轻触坐标: ({x}, {y})")
            return True
            
        except Exception as e:
            print(f"❌ 轻触坐标失败: ({x}, {y}) - {e}")
            return False

    def swipe(self, start_x, start_y, end_x, end_y, duration=1000):
        """滑动操作
        
        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 滑动持续时间（毫秒），默认1000ms
        """
        try:
            start_x, start_y = int(start_x), int(start_y)
            end_x, end_y = int(end_x), int(end_y)
            duration = int(duration)
            
            print(f"↔️ 滑动: ({start_x}, {start_y}) -> ({end_x}, {end_y}), 持续时间: {duration}ms")
            
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            
            print(f"✅ 已滑动到: ({end_x}, {end_y})")
            return True
            
        except Exception as e:
            print(f"❌ 滑动失败: ({start_x}, {start_y}) -> ({end_x}, {end_y}) - {e}")
            return False

    def swipe_up(self, start_y=None, distance=500):
        """向上滑动
        
        Args:
            start_y: 起始Y坐标（可选，默认屏幕中部）
            distance: 滑动距离（像素），默认500
        """
        try:
            # 获取屏幕尺寸
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            # 默认从屏幕中部向上滑动
            if start_y is None:
                start_y = height // 2
            
            start_y = int(start_y)
            distance = int(distance)
            
            start_x = width // 2
            end_x = start_x
            end_y = start_y - distance
            
            print(f"⬆️ 向上滑动: 距离={distance}px")
            
            return self.swipe(start_x, start_y, end_x, end_y)
            
        except Exception as e:
            print(f"❌ 向上滑动失败: {e}")
            return False

    def swipe_down(self, start_y=None, distance=500):
        """向下滑动
        
        Args:
            start_y: 起始Y坐标（可选，默认屏幕中部）
            distance: 滑动距离（像素），默认500
        """
        try:
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            if start_y is None:
                start_y = height // 2
            
            start_y = int(start_y)
            distance = int(distance)
            
            start_x = width // 2
            end_x = start_x
            end_y = start_y + distance
            
            print(f"⬇️ 向下滑动: 距离={distance}px")
            
            return self.swipe(start_x, start_y, end_x, end_y)
            
        except Exception as e:
            print(f"❌ 向下滑动失败: {e}")
            return False

    def swipe_left(self, start_x=None, distance=300):
        """向左滑动
        
        Args:
            start_x: 起始X坐标（可选，默认屏幕中部）
            distance: 滑动距离（像素），默认300
        """
        try:
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            if start_x is None:
                start_x = width // 2
            
            start_x = int(start_x)
            distance = int(distance)
            
            start_y = height // 2
            end_y = start_y
            end_x = start_x - distance
            
            print(f"⬅️ 向左滑动: 距离={distance}px")
            
            return self.swipe(start_x, start_y, end_x, end_y)
            
        except Exception as e:
            print(f"❌ 向左滑动失败: {e}")
            return False

    def swipe_right(self, start_x=None, distance=300):
        """向右滑动
        
        Args:
            start_x: 起始X坐标（可选，默认屏幕中部）
            distance: 滑动距离（像素），默认300
        """
        try:
            size = self.driver.get_window_size()
            width = size['width']
            height = size['height']
            
            if start_x is None:
                start_x = width // 2
            
            start_x = int(start_x)
            distance = int(distance)
            
            start_y = height // 2
            end_y = start_y
            end_x = start_x + distance
            
            print(f"➡️ 向右滑动: 距离={distance}px")
            
            return self.swipe(start_x, start_y, end_x, end_y)
            
        except Exception as e:
            print(f"❌ 向右滑动失败: {e}")
            return False

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
        
        目录结构: screenshots/run_{运行时间戳}/times_{执行次数}/case_{用例序号}/
        
        Args:
            name: 截图文件名，如果不指定则自动生成
            timestamp: 是否在文件名中添加时间戳
        """
        import os
        import time
        from datetime import datetime
        
        # 基础截图目录（现在 base_page.py 在子目录中，需要多一层 dirname）
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_screenshot_dir = os.path.join(base_dir, 'screenshots')
        
        # 获取运行信息（从环境变量或默认值）
        run_start_timestamp = os.environ.get('RUN_START_TIMESTAMP', datetime.now().strftime("%Y%m%d_%H%M%S"))
        run_number = os.environ.get('CURRENT_RUN_NUMBER', '1')
        case_index = os.environ.get('CURRENT_CASE_INDEX', '1')
        
        # 构建目录结构: screenshots/run_{时间戳}/times_{次数}/case_{用例序号}/
        run_dir = os.path.join(base_screenshot_dir, f"run_{run_start_timestamp}")
        times_dir = os.path.join(run_dir, f"times_{run_number}")
        case_dir = os.path.join(times_dir, f"case_{case_index}")
        
        # 创建目录（如果不存在）
        if not os.path.exists(case_dir):
            os.makedirs(case_dir, exist_ok=True)
        
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
        file_path = os.path.join(case_dir, name)
        
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

    def is_element_present_by_name(self, element_name, timeout=3):
        """通过元素名称检查元素是否存在（不抛出异常）
        
        Args:
            element_name: 元素名称，格式为 "页面名.元素名" 或直接元素名
            timeout: 超时时间（秒），默认3秒
        
        Returns:
            bool: 元素是否存在
        """
        try:
            if '.' in element_name:
                # 格式: "页面名.元素名"
                page_name, element = element_name.split('.', 1)
                by, locator = self._get_locator(page_name, element)
            else:
                # 直接元素名，使用当前页面
                by, locator = self._get_locator(self.page_name, element_name)
            
            return self.is_element_present(by, locator, timeout)
        except:
            return False

    def wait_for_element_to_appear(self, element_name, timeout=30):
        """等待指定元素出现
        
        支持两种调用方式：
        1. 通过元素名称: wait_for_element_to_appear('element_name', 30)
        2. 通过元素名称和超时: wait_for_element_to_appear(['element_name', 30])
        
        Args:
            element_name: 元素名称（字符串）或 [元素名称, 超时时间]（列表）
            timeout: 超时时间（秒），如果 element_name 是列表则忽略此参数
        """
        import time
        
        # 处理参数格式：支持 ['element_name', timeout] 或 'element_name', timeout
        if isinstance(element_name, list) and len(element_name) >= 2:
            actual_element_name = element_name[0]
            actual_timeout = element_name[1] if isinstance(element_name[1], (int, float)) else timeout
        else:
            actual_element_name = element_name
            actual_timeout = timeout
        
        try:
            by, locator = self._get_locator(self.page_name, actual_element_name)
            print(f"⏳ 等待元素出现: {actual_element_name}, 超时时间: {actual_timeout}秒")
            print(f"📍 元素定位: {by}={locator}")
        except ValueError as e:
            print(f"❌ 错误: {e}")
            print(f"💡 提示: 请检查 elements.yaml 中 {self.page_name} 页面是否定义了 '{actual_element_name}' 元素")
            # 即使元素未定义，也抛出异常，让用户知道需要先定义元素
            raise ValueError(f"元素 '{actual_element_name}' 在页面 '{self.page_name}' 中未定义，无法等待。请先在 elements.yaml 中定义该元素。") from e
        
        start_time = time.time()
        while time.time() - start_time < actual_timeout:
            if self.is_element_present(by, locator, timeout=0.5):
                print(f"✅ 元素 {actual_element_name} 已出现")
                return True
            time.sleep(0.5)  # 每0.5秒检查一次
        
        print(f"⏰ 等待元素 {actual_element_name} 出现超时 ({actual_timeout}秒)")
        return False  # 超时

    def wait_for_element_to_disappear(self, element_name, timeout=30):
        """等待指定元素消失"""
        import time
        try:
            by, locator = self._get_locator(self.page_name, element_name)
            print(f"⏳ 等待元素消失: {element_name}, 超时时间: {timeout}秒")
            print(f"📍 元素定位: {by}={locator}")
        except ValueError as e:
            print(f"❌ 错误: {e}")
            print(f"💡 提示: 请检查 elements.yaml 中 {self.page_name} 页面是否定义了 '{element_name}' 元素")
            return False
        
        # 首先检查元素是否存在，如果不存在则直接返回成功
        if not self.is_element_present(by, locator, timeout=1):
            print(f"ℹ️ 元素 {element_name} 本来就不存在，无需等待")
            return True
        
        print(f"🔍 元素 {element_name} 当前存在，开始等待消失...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查元素是否还存在
            if not self.is_element_present(by, locator, timeout=0.5):
                print(f"✅ 元素 {element_name} 已消失")
                return True
            time.sleep(0.5)  # 每0.5秒检查一次
        
        print(f"⏰ 等待元素 {element_name} 消失超时 ({timeout}秒)")
        return False  # 超时

    def _handle_popups(self):
        """处理可能的弹窗（包括系统弹窗）"""
        popup_handled = False
        
        print("🔍 开始检查弹窗...")
        
        for popup in BasePage._popups.get('popups', []):
            try:
                # 对于系统弹窗，使用稍长的超时时间（1.5秒），普通弹窗使用更短的超时（0.5秒）以加快检查速度
                timeout = 1.5 if '系统' in popup.get('description', '') or '权限' in popup.get('description', '') else 0.5
                
                # 检查弹窗是否存在
                if self.is_element_present(AppiumBy.XPATH, popup['xpath'], timeout=timeout):
                    print(f"🚨 发现弹窗: {popup['description']}")
                    print(f"📍 弹窗XPath: {popup['xpath']}")
                    
                    # 先截图记录弹窗状态
                    try:
                        self.screenshot(f"popup_{popup['description'].replace(' ', '_').replace('（', '_').replace('）', '_')}")
                    except:
                        pass  # 截图失败不影响弹窗处理
                    
                    # 点击弹窗按钮
                    # 对于系统弹窗，使用更宽松的等待
                    try:
                        self.click(AppiumBy.XPATH, popup['xpath'])
                        print(f"✅ 已点击弹窗: {popup['description']}")
                        popup_handled = True
                        
                        # 等待一下让弹窗消失
                        import time
                        time.sleep(1.5)  # 系统弹窗可能需要更长时间消失
                        break  # 处理一个弹窗后退出
                    except Exception as click_error:
                        # 如果点击失败，尝试使用坐标点击（对于系统弹窗）
                        print(f"⚠️ 使用XPath点击失败，尝试查找元素位置: {click_error}")
                        try:
                            # 尝试获取元素并点击
                            element = self.driver.find_element(AppiumBy.XPATH, popup['xpath'])
                            location = element.location
                            size = element.size
                            center_x = location['x'] + size['width'] / 2
                            center_y = location['y'] + size['height'] / 2
                            self.driver.tap([(center_x, center_y)])
                            print(f"✅ 已通过坐标点击弹窗: {popup['description']}")
                            popup_handled = True
                            import time
                            time.sleep(1.5)
                            break
                        except Exception as coord_error:
                            print(f"⚠️ 坐标点击也失败: {coord_error}")
                            continue
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


    def close_app(self, bundle_id=None):
        """关闭app
        
        Args:
            bundle_id: app的bundleId或appPackage，如果不提供则从环境变量获取
        """
        import time
        try:
            # 如果没有提供bundle_id，从环境变量获取
            if bundle_id is None:
                bundle_id = os.environ.get('CURRENT_BUNDLE_ID')
                if not bundle_id:
                    print("❌ 未提供bundle_id且环境变量中也没有，无法关闭app")
                    return False
            
            print(f"🔒 正在关闭app: {bundle_id}")
            self.driver.terminate_app(bundle_id)
            print(f"✅ App已关闭")
            time.sleep(1)  # 等待关闭完成
            return True
        except Exception as e:
            print(f"❌ 关闭app失败: {e}")
            return False

    def open_app(self, bundle_id=None):
        """打开app
        
        Args:
            bundle_id: app的bundleId或appPackage，如果不提供则从环境变量获取
        """
        import time
        try:
            # 如果没有提供bundle_id，从环境变量获取
            if bundle_id is None:
                bundle_id = os.environ.get('CURRENT_BUNDLE_ID')
                if not bundle_id:
                    print("❌ 未提供bundle_id且环境变量中也没有，无法打开app")
                    return False
            
            print(f"🚀 正在打开app: {bundle_id}")
            self.driver.execute_script("mobile: launchApp", {"bundleId": bundle_id})
            print(f"✅ App已打开")
            time.sleep(2)  # 等待app启动
            return True
        except Exception as e:
            print(f"❌ 打开app失败: {e}")
            return False



def initialize_app(driver):
    """
    App 重新安装后的初始化操作 
    v执行 m不执行
    
    只有在重新安装 app 时才会调用此函数进行初始化操作，例如：
    - 处理权限弹窗
    - 跳过引导页
    - 登录等
    
    Args:
        driver: Appium driver 实例
    """
    print("🔧 开始执行 App 初始化操作（重新安装后）...")
    
    try:
        # 创建临时页面对象用于初始化操作
        from pages.evem.base_page import BasePage
        
        # 动态创建初始化页面类
        class InitPage(BasePage):
            def __init__(self, driver):
                BasePage.__init__(self, driver)
                self.page_name = 'InitPage'
        
        init_page = InitPage(driver)
        
        # 等待 app 启动
        import time
        time.sleep(2)
        
        # 处理可能的弹窗（权限弹窗等）
        init_page.check_and_handle_popups(3)
        
        # 首次安装启动后的初始化操作
        try:
            # 点击 doraemon logo dark 按钮
            print("🔧 点击 doraemon logo dark 按钮...")
            init_page.click(AppiumBy.XPATH, "//XCUIElementTypeButton[@name='doraemon logo dark']")
            time.sleep(1)
            
            # 点击"小恶魔"文本
            print("🔧 点击小恶魔...")
            init_page.click(AppiumBy.XPATH, "//XCUIElementTypeStaticText[@name='小恶魔']")
            time.sleep(1)
            
            # 点击"OTA自动化-屏蔽网线直连"开关
            print("🔧 点击 OTA自动化-屏蔽网线直连 开关...")
            init_page.click(AppiumBy.XPATH, "//XCUIElementTypeSwitch[@name='OTA自动化-屏蔽网线直连']")
            time.sleep(0.5)
            
            # 点击"OTA自动化-屏蔽标定弹窗"开关
            print("🔧 点击 OTA自动化-屏蔽标定弹窗 开关...")
            init_page.click(AppiumBy.XPATH, "//XCUIElementTypeSwitch[@name='OTA自动化-屏蔽标定弹窗']")
            time.sleep(0.5)
            
            # 点击"关闭"按钮
            print("🔧 点击关闭按钮...")
            init_page.click(AppiumBy.XPATH, "//XCUIElementTypeButton[@name='关闭']")
            time.sleep(1)
            
            print("✅ 初始化配置完成")
        except Exception as init_error:
            print(f"⚠️ 初始化配置操作出错: {init_error}")
            # 继续执行，不影响后续测试
        
        print("✅ App 初始化操作完成")
        
    except Exception as e:
        print(f"⚠️ App 初始化操作出错: {e}")
        # 初始化失败不影响测试继续执行
        pass
