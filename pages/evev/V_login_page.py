from pages.evev.base_page import BasePage
import time
class V_LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'V_LoginPage'
    
    # 方法示例
    def login(self, username, password):
        """登录"""
        self.click_element('login_button')
        self.send_keys_element('username_input', username)
        self.send_keys_element('password_input', password)
        self.click_element('login_button')
        time.sleep(3)
        #断言登录成功
        self.assert_element_exists('V_HomePage.searchuser')

    def login_out(self):
        """登出"""
        self.click_element('logout_button')
