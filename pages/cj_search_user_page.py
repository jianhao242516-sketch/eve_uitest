from pages.base_page import BasePage

class CjSearchUserPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'CjSearchUserPage'
    
    # 方法
    def input_user_search(self, username):
        """输入用户搜索关键词"""
        by, locator = self._get_locator(self.page_name, 'user_search_input')
        self.send_keys(by, locator, value=username)

    def click_only_one_user(self):
        """点击唯一用户结果"""
        by, locator = self._get_locator(self.page_name, 'only_one_user')
        self.click(by, locator)

    def take_screenshot(self, name=None):
        """截图方法"""
        if name is None:
            name = f"cj_search_user_page"
        return self.screenshot(name)
