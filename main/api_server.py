#!/usr/bin/env python3
"""api_server.py - Ruby Eve UI Test API 服务"""
from flask import Flask, request, jsonify, send_file
import yaml
import threading
import uuid
import time
import os
import json
import shutil
from datetime import datetime
from main.device_executor import run_case_on_device
from utils.logger import Logger

# 尝试导入下载模块和检查依赖
# 使用与 download_New_ipa.py 相同的方式检查 protobuf
try:
    from google.protobuf.json_format import MessageToDict
    import sys
    import os
    # 添加 proto 文件所在目录到路径（与 download_New_ipa.py 在同一目录）
    proto_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                             'utils', 'ci_download')
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

app = Flask(__name__)
# 配置JSON编码，确保中文字符不被转义为Unicode转义序列
app.json.ensure_ascii = False

# 存储任务状态和结果
tasks = {}
tasks_lock = threading.Lock()

# 存储最新截图信息（用于实时查看）【0108新增实时截图功能】
latest_screenshot = {
    'path': None,
    'timestamp': None,
    'lock': threading.Lock()
}

# 任务持久化文件路径
def get_tasks_file():
    """获取任务持久化文件路径"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, 'logs', 'tasks.json')

def save_tasks():
    """保存任务到文件"""
    try:
        tasks_file = get_tasks_file()
        os.makedirs(os.path.dirname(tasks_file), exist_ok=True)
        with tasks_lock:
            # 只保存已完成或失败的任务，不保存运行中的任务（避免频繁写入）
            tasks_to_save = {
                task_id: task for task_id, task in tasks.items()
                if task.get('status') in ['completed', 'failed', 'cancelled']
            }
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ 保存任务数据失败: {e}")

def load_tasks():
    """从文件加载任务"""
    try:
        tasks_file = get_tasks_file()
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                loaded_tasks = json.load(f)
                with tasks_lock:
                    tasks.update(loaded_tasks)
                print(f"✅ 已加载 {len(loaded_tasks)} 个历史任务")
    except Exception as e:
        print(f"⚠️ 加载任务数据失败: {e}")

def load_task_from_file(task_id):
    """从文件加载单个任务（如果内存中没有）"""
    try:
        tasks_file = get_tasks_file()
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                all_tasks = json.load(f)
                if task_id in all_tasks:
                    with tasks_lock:
                        tasks[task_id] = all_tasks[task_id]
                    return all_tasks[task_id]
    except Exception as e:
        pass
    return None

def execute_test_with_download(task_id, device_info, bundle_id, test_file, app_path, reinstall, times=1, device_name=None, case_filters=None, app_shortcut=None, appium_host=None):
    """在后台线程中执行测试（包含自动下载功能）"""
    # 创建日志文件路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, 'logs')
    log_file = os.path.join(logs_dir, f'{task_id}.log')
    
    # 创建 Logger，同时输出到控制台和文件
    logger = Logger(prefix=f'API-{task_id[:8]}', log_file=log_file)
    
    # 将任务日志文件路径注入环境变量，供子模块 Logger 自动写入同一日志文件
    try:
        os.environ['TASK_LOG_FILE'] = log_file
    except Exception:
        pass
    
    # 检查是否是分布式部署（Appium 在远程机器）
    is_remote_appium = False
    
    def is_local_host(host_str):
        """检查是否是本地主机地址"""
        if not host_str:
            return False
        host_str_lower = host_str.lower()
        # 检查是否包含本地地址标识
        if '127.0.0.1' in host_str_lower or 'localhost' in host_str_lower:
            return True
        # 检查是否是纯 IP 或主机名
        host_str_clean = host_str_lower.replace('http://', '').replace('https://', '').split('/')[0].split(':')[0]
        return host_str_clean in ['127.0.0.1', 'localhost', '0.0.0.0']
    
    if appium_host:
        if not is_local_host(appium_host):
            is_remote_appium = True
    elif device_info and 'appium_server' in device_info:
        appium_server = device_info.get('appium_server', '')
        if appium_server and not is_local_host(appium_server):
            is_remote_appium = True
    
    # 如果需要自动下载
    if app_shortcut and app_path in ['auto_v', 'auto_m']:
        # 检查下载功能是否可用
        if not DOWNLOAD_AVAILABLE:
            error_msg = '自动下载功能不可用: 下载模块导入失败'
            logger.log(f"❌ {error_msg}")
            with tasks_lock:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['end_time'] = datetime.now().isoformat()
                tasks[task_id]['error'] = error_msg
            save_tasks()
            return
        
        try:
            # 动态导入下载函数（确保可用）
            from utils.ci_download.download_New_ipa import download_test_enterprise_package
            
            with tasks_lock:
                tasks[task_id]['status'] = 'downloading'
                tasks[task_id]['message'] = f'正在下载最新包 (app={app_shortcut})...'
            
            logger.log(f"开始下载最新包: {app_path}")
            
            # 调用下载函数
            download_result = download_test_enterprise_package(app_shortcut)
            
            if not download_result or not download_result.get('success'):
                error_msg = '自动下载失败'
                if download_result:
                    if download_result.get('download_dir'):
                        error_msg += f': 未找到测试环境企业包（app={app_shortcut}）'
                    else:
                        error_msg += f': 下载过程中出错（app={app_shortcut}）'
                else:
                    error_msg += f': 下载函数返回 None，可能是 protobuf 解析失败或网络问题（app={app_shortcut}）'
                
                logger.log(f"❌ {error_msg}")
                with tasks_lock:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['end_time'] = datetime.now().isoformat()
                    tasks[task_id]['error'] = error_msg
                save_tasks()
                return
            
            # 获取下载的文件列表
            downloaded_files = download_result.get('files', [])
            if not downloaded_files:
                error_msg = f'自动下载失败: 未找到下载的文件（app={app_shortcut}）'
                logger.log(f"❌ {error_msg}")
                with tasks_lock:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['end_time'] = datetime.now().isoformat()
                    tasks[task_id]['error'] = error_msg
                save_tasks()
                return
            
            # 使用第一个下载的文件作为 app_path（通常是 .ipa 文件）
            downloaded_file = downloaded_files[0]
            if not os.path.isabs(downloaded_file):
                app_path = os.path.join(project_root, downloaded_file)
                app_path = os.path.normpath(app_path)
            else:
                app_path = downloaded_file
            
            logger.log(f"✅ 自动下载完成: {app_path}")
            logger.log(f"📦 下载目录: {download_result.get('download_dir')}")
            logger.log(f"📱 Bundle ID: {download_result.get('bundle_id')}")
            logger.log(f"🔢 构建号: {download_result.get('build_number')}")
            
            # 检查分布式部署问题：如果 Appium 在远程机器，下载的文件在服务器端，Appium 无法访问
            if is_remote_appium:
                error_msg = (
                    f'分布式部署限制: 文件已下载到服务器端 ({app_path})，但 Appium 在远程机器上无法访问此文件。\n'
                    f'解决方案:\n'
                    f'1. 将文件传输到 Appium 机器: scp {app_path} user@{appium_host}:/path/to/app/\n'
                    f'2. 使用共享存储（NFS/SMB）\n'
                    f'3. 在 Appium 机器上也配置自动下载功能\n'
                    f'4. 使用 Appium 机器上的绝对路径，而不是 auto_v/auto_m'
                )
                logger.log(f"❌ {error_msg}")
                with tasks_lock:
                    tasks[task_id]['status'] = 'failed'
                    tasks[task_id]['end_time'] = datetime.now().isoformat()
                    tasks[task_id]['error'] = error_msg
                    tasks[task_id]['app_path'] = app_path  # 保存下载路径供参考
                save_tasks()
                return
            
            # 更新任务中的 app_path，并保存下载信息用于后续清理
            with tasks_lock:
                tasks[task_id]['app_path'] = app_path
                tasks[task_id]['downloaded_file'] = app_path  # 保存下载的文件路径
                tasks[task_id]['download_dir'] = download_result.get('download_dir')  # 保存下载目录
                tasks[task_id]['is_auto_download'] = True  # 标记为自动下载
                if not bundle_id and download_result.get('bundle_id'):
                    bundle_id = download_result.get('bundle_id')
                    tasks[task_id]['bundle_id'] = bundle_id
                    logger.log(f"📝 使用下载包对应的 Bundle ID: {bundle_id}")
            
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            logger.log(f"❌ 自动下载异常: {error_detail}")
            with tasks_lock:
                tasks[task_id]['status'] = 'failed'
                tasks[task_id]['end_time'] = datetime.now().isoformat()
                tasks[task_id]['error'] = f'自动下载失败: {str(e)}'
            save_tasks()
            return
    
    # 执行测试前检查是否被取消
    with tasks_lock:
        task_status = tasks.get(task_id, {}).get('status', '')
        if task_status == 'cancelled':
            logger.log(f"任务在下载完成后被取消，不执行测试")
            return
    
    # 执行测试
    execute_test(task_id, device_info, bundle_id, test_file, app_path, reinstall, times, device_name, case_filters)

def execute_test(task_id, device_info, bundle_id, test_file, app_path, reinstall, times=1, device_name=None, case_filters=None):
    """在后台线程中执行测试"""
    # 创建日志文件路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, 'logs')
    log_file = os.path.join(logs_dir, f'{task_id}.log')
    
    # 创建 Logger，同时输出到控制台和文件
    logger = Logger(prefix=f'API-{task_id[:8]}', log_file=log_file)
    
    # 将任务日志文件路径注入环境变量，供子模块 Logger 自动写入同一日志文件
    try:
        os.environ['TASK_LOG_FILE'] = log_file
    except Exception:
        pass
    
    try:
        with tasks_lock:
            tasks[task_id]['status'] = 'running'
            tasks[task_id]['start_time'] = datetime.now().isoformat()
            tasks[task_id]['log_file'] = log_file  # 保存日志文件路径
        
        logger.log(f"开始执行测试任务: {task_id}, 执行次数: {times}")
        
        # 设置运行时间戳
        run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.environ['RUN_START_TIMESTAMP'] = run_timestamp
        
        # 创建临时结果文件
        import tempfile
        import json
        results_file = tempfile.mktemp(suffix='.json')
        
        # 执行多次测试
        total_passed = 0
        total_failed = 0
        
        for run_number in range(1, times + 1):
            # 检查任务是否被取消
            with tasks_lock:
                task_status = tasks.get(task_id, {}).get('status', '')
                if task_status == 'cancelled':
                    logger.log(f"任务已被取消，停止执行")
                    tasks[task_id]['status'] = 'cancelled'
                    tasks[task_id]['end_time'] = datetime.now().isoformat()
                    tasks[task_id]['result'] = {
                        'passed': total_passed,
                        'failed': total_failed,
                        'total': total_passed + total_failed,
                        'success_rate': (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0,
                        'times': run_number - 1,  # 实际执行的次数
                        'cancelled': True
                    }
                    save_tasks()
                    return
            
            logger.log(f"第 {run_number}/{times} 次执行开始")
            
            # 每次执行前清空结果文件，确保只读取本次执行的结果
            try:
                with open(results_file, 'w', encoding='utf-8') as f:
                    pass  # 清空文件
            except:
                pass
            
            try:
                # 执行测试
                run_case_on_device(device_info, bundle_id, test_file, run_number, results_file, app_path, reinstall, device_name, case_filters)
                
                # 执行后再次检查是否被取消
                with tasks_lock:
                    task_status = tasks.get(task_id, {}).get('status', '')
                    if task_status == 'cancelled':
                        logger.log(f"任务在执行过程中被取消，停止后续执行")
                        tasks[task_id]['status'] = 'cancelled'
                        tasks[task_id]['end_time'] = datetime.now().isoformat()
                        tasks[task_id]['result'] = {
                            'passed': total_passed,
                            'failed': total_failed,
                            'total': total_passed + total_failed,
                            'success_rate': (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0,
                            'times': run_number,
                            'cancelled': True
                        }
                        save_tasks()
                        return
                
                # 读取本次执行结果（应该只有一行）
                try:
                    with open(results_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip():
                                result = json.loads(line.strip())
                                # 累加本次执行的结果
                                total_passed += result.get('passed', 0)
                                total_failed += result.get('failed', 0)
                                logger.log(f"第 {run_number}/{times} 次执行结果: 通过={result.get('passed', 0)}, 失败={result.get('failed', 0)}")
                except Exception as e:
                    logger.log(f"读取结果文件失败: {e}")
                
                logger.log(f"第 {run_number}/{times} 次执行完成")
                
                # 如果不是最后一次执行，等待一下（期间检查取消状态）
                if run_number < times:
                    logger.log(f"⏳ 等待5秒后进行下一次执行...")
                    # 分段等待，期间检查取消状态
                    for _ in range(5):
                        time.sleep(1)
                        with tasks_lock:
                            task_status = tasks.get(task_id, {}).get('status', '')
                            if task_status == 'cancelled':
                                logger.log(f"任务在等待期间被取消，停止执行")
                                tasks[task_id]['status'] = 'cancelled'
                                tasks[task_id]['end_time'] = datetime.now().isoformat()
                                tasks[task_id]['result'] = {
                                    'passed': total_passed,
                                    'failed': total_failed,
                                    'total': total_passed + total_failed,
                                    'success_rate': (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0,
                                    'times': run_number,
                                    'cancelled': True
                                }
                                save_tasks()
                                return
                    
            except Exception as e:
                logger.log(f"第 {run_number}/{times} 次执行出错: {e}")
                # 继续执行下一次，不中断整个任务
                continue
        
        # 清理临时文件
        try:
            os.remove(results_file)
        except:
            pass
        
        # 更新任务状态（检查是否被取消）
        with tasks_lock:
            task_status = tasks.get(task_id, {}).get('status', '')
            # 如果任务已被取消，保持取消状态，不更新为完成
            if task_status == 'cancelled':
                logger.log(f"任务已被取消，不更新为完成状态")
                # 如果还没有设置结果，设置一下
                if 'result' not in tasks[task_id] or not tasks[task_id].get('result'):
                    tasks[task_id]['result'] = {
                        'passed': total_passed,
                        'failed': total_failed,
                        'total': total_passed + total_failed,
                        'success_rate': (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0,
                        'times': times,
                        'cancelled': True
                    }
                save_tasks()
                return
            
            tasks[task_id]['status'] = 'completed'
            tasks[task_id]['end_time'] = datetime.now().isoformat()
            tasks[task_id]['result'] = {
                'passed': total_passed,
                'failed': total_failed,
                'total': total_passed + total_failed,
                'success_rate': (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0,
                'times': times
            }
            tasks[task_id]['screenshot_dir'] = f'screenshots/run_{run_timestamp}/'
            
            # 检查是否需要删除自动下载的文件
            is_auto_download = tasks[task_id].get('is_auto_download', False)
            downloaded_file = tasks[task_id].get('downloaded_file')
            download_dir = tasks[task_id].get('download_dir')
        
        # 保存到文件
        save_tasks()
        
        # 删除自动下载的文件和目录
        if is_auto_download:
            try:
                # 删除下载的文件
                if downloaded_file and os.path.exists(downloaded_file):
                    logger.log(f"🗑️ 删除下载的文件: {downloaded_file}")
                    os.remove(downloaded_file)
                    logger.log(f"✅ 已删除下载文件")
                elif downloaded_file:
                    logger.log(f"⚠️ 下载文件不存在，跳过删除: {downloaded_file}")
                
                # 删除下载目录（如果目录为空或只包含构建信息文件）
                if download_dir:
                    # 将相对路径转换为绝对路径
                    if not os.path.isabs(download_dir):
                        download_dir_abs = os.path.join(project_root, download_dir)
                        download_dir_abs = os.path.normpath(download_dir_abs)
                    else:
                        download_dir_abs = download_dir
                    
                    if os.path.exists(download_dir_abs):
                        try:
                            # 检查目录内容
                            dir_contents = os.listdir(download_dir_abs)
                            # 如果目录为空或只包含 build_info.yaml，删除整个目录
                            if not dir_contents or (len(dir_contents) == 1 and dir_contents[0] == 'build_info.yaml'):
                                logger.log(f"🗑️ 删除下载目录: {download_dir_abs}")
                                shutil.rmtree(download_dir_abs)
                                logger.log(f"✅ 已删除下载目录")
                            else:
                                # 如果还有其他文件，只删除 build_info.yaml（如果存在）
                                build_info_path = os.path.join(download_dir_abs, 'build_info.yaml')
                                if os.path.exists(build_info_path):
                                    os.remove(build_info_path)
                                    logger.log(f"✅ 已删除构建信息文件")
                        except Exception as e:
                            logger.log(f"⚠️ 删除下载目录失败: {e}")
                    else:
                        logger.log(f"⚠️ 下载目录不存在，跳过删除: {download_dir_abs}")
            except Exception as e:
                logger.log(f"⚠️ 清理下载文件时出错: {e}")
        
        logger.log(f"测试任务完成: {task_id}, 执行 {times} 次, 总通过: {total_passed}, 总失败: {total_failed}")
        
    except Exception as e:
        logger.log(f"测试执行出错: {e}")
        with tasks_lock:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['end_time'] = datetime.now().isoformat()
            tasks[task_id]['error'] = str(e)
            
            # 检查是否需要删除自动下载的文件
            is_auto_download = tasks[task_id].get('is_auto_download', False)
            downloaded_file = tasks[task_id].get('downloaded_file')
            download_dir = tasks[task_id].get('download_dir')
        
        # 保存到文件
        save_tasks()
        
        # 删除自动下载的文件和目录（即使测试失败也清理）
        if is_auto_download:
            try:
                # 删除下载的文件
                if downloaded_file and os.path.exists(downloaded_file):
                    logger.log(f"🗑️ 删除下载的文件: {downloaded_file}")
                    os.remove(downloaded_file)
                    logger.log(f"✅ 已删除下载文件")
                elif downloaded_file:
                    logger.log(f"⚠️ 下载文件不存在，跳过删除: {downloaded_file}")
                
                # 删除下载目录
                if download_dir:
                    # 将相对路径转换为绝对路径
                    if not os.path.isabs(download_dir):
                        download_dir_abs = os.path.join(project_root, download_dir)
                        download_dir_abs = os.path.normpath(download_dir_abs)
                    else:
                        download_dir_abs = download_dir
                    
                    if os.path.exists(download_dir_abs):
                        try:
                            dir_contents = os.listdir(download_dir_abs)
                            if not dir_contents or (len(dir_contents) == 1 and dir_contents[0] == 'build_info.yaml'):
                                logger.log(f"🗑️ 删除下载目录: {download_dir_abs}")
                                shutil.rmtree(download_dir_abs)
                                logger.log(f"✅ 已删除下载目录")
                            else:
                                build_info_path = os.path.join(download_dir_abs, 'build_info.yaml')
                                if os.path.exists(build_info_path):
                                    os.remove(build_info_path)
                                    logger.log(f"✅ 已删除构建信息文件")
                        except Exception as e:
                            logger.log(f"⚠️ 删除下载目录失败: {e}")
                    else:
                        logger.log(f"⚠️ 下载目录不存在，跳过删除: {download_dir_abs}")
            except Exception as e:
                logger.log(f"⚠️ 清理下载文件时出错: {e}")

@app.route('/api/test/run', methods=['POST'])
def run_test():
    """执行测试任务"""
    try:
        data = request.json or {}
        
        # 获取必需参数
        bundle_id = data.get('bundleId') or data.get('bundle_id')
        device_name = data.get('device')
        test_file = data.get('test', 'tests/test_ui_flow.yaml')
        
        if not bundle_id:
            return jsonify({'error': '缺少必需参数: bundleId'}), 400
        if not device_name:
            return jsonify({'error': '缺少必需参数: device'}), 400
        
        # 可选参数
        base_port = data.get('base_port', 4723)
        devices_file = data.get('devices', 'utils/devices.yaml')
        app_path = data.get('app')
        reinstall = data.get('reinstall', False)
        times = data.get('times', 1)  # 执行次数，默认1次
        test_device_name = data.get('device_name')  # 用于 check_connected、connect 等方法的设备名称
        # 用例名过滤：支持传入字符串（逗号分隔）或数组
        case_filters = data.get('cases') or data.get('case')
        if isinstance(case_filters, list):
            case_filters = [str(x) for x in case_filters]
        elif isinstance(case_filters, str):
            # 原样传下去，底层会自行 split
            pass
        else:
            case_filters = None
        # Appium 服务器地址（支持远程连接）
        appium_host = data.get('appium_host', '127.0.0.1')  # 默认本地，可改为远程 IP
        
        # 实时截图上传参数【0108新增实时截图功能】
        realtime_screenshot_upload = data.get('realtime_screenshot_upload', False)  # 是否启用实时截图上传
        realtime_screenshot_interval = data.get('realtime_screenshot_interval', 2)  # 截图间隔（秒）
        realtime_screenshot_api_url = data.get('realtime_screenshot_api_url', 'http://localhost:8005/api/upload')  # 上传API地址
        
        # 规范化 appium_host：如果传入的是 URL，提取主机名
        if appium_host:
            # 移除协议前缀
            host_clean = appium_host.replace('http://', '').replace('https://', '')
            # 移除路径和端口（如果有）
            host_clean = host_clean.split('/')[0].split(':')[0]
            # 如果提取后为空，使用原始值
            if host_clean:
                appium_host = host_clean
        
        # 处理 app_path：
        # 2026.01.06新增:服务器连接的iPad可自动下载最新包
        # 支持自动下载：如果 app_path 是 "auto_v" 或 "auto_m"，将在后台线程中自动下载最新包
        app_shortcut = None
        if app_path in ['auto_v', 'auto_m']:
            # 检查下载功能是否可用
            if not DOWNLOAD_AVAILABLE:
                return jsonify({
                    'error': '自动下载功能不可用: 下载模块导入失败。请检查 utils/ci_download/download_New_ipa.py 是否存在'
                }), 500
            
            # 检查 protobuf 依赖
            if not PROTOBUF_AVAILABLE:
                return jsonify({
                    'error': '自动下载功能需要 protobuf 库支持。请运行以下命令安装依赖:\n'
                             '1. pip3 install protobuf\n'
                             '2. 编译 proto 文件: protoc --python_out=. omnibus_connect_builds.proto\n'
                             '（如果 proto 文件在 utils/ci_download/ 目录下，请先切换到该目录）'
                }), 500
            
            # 提取简写（v 或 m），将在后台线程中下载
            app_shortcut = app_path.replace('auto_', '')
            # app_path 保持为 'auto_v' 或 'auto_m'，在后台线程中会被替换为实际下载路径
        
        # 处理 app_path：
        # 在分布式部署中（appium_host 是远程 IP），app_path 必须是 Appium 机器上的绝对路径
        # 在本地部署中（appium_host 是 127.0.0.1），相对路径可以转换为服务器路径
        # 注意：如果是 auto_v 或 auto_m，跳过路径检查，因为下载会在后台线程中进行
        if app_path and app_path not in ['auto_v', 'auto_m']:
            if os.path.isabs(app_path):
                # 绝对路径，直接使用（应该是 Appium 所在机器的路径）
                pass
            elif appium_host == '127.0.0.1' or appium_host == 'localhost':
                # 相对路径且 Appium 在本地（代码和 Appium 在同一机器），转换为服务器项目根目录下的路径
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                app_path = os.path.join(project_root, app_path)
                app_path = os.path.normpath(app_path)
            else:
                # 相对路径且 Appium 在远程机器
                # 在分布式部署中，相对路径无法确定，必须使用绝对路径
                return jsonify({
                    'error': f'在分布式部署中（Appium 在远程机器 {appium_host}），app 路径必须是绝对路径。当前路径 "{app_path}" 是相对路径，请提供 Appium 机器上的绝对路径，例如 "/Users/yourname/apps"'
                }), 400
        
        # 加载设备配置
        try:
            with open(devices_file, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f)
            all_devices = cfg.get('devices', [])
        except Exception as e:
            return jsonify({'error': f'加载设备配置失败: {e}'}), 400
        
        # 查找设备
        device_info = None
        for idx, device in enumerate(all_devices):
            if device.get('name') == device_name:
                assigned_port = base_port + idx
                # 如果设备配置中指定了 appium_server，优先使用
                if device.get('appium_server'):
                    appium_server = device.get('appium_server')
                else:
                    appium_server = f'http://{appium_host}:{assigned_port}'
                
                device_info = {
                    'name': device.get('name'),
                    'udid': device.get('udid'),
                    'platformName': device.get('platformName', 'iOS'),
                    'appium_port': assigned_port,
                    'appium_server': appium_server,
                }
                break
        
        if not device_info:
            return jsonify({'error': f'未找到设备: {device_name}'}), 400
        
        # 检查测试文件是否存在
        if not os.path.exists(test_file):
            return jsonify({'error': f'测试文件不存在: {test_file}'}), 400
        
        # 创建任务
        task_id = str(uuid.uuid4())
        # 创建日志文件路径（在任务创建时就确定，即使还没开始执行）
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(project_root, 'logs')
        log_file = os.path.join(logs_dir, f'{task_id}.log')
        
        with tasks_lock:
            tasks[task_id] = {
                'task_id': task_id,
                'status': 'pending',
                'bundle_id': bundle_id,
                'device': device_name,
                'test_file': test_file,
                'app_path': app_path,
                'reinstall': reinstall,
                'times': times,
                'device_name': test_device_name,  # 用于 check_connected、connect 等方法的设备名称
                'cases': case_filters,
                'create_time': datetime.now().isoformat(),
                'log_file': log_file,  # 保存日志文件路径
            }
        # 保存到文件（异步，不阻塞）
        threading.Thread(target=save_tasks, daemon=True).start()
        
        # 设置实时截图上传环境变量（如果启用）
        if realtime_screenshot_upload:
            os.environ['REALTIME_SCREENSHOT_UPLOAD'] = 'true'
            os.environ['REALTIME_SCREENSHOT_INTERVAL'] = str(realtime_screenshot_interval)
            os.environ['REALTIME_SCREENSHOT_API_URL'] = realtime_screenshot_api_url
        else:
            # 如果未启用，清除环境变量（使用默认值）
            os.environ.pop('REALTIME_SCREENSHOT_UPLOAD', None)
            os.environ.pop('REALTIME_SCREENSHOT_INTERVAL', None)
            os.environ.pop('REALTIME_SCREENSHOT_API_URL', None)
        
        # 在后台线程中执行测试（包含自动下载功能）
        # 如果 app_shortcut 不为 None，说明需要自动下载
        if app_shortcut:
            thread = threading.Thread(
                target=execute_test_with_download,
                args=(task_id, device_info, bundle_id, test_file, app_path, reinstall, times, test_device_name, case_filters, app_shortcut, appium_host)
            )
            message = f'测试任务已创建，正在下载最新包并执行测试（将执行 {times} 次）'
        else:
            thread = threading.Thread(
                target=execute_test,
                args=(task_id, device_info, bundle_id, test_file, app_path, reinstall, times, test_device_name, case_filters)
            )
            message = f'测试任务已创建，正在执行中（将执行 {times} 次）'
        
        # 如果启用了实时截图上传，在消息中添加提示
        if realtime_screenshot_upload:
            message += f'，实时截图上传已启用（间隔: {realtime_screenshot_interval}秒）'
        
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': message,
            'status_url': f'/api/test/status/{task_id}'
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'创建测试任务失败: {str(e)}'}), 500

@app.route('/api/test/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询任务状态"""
    with tasks_lock:
        task = tasks.get(task_id)
    
    # 如果内存中没有，尝试从文件加载
    if not task:
        task = load_task_from_file(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    # 检查是否请求包含日志内容
    include_log = request.args.get('include_log', 'false').lower() == 'true'
    
    result = task.copy()
    
    # 如果请求包含日志，读取日志文件内容
    if include_log and task.get('log_file'):
        log_file = task.get('log_file')
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    result['log_content'] = log_content
            except Exception as e:
                result['log_error'] = f'读取日志文件失败: {str(e)}'
        else:
            result['log_content'] = ''
            result['log_note'] = '日志文件尚未创建'
    
    return jsonify(result), 200

@app.route('/api/test/list', methods=['GET'])
def list_tasks():
    """列出任务
    
    默认只返回正在执行的任务（pending, downloading, running），不包括历史任务
    
    查询参数:
        status: 可选，过滤任务状态
            - 不传或 'running': 只返回正在执行的任务（pending, downloading, running）
            - 'all': 返回所有任务（包括历史任务，限制最近50个）
            - 'completed': 只返回已完成的任务
            - 'failed': 只返回失败的任务
    """
    # 获取过滤参数
    status_filter = request.args.get('status', '').lower()
    
    with tasks_lock:
        task_list = list(tasks.values())
    
    # 默认只返回正在执行的任务
    if not status_filter or status_filter == 'running':
        # 只返回正在执行的任务（pending, downloading, running）
        task_list = [task for task in task_list if task.get('status') in ['pending', 'downloading', 'running']]
        filter_name = 'running'
    elif status_filter == 'all':
        # 返回所有任务，限制最近50个
        task_list = task_list[:50]
        filter_name = 'all'
    elif status_filter == 'completed':
        task_list = [task for task in task_list if task.get('status') == 'completed']
        filter_name = 'completed'
    elif status_filter == 'failed':
        task_list = [task for task in task_list if task.get('status') == 'failed']
        filter_name = 'failed'
    elif status_filter == 'active':
        # active 表示所有非终态任务（pending, downloading, running）
        task_list = [task for task in task_list if task.get('status') in ['pending', 'downloading', 'running']]
        filter_name = 'active'
    else:
        # 未知的过滤参数，默认返回正在执行的任务
        task_list = [task for task in task_list if task.get('status') in ['pending', 'downloading', 'running']]
        filter_name = 'running'
    
    # 按创建时间倒序排列
    task_list.sort(key=lambda x: x.get('create_time', ''), reverse=True)
    
    return jsonify({
        'total': len(task_list),
        'tasks': task_list,
        'filter': filter_name
    }), 200

@app.route('/api/test/log/<task_id>', methods=['GET'])
def get_task_log(task_id):
    """获取任务的日志内容"""
    with tasks_lock:
        task = tasks.get(task_id)
    
    # 如果内存中没有，尝试从文件加载
    if not task:
        task = load_task_from_file(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    log_file = task.get('log_file')
    if not log_file:
        return jsonify({'error': '任务日志文件路径不存在'}), 404
    
    if not os.path.exists(log_file):
        return jsonify({
            'task_id': task_id,
            'log_content': '',
            'note': '日志文件尚未创建（任务可能还未开始执行）'
        }), 200
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        return jsonify({
            'task_id': task_id,
            'log_file': log_file,
            'log_content': log_content
        }), 200
    except Exception as e:
        return jsonify({'error': f'读取日志文件失败: {str(e)}'}), 500

@app.route('/api/test/result/<task_id>', methods=['GET'])
def get_task_result(task_id):
    """获取任务的执行结果汇总"""
    with tasks_lock:
        task = tasks.get(task_id)
    
    # 如果内存中没有，尝试从文件加载
    if not task:
        task = load_task_from_file(task_id)
    
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    
    # 检查任务是否已完成
    status = task.get('status', 'unknown')
    if status not in ['completed', 'failed', 'cancelled']:
        return jsonify({
            'error': '任务尚未完成',
            'status': status,
            'message': '任务仍在执行中，请等待完成后查询结果'
        }), 400
    
    # 构建结果汇总
    times = task.get('times', 1)
    device = task.get('device', '未知设备')
    test_file = task.get('test_file', '未知测试用例')
    result = task.get('result', {})
    
    total_passed = result.get('passed', 0)
    total_failed = result.get('failed', 0)
    total = result.get('total', total_passed + total_failed)
    success_rate = result.get('success_rate', 0)
    
    # 如果 result 中没有 success_rate，计算一下
    if success_rate == 0 and total > 0:
        success_rate = (total_passed / total) * 100
    
    screenshot_dir = task.get('screenshot_dir', '')
    create_time = task.get('create_time', '')
    start_time = task.get('start_time', '')
    end_time = task.get('end_time', '')
    error = task.get('error', '')
    
    # 构建返回结果（包含格式化的文本和结构化数据）
    summary = {
        'task_id': task_id,
        'status': status,
        'summary_text': f"""
{'='*80}
🎯 测试执行完成汇总
{'='*80}
📊 执行统计:
   🔢 总执行次数: {times}
   📱 测试设备: {device}
   📄 测试用例: {test_file}
   ✅ 成功次数: {total_passed}
   ❌ 失败次数: {total_failed}
   📈 成功率: {success_rate:.1f}%
{'='*80}
💡 提示: 详细的执行日志请查看日志文件
{'='*80}
""".strip(),
        'statistics': {
            'total_runs': times,
            'device': device,
            'test_file': test_file,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total': total,
            'success_rate': round(success_rate, 2)
        },
        'timeline': {
            'create_time': create_time,
            'start_time': start_time,
            'end_time': end_time
        },
        'screenshot_dir': screenshot_dir,
        'error': error if error else None
    }
    
    return jsonify(summary), 200

@app.route('/api/test/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消任务（仅标记，无法真正停止正在运行的任务）"""
    with tasks_lock:
        task = tasks.get(task_id)
        # 如果内存中没有，尝试从文件加载
        if not task:
            task = load_task_from_file(task_id)
            if task:
                tasks[task_id] = task
        
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        if task['status'] in ['completed', 'failed']:
            return jsonify({'error': '任务已完成，无法取消'}), 400
        
        task['status'] = 'cancelled'
        task['end_time'] = datetime.now().isoformat()
    
    # 保存到文件
    save_tasks()
    return jsonify({'success': True, 'message': '任务已标记为取消'}), 200

# ✅健康检查
@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Ruby Eve UI Test API',
        'timestamp': datetime.now().isoformat()
    }), 200

# ✅列出所有可用设备
@app.route('/api/devices', methods=['GET'])
def list_devices():
    """列出所有可用设备"""
    try:
        devices_file = request.args.get('devices', 'utils/devices.yaml')
        with open(devices_file, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f)
        devices = cfg.get('devices', [])
        
        return jsonify({
            'devices': devices,
            'total': len(devices)
        }), 200
    except Exception as e:
        return jsonify({'error': f'加载设备列表失败: {str(e)}'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_screenshot():
    """上传实时截图【0108新增实时截图功能】
    
    接收图片数据并保存，用于实时监控模式。
    支持通过 HTTP POST 上传图片数据。
    
    请求:
        Content-Type: image/jpeg 或 image/png
        Body: 图片的二进制数据
    
    返回:
        {
            'success': True,
            'message': 'Screenshot uploaded successfully',
            'path': '/path/to/screenshot.jpg',
            'timestamp': '2026-01-08T10:30:00'
        }
    """
    try:
        # 获取上传的图片数据
        if not request.data:
            return jsonify({'error': '未收到图片数据'}), 400
        
        image_data = request.data
        
        # 获取 Content-Type，确定文件扩展名
        content_type = request.headers.get('Content-Type', 'image/jpeg')
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        else:
            ext = '.jpg'  # 默认使用 jpg
        
        # 创建实时截图目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        realtime_dir = os.path.join(project_root, 'screenshots', 'realtime')
        os.makedirs(realtime_dir, exist_ok=True)
        
        # 生成文件名（使用时间戳）
        timestamp = datetime.now()
        filename = f'screenshot_{timestamp.strftime("%Y%m%d_%H%M%S")}{ext}'
        file_path = os.path.join(realtime_dir, filename)
        
        # 保存图片
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # 更新最新截图信息
        with latest_screenshot['lock']:
            # 删除旧的最新截图（只保留最新的一个）
            if latest_screenshot['path'] and os.path.exists(latest_screenshot['path']):
                try:
                    os.remove(latest_screenshot['path'])
                except:
                    pass
            
            latest_screenshot['path'] = file_path
            latest_screenshot['timestamp'] = timestamp.isoformat()
        
        return jsonify({
            'success': True,
            'message': 'Screenshot uploaded successfully',
            'path': file_path,
            'timestamp': timestamp.isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'上传截图失败: {str(e)}'}), 500

@app.route('/api/screenshot/latest', methods=['GET'])
def get_latest_screenshot():
    """获取最新上传的截图【0108新增实时截图功能】
    
    返回最新上传的截图文件。
    
    返回:
        如果存在最新截图，返回图片文件
        如果不存在，返回 404
    """
    with latest_screenshot['lock']:
        screenshot_path = latest_screenshot['path']
        timestamp = latest_screenshot['timestamp']
    
    if not screenshot_path or not os.path.exists(screenshot_path):
        return jsonify({'error': '暂无截图'}), 404
    
    try:
        return send_file(screenshot_path, mimetype='image/jpeg')
    except Exception as e:
        return jsonify({'error': f'读取截图失败: {str(e)}'}), 500

@app.route('/api/screenshot/info', methods=['GET'])
def get_screenshot_info():
    """获取最新截图信息【0108新增实时截图功能】
    
    返回最新截图的元数据信息（不返回图片本身）。
    
    返回:
        {
            'path': '/path/to/screenshot.jpg',
            'timestamp': '2026-01-08T10:30:00',
            'exists': True
        }
    """
    with latest_screenshot['lock']:
        screenshot_path = latest_screenshot['path']
        timestamp = latest_screenshot['timestamp']
    
    exists = screenshot_path and os.path.exists(screenshot_path)
    
    return jsonify({
        'path': screenshot_path,
        'timestamp': timestamp,
        'exists': exists
    }), 200

@app.route('/viewer', methods=['GET'])
@app.route('/realtime', methods=['GET'])
def realtime_viewer():
    """实时截图查看器页面【0108新增实时截图功能】"""
    try:
        # 读取HTML模板文件
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(project_root, 'main', 'templates', 'realtime_viewer.html')
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            return html_content, 200, {'Content-Type': 'text/html; charset=utf-8'}
        else:
            # 如果模板文件不存在，返回一个简单的内联HTML
            return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>iPad屏幕查看器 - 实时监控</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .controls { margin: 20px 0; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 4px; cursor: pointer; }
        .btn-primary { background: #007bff; color: white; }
        .screenshot { max-width: 100%; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 iPad屏幕查看器 - 实时监控</h1>
        <div class="controls">
            <label>刷新间隔（秒）: <input type="number" id="interval" value="2" min="1"></label>
            <button class="btn btn-primary" onclick="start()">开始监控</button>
            <button class="btn" onclick="stop()">停止</button>
            <button class="btn" onclick="refresh()">立即刷新</button>
        </div>
        <div id="status">状态: 未连接</div>
        <div id="screenshot-container">
            <img id="screenshot" class="screenshot" style="display:none;">
            <div id="placeholder">等待截图上传...</div>
        </div>
    </div>
    <script>
        let timer = null;
        const apiBase = window.location.origin;
        function refresh() {
            const img = document.getElementById('screenshot');
            const placeholder = document.getElementById('placeholder');
            fetch(apiBase + '/api/screenshot/latest?t=' + Date.now())
                .then(r => r.ok ? r.blob() : null)
                .then(blob => {
                    if (blob) {
                        img.src = URL.createObjectURL(blob);
                        img.style.display = 'block';
                        placeholder.style.display = 'none';
                        document.getElementById('status').textContent = '状态: 已连接';
                    } else {
                        img.style.display = 'none';
                        placeholder.style.display = 'block';
                        document.getElementById('status').textContent = '状态: 暂无截图';
                    }
                })
                .catch(e => {
                    document.getElementById('status').textContent = '状态: 错误 - ' + e.message;
                });
        }
        function start() {
            const interval = parseInt(document.getElementById('interval').value) * 1000;
            refresh();
            timer = setInterval(refresh, interval);
        }
        function stop() {
            if (timer) clearInterval(timer);
            timer = null;
        }
        window.onload = () => setTimeout(start, 1000);
    </script>
</body>
</html>
            """, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({'error': f'加载查看器页面失败: {str(e)}'}), 500

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ruby Eve UI Test API Server')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    parser.add_argument('--port', type=int, default=8005, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 启动时加载历史任务
    load_tasks()
    
    print(f"🚀 启动 Ruby Eve UI Test API 服务")
    print(f"📍 地址: http://{args.host}:{args.port}")
    
    # 显示自动下载功能状态
    print(f"📦 自动下载功能状态:")
    if DOWNLOAD_AVAILABLE:
        print(f"   ✅ 下载模块: 可用")
        if PROTOBUF_AVAILABLE:
            print(f"   ✅ Protobuf: 可用 (自动下载功能完全可用)")
        else:
            print(f"   ❌ Protobuf: 不可用 (需要安装 protobuf 库并编译 proto 文件)")
            print(f"      安装步骤:")
            print(f"      1. pip install protobuf")
            print(f"      2. cd utils/ci_download && protoc --python_out=. omnibus_connect_builds.proto")
    else:
        print(f"   ❌ 下载模块: 不可用")
    
    print(f"📖 API 文档:")
    print(f"   POST /api/test/run - 执行测试")
    print(f"   GET  /api/test/status/<task_id> - 查询任务状态")
    print(f"   GET  /api/test/status/<task_id>?include_log=true - 查询任务状态（包含日志内容）")
    print(f"   GET  /api/test/result/<task_id> - 获取任务执行结果汇总")
    print(f"   GET  /api/test/log/<task_id> - 获取任务日志内容")
    print(f"   GET  /api/test/list - 列出正在执行的任务（默认）")
    print(f"   GET  /api/test/list?status=all - 列出所有任务（包括历史）")
    print(f"   POST /api/test/cancel/<task_id> - 取消任务")
    print(f"   GET  /api/devices - 列出所有设备")
    print(f"   GET  /api/health - 健康检查")
    print(f"   POST /api/upload - 上传实时截图（监控模式）【0108新增实时截图功能】")
    print(f"   GET  /api/screenshot/latest - 获取最新截图【0108新增实时截图功能】")
    print(f"   GET  /api/screenshot/info - 获取最新截图信息【0108新增实时截图功能】")
    print(f"   GET  /viewer 或 /realtime - 实时截图查看器（Web界面）【0108新增实时截图功能】")
    print(f"📝 日志文件保存在: logs/ 目录下，按 task_id 命名")
    print(f"📸 实时截图查看器: http://{args.host}:{args.port}/viewer")
    
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

