from pages.base_page import BasePage

class CjUserPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'CjUserPage'
    
    # 方法
    def click_start_collect_button(self):
        """点击开始采集按钮"""
        by, locator = self._get_locator(self.page_name, 'start_collect_button')
        self.click(by, locator)
    
    def take_screenshot(self, name=None):
        """截图方法"""
        if name is None:
            name = f"cj_user_page"
        return self.screenshot(name)