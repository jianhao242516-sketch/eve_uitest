#!/usr/bin/env python3
"""run_ui.py - Ruby Eve UI Test: 多设备执行（按 devices.yaml 顺序分配端口）"""
import argparse, yaml, time, multiprocessing as mp
from main.device_executor import run_case_on_device
from utils.logger import Logger

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundleId", required=True, help="App 的 bundleId 或 appPackage")
    parser.add_argument("--device", required=True, help="要执行的设备名，多个用逗号分隔")
    parser.add_argument("--test", default="tests/test_ui_flow.yaml", help="YAML 测试用例路径")
    parser.add_argument("--base_port", type=int, default=4723, help="Appium 起始端口")
    parser.add_argument("--devices", default="utils/devices.yaml", help="设备配置文件路径")
    parser.add_argument("--times", type=int, default=1, help="执行次数，默认为1次")
    return parser.parse_args()

def main():
    args = parse_args()
    logger = Logger(prefix='MAIN')
    logger.log('加载设备配置...')

    with open(args.devices, 'r', encoding='utf-8') as f:
        cfg = yaml.safe_load(f)
    all_devices = cfg.get('devices', [])
    if not all_devices:
        logger.log('utils/devices.yaml 未配置 devices，退出。')
        return

    target_names = [d.strip() for d in args.device.split(',') if d.strip()]
    selected_devices = []
    for idx, device in enumerate(all_devices):
        if device.get('name') in target_names:
            assigned_port = args.base_port + idx
            device_info = {
                'name': device.get('name'),
                'udid': device.get('udid'),
                'platformName': device.get('platformName', 'iOS'),
                'appium_port': assigned_port,
                'appium_server': f'http://127.0.0.1:{assigned_port}',
            }
            selected_devices.append(device_info)

    if not selected_devices:
        logger.log(f'未在 devices.yaml 中找到匹配设备: {target_names}')
        return

    # 总体统计
    total_results = {
        'total_runs': 0,
        'total_passed': 0,
        'total_failed': 0,
        'devices': {},
        'run_details': []  # 存储每次执行的详细结果
    }
    
    # 用于收集结果的临时文件
    import tempfile
    import json
    results_file = tempfile.mktemp(suffix='.json')

    logger.log(f'开始执行测试，共执行 {args.times} 次')
    
    for run_number in range(1, args.times + 1):
        logger.log(f'=' * 60)
        logger.log(f'第 {run_number}/{args.times} 次执行开始')
        logger.log(f'=' * 60)
        
        processes = []
        for device_info in selected_devices:
            logger.log(f"准备运行 {device_info['name']}，Appium端口: {device_info['appium_port']}")
            p = mp.Process(target=run_case_on_device, args=(device_info, args.bundleId, args.test, run_number, results_file))
            p.start()
            processes.append(p)
            time.sleep(0.3)

        for p in processes:
            p.join()
        
        logger.log(f'第 {run_number}/{args.times} 次执行完成')
        
        # 这里我们无法直接获取子进程的返回值，所以先简化处理
        # 在实际使用中，可以通过共享内存或文件来传递结果
        
        # 等待一下再进行下一次执行
        if run_number < args.times:
            logger.log('等待5秒后进行下一次执行...')
            time.sleep(5)

    logger.log('=' * 60)
    logger.log('所有执行完成！')
    logger.log('=' * 60)
    
    # 读取并统计结果
    total_passed = 0
    total_failed = 0
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    result = json.loads(line.strip())
                    total_passed += result.get('passed', 0)
                    total_failed += result.get('failed', 0)
    except Exception as e:
        logger.log(f"读取结果文件失败: {e}")
    
    # 输出总体执行结果汇总
    print(f"\n{'='*80}")
    print(f"🎯 测试执行完成汇总")
    print(f"{'='*80}")
    print(f"📊 执行统计:")
    print(f"   🔢 总执行次数: {args.times}")
    print(f"   📱 测试设备: {', '.join([d['name'] for d in selected_devices])}")
    print(f"   📄 测试用例: {args.test}")
    print(f"   ✅ 成功次数: {total_passed}")
    print(f"   ❌ 失败次数: {total_failed}")
    if total_passed + total_failed > 0:
        success_rate = (total_passed / (total_passed + total_failed)) * 100
        print(f"   📈 成功率: {success_rate:.1f}%")
    print(f"{'='*80}")
    print(f"💡 提示: 详细的执行日志请查看日志文件")
    print(f"{'='*80}\n")
    
    # 清理临时文件
    try:
        import os
        os.remove(results_file)
    except:
        pass

if __name__ == '__main__':
    main()
