from pages.evem.base_page import BasePage

class M_LoginPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_LoginPage'
    
    # 方法示例
    def login(self, username, password):
        """登录"""
        # 如果已经登录（已在首页），则跳过登录步骤：
        # 条件：同时存在首页搜索框和“门店管理”按钮，避免误判到其他页面
        try:
            has_search = self.is_element_present_by_name('M_HomePage.searchuser', timeout=2)
            has_mdgl = self.is_element_present_by_name('M_HomePage.store_management_button', timeout=2)
            if has_search and has_mdgl:
                print("✅ 检测到首页元素 searchuser + store_management_button，判定账号已登录，跳过登录步骤")
                return
        except Exception:
            # 探测失败不影响后续正常登录流程
            pass

        self.click_element('username_input')
        print("点击左边100，100，防止键盘上移")
        self.click_by_coordinates(100, 100)
        self.send_keys_element('username_input', username)
        print("点击左边100，100，防止键盘上移")
        self.click_by_coordinates(100, 100)
        self.click_element('password_input')
        self.send_keys_element('password_input', password)
        self.click_element('login_button')
        
        # 断言登录成功：等待首页元素出现
        self.assert_login_success()
    
    def assert_login_success(self):
        """断言登录成功 - 验证首页元素出现"""
        self.wait_for_element_to_appear(['M_HomePage.searchuser', 30])
        self.wait_for_element_to_appear(['M_HomePage.store_management_button', 10])
        print("✅ 断言通过：登录成功，已进入首页")

    def login_out(self):
        """登出"""
        self.click_element('logout_button')
    
    def assert_login_page_loaded(self):
        """断言登录页已加载 - 验证登录按钮存在"""
        self.assert_element_exists('login_button')
        print("✅ 断言通过：登录页已加载")
