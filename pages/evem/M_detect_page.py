from pages.evev.base_page import BasePage
import time
class M_DetectPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.page_name = 'M_DetectPage'
    
    def detect_success(self):
        """检测成功"""
        #判断是否有弹窗，自动点击确定，如果没有再点still_button
        #轮训2分钟，查找是否有确定按钮，有的话点击，直到没有后，点击still_button
        start_time = time.time()
        clicked_confirm_once = False
        while time.time() - start_time < 20:
            print("轮训20秒，查找是否有确定按钮，有的话点击，直到没有后，点击still_button")
            # 先处理可能出现的弹窗按钮：确定 / 我知道了
            #增加继续按钮
            handled = False
            for btn in ['confirm_button', 'i_know_button', 'continue_button','delete_button']:
                if self.is_element_present_by_name(btn):
                    self.click_element(btn)
                    clicked_confirm_once = True
                    handled = True
                    time.sleep(0.5)  # 给下一次检测留一点缓冲
                    break
            if handled:
                continue
            # 未检测到弹窗按钮
            if clicked_confirm_once:
                # 曾经点通过确认，现在没有了，跳出去点 still_button
                break
            # 从未出现过确认按钮，继续轮询直至超时
            time.sleep(0.5)
        self.click_element('still_button')
