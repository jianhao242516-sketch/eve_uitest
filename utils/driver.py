from appium import webdriver
from appium.options.ios import XCUITestOptions
from appium.options.android import UiAutomator2Options
import time
import os
import glob

def get_driver(device, appium_server=None, app_path=None, bundle_id=None, reinstall=False):
    """
    创建 Appium driver
    
    Args:
        device: 设备配置字典
        appium_server: Appium 服务器地址
        app_path: 可选，app 安装包路径或目录路径（iOS: .ipa, Android: .apk）
                 如果是目录，会自动查找最新的 app 文件并安装
                 如果提供，会在创建 driver 后自动安装
        bundle_id: 可选，app 的 bundleId 或 appPackage，用于卸载
        reinstall: 是否重新安装（先卸载再安装），默认 False
    """
    if not appium_server:
        raise ValueError('appium_server 必须传入，例如 http://127.0.0.1:4723')
    
    platform = device.get("platformName", "iOS")
    
    if platform == "iOS":
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.device_name = device.get("name")
        options.automation_name = "XCUITest"
        options.udid = device.get("udid")
        
        #xcode自动打包，后面再研究
        # options.xcode_org_id = device.get("xcodeOrgId", "93QB6A5FF9")
        # options.xcode_signing_id = device.get("xcodeSigningId", "iPhone Developer")
        options.no_reset = True
    else:  # Android
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = device.get("name")
        options.automation_name = "UiAutomator2"
        options.udid = device.get("udid")
        options.no_reset = True
    
    driver = webdriver.Remote(appium_server, options=options)
    
    # 如果提供了 app_path，安装或重新安装
    if app_path:
        if reinstall:
            reinstall_app(driver, app_path, bundle_id, platform)
        else:
            install_app(driver, app_path, platform)
    
    return driver

def find_latest_app(app_path, platform=None):
    """
    查找 app 文件，如果路径是目录则查找最新的 .ipa 或 .apk 文件
    
    Args:
        app_path: app 文件路径或目录路径
        platform: 平台名称（"iOS" 或 "Android"），用于确定查找的文件类型
    
    Returns:
        找到的 app 文件路径
    """
    if not app_path:
        return None
    
    if not os.path.exists(app_path):
        raise FileNotFoundError(f'路径不存在: {app_path}')
    
    # 如果是文件，直接返回
    if os.path.isfile(app_path):
        return app_path
    
    # 如果是目录，查找最新的 app 文件
    if os.path.isdir(app_path):
        app_files = []
        
        # 根据平台确定查找的文件扩展名
        if platform == "iOS":
            extensions = ['*.ipa']
        elif platform == "Android":
            extensions = ['*.apk']
        else:
            # 如果平台未知，查找所有支持的格式
            extensions = ['*.ipa', '*.apk']
        
        # 查找所有匹配的文件
        for ext in extensions:
            pattern = os.path.join(app_path, ext)
            app_files.extend(glob.glob(pattern, recursive=False))
        
        if not app_files:
            raise FileNotFoundError(f'在目录 {app_path} 中未找到 app 文件（.ipa 或 .apk）')
        
        # 按修改时间排序，返回最新的文件
        latest_file = max(app_files, key=os.path.getmtime)
        print(f'📂 在目录中找到 {len(app_files)} 个 app 文件，选择最新的: {os.path.basename(latest_file)}')
        return latest_file
    
    raise ValueError(f'路径既不是文件也不是目录: {app_path}')

def uninstall_app(driver, bundle_id, platform=None):
    """
    从设备卸载 app
    
    Args:
        driver: Appium driver 实例
        bundle_id: app 的 bundleId (iOS) 或 appPackage (Android)
        platform: 平台名称（"iOS" 或 "Android"），如果不提供会自动检测
    """
    if not bundle_id:
        print('⚠️ 未提供 bundleId，无法卸载')
        return
    
    try:
        print(f'🗑️  正在卸载 app: {bundle_id}')
        driver.remove_app(bundle_id)
        print(f'✅ App 卸载成功')
        time.sleep(1)  # 等待卸载完成
    except Exception as e:
        print(f'⚠️ App 卸载失败（可能未安装）: {e}')

def _install_app_file(driver, actual_app_path, platform):
    """
    内部函数：安装指定的 app 文件
    
    Args:
        driver: Appium driver 实例
        actual_app_path: app 文件的完整路径
        platform: 平台名称（"iOS" 或 "Android"）
    """
    try:
        print(f'📱 正在安装 {platform} app: {actual_app_path}')
        driver.install_app(actual_app_path)
        print(f'✅ App 安装成功')
        time.sleep(2)  # 等待安装完成
    except Exception as e:
        print(f'⚠️ App 安装失败: {e}')
        # 如果安装失败，可能是已经安装了，继续执行
        pass

def install_app(driver, app_path, platform=None):
    """
    安装 app 到设备
    
    Args:
        driver: Appium driver 实例
        app_path: app 安装包路径或目录路径（iOS: .ipa, Android: .apk）
                 如果是目录，会自动查找最新的 app 文件
        platform: 平台名称（"iOS" 或 "Android"），如果不提供会自动检测
    """
    if not app_path:
        return
    
    # 查找 app 文件（如果是目录则查找最新的）
    actual_app_path = find_latest_app(app_path, platform)
    
    # 自动检测平台（如果未提供）
    if not platform:
        if actual_app_path.lower().endswith('.ipa'):
            platform = 'iOS'
        elif actual_app_path.lower().endswith('.apk'):
            platform = 'Android'
        else:
            raise ValueError(f'无法识别 app 文件类型: {actual_app_path}，请确保是 .ipa (iOS) 或 .apk (Android)')
    
    _install_app_file(driver, actual_app_path, platform)

def reinstall_app(driver, app_path, bundle_id=None, platform=None):
    """
    重新安装 app（先卸载再安装）
    
    Args:
        driver: Appium driver 实例
        app_path: app 安装包路径或目录路径（iOS: .ipa, Android: .apk）
                 如果是目录，会自动查找最新的 app 文件
        bundle_id: app 的 bundleId (iOS) 或 appPackage (Android)，用于卸载
        platform: 平台名称（"iOS" 或 "Android"），如果不提供会自动检测
    """
    if not app_path:
        return
    
    # 查找 app 文件（如果是目录则查找最新的）
    actual_app_path = find_latest_app(app_path, platform)
    
    # 自动检测平台（如果未提供）
    if not platform:
        if actual_app_path.lower().endswith('.ipa'):
            platform = 'iOS'
        elif actual_app_path.lower().endswith('.apk'):
            platform = 'Android'
        else:
            raise ValueError(f'无法识别 app 文件类型: {actual_app_path}，请确保是 .ipa (iOS) 或 .apk (Android)')
    
    # 如果提供了 bundle_id，先卸载
    if bundle_id:
        uninstall_app(driver, bundle_id, platform)
    
    # 然后安装（直接使用已找到的文件路径）
    _install_app_file(driver, actual_app_path, platform)

def restart_app(driver, bundle_id):
    try:
        driver.terminate_app(bundle_id)
    except Exception:
        pass
    time.sleep(1)
    driver.execute_script("mobile: launchApp", {"bundleId": bundle_id})
    time.sleep(2)
