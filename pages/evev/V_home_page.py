from pages.evev.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages.evev.V_login_page import V_LoginPage
class V_HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'V_HomePage'
    def isHomePage(self):
        #先找门店设置页，如果没有，就判断是否登录页，如果是登录页就登录，不是的话就报错
        if self.is_element_present_by_name('mdsz_button'):
            return True
        elif self.is_element_present_by_name('username_input'):
            login_page = V_LoginPage(self.driver)
            login_page.login('lxr55', 'Test123#')
            return True
        else:
            raise TimeoutError("页面异常，不是首页")

#判断是否勿弹线连
#连接

    def connect(self,device_name):
        """连接设备
        
        在2分钟内尝试查找设备元素，如果找到就点击，如果找不到就报错
        
        Args:
            device_name: 设备名称
        """
        self.click_element('connect_wlj')
        self.check_and_handle_popups(3)

        device_text = device_name  # 调试先用 ruby 1，后续改为 device_name
        locator = f"name == '{device_text}'"
        # 在2分钟内尝试查找元素
        print(f"🔍 开始查找设备: {device_text}，最多等待2分钟...")
        try:
            wait = WebDriverWait(self.driver, 120)  # 2分钟 = 120秒
            # 使用 name 定位元素
            element = wait.until(EC.presence_of_element_located((AppiumBy.IOS_PREDICATE, locator)))
            print(f"✅ 找到设备元素: {device_text}")
            
            # 获取元素的位置和大小
            location = element.location
            size = element.size
            print(f"📍 元素位置: x={location['x']}, y={location['y']}, width={size['width']}, height={size['height']}")
            
            # 按照 Java 代码的逻辑计算点击位置
            # Java: driver.clickactionxy(e1.getLocation().x+size, e1.getLocation().y-size*4)
            # x = 元素 x + 元素高度
            # y = 元素 y - 元素高度*4
            click_x = location['x'] + size['height']
            click_y = location['y'] - size['height'] * 4
            print(f"📍 点击坐标: ({click_x}, {click_y})")
            
            # 点击计算出的位置
            self.click_by_coordinates(click_x, click_y)
            print(f"✅ 已点击设备: {device_text}")
        except Exception as e:
            error_msg = f"❌ 在2分钟内未找到设备元素: {device_name}"
            print(error_msg)
            raise TimeoutError(error_msg) from e
        self.click_element('connect_next_button')
        #判断是否需要输入Wi-Fi密码，寻找输入密码的元素
        if self.is_element_present_by_name('connect_password_input'):
            self.send_keys_element('connect_password_input', 'meitutest85389')
            self.click_element('connect_password_button')
            self.check_and_handle_popups(3)
        
        #判断是否连接成功
        if self.is_element_present_by_name('connect_disconnect_button'):
            print("✅ 连接成功")
        else:
            print("❌ 连接失败")
            raise TimeoutError("连接失败")
        

    def searchuser(self,user_name):
        """搜索用户"""
        self.send_keys_element('searchuser', user_name)
        self.click_element('searchresult1')
        #判断是否搜索成功
        if self.is_element_present_by_name('V_UserProfilePage.start_detect_button'):
            print("✅ 进入用户资料页成功")


    def check_connected(self,device_name):
        """检查是否连接成功"""
        # 优先显式等待一段时间，避免刚进入页面状态尚未稳定
        found = self.wait_for_element_to_appear('connected_button', timeout=3) \
            or self.is_element_present_by_name('connected_button', timeout=3) \
            or self.is_element_present_by_name('connected_button_1', timeout=3)
        if found:
            print("✅ 已连接")
        else:
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
