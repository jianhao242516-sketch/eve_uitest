# _*_ coding: utf-8 _*_
"""
______________________________________________
project Name : app-ui
File Name : handle_request
Description :
Author : wendy
date : 2025/11/28
______________________________________________

"""
from api_scripts._config import get_resolved_default_data, global_data
from api_scripts._request import send_request


def with_default_data(auto_send=True):
    def decorator(func):
        def wrapper(*args, **kwargs):
            data = get_resolved_default_data()
            result = func(data, *args, **kwargs)
            if auto_send:
                send_request(data)
            return data  # 始终返回 data 给调用者
        return wrapper
    return decorator


@with_default_data(auto_send=False)
def update_module_data(data, modules_with_switch, saas_type=None):
    """
    功能开关
    modules_with_switch={'login_qr_code': 1/0 ...}
    saas_type = [1,2,3]
    """
    # 主模块 -> saas模块 映射
    saas_mapping = {
        "predict_eve": "predict_eve_saas",
        "predict": "predict_saas",
        "skin_baseline_eve": "skin_baseline_eve_saas",
        "skin_baseline_eve20": "skin_baseline_eve20_saas"
    }
    # enable_saas = not (isinstance(saas_type, list) and len(saas_type) == 0)
    enable_saas = isinstance(saas_type, list) and len(saas_type) > 0

    if modules_with_switch:
        for module, switch in modules_with_switch.items():
            if switch == 0:
                # 删除主模块
                keys_to_delete = [k for k, v in data.items() if v == module]
                for k in keys_to_delete:
                    del data[k]
                # 删除saas模块
                if module in saas_mapping:
                    saas = saas_mapping[module]
                    keys_to_delete = [k for k in data.keys() if k.startswith(saas + '[')]
                    for k in keys_to_delete:
                        del data[k]

                continue
            # 添加主模块
            exists = any(v == module for v in data.values())
            if not exists:
                module_keys = [k for k in data.keys() if k.startswith('module[')]
                indices = [int(k[k.find('[') + 1:k.find(']')]) for k in module_keys]
                next_index = max(indices) + 1 if indices else 1
                data[f'module[{next_index}]'] = module

            # 添加saas版本
            if enable_saas and module in saas_mapping and saas_type:
                saas = saas_mapping[module]

                old_keys = [k for k in data.keys() if k.startswith(saas + '[')]
                for k in old_keys:
                    del data[k]

                for i, val in enumerate(saas_type):
                    data[f"{saas}[{i}]"] = str(val)

    return data


def update_module(modules_with_switch, saas_type=None):
    """
    功能开关
    :param modules_with_switch:  login_qr_code: 扫码注册登录, skin_age_switch: 宜肤M显示肤龄开关,
                                illustrate_eve: 宜肤M图解功能, illustrate_eve20: 宜肤V图解功能
                                report_face_show: 宜肤M报告页默认展示3D图像, report_face_show_eve20: 宜肤V报告页默认展示3D图像
                                predict_eve： 宜肤M肤况预测， predict: 宜肤V肤况预测
                                predict_eve_saas
                                predict_saas
                                skin_baseline_eve: 宜肤M皮肤基准线, skin_baseline_eve20: 宜肤V皮肤基准线
                                skin_baseline_eve_saas
                                skin_baseline_eve20_saas
                                skin_beauty_plan: 宜肤M美肤方案入口, skin_beauty_plan_eve20: 宜肤V美肤方案入口
                                collect_preview_pic_eve20: 拍后预览（仅采集模式）
                                offline_eve20:支持离线模式
    :param saas_type: 1-基础版本 2-高阶版 3-旗舰版
    :return:
    """
    data = update_module_data(modules_with_switch, saas_type)
    return send_request(data)


def update_login_qr_code(switch):
    """
    扫码注册/登录
    :param switch: 0 关闭、 1 开启微信码、 2 开启普通码、 3 line码[非中国服务器]
    :return:
    """
    # global global_data
    data = get_resolved_default_data()
    if switch == 0:
        keys_to_delete = [k for k, v in data.items() if v == 'login_qr_code']
        for k in keys_to_delete:
            del data[k]
        return send_request(data)
    else:
        exists = any(v == 'login_qr_code' for v in data.values())
        if not exists:
            module_keys = [k for k in data.keys() if k.startswith('module[')]
            indices = [int(k[k.find('[') + 1:k.find(']')]) for k in module_keys]
            next_index = max(indices) + 1 if indices else 1
            data[f'module[{next_index}]'] = 'login_qr_code'
        if switch == 1:
            data['login_qr_code'] = 1
            return send_request(data)
        elif switch == 2:
            data['login_qr_code'] = 2
            return send_request(data)


