from pages.other.base_page import BasePage
from appium.webdriver.common.appiumby import AppiumBy

class LaprairiePage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'laprairiePage'  # 必须与元素配置文件中的页面名一致（小写）
    
    def click_wj1(self):
        """点击"是的，我确认"选项（点击文本左侧的选框）
        会自动滚动到元素可见位置
        """
        import time
        
        # 要点击的"是的，我确认"文本（根据 XML，可能有多个）
        yes_confirm_xpath = "//XCUIElementTypeStaticText[@name='是的，我确认']"
        
        try:
            # 等待并查找所有"是的，我确认"文本元素
            import time as time_module
            start_time = time_module.time()
            text_elements = []
            while time_module.time() - start_time < 10:
                text_elements = self.driver.find_elements(AppiumBy.XPATH, yes_confirm_xpath)
                if text_elements:
                    break
                time_module.sleep(0.5)
            
            print(f"📋 找到 {len(text_elements)} 个'是的，我确认'文本元素")
            
            if not text_elements:
                print("❌ 未找到'是的，我确认'文本元素")
                return
            
            for i, text_element in enumerate(text_elements, 1):
                print(f"start click {i}nd '是的，我确认'")
                try:
                    # 如果是第三个元素，强制向上滑动一次
                    if i == 3:
                        print(f"📍 第3个元素，强制向上滑动一次")
                        self.swipe_up(distance=400)
                        time.sleep(0.8)  # 等待滚动完成
                        # 重新获取元素（滚动后位置可能改变）
                        text_element = self.driver.find_elements(AppiumBy.XPATH, yes_confirm_xpath)[i-1]
                    
                    # 获取文本元素的位置
                    text_location = text_element.location
                    text_size = text_element.size
                    text_x = text_location['x']
                    text_y = text_location['y']
                    
                    print(f"📍 文本位置: x={text_x}, y={text_y}, width={text_size['width']}, height={text_size['height']}")
                    
                    # 根据 XML 结构，文本在 x=320，父容器从 x=290 开始
                    # 选框应该在文本左侧，大约在 x=300 左右（文本左侧20像素）
                    checkbox_x = int(text_x - 20)  # 文本左侧20像素（选框位置）
                    checkbox_y = int(text_y + text_size['height'] / 2)  # 文本垂直中心
                    
                    print(f"📍 计算选框位置: ({checkbox_x}, {checkbox_y})")
                    
                    # 尝试多种点击方式
                    clicked = False
                    
                    # 方式1: 点击计算出的选框位置（文本左侧20像素）
                    try:
                        print(f"📍 尝试点击选框位置: ({checkbox_x}, {checkbox_y})")
                        self.driver.tap([(checkbox_x, checkbox_y)], duration=250)
                        print(f"✅ 已点击第{i}个'是的，我确认'（选框位置点击）")
                        clicked = True
                        time.sleep(1.2)  # 等待响应
                    except Exception as e1:
                        print(f"⚠️ 选框位置点击失败: {e1}")
                    
                    # 方式2: 如果失败，尝试点击文本左侧更靠左的位置
                    if not clicked:
                        try:
                            checkbox_x2 = int(text_x - 30)  # 文本左侧30像素
                            checkbox_y2 = checkbox_y
                            print(f"📍 尝试点击更左侧位置: ({checkbox_x2}, {checkbox_y2})")
                            self.driver.tap([(checkbox_x2, checkbox_y2)], duration=250)
                            print(f"✅ 已点击第{i}个'是的，我确认'（更左侧位置点击）")
                            clicked = True
                            time.sleep(1.2)
                        except Exception as e2:
                            print(f"⚠️ 更左侧位置点击失败: {e2}")
                    
                    # 方式3: 点击文本本身（有些情况下点击文本也能触发选框）
                    if not clicked:
                        try:
                            text_center_x = int(text_x + text_size['width'] / 2)
                            text_center_y = int(text_y + text_size['height'] / 2)
                            print(f"📍 尝试点击文本中心: ({text_center_x}, {text_center_y})")
                            self.driver.tap([(text_center_x, text_center_y)], duration=250)
                            print(f"✅ 已点击第{i}个'是的，我确认'（文本中心点击）")
                            clicked = True
                            time.sleep(1.2)
                        except Exception as e3:
                            print(f"⚠️ 文本中心点击失败: {e3}")
                    
                    # 方式4: 直接点击文本元素
                    if not clicked:
                        try:
                            print("📍 尝试直接点击文本元素")
                            text_element.click()
                            print(f"✅ 已点击第{i}个'是的，我确认'（直接点击）")
                            clicked = True
                            time.sleep(1.2)
                        except Exception as e4:
                            print(f"⚠️ 直接点击失败: {e4}")
                    
                    if not clicked:
                        print(f"❌ 所有点击方式都失败，第{i}个'是的，我确认'无法点击")
                except Exception as e:
                    print(f"❌ 点击第{i}个'是的，我确认'失败: {e}")
                    import traceback
                    traceback.print_exc()
        except Exception as e:
            print(f"❌ 查找'是的，我确认'文本失败: {e}")
            import traceback
            traceback.print_exc()
        
        print("end click")
    
    def wait_for_element_to_appear_by_xpath(self, xpath, timeout=10):
        """等待 XPath 元素出现（即使不可见也返回）"""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        print(f"⏳ 等待元素出现: {xpath}, 超时时间: {timeout}秒")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                element = self.driver.find_element(AppiumBy.XPATH, xpath)
                # 即使元素不可见（visible="false"），只要存在就可以尝试点击
                print(f"✅ 元素已找到: {xpath}, 可见性: {element.is_displayed()}")
                return True
            except Exception as e:
                pass
            time.sleep(0.5)
        
        print(f"⏰ 等待元素出现超时: {xpath}")
        return False


    def back_to_home(self):
        self.click_element('back_to_home')
        self.click_element('yes_confirm')