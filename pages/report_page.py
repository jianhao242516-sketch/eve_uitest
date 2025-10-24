from pages.base_page import BasePage

class ReportPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'Reportpage'  # 注意：elements.yaml中使用的是'Reportpage'
    
    # 方法示例
    def click_zhfx(self):
        """点击综合分析"""
        by, locator = self._get_locator(self.page_name, 'zhfx')
        self.click(by, locator)
    

