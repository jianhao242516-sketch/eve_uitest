#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时截图上传示例【0108新增实时截图功能】

演示如何从UI自动化工具获取截图并上传到API服务器。
"""

import requests
import base64
from appium import webdriver


def upload_screenshot_from_file(image_path, api_url='http://localhost:8005/api/upload'):
    """
    从文件上传截图
    
    参数:
        image_path: 图片文件路径
        api_url: API服务器地址，默认 http://localhost:8005/api/upload
    """
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        response = requests.post(
            api_url,
            data=image_data,
            headers={'Content-Type': 'image/jpeg'}
        )
        
        result = response.json()
        print(f"上传结果: {result}")
        return result
    except Exception as e:
        print(f"上传失败: {e}")
        return None


def upload_screenshot_from_appium(driver, api_url='http://localhost:8005/api/upload'):
    """
    从Appium driver获取截图并上传
    
    参数:
        driver: Appium WebDriver 实例
        api_url: API服务器地址，默认 http://localhost:8005/api/upload
    """
    try:
        # 获取截图（base64编码）
        screenshot_base64 = driver.get_screenshot_as_base64()
        
        # 解码为二进制数据
        img_data = base64.b64decode(screenshot_base64)
        
        # 上传到服务器
        response = requests.post(
            api_url,
            data=img_data,
            headers={'Content-Type': 'image/jpeg'}
        )
        
        result = response.json()
        print(f"上传结果: {result}")
        return result
    except Exception as e:
        print(f"上传失败: {e}")
        return None


def upload_screenshot_from_bytes(image_bytes, api_url='http://localhost:8005/api/upload'):
    """
    从字节数据上传截图
    
    参数:
        image_bytes: 图片的二进制数据
        api_url: API服务器地址，默认 http://localhost:8005/api/upload
    """
    try:
        response = requests.post(
            api_url,
            data=image_bytes,
            headers={'Content-Type': 'image/jpeg'}
        )
        
        result = response.json()
        print(f"上传结果: {result}")
        return result
    except Exception as e:
        print(f"上传失败: {e}")
        return None


def get_latest_screenshot_info(api_base_url='http://localhost:8005'):
    """
    获取最新截图信息
    
    参数:
        api_base_url: API服务器基础地址，默认 http://localhost:8005
    """
    try:
        response = requests.get(f'{api_base_url}/api/screenshot/info')
        result = response.json()
        print(f"最新截图信息: {result}")
        return result
    except Exception as e:
        print(f"获取信息失败: {e}")
        return None


def download_latest_screenshot(save_path, api_base_url='http://localhost:8005'):
    """
    下载最新截图
    
    参数:
        save_path: 保存路径
        api_base_url: API服务器基础地址，默认 http://localhost:8005
    """
    try:
        response = requests.get(f'{api_base_url}/api/screenshot/latest')
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"截图已保存到: {save_path}")
            return True
        else:
            print(f"获取截图失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"下载失败: {e}")
        return False


# 使用示例
if __name__ == '__main__':
    # 示例1: 从文件上传
    print("=" * 60)
    print("示例1: 从文件上传截图")
    print("=" * 60)
    print("# upload_screenshot_from_file('screenshot.jpg', 'http://localhost:8005/api/upload')")
    
    # 示例2: 从Appium driver上传（需要先初始化driver）
    print("\n" + "=" * 60)
    print("示例2: 从Appium driver上传截图")
    print("=" * 60)
    print("""
    # 初始化Appium driver
    from appium import webdriver
    from appium.options.ios import XCUITestOptions
    
    options = XCUITestOptions()
    options.platform_name = 'iOS'
    options.device_name = 'iPhone'
    # ... 其他配置
    
    driver = webdriver.Remote('http://localhost:4723', options=options)
    
    # 截图并上传
    upload_screenshot_from_appium(driver, 'http://localhost:8005/api/upload')
    """)
    
    # 示例3: 获取最新截图信息
    print("\n" + "=" * 60)
    print("示例3: 获取最新截图信息")
    print("=" * 60)
    print("# get_latest_screenshot_info('http://localhost:8005')")
    
    # 示例4: 下载最新截图
    print("\n" + "=" * 60)
    print("示例4: 下载最新截图")
    print("=" * 60)
    print("# download_latest_screenshot('latest_screenshot.jpg', 'http://localhost:8005')")
    
    print("\n注意: 默认API服务器地址为 http://localhost:8005")
    print("如果API服务器运行在其他地址或端口，请相应修改URL")