@with_default_data(auto_send=False)
def map_user_login_type(data, app, user_login_type, anonymous_types=None):
    """
    userLoginTypeArrEve: list[int]  前端开关状态 [2, 1]
    anonymous_types: list 子选项（可选）
    """
    for idx, val in enumerate(user_login_type):
        data[f"new_store_business_config[{app}][{idx}]"] = str(val)
        data[f"{app}[{idx}]"] = str(val)

    anonymous_saas_prefix = ''
    if app == 'user_login_type_eve':
        anonymous_saas_prefix = 'anonymous_login_type_eve_saas'
    elif app == 'user_login_type_eve20':
        anonymous_saas_prefix = 'anonymous_login_type_eve20_saas'

    # 匿名模式下才传子选项
    if 1 in user_login_type and anonymous_types:
        # 清空原有子选项
        keys_to_remove = [k for k in data if k.startswith(anonymous_saas_prefix + "[")]
        for k in keys_to_remove:
            data.pop(k)

        for idx, val in enumerate(anonymous_types):
            data[f"{anonymous_saas_prefix}[{idx}]"] = str(val)
    else:
        # 如果匿名模式没开或没有传入子选项，清空
        keys_to_remove = [k for k in data if k.startswith(anonymous_saas_prefix + "[")]
        for k in keys_to_remove:
            data.pop(k)

    return data


def update_login_mode(app, user_login_type, anonymous_types=None):
    """
    登录模式切换
    :param app:user_login_type_eve、user_login_type_eve20
    :param user_login_type: [1,2] 注册匿名都开， [1]只开匿名模式， [2]只开注册模式，至少传一个模式，不能为空
    :param anonymous_types:[1, 2, 3]代表基础版/高阶版/旗舰版，看需求开
    :return:
    """
    data = map_user_login_type(app, user_login_type, anonymous_types)
    return send_request(data)


@with_default_data(auto_send=True)
def update_dimension(data, app, dimensions_with_switch):
    """
    检测维度开关
    :param data:
    :param app: eve、eve20
    :param dimensions_with_switch: pore、blackhead、speckle、wrinkle、acne、black_rim_of_eye、
                                   sensitive、oil、water、skin_glow、scar、eye_bags、eye_sagging、
                                   plump_cheeks、low_cheek、mandible_edge、
                                   forehead_wrinkle、frown_wrinkle、crows_feet、under_eye_wrinkle、
                                   lacrimal_groove、nasolabial_folds、narionette_lines、neck_lines
    :return:
    """
    for dimension, switch in dimensions_with_switch.items():
        data[f'dimensions[{app}][{dimension}]'] = switch


@with_default_data(auto_send=True)
def update_skin_age(data, app, switch):
    """
    肤龄模式切换
    :param data:
    :param app:eve、 eve20
    :param switch: 0 感官肤龄 1 基准线肤龄
    :return:
    """
    if app == 'eve':
        update_module_data({'skin_age_switch': 1})
    data[f'module_ext[{app}][skin_age_type][value]'] = switch


