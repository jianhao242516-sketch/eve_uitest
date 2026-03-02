#!/usr/bin/env python3
# author: ruby
# -*- coding: utf-8 -*-
"""
运行测试脚本
1. 调用 download_New_ipa.py 获取下载地址和 bundle_id
2. 获取当前连接的 iPad 名称或 UDID
3. 发送测试请求
"""

import subprocess
import json
import sys
import os
import requests
import shutil

# 添加项目根目录到 Python 路径，以便导入 utils 模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入下载函数
# 尝试导入下载模块和检查依赖
# 使用与 download_New_ipa.py 相同的方式检查 protobuf
try:
    from google.protobuf.json_format import MessageToDict
    # 添加 proto 文件所在目录到路径（与 download_New_ipa.py 在同一目录）
    proto_dir = os.path.join(project_root, 'utils', 'ci_download')
    if proto_dir not in sys.path:
        sys.path.insert(0, proto_dir)
    import omnibus_connect_builds_pb2  # type: ignore
    PROTOBUF_AVAILABLE = True
except ImportError as e:
    PROTOBUF_AVAILABLE = False
    print(f"⚠️ 警告: protobuf 库或生成的模块未找到: {e}")

# 尝试导入下载函数
try:
    from utils.ci_download.download_New_ipa import download_test_enterprise_package
    DOWNLOAD_AVAILABLE = True
except ImportError as e:
    DOWNLOAD_AVAILABLE = False
    print(f"⚠️ 警告: 自动下载功能不可用，导入失败: {e}")

# 尝试导入通知功能
try:
    from utils.message import NotificationSender
    NOTIFICATION_AVAILABLE = True
except ImportError as e:
    NOTIFICATION_AVAILABLE = False
    print(f"⚠️ 警告: 通知功能不可用，导入失败: {e}")

