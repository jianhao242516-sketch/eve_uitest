from pages.evev.base_page import BasePage

class V_UserProfilePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'V_UserProfilePage'
    
    # 方法
    def startdetect(self):
        """开始检测"""
        self.click_element('start_detect_button')
        #判断是否开始检测成功
        if self.is_element_present_by_name('V_DetectPage.still_button'):
            print("✅ 开始检测成功")
        else:
            print("❌ 开始检测失败")
            raise TimeoutError("开始检测失败")
