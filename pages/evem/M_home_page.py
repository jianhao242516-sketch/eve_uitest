from pages.evem.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class M_HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_HomePage'
    
    
#判断是否勿弹线连
#连接

    def connect(self, device_name, device_text=None):
        """连接设备（优化版）"""
        self.click_element('connect_wlj')
        self.check_and_handle_popups(3)

        # 优化1：扩展设备定位方式（支持XPATH/Predicate/包含匹配）
        locators = [
            (AppiumBy.IOS_PREDICATE, f"name == '{device_name}'"),  # 原方式
            (AppiumBy.IOS_PREDICATE, f"label CONTAINS '{device_name}'"),
            (AppiumBy.XPATH, f"//*[contains(@name, '{device_name}') or contains(@label, '{device_name}')]"),
        ]

        # 优化2：延长等待时间（3分钟），并增加重试
        element = None
        wait = WebDriverWait(self.driver, 180)  # 3分钟
        for by, locator in locators:
            try:
                print(f"🔍 尝试定位设备 [{device_name}]：{by} = {locator}")
                element = wait.until(EC.presence_of_element_located((by, locator)))
                if element:
                    print(f"✅ 找到设备元素: {device_name}")
                    break
            except:
                continue

        if not element:
            raise TimeoutError(f"❌ 未找到设备 [{device_name}]，所有定位方式均失败")

        # 优化3：坐标计算容错（防止负数/越界）
        location = element.location
        size = element.size
        click_x = location['x'] + size['height']
        click_y = location['y'] - size['height'] * 4

        # 确保坐标在屏幕范围内
        size = self.driver.get_window_size()
        click_x = max(0, min(click_x, size['width']))
        click_y = max(0, min(click_y, size['height']))

        print(f"📍 点击坐标: ({click_x}, {click_y})")
        self.click_by_coordinates(click_x, click_y)
        print(f"✅ 已点击设备: {device_text}")

        self.click_element('connect_next_button')

        # 处理Wi-Fi密码
        if self.is_element_present_by_name('connect_password_input'):
            self.send_keys_element('connect_password_input', 'meitutest85389')
            self.click_element('connect_password_button')
            self.check_and_handle_popups(3)

        self.click_by_coordinates(100, 100)  # 防止引导浮窗

        # 验证连接状态
        found = self.wait_for_element_to_appear('connected_button', timeout=20) \
                or self.is_element_present_by_name('connected_button_1', timeout=10) \
                or self.is_element_present_by_name('connected_button_2', timeout=10)

        if found:
            print("✅ 连接成功")
        else:
            print("❌ 连接失败")
            raise TimeoutError("连接失败")

    def searchuser(self, user_name):
        """
        搜索用户，若用户不存在则根据user_name新建用户
        :param user_name: 要搜索/新建的用户名
        """
        try:
            # 防止软关机浮窗遮挡，点击空白处
            self.click_by_coordinates(100, 100)

            # 输入用户名进行搜索
            self.send_keys_element('searchuser', user_name)

            # 先判断第一个搜索结果是否存在
            if self.is_element_present_by_name('searchresult1'):
                # 存在则点击进入
                self.click_element('searchresult1')

                # 判断是否成功进入用户资料页
                if self.is_element_present_by_name('UserProfilePage.start_detect_button'):
                    print(f"✅ 搜索到用户【{user_name}】，进入用户资料页成功")
            else:
                # 搜索结果不存在，执行新建用户逻辑
                print(f"❌ 未找到用户【{user_name}】，开始新建用户...")

                # --------------------------
                # 以下是新建用户的核心逻辑（请根据实际页面元素补充）
                # --------------------------
                # 1. 点击"新建用户"按钮（示例元素名，需替换为实际值）
                self.click_element('create_new_user_btn')

                # 2. 输入要新建的用户名（复用传入的user_name）
                self.send_keys_element('new_user_name_input', user_name)

                # 3. 点击"确认创建"按钮（示例元素名，需替换为实际值）
                self.click_element('confirm_create_user_btn')

                # 4. 验证新建是否成功（根据实际页面元素调整判断条件）
                if self.is_element_present_by_name('UserProfilePage.start_detect_button'):
                    print(f"✅ 用户【{user_name}】新建成功，并进入用户资料页")
                else:
                    print(f"❌ 用户【{user_name}】新建失败")

        except Exception as e:
            # 捕获异常，避免方法直接崩溃
            print(f"⚠️ 搜索/新建用户【{user_name}】时出现异常：{str(e)}")
            raise e  # 可选：抛出异常让上层处理，根据测试框架需求决定

    def check_connected(self,device_name):
        """检查是否连接成功"""
        # 优先显式等待一段时间，避免刚进入页面状态尚未稳定
        found = self.wait_for_element_to_appear('connected_button', timeout=3) \
            or self.is_element_present_by_name('connected_button', timeout=3) \
            or self.is_element_present_by_name('connected_button_1', timeout=3)\
            or self.is_element_present_by_name('connected_button_2', timeout=3)
        if found:
            print("✅ 已连接")
        else:
            print("❌ 未连接")
            # 兜底：截图并尝试在页面源码里查找关键字，便于定位差异
            try:
                self.screenshot("connected_check", timestamp=True)
                src = self.driver.page_source or ""
                hint = "连接良好" if "连接良好" in src else ("断开连接" if "断开连接" in src else "")
                if hint:
                    print(f"ℹ️ 在页面源码中发现关键字: {hint}，但未匹配当前定位表达式")
            except Exception as e:
                print(f"⚠️ 采集调试信息失败: {e}")
            print(f"❌ 未连接,尝试连接{device_name}")
            self.connect(device_name)


    def disconnect(self):
        """断开连接"""
        self.click_element('disconnect_button')