from pages.evem.base_page import BasePage

class M_ReportPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_ReportPage'

    def report_operation_methods(self, X, Y):
        # 点击坐标
        self.click_by_coordinates(X, Y)
        
        # 判断是否为2D视图 → 切换3D
        if self._is_2d_view():
            self._switch_to_3d_view()
        
        # 执行滑动操作
        self._perform_swipe_operations()
        return True
    
    def _is_2d_view(self):
        """判断是否为2D视图，等待2秒，如果元素出现则为2D视图，否则为3D视图"""
        # 使用原有的 is_element_present_by_name 方法，传入2秒超时
        try:
            has_content_scroll = self.is_element_present_by_name(f'{self.page_name}.content_scroll', 2)
        except Exception as e:
            print(f"DEBUG: content_scroll 检查异常: {e}")
            has_content_scroll = False
        
        try:
            has_content_scroll_xpath = self.is_element_present_by_name(f'{self.page_name}.content_scroll_xpath', 2)
        except Exception as e:
            print(f"DEBUG: content_scroll_xpath 检查异常: {e}")
            has_content_scroll_xpath = False
        
        print(f"DEBUG: content_scroll={has_content_scroll}, content_scroll_xpath={has_content_scroll_xpath}")
        
        return has_content_scroll or has_content_scroll_xpath
    
    def _switch_to_3d_view(self):
        print('进入2D视图')
        self.click_by_coordinates(601, 104)
        print('点击切换3D视图')
    
    def _perform_swipe_operations(self):
        swipe_steps = [
            (523, 411, 285, 417),
            (255, 397, 519, 387),
            (861, 533, 857, 198),
        ]
        for start_x, start_y, end_x, end_y in swipe_steps:
            self.swipe(start_x, start_y, end_x, end_y)
    
    def assert_report_page_loaded(self):
        """断言报告页已加载 - 验证综合分析元素存在"""
        self.assert_element_exists('zhfx')
        
        print("✅ 断言通过：报告页已加载")
        return True
    
    def assert_zhfx_element_exists(self):
        """断言综合分析元素存在"""
        self.assert_element_exists('zhfx')
        print("✅ 断言通过：综合分析元素存在")
        return True