def update_saas(app, saas_switch, saas_type=None):
    """
    更新报告页配置-综合分析页、维度解读页
    「显示3D图像入口」关闭时，「报告页默认展示3D图像」需要关闭
    :param app: eve、 eve20
    :param saas_switch: {'saas_skin_color': 0}
                        0 关闭, 1 开启
                        'saas_skin_color': 肤色, 'saas_skin_type': 肤质, 'saas_skin_state': 皮肤状态, 'saas_skin_diagnose':皮肤诊断
                        'saas_skin_report': 获取电子报告, 'saas_section': 3D切片, 'saas_light_contrast': 光源对比, 'saas_dimension_degree_analysis': 维度程度分析
                        'saas_reason': 原因分析, 'saas_suggest': 护理建议, 'saas_single_recommend_goods': 单维度推荐-护肤产品, 'saas_single_recommend_treatment': 单维度推荐-美肤疗程
                        'saas_show_3d_entrance': 显示3D图像入口, 'speckle_class_3d_switch': 色斑分类（仅2.0，仅3D时展示分类）, 'acne_class_3d_switch': 痤疮分类（仅2.0，仅3D时展示分类）
                        'saas_skin_contrast': 历史对比, [saas_skin_contrast][saas]: saas版本
                        'saas_print_report': 打印报告, [saas_print_report][saas]: saas版本
                        saas_create_skin_beauty_plan: 创建美肤方案, [saas_create_skin_beauty_plan][saas]: saas版本
                        saas_skin_image_enhancement:画质提升、 saas_edit_3d: 3D模拟编辑
    :param saas_type: 1-基础版, 2-高阶版, 3-旗舰版

    :return:
    """
    global global_data
    data = get_resolved_default_data()
    saas_prefix_mapping = {
        "saas_skin_contrast": "[saas_skin_contrast][saas]",
        "saas_print_report": "[saas_print_report][saas]",
        "saas_create_skin_beauty_plan": "[saas_create_skin_beauty_plan][saas]"
    }
    enable_saas = not (isinstance(saas_type, list) and len(saas_type) == 0)

    for saas, switch in saas_switch.items():
        data[f'module_ext[{app}][{saas}][value]'] = switch
        if switch == 0:
            # 删除saas版本
            if saas in saas_prefix_mapping:
                saas_prefix = saas_prefix_mapping[saas]
                saas_prefix = f'module_ext[{app}]' + saas_prefix
                keys_to_delete = [k for k in data.keys() if k.startswith(saas_prefix + '[')]
                for k in keys_to_delete:
                    del data[k]
        else:
            # 添加saas
            if enable_saas and saas in saas_prefix_mapping and saas_type:
                saas_prefix = saas_prefix_mapping[saas]
                saas_prefix = f'module_ext[{app}]' + saas_prefix
                old_keys = [k for k in data.keys() if k.startswith(saas_prefix + '[')]
                for k in old_keys:
                    del data[k]

                for i, val in enumerate(saas_type):
                    data[f'{saas_prefix}[{i}]'] = str(val)
    return send_request(data)


@with_default_data(auto_send=True)
def update_app_mode(data, app_mode, app_mode_video_collect=0, collect_preview_pic_eve20=0):
    """
    APP模式
    :param data
    :param app_mode: 1 常规模式, 2 视频采集模式
    :param app_mode_video_collect: 1 开启视频录制、 0 关闭视频录制
    :param collect_preview_pic_eve20: 1 开启 0 关闭
    :return:
    """
    data['app_mode'] = app_mode
    if app_mode == 2:
        update_module_data({'collect_preview_pic_eve20': collect_preview_pic_eve20})
        data['app_mode_video_collect'] = app_mode_video_collect
    else:
        data['app_mode_video_collect'] = 0
    # return send_request(data)


@with_default_data(auto_send=True)
def update_app_theme(data, switch, theme_id=None):
    """
    修改APP主题
    :param data:
    :param switch: 0 科技风、 1 高级简约风格
    :param theme_id: app主题json配置查看对应的ID 7302877426951156137:通用深色json、7302243609567578894:通用浅色json
    :return:
    """
    data['module_ext[eve20][app_theme][value]'] = switch
    if switch == 1:
        data['merchant_app_theme_id_map[eve20][]'] = theme_id


@with_default_data(auto_send=True)
def update_store_grant_type(data, grant_type=1, grant_limit_count=20, sasa_type=1):
    """
    修改统一授权saas版本-基础版、高阶版、旗舰版
    :param data:
    :param grant_type: new_store_business_config[grant_type]:1 统一授权、 :2 门店独立授权
    :param grant_limit_count: 授权数
    :param sasa_type: saas版本
    :return:
    """
    data['new_store_business_config[grant_type]'] = grant_type
    data['new_store_business_config[grant_limit_count]'] = grant_limit_count
    data['new_store_business_config[type]'] = sasa_type


def update_shoot_support(shoot_type_switch, shoot_pic_type_switch=None):
    """
    修改宜肤M、V拍摄辅助开关: 1 开启、0 关闭
    :param shoot_type_switch: {'last_shoot_pic_eve20': 1/0}
                       shoot_eyes_open_eve20: 睁眼拍摄、
                       last_shoot_pic_eve20: 宜肤V开启上次拍摄图像、face_area_eve20:人脸最佳取景范围、face_points_eve20:人脸点、mid_line_eve20: 中线
                       last_shoot_pic_eve:宜肤M开启上次拍摄图像、face_area_eve:人脸最佳取景范围、face_points_eve：人脸点、mid_line_eve：中线、
    :param shoot_pic_type_switch: { last_shoot_pic_first_eve20: 1/0}
                         last_shoot_pic_first_eve20: 首次拍摄图像、last_shoot_pic_last_eve20: 上次拍摄图像
    :return:
    """
    data = update_module_data(shoot_type_switch)
    for shoot_type, switch in shoot_type_switch.items():
        if shoot_type == 'last_shoot_pic_eve20' and switch == 1:
            data = update_module_data(shoot_pic_type_switch)
    send_request(data)


