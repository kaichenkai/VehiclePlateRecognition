# -*- coding:utf-8 -*-
import os
import json
import logging
import zipfile
import flask
import datetime
from io import BytesIO
from sqlalchemy import func
from flask import request, send_from_directory
from PIL import Image
from .common import get_image_path
from . import comparison_results_blu
from business import response
from business.utils.time_func import date_interval, mstime2str
from business.utils.decorator import error_handler
from business import constants as cons
from business import db
from business.models import Wfrecord


# 对比结果查询
@comparison_results_blu.route('/results', methods=['POST'])
@error_handler
def get_results():
    data_dict = request.get_json(force=True)
    current = data_dict.get('current', 1)
    pageSize = data_dict.get('pageSize', 24)
    start_time = data_dict.get('start_time', '')
    end_time = data_dict.get('end_time', '')
    reason_code = data_dict.get('reason_code', [])
    manual_check_status = data_dict.get('manual_check_status', [])
    recog_start_time = int(data_dict.get('recog_start_time', 0))
    recog_end_time = int(data_dict.get('recog_end_time', 0))
    action = str(data_dict.get('action', ''))
    # 审核页面传的参数
    simple = data_dict.get("simple", "")

    # 限制查询时间
    if start_time and end_time:
        day_num = date_interval(start_time, end_time)
        if day_num > cons.QUERY_MAX_INTERVAL:
            return response.invalid(message="最大查询区间为一个月")
    if recog_start_time and recog_end_time:
        recog_day_num = date_interval(mstime2str(recog_start_time), mstime2str(recog_end_time))
        if recog_day_num > cons.QUERY_MAX_INTERVAL:
            return response.invalid(message="最大查询区间为一个月")
    #

    # records, total = model_manager.wfrecord.search(filter_params, offset=current, limit=pageSize)

    # 总的查询集
    query = db.session.query(Wfrecord.id, Wfrecord.src_record_id, Wfrecord.src_car_plate_type,
                             Wfrecord.src_car_plate_number, Wfrecord.sdk_car_plate_number,
                             Wfrecord.sdk_car_plate_type, Wfrecord.sdk_reason_code,
                             Wfrecord.data_entry_time, Wfrecord.car_num_pic_url, Wfrecord.car_num_pic_path,
                             Wfrecord.sdk_plate_rect, Wfrecord.manual_check_status,
                             Wfrecord.src_illegal_action, Wfrecord.sdk_recog_time, Wfrecord.recog_data)\
                      .filter(Wfrecord.check_status == 2)
    # .filter(Wfrecord.sdk_reason_code>0)\
    # .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number)

    if not cons.NO_CAR_DISPLAY:
        query = query.filter(Wfrecord.sdk_reason_code > 0) \
            .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number)
    # id 的查询集
    s_query = db.session.query(Wfrecord.id).filter(Wfrecord.check_status != 0)

    # 过滤查询时间
    if start_time and end_time:
        query = query \
            .filter(Wfrecord.data_entry_time >= start_time) \
            .filter(Wfrecord.data_entry_time <= end_time)
        s_query = s_query \
            .filter(Wfrecord.data_entry_time >= start_time) \
            .filter(Wfrecord.data_entry_time <= end_time)

    if recog_start_time and recog_end_time:
        query = query \
            .filter(Wfrecord.sdk_recog_time >= recog_start_time) \
            .filter(Wfrecord.sdk_recog_time <= recog_end_time)

        s_query = s_query \
            .filter(Wfrecord.sdk_recog_time >= recog_start_time) \
            .filter(Wfrecord.sdk_recog_time <= recog_end_time)

    if reason_code:
        if not cons.NO_CAR_DISPLAY:
            if 5 in reason_code:
                reason_code.remove(5)
        # 过滤类型
        query = query.filter(Wfrecord.sdk_reason_code.in_(reason_code))
    else:
        if not cons.NO_CAR_DISPLAY:
            query = query.filter(Wfrecord.sdk_reason_code != 5)

    # 过滤人工审核
    if manual_check_status:
        query = query.filter(Wfrecord.manual_check_status.in_(manual_check_status))
    # 过滤操作
    if action:
        query = query.filter(Wfrecord.src_illegal_action == action)

    # 将两个统计数据存到 g 变量, 不一定每次都查询总数 (查询总数比较耗时)
    # if not simple:
    #     time_total = s_query.with_entities(func.count(Wfrecord.id)).scalar()
    #     flask.g = dict()
    #     flask.g["time_total"] = time_total
    # else:
    #     time_total = flask.g["time_total"]

    # if not simple:
    #     total = query.with_entities(func.count(Wfrecord.id)).scalar()
    #     flask.g["total"] = total
    # else:
    #     total = flask.g["total"]

    # 先从 g 变量中去取， 取不到则查询数据库
    try:
        time_total = flask.g["time_total"]
        total = flask.g["total"]
    except Exception as e:
        time_total = s_query.with_entities(func.count(Wfrecord.id)).scalar()
        total = query.with_entities(func.count(Wfrecord.id)).scalar()
        logging.info("again query wfrecord total")

    # 数据量大了导致分页较慢(从查询的时候限制查询区间)
    # 使用内存分页 (不可取)
    # records = query.all()
    # records = records[0: pageSize]
    records = query.offset(current).limit(pageSize).all()

    result = []
    for r in records:
        recog_data = json.loads(r[14])
        plate_scores = recog_data["PlateScores"]
        result.append({
            'id': r[0],
            'src_record_id': r[1],
            'src_car_plate_type': r[2],
            'src_car_plate_number': r[3],
            'sdk_car_plate_number': r[4],
            'sdk_car_plate_type': r[5],
            'sdk_reason_code': r[6],
            'data_entry_time': str(r[7]),
            'car_num_pic_url': r[8],
            'car_num_pic_path': get_image_path(r[9]),
            'sdk_plate_rect': r[10],
            'manual_check_status': r[11],
            'src_illegal_action': r[12],
            'sdk_recog_time': r[13],
            'plate_scores': plate_scores,
        })
    result_data = {"result": result, "time_total": time_total}
    return response.success_with_pagenation(total, current, pageSize, result_data)


