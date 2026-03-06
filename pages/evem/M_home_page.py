from pages.evem.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class M_HomePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_HomePage'
    
    
#判断是否勿弹线连
#连接

    def connect(self, device_name, device_text=None):
        """连接设备（优化版）"""
        self.click_element('connect_wlj')
        self.check_and_handle_popups(3)

        # 优化1：扩展设备定位方式（支持XPATH/Predicate/包含匹配）
        locators = [
            (AppiumBy.IOS_PREDICATE, f"name == '{device_name}'"),  # 原方式
            (AppiumBy.IOS_PREDICATE, f"label CONTAINS '{device_name}'"),
            (AppiumBy.XPATH, f"//*[contains(@name, '{device_name}') or contains(@label, '{device_name}')]"),
        ]

        # 优化2：延长等待时间（3分钟），并增加重试
        element = None
        wait = WebDriverWait(self.driver, 180)  # 3分钟
        for by, locator in locators:
            try:
                print(f"🔍 尝试定位设备 [{device_name}]：{by} = {locator}")
                element = wait.until(EC.presence_of_element_located((by, locator)))
                if element:
                    print(f"✅ 找到设备元素: {device_name}")
                    break
            except:
                continue

        if not element:
            raise TimeoutError(f"❌ 未找到设备 [{device_name}]，所有定位方式均失败")

        # 优化3：坐标计算容错（防止负数/越界）
        location = element.location
        size = element.size
        click_x = location['x'] + size['height']
        click_y = location['y'] - size['height'] * 4

        # 确保坐标在屏幕范围内
        size = self.driver.get_window_size()
        click_x = max(0, min(click_x, size['width']))
        click_y = max(0, min(click_y, size['height']))

        print(f"📍 点击坐标: ({click_x}, {click_y})")
        self.click_by_coordinates(click_x, click_y)
        print(f"✅ 已点击设备: {device_text}")

        self.click_element('connect_next_button')

        # 处理Wi-Fi密码
        if self.is_element_present_by_name('connect_password_input'):
            self.send_keys_element('connect_password_input', 'meitutest85389')
            self.click_element('connect_password_button')
            self.check_and_handle_popups(3)

        self.click_by_coordinates(100, 100)  # 防止引导浮窗

        # 验证连接状态
        found = self.wait_for_element_to_appear('connected_button', timeout=20) \
                or self.is_element_present_by_name('connected_button_1', timeout=10) \
                or self.is_element_present_by_name('connected_button_2', timeout=10)

        if found:
            print("✅ 连接成功")
        else:
            print("❌ 连接失败")
            raise TimeoutError("连接失败")

    def searchuser(self, user_name):
        """
        搜索用户，若用户不存在则根据user_name新建用户
        :param user_name: 要搜索/新建的用户名
        """
        try:
            import time

            # 防止浮窗/键盘遮挡，先点一下空白处
            self.click_by_coordinates(100, 100)
            
            # 1) 输入用户名
            self.send_keys_element('searchuser', user_name)

            # 2) 触发搜索（有的版本需要点“搜索”按钮才刷新结果）
            if self.is_element_present_by_name('search_button', timeout=1):
                self.click_element('search_button')
            else:
                # 没有搜索按钮也不直接失败，给 UI 一点时间刷新结果
                time.sleep(0.3)

            # 3) 等待搜索结果或直接跳转到用户资料页（两种都兼容）
            profile_ok = self.is_element_present_by_name('M_UserProfilePage.start_detect_button', timeout=2)
            if not profile_ok:
                self.wait_for_element_to_appear('searchresult1', timeout=6)

            # 4) 如果出现了第一条搜索结果，点击进入
            if self.is_element_present_by_name('searchresult1', timeout=1):
                self.click_element('searchresult1')

            # 5) 以“用户资料页-开始检测”作为最终成功判定
            if self.is_element_present_by_name('M_UserProfilePage.start_detect_button', timeout=8):
                print(f"✅ 搜索到用户【{user_name}】，进入用户资料页成功")
                return True

            # 6) 未进入资料页：尝试走“新建用户”流程（仅当元素已配置且真实存在时）
            print(f"❌ 未找到用户【{user_name}】或未能进入用户资料页，尝试新建用户分支...")
            timeout=10
            create_flow_candidates = [
                # 你提供的入口按钮：新客
                ('newuser_button', 'new_user_name_input', 'confirm_create_user_btn'),
                # 兼容旧占位名（如果后续有人在 yaml 里按旧名加了也能跑）
                ('create_new_user_btn', 'new_user_name_input', 'confirm_create_user_btn'),
            ]

            created_new_user = False
            for create_btn, name_input, confirm_btn in create_flow_candidates:
                if self.is_element_present_by_name(create_btn, timeout=1):
                    self.click_element(create_btn)
                    # 新客建档：按照页面要求随机填充信息并下一步
                    if create_btn == 'newuser_button':
                        from pages.evem.M_new_user_page import M_NewUserPage
                        # 新建用户：点完“下一步”进入拍照页即算流程结束
                        M_NewUserPage(self.driver).create_random_user(user_name=user_name)
                        created_new_user = True
                    else:
                        # 旧占位流程：如你后续在 yaml 里补齐了这些元素，也能继续工作
                        if self.is_element_present_by_name(name_input, timeout=2):
                            self.send_keys_element(name_input, user_name)
                        if self.is_element_present_by_name(confirm_btn, timeout=2):
                            self.click_element(confirm_btn)

                    # 新客建档成功的判定已在 M_NewUserPage.create_random_user 内完成（进入拍照页/检测页）
                    if created_new_user:
                        print(f"✅ 用户【{user_name}】新建流程完成（已进入拍照页）")
                        return True

                    if self.is_element_present_by_name('M_UserProfilePage.start_detect_button', timeout=10):
                        print(f"✅ 用户【{user_name}】新建成功，并进入用户资料页")
                        return True

                    # 已执行新客建档但未进入资料页：给出更准确的错误提示
                    if created_new_user:
                        try:
                            self.screenshot("new_user_after_submit_not_detect", timestamp=True)
                        except Exception:
                            pass
                        raise TimeoutError("新建用户后未进入拍照页：疑似协议未勾选生效/下一步未生效，或跳转慢导致超时")

            # 7) 兜底：采集调试信息并抛出异常（避免“逻辑不生效但不报错”）
            try:
                self.screenshot("searchuser_failed", timestamp=True)
                src = self.driver.page_source or ""
                hints = []
                for k in ["无结果", "没有找到", "新建", "创建", "用户"]:
                    if k in src:
                        hints.append(k)
                if hints:
                    print(f"ℹ️ 页面源码关键字提示: {', '.join(hints)}")
            except Exception as debug_e:
                print(f"⚠️ 采集调试信息失败: {debug_e}")

            raise TimeoutError(
                f"搜索用户【{user_name}】未进入用户资料页："
                f"未出现 searchresult1，且未配置/未出现新建用户入口元素（如需新建请在 elements yaml 中补齐）"
            )

        except Exception as e:
            # 捕获异常，避免方法直接崩溃
            print(f"⚠️ 搜索/新建用户【{user_name}】时出现异常：{str(e)}")
            raise e  # 可选：抛出异常让上层处理，根据测试框架需求决定

    def _start_detect_and_take_photo(self):
        """用户资料页：点击开始检测 -> 检测页执行拍照流程"""
        import time
        # 等待进入用户资料页
        if not self.is_element_present_by_name('M_UserProfilePage.start_detect_button', timeout=15):
            raise TimeoutError("新建成功后未进入用户资料页，找不到开始检测按钮（M_UserProfilePage.start_detect_button）")

        # 点击开始检测
        self.click_element('M_UserProfilePage.start_detect_button')
        time.sleep(1)

        # 进入检测页拍照
        try:
            from pages.evem.M_detect_page import M_DetectPage
            detect_page = M_DetectPage(self.driver)
            detect_page.take_photo_flow()
        except Exception as e:
            # 兜底：如果导入或调用失败，至少尝试直接点击相机按钮和 still_button
            print(f"⚠️ 调用拍照流程封装失败，将使用兜底点击: {e}")
            if self.is_element_present_by_name('M_DetectPage.camera_button', timeout=8):
                self.click_element('M_DetectPage.camera_button')
            # still_button/弹窗处理交给 detect_success 更稳，这里仅尽量推进
            if self.is_element_present_by_name('M_DetectPage.still_button', timeout=10):
                self.click_element('M_DetectPage.still_button')

    def check_connected(self,device_name):
        """检查是否连接成功"""
        # 优先显式等待一段时间，避免刚进入页面状态尚未稳定
        found = self.wait_for_element_to_appear('connected_button', timeout=3) \
            or self.is_element_present_by_name('connected_button', timeout=3) \
            or self.is_element_present_by_name('connected_button_1', timeout=3)\
            or self.is_element_present_by_name('connected_button_2', timeout=3)
        if found:
            print("✅ 已连接")
        else:
            print("❌ 未连接")
            # 兜底：截图并尝试在页面源码里查找关键字，便于定位差异
            try:
                self.screenshot("connected_check", timestamp=True)
                src = self.driver.page_source or ""
                hint = "连接良好" if "连接良好" in src else ("断开连接" if "断开连接" in src else "")
                if hint:
                    print(f"ℹ️ 在页面源码中发现关键字: {hint}，但未匹配当前定位表达式")
            except Exception as e:
                print(f"⚠️ 采集调试信息失败: {e}")
            print(f"❌ 未连接,尝试连接{device_name}")
            self.connect(device_name)

    def mdgl_button(self):
        """点击首页门店管理按钮"""
        self.click_element('mdgl_button')
        
        
    def disconnect(self):
        """断开连接"""
        self.click_element('disconnect_button')