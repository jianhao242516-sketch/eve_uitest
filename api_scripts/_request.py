# _*_ coding: utf-8 _*_
"""
______________________________________________
project Name : app-ui
File Name : _request
Description :
Author : wendy
date : 2025/12/1
______________________________________________

"""
import requests
from urllib.parse import urlparse
from api_scripts._config import config


def send_request(req_data):
    # 1. 创建 session，保持 cookies
    session = requests.Session()

    url = f"{config['base_url']}/content/merchant/module_edit"

    # 2. 设置 headers（模拟浏览器）
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Cookie": config['cookie'],
        "Host":  (urlparse(config['base_url'])).hostname,
        "Origin": config['base_url'],
        "Pragma": "no-cache",
    }

    resp = session.post(url=url, headers=headers, data=req_data)
    # print("\n===== 请求参数 =====")
    # print(req_data)
    # print("===== 返回结果 =====")
    # print(resp.text, "\n")

    return resp
