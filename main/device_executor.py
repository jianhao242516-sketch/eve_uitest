#!/usr/bin/env python3
import yaml, time
from utils.driver import get_driver, restart_app
from utils.logger import Logger

def run_case_on_device(device_info, bundle_id, yaml_path, run_number=1, results_file=None):
    logger = Logger(prefix=device_info.get('name', 'DEV'))
    logger.log(f"设备子进程启动: {device_info} (第{run_number}次执行)")

    # 设置环境变量，传递运行次数信息给截图功能
    import os
    os.environ['CURRENT_RUN_NUMBER'] = str(run_number)

    # 测试结果统计
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'device_name': device_info.get('name', 'DEV'),
        'run_number': run_number
    }

    try:
        driver = get_driver(device_info, appium_server=device_info['appium_server'])
    except Exception as e:
        logger.log(f"无法创建 driver: {e}")
        return

    try:
        restart_app(driver, bundle_id)
    except Exception as e:
        logger.log(f"重启 App 出错: {e}")

    with open(yaml_path, 'r', encoding='utf-8') as f:
        cases = yaml.safe_load(f)

    for case_index, case in enumerate(cases):
        logger.log(f"开始用例 ({case_index + 1}/{len(cases)}): {case.get('name')}")
        test_results['total'] += 1
        case_failed = False  # 用例失败标志
        
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
        
        for step in case.get('steps', []):
            if case_failed:  # 如果用例已失败，跳过后续步骤
                break
                
            page_name = step.get('page')
            actions = step.get('actions', [])
            
            # 尝试加载页面类，如果不存在则动态创建
            page_class = None
            try:
                import re
                module_name = re.sub(r'(?<!^)(?=[A-Z])', '_', page_name).lower()  # LoginPage -> login_page
                module = __import__(f"pages.{module_name}", fromlist=[page_name])
                page_class = getattr(module, page_name, None)
            except (ImportError, AttributeError) as e:
                logger.log(f"⚠️ 页面类 {page_name} 不存在，将动态创建")
            
            # 如果页面类不存在，动态创建
            if page_class is None:
                from pages.base_page import BasePage
                
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
                logger.log(f"✅ 已动态创建页面类: {page_name}")
            
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
                    
                    # 如果是断言方法，记录断言结果
                    if method_name.startswith('assert_'):
                        logger.log(f"断言通过: {method_name}")
                        
                except AssertionError as e:
                    logger.log(f"断言失败: {method_name} - {str(e)}")
                    case_failed = True  # 标记用例失败
                    break  # 跳出action循环
                except Exception as e:
                    error_msg = str(e)
                    logger.log(f"执行出错: {page_name}.{method_name} - {error_msg}")
                    
                    # 检查是否是元素找不到的错误
                    if "NoSuchElementError" in error_msg or "element could not be located" in error_msg:
                        logger.log(f"元素找不到，停止执行当前用例: {case.get('name')}")
                        case_failed = True  # 标记用例失败
                        break  # 跳出action循环
                    
                    # 其他类型的错误也可以选择停止
                    # case_failed = True  # 取消注释这行会让所有错误都停止执行
                    # break
        
        if case_failed:
            logger.log(f"❌ 用例失败: {case.get('name')}")
            test_results['failed'] += 1
        else:
            logger.log(f"✅ 用例通过: {case.get('name')}")
            test_results['passed'] += 1
        
        # 用例之间等待，确保串行执行
        if case_index < len(cases) - 1:  # 不是最后一个用例
            logger.log(f"⏳ 等待3秒后执行下一个用例...")
            time.sleep(3)

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
