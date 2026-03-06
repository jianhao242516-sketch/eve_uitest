from pages.evem.base_page import BasePage


class M_NewUserPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_NewUserPage'

    def create_random_user(self, user_name=None):
        """新客建档：手机号/性别/生日/协议/下一步（姓名默认由搜索词带入，若页面要求则兜底）"""
        import random
        import time

        try:
            self.check_and_handle_popups(1)
        except Exception:
            pass

        # 姓名一般由搜索词带入；如页面仍提供输入框则兜底填充（不作为强依赖）
        if self.is_element_present_by_name('name_input', timeout=1):
            fallback_name = user_name or f"自动化{random.randint(1000, 9999)}"
            try:
                self.send_keys_element('name_input', fallback_name)
            except Exception:
                pass

        # 2) 输入手机号（155 开头 11 位）
        random_phone = "155" + "".join(str(random.randint(0, 9)) for _ in range(8))
        if self.is_element_present_by_name('phone_input', timeout=3):
            self.send_keys_element('phone_input', random_phone)
        else:
            raise TimeoutError("新客建档页未找到手机号输入框（M_NewUserPage.phone_input）")

        # 3) 选择性别（男女随机，找不到女则退化点击男）
        gender_pick = random.choice(["male", "female"])
        if gender_pick == "female" and self.is_element_present_by_name('gender_female', timeout=1):
            self.click_element('gender_female')
        elif self.is_element_present_by_name('gender_male', timeout=1):
            self.click_element('gender_male')

        # 4) 选择生日：点“请选择出生日期”->点“确定”（不改滚轮，使用默认日期）
        if self.is_element_present_by_name('birthday_select', timeout=2):
            self.click_element('birthday_select')
            if self.is_element_present_by_name('birthday_confirm', timeout=3):
                self.click_element('birthday_confirm')

        # 5) 勾选协议：优先 class chain，其次 xpath，最后坐标兜底
        clicked_agreement = False
        try:
            if self.is_element_present_by_name('agreement_checkbox_chain', timeout=2):
                clicked_agreement = self._tap_element_center('agreement_checkbox_chain')
            elif self.is_element_present_by_name('agreement_checkbox', timeout=2):
                clicked_agreement = self._tap_element_center('agreement_checkbox')
        except Exception as e:
            print(f"⚠️ 协议勾选元素点击失败: {type(e).__name__}: {e}")

        if not clicked_agreement:
            try:
                # 你抓到的元素位置约为 x=30,y=755,w=14,h=14；点中心更稳
                ok = self.click_by_coordinates(37, 762)
                if ok:
                    clicked_agreement = True
                else:
                    # click_by_coordinates 失败时通常不会抛异常，而是返回 False
                    print("⚠️ 协议勾选坐标点击失败(37,762): 返回 False（可能坐标不准/被遮挡/Session异常）")
            except Exception as _e:
                print(f"⚠️ 协议勾选坐标点击异常(37,762): {type(_e).__name__}: {_e}")

        # 6) 点击下一步
        if self.is_element_present_by_name('next_step', timeout=5):
            self.click_element('next_step')
        else:
            raise TimeoutError("新客建档页未找到下一步按钮（M_NewUserPage.next_step）")

        # 7) 校验是否真正提交成功并跳转到拍照页/检测页
        # 注意：点击“下一步”不代表一定生效；若协议未真正勾选，常见表现是仍停留在建档页
        if self.is_element_present_by_name('M_DetectPage.camera_button', timeout=10) or \
           self.is_element_present_by_name('M_DetectPage.still_button', timeout=2):
            print("✅ 新客建档提交成功：已进入拍照页/检测页")
            return True

        # 若未跳转：做一次“协议坐标兜底 + 再点下一步”的重试
        try:
            print("⚠️ 点击下一步后未进入拍照页，尝试重试：坐标勾选协议(37,762) -> 再点下一步")
            self.click_by_coordinates(37, 762)
            time.sleep(0.2)
            if self.is_element_present_by_name('next_step', timeout=2):
                self.click_element('next_step')
        except Exception as retry_e:
            print(f"⚠️ 重试勾选协议/下一步时异常: {type(retry_e).__name__}: {retry_e}")

        if self.is_element_present_by_name('M_DetectPage.camera_button', timeout=10) or \
           self.is_element_present_by_name('M_DetectPage.still_button', timeout=2):
            print("✅ 新客建档提交成功：已进入拍照页/检测页（重试后）")
            return True

        # 仍未跳转：截图并抛出明确错误，指向第5步（协议）/第6步（下一步）未生效
        try:
            self.screenshot("new_user_submit_failed", timestamp=True)
        except Exception:
            pass

        still_on_new_user_page = (
            self.is_element_present_by_name('phone_input', timeout=1)
            or self.is_element_present_by_name('next_step', timeout=1)
        )
        if still_on_new_user_page:
            raise TimeoutError("新客建档提交失败：疑似第5步协议未勾选生效或第6步下一步未生效（仍停留在建档页）")
        raise TimeoutError("新客建档提交失败：未检测到进入拍照页/检测页（M_DetectPage.camera_button/still_button）")

    def _tap_element_center(self, element_name: str) -> bool:
        """直接点击元素中心坐标，尽量绕开 visible=false 导致的 click 不生效问题"""
        try:
            by, locator = self._get_locator(self.page_name, element_name)
            el = self.find(by, locator)
            loc = el.location
            size = el.size
            cx = int(loc.get('x', 0) + size.get('width', 0) / 2)
            cy = int(loc.get('y', 0) + size.get('height', 0) / 2)
            print(f"🎯 协议勾选点元素中心: ({cx},{cy}) visible={getattr(el, 'is_displayed', lambda: 'n/a')()}")
            return self.click_by_coordinates(cx, cy)
        except Exception as e:
            print(f"⚠️ 计算/点击元素中心失败({element_name}): {type(e).__name__}: {e}")
            return False

