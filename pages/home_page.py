from pages.base_page import BasePage

class HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'HomePage'
    
    #方法
    def click_searchuser(self):
        by, locator = self._get_locator(self.page_name, 'searchuser')
        self.click(by, locator)

    def input_searchuser(self, username):
        by, locator = self._get_locator(self.page_name, 'searchuser')
        self.send_keys(by, locator, value=username)

    def click_searchresult1(self):
        by, locator = self._get_locator(self.page_name, 'searchresult1')
        self.click(by, locator)
    
    # 断言方法示例
    def assert_searchuser_exists(self):
        """断言搜索框存在"""
        by, locator = self._get_locator(self.page_name, 'searchuser')
        return self.is_element_present(by, locator)
    
    def assert_searchresult1_exists(self):
        """断言第一个搜索结果存在"""
        by, locator = self._get_locator(self.page_name, 'searchresult1')
        return self.is_element_present(by, locator)
    