# 根据记录id 获取图片
@comparison_results_blu.route('/show/image/<int:id>', methods=['GET'])
@error_handler
def show_image(id):
    # TODO 一直是测试图片
    id = 2

    w = request.args.get('w', None)
    h = request.args.get('h', None)
    box = request.args.get('box', None)
    scale = float(request.args.get('scale', 1))

    img_path = db.session.query(Wfrecord.car_num_pic_path).filter(Wfrecord.id == id).first()[0]
    img_absolute_path = get_image_path(img_path)

    if w or h or box or scale != 1:
        img = Image.open(img_absolute_path)
        img_io = BytesIO()

    if box:
        bx, by, bw, bh = map(int, box.split(','))
        img = img.crop((bx, by, bx + bw, by + bh))

    if scale != 1:
        w, h = img.size
        w = w * scale
        h = h * scale
    if w and h:
        w = int(w);
        h = int(h)
        img.thumbnail((w, h), Image.ANTIALIAS)

    if w or h or box or scale != 1:
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        response = flask.send_file(img_io, mimetype='image/jpeg')
    else:
        # response = draw_box(path)
        response = flask.send_file(img_absolute_path)

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# 人工审核
@comparison_results_blu.route('/update/manual/status', methods=['PATCH'])
@error_handler
def update_manual_status():
    data = request.get_json(force=True)
    ids = data.get('ids', [])
    manual_check_status = data.get('manual_check_status', 0)
    if not ids:
        return response.invalid('no ids')

    # 查询的同时直接更新
    # [(s.query(Wfrecord).filter(Wfrecord.id == id).update({"manual_check_status": manual_check_status})) for id in ids]
    for id in ids:
        db.session.query(Wfrecord).filter(Wfrecord.id == id).update({"manual_check_status": manual_check_status})
    # 手动提交事务
    db.session.commit()

    return response.success()


# 导出对比查询结果
@comparison_results_blu.route('/download/result', methods=['GET'])
@error_handler
def download_result():
    start_time = request.args.get('start_time', "", type=str)
    end_time = request.args.get('end_time', "", type=str)
    reason_code = request.args.get('reason_code', [], type=str)
    reason_code = json.loads(reason_code)
    result_images_path = cons.EXCEL_PATH
    manual_check_status = json.loads(request.args.get('manual_check_status', []))
    recog_start_time = request.args.get('recog_start_time', 0, type=int)
    recog_end_time = request.args.get('recog_end_time', 0, type=int)
    action = request.args.get('action', '', type=str)

    query = db.session.query(Wfrecord.src_record_id, Wfrecord.src_car_plate_type,
                             Wfrecord.src_car_plate_number, Wfrecord.sdk_car_plate_number,
                             Wfrecord.sdk_car_plate_type, Wfrecord.sdk_reason_code,
                             Wfrecord.data_entry_time, Wfrecord.car_num_pic_url, Wfrecord.car_num_pic_path) \
                      .filter(Wfrecord.check_status == 2) \
                      .filter(Wfrecord.sdk_reason_code > 0) \
                      .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number)
    if reason_code:
        if not cons.NO_CAR_DISPLAY:
            if 5 in reason_code:
                reason_code.remove(5)
        query = query.filter(Wfrecord.sdk_reason_code.in_(reason_code))
    else:
        if not cons.NO_CAR_DISPLAY:
            query = query.filter(Wfrecord.sdk_reason_code != 5)

    if start_time and end_time:
        query = query \
            .filter(Wfrecord.data_entry_time >= start_time) \
            .filter(Wfrecord.data_entry_time <= end_time)

    if recog_start_time and recog_end_time:
        query = query \
            .filter(Wfrecord.sdk_recog_time >= recog_start_time) \
            .filter(Wfrecord.sdk_recog_time <= recog_end_time)

    if manual_check_status:
        query = query.filter(Wfrecord.manual_check_status.in_(manual_check_status))

    if action:
        query = query.filter(Wfrecord.src_illegal_action == action)

    records = query.all()
    # folder_name = '{}_{}_{}_{}'.format(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(start_time/1000))),
    #        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(end_time/1000))), reason_code,
    #        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    # folder_name = '{}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    folder_name = '{}'.format(datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))

    # dest_folder = result_images_path + '{}'.format(folder_name)
    dest_folder = os.path.join(result_images_path, folder_name)

    # if not os.path.exists(dest_folder):
    #    os.makedirs(dest_folder)
    zip = zipfile.ZipFile('{}.zip'.format(dest_folder), "w", zipfile.ZIP_DEFLATED)

    for r in records:
        src = get_image_path(r[-1])
        dest = os.path.join(dest_folder, '{}_{}_{}.jpg'.format(r[3], r[2], r[-3]))
        # shutil.copy(src, dest)
        zip.write(src, dest)
    zip.close()
    # zipDir(dest_folder, '{}.zip'.format(dest_folder))

    return send_from_directory(result_images_path, folder_name + '.zip', as_attachment=True)
