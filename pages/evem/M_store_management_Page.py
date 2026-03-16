from pages.evem.base_page import BasePage


class M_store_management_Page(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        # 与 EveM_pages.yaml 中的页面名保持一致
        self.page_name = 'M_store_management_Page'

    def open_customer_profile_detail(self):
        """
        门店管理页：
        1）点击"顾客档案"入口
        2）再点击顾客档案详情（固定坐标 x=565, y=243）
        """
        # 1. 点击"顾客档案"按钮（通过元素定位）
        self.click_element('customer_profile')
        # 2. 点击顾客档案详情（你提供的坐标）
        self.click_by_coordinates(565, 243)
    
    def assert_store_management_page_loaded(self):
        """断言门店管理页已加载 - 验证顾客档案元素存在"""
        self.assert_element_exists('customer_profile')
        print("✅ 断言通过：门店管理页已加载")
        return True
