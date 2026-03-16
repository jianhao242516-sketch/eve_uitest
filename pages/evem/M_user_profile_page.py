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
        if self.is_element_present_by_name('start_detect_button', timeout=3):
            self.click_element('start_detect_button')
            return True

        print("ℹ️ 未找到 M_UserProfilePage.start_detect_button，可能已直接进入拍照页，跳过点击。")
        return True

    def new_report_button(self, *args, **kwargs):
        """点击用户资料页中的“最新报告/新建报告”按钮（必要时滚动后重试）"""
        # 先快速探测一下，避免直接等待 10s 超时
        if self.is_element_present_by_name('new_report_button', timeout=2):
            self.click_element('new_report_button')
            return True

        # 可能在屏幕下方，尝试上滑后重试
        for _ in range(3):
            self.swipe_up(distance=500)
            if self.is_element_present_by_name('new_report_button', timeout=2):
                self.click_element('new_report_button')
                return True

        # 兜底：让 click_element 抛出更明确的超时异常并触发截图
        self.click_element('new_report_button')
        return True
    
    def assert_user_profile_page_loaded(self):
        """断言用户资料页已加载 - 验证开始检测按钮或头像存在"""
        found = self.is_element_present_by_name('start_detect_button', timeout=5) \
            or self.is_element_present_by_name('user_avatar', timeout=5)
        if not found:
            raise AssertionError("用户资料页未加载：未找到开始检测按钮或头像元素")
        print("✅ 断言通过：用户资料页已加载")
        return True
    
    def assert_start_detect_button_exists(self):
        """断言开始检测按钮存在"""
        self.assert_element_exists('start_detect_button')
        print("✅ 断言通过：开始检测按钮存在")
        return True

