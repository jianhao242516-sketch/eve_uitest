from pages.evev.base_page import BasePage

class DetectPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'DetectPage'
    
    def detect_success(self):
        """检测成功"""
        self.click_element('still_button')
        
