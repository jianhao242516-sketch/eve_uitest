from pages.evev.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'HomePage'
    
    
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
        by = AppiumBy.XPATH
        locator = "//XCUIElementTypeStaticText[@name='V_{}']".format(device_name)
        
        # 在2分钟内尝试查找元素
        print(f"🔍 开始查找设备: V_{device_name}，最多等待2分钟...")
        try:
            wait = WebDriverWait(self.driver, 120)  # 2分钟 = 120秒
            element = wait.until(EC.presence_of_element_located((by, locator)))
            print(f"✅ 找到设备元素: V_{device_name}")
            element.click()
            print(f"✅ 已点击设备: V_{device_name}")
        except Exception as e:
            error_msg = f"❌ 在2分钟内未找到设备元素: V_{device_name}"
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
        if self.is_element_present_by_name('UserProfilePage.start_detect_button'):
            print("✅ 进入用户资料页成功")





    def disconnect(self):
        """断开连接"""
        self.click_element('disconnect_button')