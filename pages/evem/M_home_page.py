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

    def connect(self,device_name):
        """连接设备
        
        在2分钟内尝试查找设备元素，如果找到就点击，如果找不到就报错
        
        Args:
            device_name: 设备名称
        """
        self.click_element('connect_wlj')
        self.check_and_handle_popups(3)
        # 使用 name 定位元素（类似 Java 的 name == 'name'）
        device_text = 'ruby 1'  # 调试先用 ruby 1，后续改为 device_name
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
            error_msg = f"❌ 查找或点击设备元素失败: ruby 1, 错误: {e}"
            print(error_msg)
            print(f"🔍 错误详情: {type(e).__name__}: {str(e)}")
            raise TimeoutError(error_msg) from e
        self.click_element('connect_next_button')
        #判断是否需要输入Wi-Fi密码，寻找输入密码的元素
        if self.is_element_present_by_name('connect_password_input'):
            self.send_keys_element('connect_password_input', 'meitutest85389')
            self.click_element('connect_password_button')
            self.check_and_handle_popups(3)
        print("点击空白处，防止eve king关机引导")
        self.click_by_coordinates(100, 100)
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