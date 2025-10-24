from pages.base_page import BasePage

class VideoDetectPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'VideoDetectPage'
    
    # 方法
    def click_start_video_button(self):
        """点击开始录制按钮"""
        by, locator = self._get_locator(self.page_name, 'start_video_button')
        self.click(by, locator)

    def click_save_button(self):
        """点击保存按钮"""
        by, locator = self._get_locator(self.page_name, 'save_button')
        self.click(by, locator)
