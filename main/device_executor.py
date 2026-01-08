#!/usr/bin/env python3
import yaml, time, inspect
import threading
from utils.driver import get_driver, restart_app
from utils.logger import Logger

def run_case_on_device(device_info, bundle_id, yaml_path, run_number=1, results_file=None, app_path=None, reinstall=False, device_name=None, case_filters=None):
    logger = Logger(prefix=device_info.get('name', 'DEV'))
    logger.log(f"设备子进程启动: {device_info} (第{run_number}次执行)")

    # 设置环境变量，传递运行次数信息给截图功能
    import os
    os.environ['CURRENT_RUN_NUMBER'] = str(run_number)
    
    # 设置环境变量，传递运行时传入的 device_name（如果提供了）
    if device_name:
        os.environ['RUNTIME_DEVICE_NAME'] = device_name
    else:
        # 如果没有传入，清除环境变量（如果之前设置过）
        os.environ.pop('RUNTIME_DEVICE_NAME', None)

    # 测试结果统计
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'device_name': device_info.get('name', 'DEV'),
        'run_number': run_number
    }

    # 如果传入的是 .py 文件，自动尝试 .yaml 文件
    import os
    if yaml_path.endswith('.py'):
        yaml_path_alt = yaml_path.replace('.py', '.yaml')
        if os.path.exists(yaml_path_alt):
            logger.log(f"⚠️ 检测到传入的是 .py 文件，自动使用对应的 .yaml 文件: {yaml_path_alt}")
            yaml_path = yaml_path_alt
        else:
            logger.log(f"⚠️ 传入的是 .py 文件，但对应的 .yaml 文件不存在: {yaml_path_alt}")
    
    # 检查文件是否存在
    if not os.path.exists(yaml_path):
        logger.log(f"❌ 测试用例文件不存在: {yaml_path}")
        return
    
    # 先读取 YAML 文件
    with open(yaml_path, 'r', encoding='utf-8') as f:
        cases = yaml.safe_load(f)
    # 按用例名过滤（如果提供了筛选条件）
    try:
        if case_filters:
            if isinstance(case_filters, str):
                filters = [x.strip() for x in case_filters.split(',') if x.strip()]
            elif isinstance(case_filters, list):
                filters = [str(x).strip() for x in case_filters if str(x).strip()]
            else:
                filters = []
            if filters:
                before = len(cases) if isinstance(cases, list) else 0
                cases = [c for c in cases if isinstance(c, dict) and c.get('name') in filters]
                logger.log(f"仅运行指定用例: {filters}（已从 {before} 条筛到 {len(cases)} 条）")
    except Exception as e:
        logger.log(f"按用例名过滤时出错，将忽略过滤并运行全部用例: {e}")
    # 说明：原先这里会“收集所有用例的 setup_method 并在启动 app 前一次性执行”，
    # 这会导致后续用例的配置覆盖前面用例，且显得“第二个用例没有执行 setup”。
    # 现调整为：按用例逐条执行各自的 setup_method（见下面的用例循环）。

    # 执行完前置方法后，再创建 driver（不启动 app，等用例开始时再启动）
    try:
        driver = get_driver(device_info, appium_server=device_info['appium_server'], app_path=app_path, bundle_id=bundle_id, reinstall=reinstall)
        # 设置环境变量，传递bundle_id给BasePage的方法使用
        if bundle_id:
            os.environ['CURRENT_BUNDLE_ID'] = bundle_id
    except Exception as e:
        logger.log(f"无法创建 driver: {e}")
        return
    
    # 启动实时截图上传线程（如果启用）【0108新增实时截图功能】
    screenshot_thread = None
    stop_screenshot_thread = threading.Event()
    
    if os.environ.get('REALTIME_SCREENSHOT_UPLOAD', 'false').lower() == 'true':
        try:
            import base64
            import requests
            
            upload_url = os.environ.get('REALTIME_SCREENSHOT_API_URL', 'http://localhost:8005/api/upload')
            upload_interval = float(os.environ.get('REALTIME_SCREENSHOT_INTERVAL', '2'))  # 默认2秒
            
            def screenshot_upload_worker():
                """后台线程：定期截图并上传【0108新增实时截图功能】"""
                while not stop_screenshot_thread.is_set():
                    try:
                        # 获取截图（base64编码）
                        screenshot_base64 = driver.get_screenshot_as_base64()
                        img_data = base64.b64decode(screenshot_base64)
                        
                        # 上传到服务器
                        response = requests.post(
                            upload_url,
                            data=img_data,
                            headers={'Content-Type': 'image/jpeg'},
                            timeout=5
                        )
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success'):
                                logger.log(f"📤 实时截图已上传")
                            else:
                                logger.log(f"⚠️ 上传截图失败: {result.get('error', '未知错误')}")
                        else:
                            logger.log(f"⚠️ 上传截图失败，HTTP状态码: {response.status_code}")
                    except Exception as e:
                        # 截图或上传失败不影响主流程
                        logger.log(f"⚠️ 实时截图上传出错（不影响测试）: {e}")
                    
                    # 等待指定间隔，或收到停止信号
                    if stop_screenshot_thread.wait(upload_interval):
                        break  # 收到停止信号
            
            screenshot_thread = threading.Thread(target=screenshot_upload_worker, daemon=True)
            screenshot_thread.start()
            logger.log(f"📸 实时截图上传线程已启动（间隔: {upload_interval}秒）")
        except ImportError:
            logger.log("⚠️ requests库未安装，无法启用实时截图上传。请运行: pip install requests")
        except Exception as e:
            logger.log(f"⚠️ 启动实时截图上传线程失败: {e}")

    for case_index, case in enumerate(cases):
        logger.log(f"开始用例 ({case_index + 1}/{len(cases)}): {case.get('name')}")
        test_results['total'] += 1
        case_failed = False  # 用例失败标志
        
        # 每条用例独立执行其前置方法（若有）
        setup_method = case.get('setup_method')
        if setup_method:
            try:
                from api_scripts.test_setup_methods import execute_setup_method
                logger.log(f"🔧 执行前置方法: {setup_method}")
                setup_success = execute_setup_method(setup_method)
                if not setup_success:
                    logger.log(f"⚠️ 前置方法 {setup_method} 执行失败，但继续执行用例")
            except Exception as e:
                logger.log(f"⚠️ 执行前置方法时出错: {e}")
        
        # 设置用例索引环境变量，供截图功能使用
        import os
        os.environ['CURRENT_CASE_INDEX'] = str(case_index + 1)
        
        # 每个用例开始时重启APP，确保环境干净
        try:
            logger.log(f"🔄 重启APP为用例做好准备...")
            restart_app(driver, bundle_id)
            logger.log(f"✅ APP已重启")
            time.sleep(2)  # 给APP一点启动时间
        except Exception as e:
            logger.log(f"⚠️ 重启APP失败: {e}")
        
        # 只有在第一个用例且重新安装 app 且 bundleId 包含 "MTKing" 时才执行初始化操作
        if case_index == 0 and reinstall and app_path:
            if bundle_id and 'MTKing' in bundle_id:
                try:
                    logger.log("🔧 检测到重新安装且 bundleId 包含 'MTKing'，开始执行 App 初始化操作...")
                    from pages.evev.base_page import initialize_app
                    initialize_app(driver)
                    logger.log("✅ App 初始化操作完成")
                except Exception as e:
                    logger.log(f"⚠️ App 初始化操作出错: {e}")
        
        for step in case.get('steps', []):
            if case_failed:  # 如果用例已失败，跳过后续步骤
                break
                
            page_name = step.get('page')
            actions = step.get('actions', [])
            
            # 根据页面名称前缀或 bundleId 判断项目类型
            # 优先级：页面名称前缀 > bundleId
            # M_ -> evem, V_ -> evev
            if page_name.startswith('M_'):
                project_dir = 'evem'
            elif page_name.startswith('V_'):
                project_dir = 'evev'
            elif bundle_id and 'eve' in bundle_id.lower():
                project_dir = 'evev'
            else:
                project_dir = 'other'
            
            # 尝试加载页面类，如果不存在则动态创建
            page_class = None
            try:
                import re
                
                # 对于 M_ / V_ 前缀的页面，尝试多种模块名格式（不做前缀映射）
                if page_name.startswith('M_') or page_name.startswith('V_'):
                    # 尝试顺序（优先大写前缀模块名）：
                    # 1) 大写前缀模块名（M_login_page / V_login_page）
                    # 2) 小写前缀模块名（m_login_page / v_login_page）
                    # 3) 无前缀模块名（login_page）
                    prefix = 'M_' if page_name.startswith('M_') else 'V_'
                    clean_page_name = page_name.replace(prefix, '')  # M_LoginPage -> LoginPage / V_LoginPage -> LoginPage
                    module_base = re.sub(r'(?<!^)(?=[A-Z])', '_', clean_page_name).lower()  # LoginPage -> login_page
                    module_name_upper_pref = f"{prefix}{module_base}"         # M_login_page / V_login_page
                    module_name_lower_pref = f"{prefix.lower()}{module_base}" # m_login_page / v_login_page
                    module_name_no_pref = module_base                          # login_page
                    
                    tried = []
                    for module_name in (module_name_upper_pref, module_name_lower_pref, module_name_no_pref):
                        try:
                            tried.append(module_name)
                            logger.log(f"🔍 尝试导入模块: pages.{project_dir}.{module_name}")
                            module = __import__(f"pages.{project_dir}.{module_name}", fromlist=[page_name])
                            logger.log(f"📦 模块导入成功: {module}")
                            page_class = getattr(module, page_name, None)
                            logger.log(f"🔍 查找类 {page_name}，结果: {page_class}")
                            if page_class:
                                logger.log(f"✅ 从 {project_dir} 项目加载页面类: {page_name} (模块: {module_name})")
                                break
                        except (ImportError, AttributeError) as e:
                            logger.log(f"⚠️ 导入模块失败: pages.{project_dir}.{module_name} - {e}")
                            continue
                else:
                    # 普通页面名称
                    module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', page_name).lower()  # LoginPage -> login_page
                    
                    # 尝试从项目目录加载
                    try:
                        module = __import__(f"pages.{project_dir}.{module_name}", fromlist=[page_name])
                        page_class = getattr(module, page_name, None)
                        if page_class:
                            logger.log(f"✅ 从 {project_dir} 项目加载页面类: {page_name}")
                    except (ImportError, AttributeError):
                        # 如果项目目录中找不到，尝试从根目录加载（向后兼容）
                        try:
                            module = __import__(f"pages.{module_name}", fromlist=[page_name])
                            page_class = getattr(module, page_name, None)
                            if page_class:
                                logger.log(f"✅ 从根目录加载页面类: {page_name}")
                        except (ImportError, AttributeError):
                            pass
            except Exception as e:
                logger.log(f"⚠️ 页面类 {page_name} 不存在，将动态创建: {e}")
            
            # 如果页面类不存在，动态创建
            if page_class is None:
                # 根据项目目录导入 BasePage
                if project_dir == 'evem':
                    from pages.evem.base_page import BasePage
                elif project_dir == 'evev':
                    from pages.evev.base_page import BasePage
                else:  # other
                    from pages.other.base_page import BasePage
                
                # 动态创建页面类
                def __init__(self, driver):
                    BasePage.__init__(self, driver)
                    self.page_name = page_name
                
                # 创建类字典
                class_dict = {
                    '__init__': __init__,
                    'page_name': page_name
                }
                
                # 动态创建类
                page_class = type(page_name, (BasePage,), class_dict)
                logger.log(f"✅ 已动态创建页面类: {page_name} (项目: {project_dir})")
            
            page = page_class(driver)
            
            for action in actions:
                if case_failed:  # 如果用例已失败，跳出action循环
                    break
                    
                # 检查是否为wait操作
                if action.get('method') == 'wait':
                    wait_time = action.get('params', 1)  # 默认等待1秒
                    logger.log(f"执行强制等待: {wait_time}秒")
                    time.sleep(wait_time)
                    continue
                
                method_name = action.get('method')
                params = action.get('params', None)
                logger.log(f"执行: {page_name}.{method_name}({params})")
                method = getattr(page, method_name, None)
                if not method:
                    logger.log(f"方法未找到: {page_name}.{method_name}")
                    continue
                
                # 通用处理：检查方法是否需要 device_name 参数，优先使用运行时传入的值
                try:
                    sig = inspect.signature(method)
                    param_names = list(sig.parameters.keys())
                    
                    # 检查方法是否有 device_name 参数
                    if 'device_name' in param_names:
                        runtime_device_name = os.environ.get('RUNTIME_DEVICE_NAME')
                        
                        # 优先使用运行时传入的值（覆盖 YAML 中的值）
                        if runtime_device_name:
                            params = runtime_device_name
                            if params != action.get('params', None):
                                logger.log(f"检测到方法 {method_name} 需要 device_name 参数，优先使用运行时传入的值: {runtime_device_name}（覆盖 YAML 中的值）")
                            else:
                                logger.log(f"检测到方法 {method_name} 需要 device_name 参数，使用运行时传入的值: {runtime_device_name}")
                        # 如果运行时没有传入，使用 YAML 中的 params
                        elif params is None:
                            # 检查方法是否有默认值
                            param = sig.parameters['device_name']
                            if param.default != inspect.Parameter.empty:
                                # 有默认值，不传参数，让方法使用默认值
                                logger.log(f"检测到方法 {method_name} 需要 device_name 参数，但运行时未传入，将使用方法的默认值")
                                # params 保持为 None，后续会调用 method() 使用默认值
                            else:
                                # 没有默认值且运行时也没有传入，使用全局默认值 '200018'
                                params = '200018'
                                logger.log(f"⚠️ 方法 {method_name} 需要 device_name 参数，但运行时未传入，使用默认值: 200018")
                        else:
                            # 运行时没有传入，但 YAML 中有传入，使用 YAML 中的值
                            logger.log(f"检测到方法 {method_name} 需要 device_name 参数，运行时未传入，使用 YAML 中的值: {params}")
                except Exception as e:
                    # 如果检查方法签名失败，不影响正常执行
                    logger.log(f"⚠️ 检查方法签名时出错: {e}")
                
                try:
                    # 执行方法
                    if params is not None:
                        # 处理不同参数格式
                        if isinstance(params, str) and '.' in params and method_name.startswith('assert_'):
                            # 元素名称格式，如 'HomePage.searchuser'
                            result = method(params)
                        elif isinstance(params, list) and len(params) >= 2 and method_name.startswith('assert_'):
                            # 传统格式，如 ['xpath', '//XCUIElementTypeTextField'] 或 ['HomePage.searchuser', 'expected_text']
                            if len(params) == 2 and not params[0] in ['xpath', 'id', 'name', 'class', 'tag', 'accessibility_id']:
                                # 元素名称 + 文本参数格式
                                result = method(params[0], params[1])
                            else:
                                # 传统定位器格式
                                result = method(*params)
                        else:
                            # 普通参数
                            if isinstance(params, list):
                                result = method(*params)
                            else:
                                result = method(params)
                    else:
                        result = method()
                    
                    # 检查方法返回值，如果返回 False 也标记为失败
                    if result is False:
                        # 用例失败时先截图
                        try:
                            shot_name = f"FAIL_{page_name}.{method_name}".replace(' ', '_')
                            if hasattr(page, 'screenshot'):
                                file_path = page.screenshot(shot_name, timestamp=True)
                                if file_path:
                                    logger.log(f"📸 失败截图已保存: {file_path}")
                        except Exception as shot_err:
                            logger.log(f"⚠️ 失败截图出错: {shot_err}")
                        logger.log(f"❌ 方法返回 False，标记用例失败: {page_name}.{method_name}")
                        case_failed = True
                        break  # 跳出action循环
                    
                    # 如果是断言方法，记录断言结果
                    if method_name.startswith('assert_'):
                        logger.log(f"断言通过: {method_name}")
                        
                except AssertionError as e:
                    # 断言失败时先截图
                    try:
                        shot_name = f"ASSERT_FAIL_{page_name}.{method_name}".replace(' ', '_')
                        if hasattr(page, 'screenshot'):
                            file_path = page.screenshot(shot_name, timestamp=True)
                            if file_path:
                                logger.log(f"📸 失败截图已保存: {file_path}")
                    except Exception as shot_err:
                        logger.log(f"⚠️ 失败截图出错: {shot_err}")
                    logger.log(f"断言失败: {method_name} - {str(e)}")
                    case_failed = True  # 标记用例失败
                    break  # 跳出action循环
                except Exception as e:
                    error_msg = str(e)
                    error_type = type(e).__name__
                    logger.log(f"执行出错: {page_name}.{method_name} - {error_type}: {error_msg}")
                    # 其他执行异常时先截图
                    try:
                        shot_name = f"ERROR_{error_type}_{page_name}.{method_name}".replace(' ', '_')
                        if hasattr(page, 'screenshot'):
                            file_path = page.screenshot(shot_name, timestamp=True)
                            if file_path:
                                logger.log(f"📸 失败截图已保存: {file_path}")
                    except Exception as shot_err:
                        logger.log(f"⚠️ 失败截图出错: {shot_err}")
                    
                    # 检查是否是元素找不到或超时的错误（所有元素查找相关的异常）
                    element_not_found_keywords = [
                        "NoSuchElement",
                        "TimeoutException",
                        "Timeout",
                        "element could not be located",
                        "Unable to locate element",
                        "Message: An element could not be located",
                        "selenium.common.exceptions.NoSuchElementException",
                        "selenium.common.exceptions.TimeoutException",
                        "appium.common.exceptions.NoSuchContextException"
                    ]
                    
                    is_element_error = any(keyword in error_msg or keyword in error_type for keyword in element_not_found_keywords)
                    
                    if is_element_error:
                        logger.log(f"❌ 元素找不到或超时，立即停止执行当前用例: {case.get('name')}")
                        logger.log(f"   错误类型: {error_type}")
                        logger.log(f"   错误信息: {error_msg}")
                        case_failed = True  # 标记用例失败
                        break  # 跳出action循环
                    else:
                        # 其他类型的错误也停止执行
                        logger.log(f"❌ 执行出错，停止执行当前用例: {case.get('name')}")
                        logger.log(f"   错误类型: {error_type}")
                        logger.log(f"   错误信息: {error_msg}")
                        case_failed = True  # 标记用例失败
                        break  # 跳出action循环
        
        if case_failed:
            logger.log(f"❌ 用例失败: {case.get('name')}")
            test_results['failed'] += 1
        else:
            logger.log(f"✅ 用例通过: {case.get('name')}")
            test_results['passed'] += 1
        
        # 执行清理方法（如果指定）
        teardown_method = case.get('teardown_method')
        if teardown_method:
            try:
                from api_scripts.test_setup_methods import execute_teardown_method
                logger.log(f"🧹 执行用例清理方法: {teardown_method}")
                teardown_success = execute_teardown_method(teardown_method)
                if not teardown_success:
                    logger.log(f"⚠️ 清理方法执行失败，但继续执行")
                    # 清理方法失败不阻止后续操作，只记录警告
            except Exception as e:
                logger.log(f"⚠️ 执行清理方法时出错: {e}")
                # 清理方法出错不阻止后续操作，只记录警告
        
        # 用例执行完后关闭 app
        try:
            logger.log(f"🔒 关闭 app...")
            driver.terminate_app(bundle_id)
            logger.log(f"✅ App 已关闭")
        except Exception as e:
            logger.log(f"⚠️ 关闭 app 失败: {e}")
        
        # 用例之间等待，确保串行执行
        if case_index < len(cases) - 1:  # 不是最后一个用例
            logger.log(f"⏳ 等待3秒后执行下一个用例...")
            time.sleep(3)

    # 停止实时截图上传线程【0108新增实时截图功能】
    if screenshot_thread and screenshot_thread.is_alive():
        stop_screenshot_thread.set()
        screenshot_thread.join(timeout=2)  # 等待最多2秒
        logger.log('📸 实时截图上传线程已停止')
    
    try:
        driver.quit()
    except Exception:
        pass

    logger.log('设备执行结束。')
    
    # 只在日志中记录结果，不打印到控制台
    logger.log(f"📊 设备 {test_results['device_name']} 第{run_number}次执行结果: 总用例数={test_results['total']}, 通过={test_results['passed']}, 失败={test_results['failed']}")
    
    # 将结果写入文件
    if results_file:
        import json
        try:
            with open(results_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(test_results, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.log(f"写入结果文件失败: {e}")
    
    # 返回测试结果
    return test_results