@with_default_data(auto_send=True)
def update_common_function(data, function_with_switch):
    """
    切换通用功能开关
    :param data:
    :param function_with_switch:usb_debug: USB调试模式（M/V）、smart_connection:使用智慧连线模式、
                                           saas_change_logo:更换Logo、
                                           eve_self_service_mode:宜肤M自助模式、eve_self_service_finish_page: 0-检测完成页，1-报告页
                                           eve20_self_service_mode:宜肤V自助模式、eve20_self_service_finish_page: 0-检测完成页，1-报告页
    :return:
    """
    for function, switch in function_with_switch.items():
        data[function] = switch


@with_default_data(auto_send=True)
def update_page_mode(data, mode, default_mode):
    """
    修改宜肤页面模式
    :param data
    :param mode: 页面模式-0 专业模式、1 经典模式、2 经典模式-无肤龄
    :param default_mode:默认模式
    :return:
    """
    # remove_values = [v for v in [0, 1, 2] if v not in mode]
    keys_to_delete = []
    for key, val in data.items():
        if key.startswith('page_mode_lists'):
            keys_to_delete.append(key)

    for key in keys_to_delete:
        del data[key]

    for idx, val in enumerate(mode):
        data[f'page_mode_lists[{idx}]'] = str(val)
    data['show_model'] = default_mode

#2025-12-09 新增
@with_default_data(auto_send=True)
def update_module_ext_common(data, module_ext_common, saas_type=[1, 2, 3]):
    """
    切换以module[ext_common]参数名开头的功能
    :param data:
    :param module_ext_common:saas_change_logo:首页logo、usb_debug:USB调试模式（M/V）、
                                      smart_connection:使用智慧连线模式、customize_questionnaire:自定义问卷
    :param saas_type:saas版本[1,2,3]

    :return:
    """
    saas_prefix_mapping = {
        "saas_change_logo": "[saas_change_logo][saas]",
    }
    enable_saas = not (isinstance(saas_type, list) and len(saas_type) == 0)
    for ext_common, switch in module_ext_common.items():
        data[f'module_ext[common][{ext_common}][value]'] = switch
        if switch == 1:
            if enable_saas and ext_common in saas_prefix_mapping and saas_type:
                saas_prefix = 'module_ext[common]' + saas_prefix_mapping[ext_common]
                for i, val in enumerate(saas_type):
                    data[f'{saas_prefix}[{i}]'] = str(val)

#2025-12-09 新增
@with_default_data(auto_send=True)
def update_staff_management(data, switch):
    """
    店员管理开关
    :param data:
    :param bid
    :param switch:
    :return:
    """
    bid = '6841574584163268059'
    if switch == 0:
        keys_to_delete = [k for k, v in data.items() if v == bid]
        for k in keys_to_delete:
            del data[k]
    else:
        # 添加主模块
        exists = any(v == bid for v in data.values())
        if not exists:
            bid_keys = [k for k in data.keys() if k.startswith('business_ids[')]
            indices = [int(k[k.find('[') + 1:k.find(']')]) for k in bid_keys]
            next_index = max(indices) + 1 if indices else 1
            data[f'business_ids[{next_index}]'] = bid
            data['employee_manage_config[enable_single]'] = 1
            data['employee_manage_config[enable_pro]'] = 1
            data['employee_manage_config[enable_ultimate]'] = 1


if __name__ == '__main__':

    # update_login_mode('user_login_type_eve', [1, 2], [1, 3])
    # update_module({'skin_age_switch': 0})
    # update_login_qr_code(0) #0、1、2、3
    # update_login_qr_code(1)
    # update_store_grant_type(sasa_type=1)
    # update_store_grant_type(sasa_type=2)
    update_login_mode('user_login_type_eve',[1], [1,2,3])
    # update_login_mode('user_login_type_eve',[2])
    # update_app_mode(app_mode=1)
    # update_dimension('eve20', {'pore': 0})
    # update_skin_age('eve20', 1)
    # update_saas('eve', {'saas_skin_report': 0})
    # update_app_theme(1, 7302
    # 243609567578894)
    # update_store_grant_type(sasa_type=1)
    # update_shoot_support({'face_area_eve20': 1})
    # update_common_function({'eve_self_service_mode': 1, 'eve_self_service_finish_page': 0})
    # update_saas('eve', {'saas_skin_color': 0})
    # update_page_mode([0, 1, 2], 2)
    

#python -m api_scripts.handle_switch