def get_connected_devices():
    """获取当前连接的 iOS 设备（返回第一个设备）"""
    try:
        # 使用 idevice_id 获取设备 UDID 列表
        result = subprocess.run(['idevice_id', '-l'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            udids = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            if udids:
                # 返回第一个设备
                return udids[0]
    except FileNotFoundError:
        print("警告: idevice_id 命令未找到")
    except subprocess.TimeoutExpired:
        print("警告: 获取设备列表超时")
    except Exception as e:
        print(f"获取设备列表失败: {e}")
    
    return None

def get_device_name(udid):
    """根据 UDID 获取设备名称"""
    try:
        # 使用 ideviceinfo 获取设备名称
        result = subprocess.run(['ideviceinfo', '-u', udid, '-k', 'DeviceName'], 
                              capture_output=True, 
                              text=True, 
                              timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        print(f"获取设备名称失败: {e}")
    
    # 如果无法获取名称，返回 UDID
    return udid

def send_feishu_notification(status, task_id, test_file, device_name, bundle_id, 
                             passed=0, failed=0, total=0, success_rate=0, error_msg=None, 
                             webhook_url=None, build_number=None):
    """
    发送飞书通知
    
    参数:
        status: 任务状态 ('completed', 'failed', 'cancelled', 'timeout')
        task_id: 任务ID
        test_file: 测试文件路径
        device_name: 设备名称
        bundle_id: Bundle ID
        passed: 通过的测试数（仅 completed 状态）
        failed: 失败的测试数（仅 completed 状态）
        total: 总测试数（仅 completed 状态）
        success_rate: 成功率（仅 completed 状态）
        error_msg: 错误信息（仅 failed 状态）
        webhook_url: 飞书 webhook URL，如果为 None 则从环境变量获取
        build_number: 构建号（可选）
    """
    if not NOTIFICATION_AVAILABLE:
        return
    webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/e2d29e9b-0923-4d99-a90e-322572ca83dc"
    # webhook_url = "https://open.feishu.cn/open-apis/bot/v2/hook/1256e800-a592-4c2e-841d-fd3db6128b56"
    # 从环境变量获取 webhook_url（如果未提供）
    if webhook_url is None:
        webhook_url = os.getenv('FEISHU_WEBHOOK_URL')
    
    if not webhook_url:
        print("⚠️ 未配置飞书 webhook URL，跳过通知发送")
        print("   提示: 设置环境变量 FEISHU_WEBHOOK_URL 或在配置中指定 webhook_url")
        return
    
    try:
        sender = NotificationSender()
        
        # 0113新增：根据状态构建消息，失败时显示详细错误信息到飞书
        # 0114新增：添加build信息
        build_info = f"\nBuild: {build_number}" if build_number else ""
        
        if status == 'completed':
            # 判断是否全部通过
            if failed == 0:
                title = "✅ UI测试任务执行成功"
                content = f"""任务ID: {task_id}
测试文件: {test_file}
设备: {device_name}
Bundle ID: {bundle_id}{build_info}
执行结果: 
通过: {passed}
总计: {total}"""
            else:
                title = "⚠️ UI测试任务执行完成（有失败）"
                # 0113新增：格式化错误信息，显示失败用例和断言错误详情
                error_details = ""
                if error_msg:
                    # error_msg 可能是字符串或列表
                    if isinstance(error_msg, list):
                        for case_error in error_msg:
                            case_name = case_error.get('case_name', '未知用例')
                            errors = case_error.get('errors', [])
                            error_details += f"\n用例: {case_name}\n"
                            for err in errors:
                                error_details += f"  - {err}\n"
                    else:
                        error_details = f"\n错误信息: {error_msg}"
                
                content = f"""任务ID: {task_id}
测试文件: {test_file}
设备: {device_name}
Bundle ID: {bundle_id}{build_info}
执行结果: 
通过: {passed}
失败: {failed}
总计: {total}{error_details}"""
        elif status == 'failed':
            title = "❌ 测试任务执行失败"
            # 0113新增：格式化错误信息，显示失败用例和断言错误详情
            error_details = ""
            if error_msg:
                if isinstance(error_msg, list):
                    for case_error in error_msg:
                        case_name = case_error.get('case_name', '未知用例')
                        errors = case_error.get('errors', [])
                        error_details += f"\n用例: {case_name}\n"
                        for err in errors:
                            error_details += f"  - {err}\n"
                else:
                    error_details = f"\n错误信息: {error_msg}"
            
            content = f"""任务ID: {task_id}
测试文件: {test_file}
设备: {device_name}
Bundle ID: {bundle_id}{build_info}{error_details if error_details else "错误信息: 未知错误"}"""
        elif status == 'cancelled':
            title = "⚠️ 测试任务已取消"
            content = f"""任务ID: {task_id}
测试文件: {test_file}
设备: {device_name}
Bundle ID: {bundle_id}{build_info}"""
        elif status == 'timeout':
            title = "⏱️ 测试任务查询超时"
            content = f"""任务ID: {task_id}
测试文件: {test_file}
设备: {device_name}
Bundle ID: {bundle_id}{build_info}
注意: 任务状态查询超时，请手动检查任务状态"""
        else:
            title = f"ℹ️ 测试任务状态更新: {status}"
            content = f"""任务ID: {task_id}
测试文件: {test_file}
设备: {device_name}
Bundle ID: {bundle_id}{build_info}"""
        
        sender.send_text_to_feishu(title, content, webhook_url)
        print(f"✓ 飞书通知已发送: {title}")
    except Exception as e:
        print(f"⚠️ 发送飞书通知失败: {e}")

def cleanup_downloaded_files(download_dir, files):
    """
    清理下载的文件和目录
    
    参数:
        download_dir: 下载目录路径
        files: 下载的文件列表
    """
    if not download_dir:
        return False
    
    try:
        print(f"\n🗑️  正在清理下载的文件")
        print("-" * 60)
        
        # 将相对路径转换为绝对路径
        if not os.path.isabs(download_dir):
            download_dir_abs = os.path.join(project_root, download_dir)
            download_dir_abs = os.path.normpath(download_dir_abs)
        else:
            download_dir_abs = download_dir
        
        # 删除下载的文件
        deleted_files = 0
        for file_path in files:
            if file_path and os.path.exists(file_path):
                try:
                    print(f"  删除文件: {file_path}")
                    os.remove(file_path)
                    deleted_files += 1
                except Exception as e:
                    print(f"  ⚠️ 删除文件失败 {file_path}: {e}")
        
        if deleted_files > 0:
            print(f"✅ 已删除 {deleted_files} 个下载文件")
        
        # 删除下载目录（如果目录为空或只包含构建信息文件）
        if os.path.exists(download_dir_abs):
            try:
                dir_contents = os.listdir(download_dir_abs)
                # 如果目录为空或只包含 build_info.yaml，删除整个目录
                if not dir_contents or (len(dir_contents) == 1 and dir_contents[0] == 'build_info.yaml'):
                    print(f"  删除下载目录: {download_dir_abs}")
                    shutil.rmtree(download_dir_abs)
                    print(f"✅ 已删除下载目录")
                else:
                    # 如果还有其他文件，只删除 build_info.yaml（如果存在）
                    build_info_path = os.path.join(download_dir_abs, 'build_info.yaml')
                    if os.path.exists(build_info_path):
                        print(f"  删除构建信息文件: {build_info_path}")
                        os.remove(build_info_path)
                        print(f"✅ 已删除构建信息文件")
            except Exception as e:
                print(f"⚠️ 删除下载目录失败: {e}")
        else:
            print(f"⚠️ 下载目录不存在，跳过删除: {download_dir_abs}")
        
        return True
    except Exception as e:
        print(f"⚠️ 清理下载文件时出错: {e}")
        return False

def run_test(app_uid_or_shortcut, device=None, test_file="tests/test_api_V.yaml", 
             appium_host="172.21.126.183", device_name=None, reinstall=True, dry_run=False,
             feishu_webhook_url=None):
    """
    运行测试
    
    参数:
        app_uid_or_shortcut: APP_UID 或简写 ('m' 或 'v')
        device: 设备标识（UDID 或设备名），如果为 None 则自动获取
        test_file: 测试文件路径
        appium_host: Appium 服务器地址
        device_name: 固件设备名称（可选）
        reinstall: 是否重新安装应用
        feishu_webhook_url: 飞书 webhook URL（可选，也可通过环境变量 FEISHU_WEBHOOK_URL 设置）
    """
    print("=" * 60)
    print("开始运行测试")
    print("=" * 60)
    
    # 1. 下载 IPA 文件
    print("\n步骤 1: 下载测试环境企业包")
    print("-" * 60)
    
    # 检查下载功能是否可用
    if not DOWNLOAD_AVAILABLE:
        print("错误: 自动下载功能不可用")
        print("请确保:")
        print("  1. utils 模块可以正常导入")
        print("  2. 已安装必要的依赖: pip install protobuf")
        print("  3. proto 文件已正确编译")
        return False
    
    download_result = download_test_enterprise_package(app_uid_or_shortcut)
    
    if not download_result['success']:
        print("下载失败，无法继续")
        return False
    
    bundle_id = download_result['bundle_id']
    download_dir = download_result['download_dir']
    files = download_result['files']
    build_number = download_result.get('build_number')  # 0114新增：获取build号
    
    if not files:
        print("未找到下载的文件")
        return False
    
    # 使用第一个下载的文件作为 app 路径
    app_path = files[0]
    # 转换为绝对路径
    if not os.path.isabs(app_path):
        app_path = os.path.abspath(app_path)
    
    print(f"Bundle ID: {bundle_id}")
    print(f"应用路径: {app_path}")
    
    # 2. 获取设备信息
    print("\n步骤 2: 获取连接的设备")
    print("-" * 60)
    
    if device is None:
        device = get_connected_devices()
        if not device:
            print("错误: 未找到连接的设备")
            return False
    
    # 获取设备名称（iPad名称）
    dev_name = get_device_name(device)
    print(f"设备标识: {device}")
    print(f"设备名称（iPad名称）: {dev_name}")
    print(f"固件设备名称: {device_name}")
    
    # 3. 构建请求数据
    print("\n步骤 3: 构建测试请求")
    print("-" * 60)
    
    request_data = {
        "bundleId": bundle_id,  # 添加 bundleId
        "device": dev_name,   #iPad名称
        "device_name": device_name,  #固件设备名称
        "test": test_file,
        "appium_host": appium_host,
        "app": app_path,
        "reinstall": reinstall
    }
    # 注意：不传 device_name 字段
    
    print("请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    # 4. 显示请求信息
    print("\n步骤 4: 准备发送请求")
    print("-" * 60)
    
    url = "http://172.21.19.89:8005/api/test/run"
    
    # 显示请求信息（用于 dry-run 模式）
    print(f"请求 URL: {url}")
    print("请求方法: POST")
    print("请求头: Content-Type: application/json")
    print("请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    # 如果是 dry_run 模式，只输出信息不执行
    if dry_run:
        print("\n[DRY RUN 模式] 仅显示请求信息，不执行")
        # 同时输出 curl 命令格式（方便手动测试）
        json_data = json.dumps(request_data, ensure_ascii=False)
        curl_cmd = f"""curl -X POST {url} \\
  -H "Content-Type: application/json" \\
  -d '{json_data}'"""
        print("\n等效的 curl 命令:")
        print("-" * 60)
        print(curl_cmd)
        print("-" * 60)
        return True
    
    # 标记是否已发送测试请求（用于决定是否删除 app）
    test_request_sent = False
    
    # 5. 发送请求
    print("\n步骤 5: 发送测试请求")
    print("-" * 60)
    
    try:
        # 使用 requests 发送 POST 请求
        headers = {
            'Content-Type': 'application/json'
        }
        
        print(f"正在发送请求到: {url}")
        
        response = requests.post(
            url,
            json=request_data,  # 使用 json 参数自动设置 Content-Type 和序列化
            headers=headers,
            timeout=300  # 5分钟超时
        )
        
        # 标记测试请求已发送
        test_request_sent = True
        
        print(f"响应状态码: {response.status_code}")
        
        # 输出响应内容
        response_json = None
        try:
            response_json = response.json()
            print("响应内容 (JSON):")
            print(json.dumps(response_json, indent=2, ensure_ascii=False))
        except ValueError:
            # 如果不是 JSON，输出原始文本
            print("响应内容 (文本):")
            print(response.text)
        # 从响应中提取 task_id 并查询任务状态
        if response_json is not None and 'task_id' in response_json:
            task_id = response_json['task_id']
            print(f"\n✓ 测试请求已提交")
            print(f"任务ID: {task_id}")
            
            if 'status_url' in response_json:
                print(f"状态查询URL: {response_json['status_url']}")
            
            # 从请求 URL 提取基础地址
            from urllib.parse import urlparse, urlunparse
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # 查询任务状态
            status_url = f"{base_url}/api/test/status/{task_id}"
            print(f"\n正在查询任务状态...")
            
            try:
                import time
                import signal
                max_wait_time = 3600  # 最多等待60分钟
                check_interval = 10  # 每10秒查询一次（更频繁的查询）
                start_time = time.time()
                
                # 定义信号处理函数，用于优雅地处理中断
                def signal_handler(sig, frame):
                    print(f"\n\n⚠️ 收到中断信号 (Ctrl+C)，正在清理...")
                    if test_request_sent:
                        cleanup_downloaded_files(download_dir, files)
                    print("已清理下载文件，程序退出")
                    sys.exit(130)  # 130 是 Ctrl+C 的标准退出码
                
                # 注册信号处理器
                signal.signal(signal.SIGINT, signal_handler)
                
                while True:
                    status_response = requests.get(status_url, timeout=10)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        task_status = status_data.get('status', 'unknown')
                        
                        # 显示当前状态
                        status_msg = status_data.get('message', '')
                        if status_msg:
                            print(f"任务状态: {task_status} - {status_msg}")
                        else:
                            print(f"任务状态: {task_status}")
                        
                        # 如果任务已完成或失败，退出循环
                        if task_status in ['completed', 'failed', 'cancelled']:
                            if task_status == 'completed':
                                result = status_data.get('result', {})
                                passed = result.get('passed', 0)
                                failed = result.get('failed', 0)
                                total = result.get('total', 0)
                                success_rate = result.get('success_rate', 0)
                                error_messages = result.get('error_messages', [])
                                print(f"\n✓ 任务执行完成")
                                print(f"  通过: {passed}, 失败: {failed}, 总计: {total}")
                                if error_messages:
                                    print(f"  失败用例数: {len(error_messages)}")
                                    for case_error in error_messages:
                                        case_name = case_error.get('case_name', '未知用例')
                                        errors = case_error.get('errors', [])
                                        print(f"    - {case_name}: {len(errors)} 个错误")
                                # 0113新增：发送飞书通知，包含错误信息
                                # 0114新增：添加build信息
                                send_feishu_notification(
                                    status='completed',
                                    task_id=task_id,
                                    test_file=test_file,
                                    device_name=device_name or dev_name,
                                    bundle_id=bundle_id,
                                    passed=passed,
                                    failed=failed,
                                    total=total,
                                    success_rate=success_rate,
                                    error_msg=error_messages if error_messages else None,
                                    webhook_url=feishu_webhook_url,
                                    build_number=build_number
                                )
                                # 测试完成后清理下载的文件
                                if test_request_sent:
                                    cleanup_downloaded_files(download_dir, files)
                                return True
                            elif task_status == 'failed':
                                error_msg = status_data.get('error', '未知错误')
                                print(f"\n✗ 任务执行失败: {error_msg}")
                                # 发送飞书通知
                                send_feishu_notification(
                                    status='failed',
                                    task_id=task_id,
                                    test_file=test_file,
                                    device_name=device_name or dev_name,
                                    bundle_id=bundle_id,
                                    error_msg=error_msg,
                                    webhook_url=feishu_webhook_url,
                                    build_number=build_number
                                )
                                # 测试失败后也清理下载的文件
                                if test_request_sent:
                                    cleanup_downloaded_files(download_dir, files)
                                return False
                            elif task_status == 'cancelled':
                                print(f"\n⚠ 任务已取消")
                                # 发送飞书通知
                                send_feishu_notification(
                                    status='cancelled',
                                    task_id=task_id,
                                    test_file=test_file,
                                    device_name=device_name or dev_name,
                                    bundle_id=bundle_id,
                                    webhook_url=feishu_webhook_url,
                                    build_number=build_number
                                )
                                # 任务取消后也清理下载的文件
                                if test_request_sent:
                                    cleanup_downloaded_files(download_dir, files)
                                return False
                        
                        # 检查是否超时
                        elapsed_time = time.time() - start_time
                        if elapsed_time > max_wait_time:
                            print(f"\n⚠ 查询任务状态超时（超过 {max_wait_time} 秒）")
                            print(f"当前状态: {task_status}")
                            # 发送飞书通知
                            send_feishu_notification(
                                status='timeout',
                                task_id=task_id,
                                test_file=test_file,
                                device_name=device_name or dev_name,
                                bundle_id=bundle_id,
                                webhook_url=feishu_webhook_url,
                                build_number=build_number
                            )
                            # 超时后也清理下载的文件
                            if test_request_sent:
                                cleanup_downloaded_files(download_dir, files)
                            return False
                        
                        # 等待后继续查询
                        try:
                            time.sleep(check_interval)
                        except KeyboardInterrupt:
                            # 如果在 sleep 期间收到中断信号，会被 signal_handler 处理
                            # 但为了保险，这里也处理一下
                            print(f"\n\n⚠️ 收到中断信号，正在清理...")
                            if test_request_sent:
                                cleanup_downloaded_files(download_dir, files)
                            raise  # 重新抛出异常，让 signal_handler 处理
                    else:
                        print(f"\n⚠ 查询任务状态失败，HTTP状态码: {status_response.status_code}")
                        # 如果查询失败，但任务已提交，返回 True（任务可能在后台执行）
                        # 注意：这种情况下不清理下载文件，因为任务可能在后台执行
                        return True
                        
            except KeyboardInterrupt:
                # 处理键盘中断
                print(f"\n\n⚠️ 收到中断信号，正在清理...")
                if test_request_sent:
                    cleanup_downloaded_files(download_dir, files)
                raise  # 重新抛出，让上层处理
            except requests.exceptions.RequestException as e:
                print(f"\n⚠ 查询任务状态时出错: {e}")
                # 如果查询失败，但任务已提交，返回 True（任务可能在后台执行）
                # 注意：这种情况下不清理下载文件，因为任务可能在后台执行
                return True
        else:
            # 如果没有 task_id，检查是否有错误信息
            if response_json is not None:
                error_msg = response_json.get('error', '未知错误')
                print(f"\n✗ 测试请求失败: {error_msg}")
                # 请求失败，不删除 app（可能未安装）
                return False
            else:
                print(f"\n✗ 测试请求失败: 响应中未包含 task_id")
                # 请求失败，不删除 app（可能未安装）
                return False
            
    except requests.exceptions.Timeout:
        print("请求超时")
        # 请求超时，如果已发送请求则清理下载的文件
        if test_request_sent:
            cleanup_downloaded_files(download_dir, files)
        return False
    except requests.exceptions.RequestException as e:
        print(f"发送请求失败: {e}")
        import traceback
        traceback.print_exc()
        # 请求异常，如果已发送请求则清理下载的文件
        if test_request_sent:
            cleanup_downloaded_files(download_dir, files)
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()
        # 其他异常，如果已发送请求则清理下载的文件
        if test_request_sent:
            cleanup_downloaded_files(download_dir, files)
        return False

def main():
    """主函数 - 支持配置数组，循环执行多个测试配置"""
    
    # 配置参数数组 - 每个字典代表一个测试配置
    # 可以添加多个配置，脚本会按顺序循环执行
    test_configs = [
        {
            'app_uid_or_shortcut': 'v',  # APP_UID 或简写 (m 或 v)
            'device': "iPad7",  # 设备名，None 则自动获取
            'test_file': 'tests/test_ui_flow.yaml',  # 测试文件路径
            'device_name': 'evetest 1',  # 设备sn
            'appium_host': '127.0.0.1',  # Appium 服务器地址
            'reinstall': True,  # 是否重新安装应用
            'dry_run': False,  # 是否仅输出请求信息，不执行
            'feishu_webhook_url': None,  # 飞书 webhook URL，None 则从环境变量获取
        },
        {
            'app_uid_or_shortcut': 'v',  # APP_UID 或简写 (m 或 v)
            'device': "iPad7",  # 设备名，None 则自动获取
            'test_file': 'tests/test_api_V.yaml',  # 测试文件路径
            'device_name': 'evetest 1',  # 设备sn
            'appium_host': '127.0.0.1',  # Appium 服务器地址
            'reinstall': True,  # 是否重新安装应用
            'dry_run': False,  # 是否仅输出请求信息，不执行
            'feishu_webhook_url': None,  # 飞书 webhook URL，None 则从环境变量获取
        },
        # 示例：添加更多配置（取消注释即可使用）
        {
            'app_uid_or_shortcut': 'm',  # M 版本
            'device': "iPad7",
            'test_file': 'tests/test_ui_flow_m.yaml',
            'device_name': 'ruby 1',  # 不同的设备SN
            'appium_host': '127.0.0.1',
            'reinstall': True,
            'dry_run': False,
        },
        {
            'app_uid_or_shortcut': 'm',  # M 版本
            'device': "iPad7",
            'test_file': 'tests/test_api_M.yaml',
            'device_name': 'ruby 1',  # 不同的设备SN
            'appium_host': '127.0.0.1',
            'reinstall': True,
            'dry_run': False,
        },
        # {
        #     'app_uid_or_shortcut': 'lp',
        #     'device': 'iPad7',
        #     'test_file': 'tests/laprairie/test_press_flow.yaml', 
        #     'device_name': 'evetest 1', 
        #     'appium_host': '127.0.0.1',
        #     'reinstall': True,  
        #     'dry_run': False,
        # },
    ]
    
    # 统计信息
    total_configs = len(test_configs)
    success_count = 0
    failed_count = 0
    
    print("=" * 80)
    print(f"开始批量执行测试，共 {total_configs} 个配置")
    print("=" * 80)
    
    # 循环执行每个配置
    for idx, config in enumerate(test_configs, 1):
        print("\n" + "=" * 80)
        print(f"执行配置 {idx}/{total_configs}")
        print("=" * 80)
        print(f"配置详情:")
        print(f"  - APP: {config.get('app_uid_or_shortcut', 'N/A')}")
        print(f"  - 设备: {config.get('device', '自动获取')}")
        print(f"  - 设备SN: {config.get('device_name', 'N/A')}")
        print(f"  - 测试文件: {config.get('test_file', 'N/A')}")
        print(f"  - Appium地址: {config.get('appium_host', 'N/A')}")
        print(f"  - 重新安装: {config.get('reinstall', False)}")
        print(f"  - 仅预览: {config.get('dry_run', False)}")
        print("-" * 80)
        
        # 调用测试函数
        try:
            success = run_test(
                app_uid_or_shortcut=config.get('app_uid_or_shortcut', 'v'),
                device=config.get('device'),
                device_name=config.get('device_name'),
                test_file=config.get('test_file', 'tests/test_ui_flow.yaml'),
                appium_host=config.get('appium_host', '127.0.0.1'),
                reinstall=config.get('reinstall', True),
                dry_run=config.get('dry_run', False),
                feishu_webhook_url=config.get('feishu_webhook_url')
            )
            
            if success:
                success_count += 1
                print(f"\n✓ 配置 {idx} 执行成功")
            else:
                failed_count += 1
                print(f"\n✗ 配置 {idx} 执行失败")
        except Exception as e:
            failed_count += 1
            print(f"\n✗ 配置 {idx} 执行出错: {e}")
            import traceback
            traceback.print_exc()
        
        # 如果不是最后一个配置，添加分隔
        if idx < total_configs:
            print("\n" + "-" * 80)
            print("等待 3 秒后执行下一个配置...")
            import time
            time.sleep(3)
    
    # 输出最终统计
    print("\n" + "=" * 80)
    print("批量执行完成")
    print("=" * 80)
    print(f"总配置数: {total_configs}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"成功率: {(success_count / total_configs * 100) if total_configs > 0 else 0:.1f}%")
    print("=" * 80)
    
    
    
    # 如果有失败的配置，返回非0退出码
    sys.exit(0 if failed_count == 0 else 1)

if __name__ == "__main__":
    main()
    # print(get_device_name(get_connected_devices()))
