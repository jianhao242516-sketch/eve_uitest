# 获取最新【测试环境企业包】构建并下载
# 正式环境域名：https://omnibus.meitu-int.com
# 
# 使用的接口：
# 1. GET api/apps/{appUid}/builds - 获取构建列表（只返回成功构建）
# 3. GET api/apps/{appUid}/builds/{buildUid|number}/artifacts - 获取构建产物列表

import requests
import yaml
import os
from datetime import datetime

# 设置 protobuf 实现（解决版本兼容性问题）
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# 尝试导入 protobuf 库和生成的模块
try:
    from google.protobuf.json_format import MessageToDict
    import omnibus_connect_builds_pb2
    PROTOBUF_AVAILABLE = True
except ImportError as e:
    PROTOBUF_AVAILABLE = False
    print(f"警告: protobuf 库或生成的模块未找到: {e}")
    print("请运行: pip3 install protobuf")
    print("然后运行: protoc --python_out=. omnibus_connect_builds.proto")

# 正式环境域名
BASE_URL = "https://omnibus.meitu-int.com"

# 应用UID（默认值）
APP_UID = "ddvdg4xmk9ibn5skh6zxpw882i"

# APP_UID 简写映射
APP_UID_SHORTCUT_MAP = {
    "m": "d5immxtv3bj2p37d3bcvrx5f2e",
    "v": "ddvdg4xmk9ibn5skh6zxpw882i"
}

# Bundle ID 映射
BUNDLE_ID_MAP = {
    "d5immxtv3bj2p37d3bcvrx5f2e": "com.evelabinsight.MTEveEnterprise",
    "ddvdg4xmk9ibn5skh6zxpw882i": "com.evelabinsight.MTKingEnterprise"
}

def get_bundle_id(app_uid):
    """根据 APP_UID 获取对应的 Bundle ID"""
    return BUNDLE_ID_MAP.get(app_uid, None)

def resolve_app_uid(app_uid_or_shortcut):
    """
    解析 APP_UID，支持简写形式
    参数:
        app_uid_or_shortcut: APP_UID 或简写 ('m' 或 'v')
    返回:
        str: 实际的 APP_UID
    """
    # 如果是简写，转换为实际的 APP_UID
    if app_uid_or_shortcut in APP_UID_SHORTCUT_MAP:
        return APP_UID_SHORTCUT_MAP[app_uid_or_shortcut]
    return app_uid_or_shortcut

def parse_protobuf_build(build_data):
    """解析 protobuf 格式的构建数据
    字段映射：
    1: uid (string)
    2: number (int32) - 构建号
    3: appUid (string)
    4: startTime (timestamp)
    5: version (string)
    6: result (enum, 1=SUCCESS)
    7: vcs (object)
    8: buildPlatform (object)
    10: variants/runners
    """
    build = {}
    
    if isinstance(build_data, dict):
        # 解析 protobuf 格式
        if '1' in build_data:
            build['uid'] = build_data['1']
        if '2' in build_data:
            build['number'] = build_data['2']
        if '3' in build_data:
            build['appUid'] = build_data['3']
        if '4' in build_data:
            start_time = build_data['4']
            if isinstance(start_time, dict) and '1' in start_time:
                build['startTime'] = start_time['1']
            else:
                build['startTime'] = start_time
        if '5' in build_data:
            build['version'] = build_data['5']
        if '6' in build_data:
            build['result'] = build_data['6']  # 1=SUCCESS
        if '7' in build_data:
            vcs = build_data['7']
            build['vcs'] = {}
            if isinstance(vcs, dict):
                if '1' in vcs:
                    build['vcs']['commit'] = vcs['1']
                if '2' in vcs:
                    build['vcs']['ref'] = vcs['2']
        if '8' in build_data:
            platform = build_data['8']
            build['buildPlatform'] = {}
            if isinstance(platform, dict):
                if '1' in platform:
                    build['buildPlatform']['buildType'] = platform['1']
                if '2' in platform:
                    build['buildPlatform']['configName'] = platform['2']
        if '10' in build_data:
            build['variants'] = build_data['10']
    else:
        # 如果是标准 JSON 格式，直接返回
        build = build_data
    
    return build

