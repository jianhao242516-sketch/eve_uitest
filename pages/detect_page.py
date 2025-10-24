from pages.base_page import BasePage

class DetectPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'DetectPage'
    
    # 方法
    def click_still(self):
        by, locator = self._get_locator(self.page_name, 'still_button')
        self.click(by, locator)

    def click_save_button(self):
        """点击保存按钮"""
        by, locator = self._get_locator(self.page_name, 'detect_next_button')
        self.click(by, locator)
    
    def take_screenshot(self, name=None):
        """截图方法"""
        if name is None:
            name = f"detect_page"
        return self.screenshot(name)
