
#by ruby 2025-03-24
# 发送企业微信消息

import requests
from datetime import datetime
import logging

logger = logging.getLogger()

#飞书 by ruby 2025-04-08

class NotificationSender:
 

    def send_text_to_feishu(self, title, content, webhook_url):
        """
        发送纯文本消息到飞书群机器人

        :param title: 消息标题（会作为消息开头）
        :param content: Markdown 格式的正文
        :param webhook_url: 飞书群机器人 Webhook 地址
        """
        headers = {"Content-Type": "application/json"}
        payload = {
            "msg_type": "text",
            "content": {
                "text": f"{title}\n{content}"
            }
        }

        try:
            response = requests.post(webhook_url, json=payload, headers=headers)
            response.raise_for_status()
            logging.info(f"[√] 飞书消息已发送成功：{title}")
        except Exception as e:
            logging.error(f"[×] 飞书消息发送失败: {e}")



