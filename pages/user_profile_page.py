from pages.base_page import BasePage

class UserProfilePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'UserProfilePage'
    
    # 方法
    def click_startdetect(self):
        by, locator = self._get_locator(self.page_name, 'start_detect_button')
        self.click(by, locator)
