# -*- coding:utf-8 -*-
import os
import json
import xlwt
import logging
import datetime
from flask import request, send_from_directory
from . import report_statistics_blu
from .common import get_date_count, create_results_info
from business import response, constants as cons
from business.utils.decorator import error_handler


# 通报统计查询
@report_statistics_blu.route('/create/results', methods=['POST'])
@error_handler
def get_create_results():
    data = request.get_json(force=True)
    current = data.get('current', 1)
    pageSize = data.get('pageSize', 24)
    start_time = data.get('start_time', "")
    end_time = data.get('end_time', "")
    manual_check_status = int(data.get('manual_check_status', 3))

    # time_total = []
    # err_total = []
    # csector_list = sector_list[current:current + pageSize]
    # csector_list = cons.SECTOR_MAP.keys()[current:current + pageSize]

    # result_data, total = create_results(start_time, end_time, manual_check_status, current=current, pageSize=pageSize)
    result_data, total = get_date_count(start_time, end_time, manual_check_status)

    return response.success_with_pagenation(total, current, pageSize, result_data)


# 导出统计
@report_statistics_blu.route('/get/create/results', methods=['GET'])
@error_handler
def create_results_excel():
    start_time = request.args.get("start_time", "", type=str)
    end_time = request.args.get("end_time", "", type=str)
    manual_check_status = request.args.get('manual_check_status', 3, type=int)

    raw = ["name", "insert_count", "ana_count", "err_count", "m1_count", "m2_count", "m2_p", "recall", "jianchu"]
    raw_c = ['机关', '录入量', '分析量', '疑似错误量', '正片量', '废片量', '准确率', '召回率', '检出率']
    raw_x = ["inserts", "ana_counts", "errs", "m1s", "m2s", "m2_p", "recall", "jianchu"]

    # result_data, _ = create_results(start_time, end_time, manual_check_status, current=None, pageSize=None)
    result_data, total = get_date_count(start_time, end_time, manual_check_status)

    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet('Sheet1', cell_overwrite_ok=True)
    for j in range(len(result_data["result"])):
        for i in range(len(raw)):
            sheet.write(j + 1, i, result_data["result"][j][raw[i]])
            sheet.write(0, i, raw_c[i])

    for q in range(len(raw_x)):
        sheet.write(len(result_data["result"]) + 1, q + 1, result_data[raw_x[q]])

    # 以传递的name+当前日期作为excel名称保存。
    result_images_path = cons.EXCEL_PATH

    file_name = '{}'.format(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

    wbk.save(os.path.join(result_images_path, file_name + '.xls'))

    return send_from_directory(result_images_path, file_name + '.xls', as_attachment=True)


# 导出废片
@report_statistics_blu.route('/get/create/results/info', methods=['GET'])
@error_handler
def create_results_info_excel():
    start_time = request.args.get("start_time", "", type=str)
    end_time = request.args.get("end_time", "", type=str)
    name = request.args.get("name", "", type=str)

    manual_check_status = json.loads(request.args.get("manual_check_status", "[]", type=str))

    result_data, _ = create_results_info(start_time, end_time, name, manual_check_status, current=None, pageSize=None)

    raw = [
        'id',
        'src_record_id',
        'traffic_sector_name',
        'data_entry_person',
        'data_entry_time',
        'src_illegal_action',
        'src_car_plate_number',
        'sdk_car_plate_number',
        'sdk_reason_code',
        'manual_check_status',
    ]
    raw_c = ['id', '违法id', '机关', '录入人', '录入时间', '违法代码', '原车牌', '识别车牌', '识别结果', '审核状态']
    reason_map = {
        0: '正片',
        1: '车牌更正',
        2: '疑似',
        3: '模糊',
        4: '遮挡'
    }
    check_map = {0: '未复审', 1: '正片', 2: '废片'}
    wbk = xlwt.Workbook()
    sheet = wbk.add_sheet('Sheet1', cell_overwrite_ok=True)

    for j in range(len(result_data["result"])):
        for i in range(len(raw)):
            if i == 8:
                data = reason_map.get(result_data["result"][j][raw[i]])
            elif i == 9:
                data = check_map.get(result_data["result"][j][raw[i]])
            else:
                data = result_data["result"][j][raw[i]]
            sheet.write(j + 1, i, data)
            sheet.write(0, i, raw_c[i])
    # 以传递的name+当前日期作为excel名称保存。

    result_images_path = cons.EXCEL_PATH

    name = '{}'.format(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

    wbk.save(os.path.join(result_images_path, name + '.xls'))

    return send_from_directory(result_images_path, name + '.xls', as_attachment=True)


# 疑似错误量 POST
@report_statistics_blu.route('/create/results/info', methods=['POST'])
@error_handler
def get_create_results_info():
    data = request.get_json(force=True)
    current = data.get('current', 1)
    page_size = data.get('pageSize', 24)
    start_time = data.get('start_time', "")
    end_time = data.get('end_time', "")
    name = data.get("name", "")
    manual_check_status = data.get('manual_check_status', [])

    result_data, total = create_results_info(start_time, end_time, name, manual_check_status, current=current, pageSize=page_size)

    return response.success_with_pagenation(total, current, page_size, result_data)
