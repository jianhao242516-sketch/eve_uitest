# _*_ coding: utf-8 _*_
"""
______________________________________________
project Name : app-ui
File Name : api_pre
Description :
Author : wendy
date : 2025/11/28
______________________________________________

"""
from copy import deepcopy

config = {
        'merchant_id': '7056154316203392273',
        'cookie': "_ga=GA1.1.1378342279.1698819484; _fbp=fb.1.1756286971685.264241572382785875; MUSID=4353c9110f18742a357728245c655020",
        'base_url': 'http://preadmin.eve.meitu.com',
        'default_data': {
        'id': '{merchant_id}',
        'business_ids[0]': '1', 'business_ids[1]': '5', 'business_ids[2]': '7', 'business_ids[3]': '9',
        'business_ids[4]': '13',
        'business_ids[6]': '6841574584163268059',
        'business_ids[7]': '6876052284567210305', 'business_ids[8]': '6907928640347204045',
        'business_ids[9]': '6998911853185493661', 'business_ids[10]': '7233777050184866407',
        # 'business_ids[5]': '6753200267484791809',

        'new_store_business_config[merchant_id]': '{merchant_id}', 'new_store_business_config[able]': '1',
        'new_store_business_config[type]': '2', 'new_store_business_config[data_style]': '1',
        'new_store_business_config[single_start_time]': '2025-11-27',
        'new_store_business_config[single_end_time]': '2035-11-27',
        'new_store_business_config[pro_start_time]': '2025-11-27',
        'new_store_business_config[pro_end_time]': '2026-11-27',
        'new_store_business_config[ultimate_start_time]': '2025-11-27',
        'new_store_business_config[ultimate_end_time]': '2026-11-27',
        'new_store_business_config[grant_type]': '1',
        'new_store_business_config[grant_limit_count]': '20', 'new_store_business_config[pro_overdue_rule]': '1',
        'new_store_business_config[pro_overdue_use_single_days]': '3285', 'new_store_business_config[app_type][0]': '2',
        'new_store_business_config[app_type][1]': '1', 'new_store_business_config[report_limit_type]': '1',
        'new_store_business_config[report_limit_value][1]': '1000',
        'new_store_business_config[report_limit_value][2]': '5000',
        'new_store_business_config[report_limit_value][3]': '10000',
        'new_store_business_config[store_login_limit]': '0',
        'new_store_business_config[ba_login_limit]': '0', 'new_store_business_config[ba_gps_limit]': '0',
        'new_store_business_config[user_login_type_eve][0]': '2',  # 注册模式开启为2
        # 'new_store_business_config[user_login_type_eve][1]': '1',  # 匿名模式为1
        'new_store_business_config[user_login_type_eve20][0]': '2',
        'new_store_business_config[user_login_type_eve20][1]': '1',
        'new_store_business_config[years]': '9',
        'new_store_business_config[days]': '0',

        'app_type[0]': '2', 'app_type[1]': '1',
        'user_login_type_eve[0]': '2',
        # 'user_login_type_eve[1]': '1',
        'anonymous_login_type_eve_saas[0]': 1,
        'anonymous_login_type_eve_saas[1]': 2,
        'anonymous_login_type_eve_saas[2]': 3,

        'user_login_type_eve20[0]': '2',
        'sdk_area_limit': '0',

        'module[1]': 'report_face_show', 'module[2]': 'skin_beauty_plan_eve20', 'module[3]': 'show_theme_color_switch',
        'module[4]': 'predict', 'module[5]': 'predict_eve', 'module[6]': 'treatment_eve20', 'module[7]': 'case_lib',
        'module[8]': 'illustrate_eve', 'module[9]': 'illustrate_eve20', 'module[10]': 'skin_baseline_eve20',
        'module[11]': '3d_landscaping_entrance_eve20', 'module[12]': 'shoot_eyes_open_eve20',
        'module[13]': 'skin_age_switch', 'module[14]': 'login_qr_code',

        'module_ext[common][saas_change_logo][value]': '0',
        'module_ext[common][saas_multi_skin_picture_contrast][value]': '0', 'module_ext[common][usb_debug][value]': '0',
        'module_ext[common][smart_connection][value]': '0', 'module_ext[common][saas_store_data_transfer][value]': '0',
        'module_ext[common][customize_questionnaire][value]': '0', 'module_ext[common][report_period][value]': '0',

        # 宜肤M检测维度开关
        'dimensions[eve][scar]': '1',
        'dimensions[eve][skin_texture]': '1',
        'dimensions[eve][skin_homogenity]': '1',
        'dimensions[eve][oil]': '1',
        'dimensions[eve][water]': '1',
        'dimensions[eve][skin_glow]': '1',
        'dimensions[eve][sensitive]': '1',
        'dimensions[eve][black_rim_of_eye]': '1',
        'dimensions[eve][acne]': '1',
        'dimensions[eve][wrinkle]': '1',
        'dimensions[eve][speckle]': '1',
        'dimensions[eve][blackhead]': '1',
        'dimensions[eve][pore]': '1',

        'module_ext[eve][skin_age_type][value]': 0,  # 感官肤龄
        'module_ext[eve][saas_skin_color][value]': 1,  # 肤色
        'module_ext[eve][saas_skin_type][value]': 1,  # 肤质
        'module_ext[eve][saas_skin_state][value]': 1,  # 皮肤状态
        'module_ext[eve][saas_skin_diagnose][value]': 1,  # 皮肤诊断

        'module_ext[eve][saas_skin_report][value]': 1,  # m获取电子报告
        'module_ext[eve][saas_section][value]': 1,  # m3d切片
        'module_ext[eve][saas_light_contrast][value]': 1,  # m光源对比
        'module_ext[eve][saas_dimension_degree_analysis][value]': 1,  # m维度程度分析
        'module_ext[eve][saas_reason][value]': 1,  # m原因分析
        'module_ext[eve][saas_suggest][value]': 1,  # m护理建议

        'module_ext[eve20][saas_skin_report][value]': '1', 'module_ext[eve20][saas_section][value]': '1',
        'module_ext[eve20][saas_dimension_degree_analysis][value]': '1', 'module_ext[eve20][saas_reason][value]': '1',
        'module_ext[eve20][saas_suggest][value]': '1', 'module_ext[eve20][saas_single_recommend_goods][value]': '0',
        'module_ext[eve20][saas_single_recommend_treatment][value]': '0',
        'module_ext[eve20][saas_skin_contrast][value]': '1', 'module_ext[eve20][saas_skin_contrast][saas][0]': '2',
        'module_ext[eve20][saas_skin_contrast][saas][1]': '3', 'module_ext[eve20][saas_print_report][value]': '1',
        'module_ext[eve20][saas_print_report][saas][0]': '2', 'module_ext[eve20][saas_print_report][saas][1]': '3',
        'module_ext[eve20][saas_create_skin_beauty_plan][value]': '1',
        'module_ext[eve20][saas_create_skin_beauty_plan][saas][0]': '3',
        'module_ext[eve20][saas_create_skin_beauty_plan][saas][1]': '2',
        'module_ext[eve20][saas_set_home_video][value]': '0', 'module_ext[eve20][saas_change_background][value]': '0',
        'module_ext[eve20][saas_edit_3d][value]': '0', 'module_ext[eve20][report_check][value]': '0',
        'module_ext[eve20][saas_skin_image_enhancement][value]': '0', 'module_ext[eve20][skin_age_type][value]': '0',
        'module_ext[eve20][app_theme][value]': '0', 'module_ext[eve20][sale_log][value]': '0',

        'login_qr_code': 1, 'show_model': '0', 'page_mode_lists[0]': '0', 'page_mode_lists[1]': '1',
        'page_mode_lists[2]': '2', 'show_model_muse': '0',

        'dimensions[eve20][scar]': '0', 'dimensions[eve20][skin_texture]': '0',
        'dimensions[eve20][skin_homogenity]': '0',
        'dimensions[eve20][neck_fine_lines]': '0', 'dimensions[eve20][neck_lines]': '0',
        'dimensions[eve20][dennie_morgan_fold]': '0', 'dimensions[eve20][forehead_fine_line]': '0',
        'dimensions[eve20][under_eye_fine_line]': '0', 'dimensions[eve20][oil]': '0', 'dimensions[eve20][water]': '0',
        'dimensions[eve20][narionette_lines]': '1', 'dimensions[eve20][nasolabial_folds]': '1',
        'dimensions[eve20][lacrimal_groove]': '1', 'dimensions[eve20][under_eye_wrinkle]': '1',
        'dimensions[eve20][crows_feet]': '1', 'dimensions[eve20][frown_wrinkle]': '1',
        'dimensions[eve20][forehead_wrinkle]': '1', 'dimensions[eve20][mandible_edge]': '1',
        'dimensions[eve20][low_cheek]': '1', 'dimensions[eve20][eye_sagging]': '1', 'dimensions[eve20][eye_bags]': '1',
        'dimensions[eve20][skin_glow]': '1', 'dimensions[eve20][wrinkle]': '1', 'dimensions[eve20][plump_cheeks]': '1',
        'dimensions[eve20][sensitive]': '1', 'dimensions[eve20][black_rim_of_eye]': '1', 'dimensions[eve20][acne]': '1',
        'dimensions[eve20][speckle]': '1', 'dimensions[eve20][blackhead]': '1', 'dimensions[eve20][pore]': '1',

        'enable_custom_dimensions': '0', 'enable_custom_suggest': '1', 'enable_nav_degree_tags': '0', 'user': '1',
        'report': '1', 'report_image': '1', 'report_3d': '1', 'report_3d_high': '0', 'report_2d_mask': '1',
        'limit_per_day': '', 'limit_total': '', 'limit_total_begin_at': '', 'limit_total_end_at': '',
        'export_report': '1',
        'export_2d_mask': '0', 'key_await': '0', 'clause_agreement': '0',

        'mobile_skin_mode': '1',
        'employee_manage_config[enable_single]': '0', 'employee_manage_config[enable_pro]': '1',
        'employee_manage_config[enable_ultimate]': '1', 'employee_manage_config[created_at]': '1764153813',
        'employee_manage_config[updated_at]': '1764236202',

        'service_ext_config[enable_adx]': '0', 'service_ext_config[adx_id]': '',
        'service_ext_config[created_at]': '1764153813', 'service_ext_config[updated_at]': '1764236202',
        'service_ext_config[merchant_id]': '{merchant_id}',

        'show_single_url': '0', 'able_modify_timezone': '0', 'case_lib_config[case_of_eve]': '1',
        'case_lib_config[case_of_eve20]': '0', 'case_lib_config[case_of_muse]': '0', 'pad_report_mode': '0',
        'mobile_report_mode': '0', 'eve20_meitukey_device[0]': '1.5', 'meitukey_connect': '0',

        'crm_saas[0]': 1,

        'predict_eve_saas[0]': '2', 'predict_eve_saas[1]': '3',
        'predict_saas[0]': '2', 'predict_saas[1]': '3',
        'treatment_eve20_saas[0]': '2', 'treatment_eve20_saas[1]': '3',
        'skin_baseline_eve20_saas[0]': '2', 'skin_baseline_eve20_saas[1]': '3', 'app_mode': '1',
        'app_mode_video_collect': '0', 'user_multi_face_id_alert': '0', 'line_channel': '1',
        'pad_full_face_mode_type': '1',
        'sdk_full_face_mode_type': '1', 'export_skin_age_prohibited': '0', 'line_grant_from_cdp': '0',
        'sdk_face_show_mode_lists[0]': '0', 'mobile_app_type[0]': '1', 'mobile_face_show_mode_lists[0]': '0',
        'eve_self_service_mode': '0', 'eve_self_service_finish_page': '0', 'eve20_self_service_mode': '0',
        'eve20_self_service_finish_page': '0', 'merchant_app_theme_id_map[eve20][]': '7302877426951156137',

        'employee_manage_config[merchant_id]': '{merchant_id}',
        # 'merchant_app_theme_id_map[eve20]': 7302877426951156137,

    }
}


def update_config(**kwargs):
    """允许外部动态覆盖参数"""
    for k, v in kwargs.items():
        config[k] = v


# 全局请求参数，初始为默认值
global_data = None


def get_resolved_default_data():
    global global_data
    merchant_id = config['merchant_id']
    resolved = {}

    for k, v in config['default_data'].items():
        if isinstance(v, str):
            v = v.replace("{merchant_id}", merchant_id)
        resolved[k] = v

    # 初始化全局 data，只在第一次调用时赋值
    if global_data is None:
        global_data = deepcopy(resolved)

    return global_data
