from pages.base_page import BasePage

class CjSearchXmPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'CjSearchXmPage'
    
    # 方法
    def input_project_search(self, project_name):
        """输入项目搜索关键词"""
        by, locator = self._get_locator(self.page_name, 'project_search_input')
        self.send_keys(by, locator, value=project_name)


    def click_first_project(self):
        """点击第一个项目结果"""
        by, locator = self._get_locator(self.page_name, 'first_project_result')
        self.click(by, locator)

    def take_screenshot(self, name=None):
        """截图方法"""
        if name is None:
            name = f"cj_search_xm_page"
        return self.screenshot(name)

    def search_project_enter(self, project_name):
        """搜索项目"""
        self.input_project_search(project_name)
        self.click_first_project()
        self.wait(2)