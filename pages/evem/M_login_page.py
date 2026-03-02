from pages.evem.base_page import BasePage

class M_LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_LoginPage'
    
    # 方法示例
    def login(self, username, password):
        """登录"""
                # 如果已经登录（已在首页/可见首页元素），则跳过登录步骤
        try:
            if self.is_element_present_by_name('M_HomePage.searchuser', timeout=2):
                print("✅ 检测到账号已登录，跳过登录步骤1")
                return
        except Exception:
            # 探测失败不影响后续正常登录流程
            pass

        self.click_element('username_input')
        print("点击左边100，100，防止键盘上移")
        self.click_by_coordinates(100, 100)
        self.send_keys_element('username_input', username)
        print("点击左边100，100，防止键盘上移")
        self.click_by_coordinates(100, 100)
        self.click_element('password_input')
        self.send_keys_element('password_input', password)
        self.click_element('login_button')
        #断言登录成功
        self.assert_element_exists('M_HomePage.searchuser')

    def login_out(self):
        """登出"""
        self.click_element('logout_button')
