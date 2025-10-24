from pages.base_page import BasePage

class LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'LoginPage'
    
    # 方法示例
    def input_username(self, username):
        """输入用户名"""
        by, locator = self._get_locator(self.page_name, 'username_input')
        self.send_keys(by, locator, value=username)
    
    def input_password(self, password):
        """输入密码"""
        by, locator = self._get_locator(self.page_name, 'password_input')
        self.send_keys(by, locator, value=password)
    
    def click_login(self):
        """点击登录按钮"""
        by, locator = self._get_locator(self.page_name, 'login_button')
        self.click(by, locator)
    
    def get_error_message(self):
        """获取错误信息"""
        by, locator = self._get_locator(self.page_name, 'error_message')
        return self.get_text(by, locator)