def parse_binary_protobuf(binary_data):
    """解析二进制 protobuf 数据"""
    try:
        # 使用编译好的 protobuf 模块解析
        builds_page = omnibus_connect_builds_pb2.BuildsPage()
        builds_page.ParseFromString(binary_data)
        
        # 转换为字典格式
        parsed_data = MessageToDict(builds_page)
        
        # 转换构建数据格式
        result = {}
        
        # 解析分页信息
        if 'page' in parsed_data:
            result['page'] = {
                'number': parsed_data['page'].get('number', 0),
                'size': parsed_data['page'].get('size', 0),
                'totalElements': parsed_data['page'].get('totalElements', 0),
                'totalPages': parsed_data['page'].get('totalPages', 0)
            }
        
        # 解析构建列表
        if 'content' in parsed_data:
            builds = []
            for build_dict in parsed_data['content']:
                build = {}
                build['uid'] = build_dict.get('uid', '')
                build['number'] = build_dict.get('number', 0)
                build['appUid'] = build_dict.get('appUid', '')
                
                # 解析时间戳
                if 'startTime' in build_dict:
                    start_time = build_dict['startTime']
                    if 'seconds' in start_time:
                        build['startTime'] = start_time['seconds']
                    else:
                        build['startTime'] = start_time
                
                build['version'] = build_dict.get('version', '')
                build['result'] = build_dict.get('result', 0)
                
                # 解析 VCS
                if 'vcs' in build_dict:
                    build['vcs'] = {
                        'commit': build_dict['vcs'].get('commit', ''),
                        'ref': build_dict['vcs'].get('ref', '')
                    }
                
                # 解析构建平台
                if 'buildPlatform' in build_dict:
                    build['buildPlatform'] = {
                        'buildType': build_dict['buildPlatform'].get('buildType', ''),
                        'configName': build_dict['buildPlatform'].get('configName', '')
                    }
                
                builds.append(build)
            
            result['content'] = builds
        
        return result
        
    except Exception as e:
        print(f"二进制 protobuf 解析失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_protobuf_response(data):
    """解析 protobuf 格式的响应数据（JSON 格式的 protobuf，使用数字键）"""
    if isinstance(data, dict):
        # 检查是否是 protobuf 格式（包含数字键）
        if any(str(k).isdigit() for k in data.keys()):
            # 这是 protobuf JSON 格式
            parsed = {}
            
            # 解析 page 信息（如果有）
            if '1' in data:
                page_info = data['1']
                if isinstance(page_info, dict):
                    parsed['page'] = {}
                    if '1' in page_info:  # page number
                        parsed['page']['number'] = page_info['1']
                    if '2' in page_info:  # page size
                        parsed['page']['size'] = page_info['2']
                    if '3' in page_info:  # total elements
                        parsed['page']['totalElements'] = page_info['3']
                    if '4' in page_info:  # total pages
                        parsed['page']['totalPages'] = page_info['4']
            
            # 解析 content（构建列表）
            if '2' in data:
                content = data['2']
                if isinstance(content, list):
                    parsed['content'] = []
                    for build_data in content:
                        build = parse_protobuf_build(build_data)
                        parsed['content'].append(build)
                elif isinstance(content, dict):
                    # 单个构建对象
                    build = parse_protobuf_build(content)
                    parsed['content'] = [build]
            
            return parsed
        else:
            # 标准 JSON 格式，直接返回
            return data
    elif isinstance(data, list):
        # 如果是数组，解析每个元素
        parsed = []
        for item in data:
            if isinstance(item, dict) and any(str(k).isdigit() for k in item.keys()):
                parsed.append(parse_protobuf_build(item))
            else:
                parsed.append(item)
        return {'content': parsed}
    else:
        return data

def get_builds(app_uid, page=0, size=10, sort="number,desc", ref=None, version=None):
    """获取构建列表（只返回成功构建）"""
    url = f"{BASE_URL}/api/apps/{app_uid}/builds"
    params = {
        "page": page,
        "size": size,
        "sort": sort
    }
    
    if ref:
        params["ref"] = ref
    if version:
        params["version"] = version
    
    print(f"正在获取构建列表: {url}")
    print(f"参数: {params}")
    
    try:
        # 添加 Accept 头
        headers = {
            'Accept': '*/*'
        }
        response = requests.get(url, params=params, headers=headers, verify=False)
        response.raise_for_status()
        
        # 检查响应内容类型
        content_type = response.headers.get('Content-Type', '')
        print(f"响应 Content-Type: {content_type}")
        print(f"响应状态码: {response.status_code}")
        
        # 尝试解析 JSON（可能是 JSON 格式的 protobuf）
        try:
            json_data = response.json()
            print(f"\n原始 JSON 响应:")
            print(json_data)
            
            # 解析 protobuf 格式
            parsed_data = parse_protobuf_response(json_data)
            
            print(f"\n解析后的数据:")
            print("=" * 60)
            if isinstance(parsed_data, dict):
                if 'page' in parsed_data:
                    print("分页信息:")
                    page_info = parsed_data['page']
                    print(f"  页码: {page_info.get('number', 'N/A')}")
                    print(f"  每页大小: {page_info.get('size', 'N/A')}")
                    print(f"  总元素数: {page_info.get('totalElements', 'N/A')}")
                    print(f"  总页数: {page_info.get('totalPages', 'N/A')}")
                    print()
                
                if 'content' in parsed_data:
                    builds = parsed_data['content']
                    print(f"构建列表 (共 {len(builds)} 个):")
                    print("-" * 60)
                    for idx, build in enumerate(builds, 1):
                        print(f"\n构建 {idx}:")
                        print(f"  构建UID: {build.get('uid', 'N/A')}")
                        print(f"  构建号: {build.get('number', 'N/A')}")
                        print(f"  应用UID: {build.get('appUid', 'N/A')}")
                        print(f"  版本: {build.get('version', 'N/A')}")
                        result = build.get('result', 'N/A')
                        result_map = {0: 'PENDING', 1: 'SUCCESS', 2: 'FAILURE'}
                        print(f"  结果: {result_map.get(result, result)}")
                        if 'startTime' in build:
                            start_time = build.get('startTime')
                            if start_time:
                                try:
                                    dt = datetime.fromtimestamp(start_time)
                                    print(f"  开始时间: {dt.strftime('%Y-%m-%d %H:%M:%S')} (时间戳: {start_time})")
                                except:
                                    print(f"  开始时间: {start_time}")
                        if 'vcs' in build and build['vcs']:
                            vcs = build['vcs']
                            print(f"  版本控制:")
                            print(f"    Commit: {vcs.get('commit', 'N/A')}")
                            print(f"    Ref: {vcs.get('ref', 'N/A')}")
                        if 'buildPlatform' in build and build['buildPlatform']:
                            platform = build['buildPlatform']
                            print(f"  构建平台:")
                            print(f"    类型: {platform.get('buildType', 'N/A')}")
                            print(f"    配置: {platform.get('configName', 'N/A')}")
                        if 'variants' in build:
                            print(f"  Variants: {build.get('variants', 'N/A')}")
            
            return parsed_data
        except ValueError as json_error:
            # 如果不是 JSON，可能是二进制 protobuf
            print(f"\nJSON 解析失败: {json_error}")
            
            if 'application/x-protobuf' in content_type or 'application/octet-stream' in content_type:
                print("检测到二进制 protobuf 格式")
                
                if not PROTOBUF_AVAILABLE:
                    print("错误: protobuf 库未安装")
                    print("请运行以下命令安装: pip3 install protobuf")
                    print("然后需要编译 proto 文件生成 Python 代码")
                    return None
                
                # 尝试使用 protobuf 解析
                try:
                    parsed_data = parse_binary_protobuf(response.content)
                    
                    # 打印解析后的数据
                    if parsed_data:
                        print(f"\n解析后的数据:")
                        print("=" * 60)
                        if isinstance(parsed_data, dict):
                            if 'page' in parsed_data:
                                print("分页信息:")
                                page_info = parsed_data['page']
                                print(f"  页码: {page_info.get('number', 'N/A')}")
                                print(f"  每页大小: {page_info.get('size', 'N/A')}")
                                print(f"  总元素数: {page_info.get('totalElements', 'N/A')}")
                                print(f"  总页数: {page_info.get('totalPages', 'N/A')}")
                                print()
                            
                            if 'content' in parsed_data:
                                builds = parsed_data['content']
                                print(f"构建列表 (共 {len(builds)} 个):")
                                print("-" * 60)
                                for idx, build in enumerate(builds, 1):
                                    print(f"\n构建 {idx}:")
                                    print(f"  构建UID: {build.get('uid', 'N/A')}")
                                    print(f"  构建号: {build.get('number', 'N/A')}")
                                    print(f"  应用UID: {build.get('appUid', 'N/A')}")
                                    print(f"  版本: {build.get('version', 'N/A')}")
                                    result = build.get('result', 'N/A')
                                    result_map = {0: 'PENDING', 1: 'SUCCESS', 2: 'FAILURE'}
                                    print(f"  结果: {result_map.get(result, result)}")
                                    if 'startTime' in build:
                                        start_time = build.get('startTime')
                                        if start_time:
                                            try:
                                                dt = datetime.fromtimestamp(start_time)
                                                print(f"  开始时间: {dt.strftime('%Y-%m-%d %H:%M:%S')} (时间戳: {start_time})")
                                            except:
                                                print(f"  开始时间: {start_time}")
                                    if 'vcs' in build and build['vcs']:
                                        vcs = build['vcs']
                                        print(f"  版本控制:")
                                        print(f"    Commit: {vcs.get('commit', 'N/A')}")
                                        print(f"    Ref: {vcs.get('ref', 'N/A')}")
                                    if 'buildPlatform' in build and build['buildPlatform']:
                                        platform = build['buildPlatform']
                                        print(f"  构建平台:")
                                        print(f"    类型: {platform.get('buildType', 'N/A')}")
                                        print(f"    配置: {platform.get('configName', 'N/A')}")
                    
                    return parsed_data
                except Exception as pb_error:
                    print(f"protobuf 解析失败: {pb_error}")
                    import traceback
                    traceback.print_exc()
                    print("提示: 需要先编译 proto 文件")
                    print("运行: protoc --python_out=. omnibus_connect_builds.proto")
                    return None
            else:
                print(f"响应内容 (前200字节): {response.content[:200]}")
                print("未知的响应格式")
                return None
            
    except Exception as e:
        print(f"获取构建列表失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_build_artifacts(app_uid, build_uid_or_number):
    """获取构建产物列表（只返回成功构建，可缓存）"""
    # 注意：根据接口文档，这里使用 api/connect/apps 路径
    url = f"{BASE_URL}/api/connect/apps/{app_uid}/builds/{build_uid_or_number}/artifacts"
    
    print(f"\n正在获取构建产物: {url}")
    
    try:
        headers = {
            'Accept': '*/*'
        }
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '')
        print(f"响应 Content-Type: {content_type}")
        print(f"响应状态码: {response.status_code}")
        
        # 尝试解析 JSON
        try:
            json_data = response.json()
            print(f"\n原始 JSON 响应:")
            print(json_data)
            # 如果是 JSON 格式，解析 protobuf JSON
            parsed_data = parse_protobuf_response(json_data)
            return parsed_data
        except ValueError as json_error:
            # 如果不是 JSON，可能是二进制 protobuf
            print(f"\nJSON 解析失败: {json_error}")
            
            if 'application/x-protobuf' in content_type or 'application/octet-stream' in content_type:
                print("检测到二进制 protobuf 格式")
                
                if not PROTOBUF_AVAILABLE:
                    print("错误: protobuf 库未安装")
                    return None
                
                try:
                    # 使用 protobuf 解析
                    artifacts_msg = omnibus_connect_builds_pb2.Artifacts()
                    artifacts_msg.ParseFromString(response.content)
                    
                    # 手动解析产物数据（避免 MessageToDict 对 map 字段的问题）
                    result = {}
                    artifacts = []
                    
                    # 遍历所有 artifact
                    for artifact_msg in artifacts_msg.content:
                        artifact = {}
                        artifact['classifier'] = artifact_msg.classifier
                        artifact['name'] = artifact_msg.name
                        artifact['variant'] = artifact_msg.variant
                        artifact['component'] = artifact_msg.component
                        
                        # 解析文件信息
                        if artifact_msg.HasField('file'):
                            file_msg = artifact_msg.file
                            artifact['file'] = {
                                'url': file_msg.url,
                                'sha1': file_msg.sha1,
                                'name': file_msg.name,
                                'length': file_msg.length
                            }
                        else:
                            artifact['file'] = None
                        
                        # 解析 attributes（map 字段）
                        # 注意：由于编译问题，attributes 可能被编译为 repeated 字段
                        # 暂时跳过 attributes 解析，不影响主要功能（获取文件下载链接）
                        artifact['attributes'] = {}
                        
                        artifacts.append(artifact)
                    
                    result['content'] = artifacts
                    
                    # 打印产物信息
                    # print(f"\n构建产物列表:")
                    # print("=" * 60)
                    if 'content' in result:
                        artifacts = result['content']
                        # print(f"找到 {len(artifacts)} 个构建产物")
                        # print("-" * 60)
                        for idx, artifact in enumerate(artifacts, 1):
                            # print(f"\n产物 {idx}:")
                            # print(f"  类型 (classifier): {artifact.get('classifier', 'N/A')}")
                            # print(f"  名称 (name): {artifact.get('name', 'N/A')}")
                            # print(f"  Variant: {artifact.get('variant', 'N/A')}")
                            # print(f"  组件 (component): {artifact.get('component', 'N/A')}")
                            
                            if 'attributes' in artifact and artifact['attributes']:
                                print(f"  属性: {artifact['attributes']}")
                            
                            if 'file' in artifact and artifact['file']:
                                file_info = artifact['file']
                                file_name = file_info.get('name', 'N/A')
                                is_ipa = file_name.lower().endswith('.ipa')
                                # print(f"  文件信息:")
                                # print(f"    文件名: {file_name} {'[.ipa 文件]' if is_ipa else ''}")
                                file_size = file_info.get('length', 0)
                                # if file_size > 0:
                                #     print(f"    文件大小: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
                                # else:
                                #     print(f"    文件大小: {file_size} bytes")
                                # print(f"    SHA1: {file_info.get('sha1', 'N/A')}")
                                # print(f"    URL: {file_info.get('url', 'N/A')}")
                            else:
                                print(f"  文件信息: 无")
                    
                    return result
                except Exception as pb_error:
                    print(f"protobuf 解析失败: {pb_error}")
                    import traceback
                    traceback.print_exc()
                    return None
            else:
                print(f"响应内容 (前200字节): {response.content[:200]}")
                print("未知的响应格式")
                return None
                
    except Exception as e:
        print(f"获取构建产物失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def is_test_enterprise_package(build, artifact):
    """判断是否是测试环境企业包
    检查条件：
    1. 文件是 .ipa 格式
    2. 构建平台的配置名称包含"测试"和"企业"
    """
    # 检查文件是否是 .ipa
    if 'file' not in artifact or not artifact['file']:
        return False
    
    file_name = artifact['file'].get('name', '')
    if not file_name.lower().endswith('.ipa'):
        return False
    
    # 检查构建平台的配置名称
    if 'buildPlatform' in build and build['buildPlatform']:
        config_name = build['buildPlatform'].get('configName', '')
        # 检查是否同时包含"测试"和"企业"
        if '测试' in config_name and '企业' in config_name:
            return True
    
    # 也可以检查 variant 或其他字段
    variant = artifact.get('variant', '')
    if '测试' in variant and '企业' in variant:
        return True
    
    return False

def download_file(file_url, save_path):
    """下载文件"""
    print(f"\n正在下载文件: {file_url}")
    print(f"保存路径: {save_path}")
    
    try:
        response = requests.get(file_url, stream=True, verify=False)
        response.raise_for_status()
        
        # 确保目录存在
        os.makedirs(os.path.dirname(save_path) if os.path.dirname(save_path) else '.', exist_ok=True)
        
        # 获取文件大小
        total_size = int(response.headers.get('content-length', 0))
        
        # 下载文件
        downloaded = 0
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        # print(f"\r下载进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print(f"\n文件下载完成: {save_path}")
        return True
    except Exception as e:
        print(f"\n下载文件失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def download_test_enterprise_package(app_uid_or_shortcut):
    """
    下载测试环境企业包
    
    参数:
        app_uid_or_shortcut (str): 应用UID 或简写
            - 'm' 代表 'd5immxtv3bj2p37d3bcvrx5f2e'
            - 'v' 代表 'ddvdg4xmk9ibn5skh6zxpw882i'
            - 也可以直接传入完整的 APP_UID
    
    返回:
        dict: {
            'success': bool,  # 是否成功
            'download_dir': str,  # 下载目录路径
            'bundle_id': str,  # Bundle ID
            'build_number': int,  # 构建号
            'files': list  # 下载的文件列表
        }
    """
    # 解析 APP_UID（支持简写）
    app_uid = resolve_app_uid(app_uid_or_shortcut)
    
    print("=" * 60)
    print("获取最新构建并下载")
    print("=" * 60)
    if app_uid_or_shortcut != app_uid:
        print(f"简写: {app_uid_or_shortcut} -> APP_UID: {app_uid}")
    else:
        print(f"应用UID: {app_uid}")
    
    # 获取 Bundle ID
    bundle_id = get_bundle_id(app_uid)
    if not bundle_id:
        print(f"警告: 未找到 APP_UID {app_uid} 对应的 Bundle ID")
        bundle_id = None
    
    # 1. 循环获取构建列表并查找测试环境企业包
    print("\n" + "=" * 60)
    print("开始查找测试环境企业包")
    print("=" * 60)
    
    found_package = False
    target_build = None
    target_artifacts = []
    page = 0
    page_size = 20
    total_checked = 0
    
    while not found_package:
        # 获取当前页的构建列表
        result = get_builds(app_uid, page=page, size=page_size, sort="number,desc")
        if not result:
            print(f"无法获取构建列表（第 {page + 1} 页），退出")
            break
        
        # 提取构建列表
        if isinstance(result, dict) and 'content' in result:
            builds = result['content']
            # 获取分页信息
            if 'page' in result:
                page_info = result['page']
                total_pages = page_info.get('totalPages', 0)
                print(f"总页数: {total_pages}, 当前页: {page + 1}")
        elif isinstance(result, list):
            builds = result
        else:
            builds = []
        
        if not builds:
            print(f"第 {page + 1} 页未找到构建，退出")
            break
        
        # 按构建号排序，从最新开始查找
        builds.sort(key=lambda x: x.get('number', 0), reverse=True)
        
        # 2. 循环查找测试环境企业包
        for build_idx, build in enumerate(builds, 1):
            total_checked += 1
            build_number = build.get('number', 'N/A')
            build_uid = build.get('uid', 'N/A')
            
            print(f"\n检查构建 #{total_checked} (第 {page + 1} 页, {build_idx}/{len(builds)}): 构建号 {build_number}")
            if 'buildPlatform' in build and build['buildPlatform']:
                config_name = build['buildPlatform'].get('configName', 'N/A')
                print(f"  配置: {config_name}")
        
            # 获取构建产物列表
            build_identifier = build.get('number')
            artifacts_result = get_build_artifacts(app_uid, build_identifier)
            
            if not artifacts_result or 'content' not in artifacts_result:
                print(f"  无法获取构建产物，跳过")
                continue
            
            artifacts = artifacts_result['content']
            if not artifacts:
                print(f"  未找到构建产物，跳过")
                continue
            
            # 筛选出测试环境企业包
            test_enterprise_artifacts = []
            for artifact in artifacts:
                if is_test_enterprise_package(build, artifact):
                    test_enterprise_artifacts.append(artifact)
            
            if test_enterprise_artifacts:
                print(f"  ✓ 找到 {len(test_enterprise_artifacts)} 个测试环境企业包！")
                found_package = True
                target_build = build
                target_artifacts = test_enterprise_artifacts
                break
            else:
                print(f"  ✗ 未找到测试环境企业包，继续查找...")
        
        # 如果当前页没找到，继续下一页
        if not found_package:
            page += 1
            if page > 10:  # 限制最多查找 10 页，避免无限循环
                print(f"\n已查找 {page} 页，仍未找到测试环境企业包，退出")
                break
    
    if not found_package:
        print("\n" + "=" * 60)
        print("未找到测试环境企业包，退出")
        print("=" * 60)
        return {
            'success': False,
            'download_dir': None,
            'bundle_id': bundle_id,
            'build_number': None,
            'files': []
        }
    
    # 3. 下载测试环境企业包
    print("\n" + "=" * 60)
    print("开始下载测试环境企业包")
    print("=" * 60)
    print(f"构建号: {target_build.get('number', 'N/A')}")
    print(f"构建UID: {target_build.get('uid', 'N/A')}")
    if 'buildPlatform' in target_build and target_build['buildPlatform']:
        config_name = target_build['buildPlatform'].get('configName', 'N/A')
        print(f"配置: {config_name}")
    print("-" * 60)
    
    for idx, artifact in enumerate(target_artifacts, 1):
        file_info = artifact['file']
        file_name = file_info.get('name', 'N/A')
        file_size = file_info.get('length', 0) / 1024 / 1024
        print(f"{idx}. {file_name} ({file_size:.2f} MB)")
    
    # 创建下载目录
    build_identifier = target_build.get('number')
    download_dir = f"downloads/{app_uid}/build_{build_identifier}_{datetime.now().strftime('%y%m%d_%H%M%S')}"
    os.makedirs(download_dir, exist_ok=True)
    
    downloaded_files = []
    for idx, artifact in enumerate(target_artifacts, 1):
        file_info = artifact['file']
        file_url = file_info.get('url')
        file_name = file_info.get('name', f"artifact_{idx}.ipa")
        
        if file_url:
            # 构建保存路径
            save_path = os.path.join(download_dir, file_name)
            
            # 下载文件
            print(f"\n[{idx}/{len(target_artifacts)}] 正在下载: {file_name}")
            if download_file(file_url, save_path):
                downloaded_files.append(save_path)
            print()  # 换行
    
    # 4. 保存构建信息到YAML
    build_info = {
        'app_uid': app_uid,
        'bundle_id': bundle_id,
        'build': target_build,
        'artifacts': target_artifacts,
        'download_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'downloaded_files': downloaded_files
    }
    
    yaml_filename = os.path.join(download_dir, 'build_info.yaml')
    with open(yaml_filename, 'w', encoding='utf-8') as f:
        yaml.safe_dump(build_info, f, default_flow_style=False, allow_unicode=True)
    
    print("\n" + "=" * 60)
    print("下载完成！")
    print("=" * 60)
    print(f"下载目录: {download_dir}")
    print(f"Bundle ID: {bundle_id}")
    print(f"下载文件数: {len(downloaded_files)}")
    print(f"构建信息已保存到: {yaml_filename}")
    
    return {
        'success': True,
        'download_dir': download_dir,
        'bundle_id': bundle_id,
        'build_number': build_identifier,
        'files': downloaded_files
    }

def main():
    """主函数，使用默认 APP_UID"""
    result = download_test_enterprise_package("m")
    if result['success']:
        print(f"\n成功下载到: {result['download_dir']}")
        print(f"Bundle ID: {result['bundle_id']}")
    else:
        print("\n下载失败")
if __name__ == "__main__":
    main()
