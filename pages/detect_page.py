from pages.base_page import BasePage

class DetectPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'DetectPage'
    
    def take_screenshot(self, name=None):
        """截图方法"""
        if name is None:
            name = f"detect_page"
        return self.screenshot(name)
