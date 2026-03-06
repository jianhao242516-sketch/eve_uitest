from pages.evem.base_page import BasePage


class M_UserProfilePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_UserProfilePage'

    def click_start_detect_if_exists(self):
        """
        如果在用户资料页且存在“开始检测”按钮，则点击；
        如果当前不是资料页（例如新建用户后直接进入拍照页），则什么都不做。
        """
        # 资料页场景：存在开始检测按钮
        if self.is_element_present_by_name('start_detect_button', timeout=3):
            self.click_element('start_detect_button')
            return True

        # 新建用户场景：直接进入拍照页/其他页面，没有资料页按钮，安全跳过
        print("ℹ️ 未找到 M_UserProfilePage.start_detect_button，可能已直接进入拍照页，跳过点击。")
        return True

