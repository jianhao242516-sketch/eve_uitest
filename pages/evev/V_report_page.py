from pages.evev.base_page import BasePage

class V_ReportPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        # 注意：elements.yaml中使用的是'Reportpage'，V_后仍沿用此大小写
        self.page_name = 'V_Reportpage'
    
    # 方法示例
    def click_zhfx(self):
        """点击综合分析"""
        by, locator = self._get_locator(self.page_name, 'zhfx')
        self.click(by, locator)
    
