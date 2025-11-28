from pages.evem.base_page import BasePage

class M_LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_LoginPage'
    
    # 方法示例
    def login(self, username, password):
        """登录"""
        self.click_element('username_input')
        self.send_keys_element('username_input', username)
        print("点击左边100，100，防止键盘上移")
        self.click_by_coordinates(100, 100)
        self.click_element('password_input')
        self.send_keys_element('password_input', password)
        self.click_element('login_button')
        #断言登录成功
        self.assert_element_exists('HomePage.searchuser')

    def login_out(self):
        """登出"""
        self.click_element('logout_button')
