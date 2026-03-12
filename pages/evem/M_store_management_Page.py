from pages.evem.base_page import BasePage


class M_store_management_Page(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        # page_name 必须和 elements.yaml 中的键一致
        self.page_name = 'M_store_management_Page'

    def open_customer_profile_detail(self):
        """
        门店管理页：点击“顾客档案”按钮，然后点击顾客档案详情（固定坐标）
        """
        # 1）点击“顾客档案”按钮
        self.click_element('customer_profile')

        # 2）点击顾客档案详情（你提供的坐标：x=565, y=243）
        self.click_by_coordinates(565, 243)

