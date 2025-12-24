#!/usr/bin/env python3
"""api_server.py - Ruby Eve UI Test API 服务"""
from flask import Flask, request, jsonify
import yaml
import threading
import uuid
import time
import os
from datetime import datetime
from main.device_executor import run_case_on_device
from utils.logger import Logger

app = Flask(__name__)

# 存储任务状态和结果
tasks = {}
tasks_lock = threading.Lock()

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
                
                # 如果不是最后一次执行，等待一下
                if run_number < times:
                    logger.log(f"⏳ 等待5秒后进行下一次执行...")
                    time.sleep(5)
                    
            except Exception as e:
                logger.log(f"第 {run_number}/{times} 次执行出错: {e}")
                # 继续执行下一次，不中断整个任务
                continue
        
        # 清理临时文件
        try:
            os.remove(results_file)
        except:
            pass
        
        # 更新任务状态
        with tasks_lock:
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
        
        logger.log(f"测试任务完成: {task_id}, 执行 {times} 次, 总通过: {total_passed}, 总失败: {total_failed}")
        
    except Exception as e:
        logger.log(f"测试执行出错: {e}")
        with tasks_lock:
            tasks[task_id]['status'] = 'failed'
            tasks[task_id]['end_time'] = datetime.now().isoformat()
            tasks[task_id]['error'] = str(e)

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
        
        # 处理 app_path：
        # 在分布式部署中（appium_host 是远程 IP），app_path 必须是 Appium 机器上的绝对路径
        # 在本地部署中（appium_host 是 127.0.0.1），相对路径可以转换为服务器路径
        if app_path:
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
        
        # 在后台线程中执行测试
        thread = threading.Thread(
            target=execute_test,
            args=(task_id, device_info, bundle_id, test_file, app_path, reinstall, times, test_device_name, case_filters)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': f'测试任务已创建，正在执行中（将执行 {times} 次）',
            'status_url': f'/api/test/status/{task_id}'
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'创建测试任务失败: {str(e)}'}), 500

@app.route('/api/test/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询任务状态"""
    with tasks_lock:
        task = tasks.get(task_id)
    
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
    """列出所有任务"""
    with tasks_lock:
        task_list = list(tasks.values())
    
    # 按创建时间倒序排列
    task_list.sort(key=lambda x: x.get('create_time', ''), reverse=True)
    
    # 限制返回最近 50 个任务
    return jsonify({
        'total': len(task_list),
        'tasks': task_list[:50]
    }), 200

@app.route('/api/test/log/<task_id>', methods=['GET'])
def get_task_log(task_id):
    """获取任务的日志内容"""
    with tasks_lock:
        task = tasks.get(task_id)
    
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

@app.route('/api/test/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """取消任务（仅标记，无法真正停止正在运行的任务）"""
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        if task['status'] in ['completed', 'failed']:
            return jsonify({'error': '任务已完成，无法取消'}), 400
        
        task['status'] = 'cancelled'
        task['end_time'] = datetime.now().isoformat()
    
    return jsonify({'success': True, 'message': '任务已标记为取消'}), 200

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'Ruby Eve UI Test API',
        'timestamp': datetime.now().isoformat()
    }), 200

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

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Ruby Eve UI Test API Server')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    parser.add_argument('--port', type=int, default=8005, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    print(f"🚀 启动 Ruby Eve UI Test API 服务")
    print(f"📍 地址: http://{args.host}:{args.port}")
    print(f"📖 API 文档:")
    print(f"   POST /api/test/run - 执行测试")
    print(f"   GET  /api/test/status/<task_id> - 查询任务状态")
    print(f"   GET  /api/test/status/<task_id>?include_log=true - 查询任务状态（包含日志内容）")
    print(f"   GET  /api/test/log/<task_id> - 获取任务日志内容")
    print(f"   GET  /api/test/list - 列出所有任务")
    print(f"   POST /api/test/cancel/<task_id> - 取消任务")
    print(f"   GET  /api/devices - 列出所有设备")
    print(f"   GET  /api/health - 健康检查")
    print(f"📝 日志文件保存在: logs/ 目录下，按 task_id 命名")
    
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)

