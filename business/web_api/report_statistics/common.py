# -*- coding:utf-8 -*-
import os
import json
import datetime
from sqlalchemy import func, distinct
from business import db
from business import constants as cons
from business.models import Wfrecord, SectorDataCount


# 通报统计查询
def get_date_count(start_time, end_time, manual_check_status):
    start_date = start_time.split(' ')[0]
    end_date = end_time.split(' ')[0]
    today = datetime.datetime.now().strftime("%Y-%m-%d")

    if start_time and end_time:
        if today > end_date:
            # 查end-start的数量
            counts = db.session.query(SectorDataCount).filter(SectorDataCount.date >= start_date) \
                                                      .filter(SectorDataCount.date <= end_date) \
                                                      .filter(SectorDataCount.manual_check_status == manual_check_status) \
                                                      .all()
            result_data, total = objs_get_result(counts)

        elif start_date < today <= end_date:
            # 查today-start的数量
            counts = db.session.query(SectorDataCount).filter(SectorDataCount.date >= start_date) \
                .filter(SectorDataCount.date <= end_date) \
                .filter(SectorDataCount.manual_check_status == manual_check_status) \
                .all()
            # today数量
            today_result, _ = create_results(today + ' 00:00:00', today + ' 23:59:59', manual_check_status,
                                             current=None, pageSize=None)

            result_data, total = objs_get_result(counts, today_result=today_result)

        elif today < start_date:
            # 无数据
            result_data, total = {}, 0
        elif today == start_date:
            # 查today数量
            result_data, total = create_results(today + ' 00:00:00', today + ' 23:59:59', manual_check_status,
                                                current=None, pageSize=None)
    else:
        # 查历史和today
        counts = db.session.query(SectorDataCount) \
            .filter(SectorDataCount.manual_check_status == manual_check_status) \
            .all()
        # today数量
        today_result, _ = create_results(today + ' 00:00:00', today + ' 23:59:59', manual_check_status, current=None,
                                         pageSize=None)

        result_data, total = objs_get_result(counts, today_result=today_result)

    return result_data, total


def objs_get_result(counts, today_result=None):
    result = []

    inserts = 0
    errs = 0
    m1s = 0
    m2s = 0
    ana_counts = 0

    tmp = {}
    for count in counts:
        tmp.setdefault(count.sector_code, {})
        tmp[count.sector_code].setdefault('insert_count', 0)
        tmp[count.sector_code].setdefault('ana_count', 0)
        tmp[count.sector_code].setdefault('err_count', 0)
        tmp[count.sector_code].setdefault('m1_count', 0)
        tmp[count.sector_code].setdefault('m2_count', 0)

        tmp[count.sector_code]['insert_count'] += count.insert_count
        inserts += count.insert_count
        tmp[count.sector_code]['ana_count'] += count.ana_count
        ana_counts += count.ana_count
        tmp[count.sector_code]['err_count'] += count.err_count
        errs += count.err_count
        tmp[count.sector_code]['m1_count'] += count.m1_count
        m1s += count.m1_count
        tmp[count.sector_code]['m2_count'] += count.m2_count
        m2s += count.m2_count

    # 加入today数据
    if today_result:
        inserts += today_result.get('inserts', 0)
        errs += today_result.get('errs', 0)
        ana_counts += today_result.get('ana_counts', 0)
        m1s += today_result.get('m1s', 0)
        m2s += today_result.get('m2s', 0)

        for r in today_result.get('result', []):
            sector_code = cons.SECTOR_MAP.get(r['name'], '')

            if sector_code not in tmp:
                tmp.setdefault(sector_code, {})
                tmp[sector_code].setdefault('insert_count', 0)
                tmp[sector_code].setdefault('ana_count', 0)
                tmp[sector_code].setdefault('err_count', 0)
                tmp[sector_code].setdefault('m1_count', 0)
                tmp[sector_code].setdefault('m2_count', 0)

            tmp[sector_code]['insert_count'] += r.get('insert_count', 0)
            tmp[sector_code]['ana_count'] += r.get('ana_count', 0)
            tmp[sector_code]['err_count'] += r.get('err_count', 0)
            tmp[sector_code]['m1_count'] += r.get('m1_count', 0)
            tmp[sector_code]['m2_count'] += r.get('m2_count', 0)

    for k, v in tmp.items():
        result.append({"name": cons.SECTOR_MAP.get(k, "无名称或未录入"), "insert_count": v.get('insert_count', 0),
                       "ana_count": v.get('ana_count', 0),
                       "err_count": v.get('err_count', 0), "m1_count": v.get('m1_count', 0),
                       "m2_count": v.get('m2_count', 0),
                       "m2_p": get_lv_bai(v.get('m2_count', 0), v.get('err_count', 0)),
                       "recall": get_lv(v.get('m2_count', 0), v.get('ana_count', 0)),
                       "jianchu": get_lv(v.get('err_count', 0), v.get('insert_count', 0))})

    result_data = {"result": result, "inserts": inserts, "ana_counts": ana_counts, "errs": errs, "m1s": m1s, "m2s": m2s,
                   "m2_p": get_lv_bai(m2s, errs), "recall": get_lv(m2s, inserts), "jianchu": get_lv(errs, inserts)}
    total = len(tmp)
    return result_data, total


def create_results(start_time, end_time, manual_check_status, current=None, pageSize=None):
    # current = data.get('current', 1)
    # pageSize = data.get('pageSize', 24)
    # start_time = data.get('start_time', "")
    # end_time = data.get('end_time', "")
    time_total = []
    err_total = []
    if pageSize:
        csector_list = cons.SECTOR_MAP.keys()[current:current + pageSize]
    else:
        csector_list = cons.SECTOR_MAP.keys()
    #
    query = db.session.query(Wfrecord)
    if start_time and end_time:
        query = query \
            .filter(Wfrecord.data_entry_time >= start_time) \
            .filter(Wfrecord.data_entry_time <= end_time)

    # for i in csector_list:
    #    v = sector_map.get(i)
    #    x = "{}%".format(i)
    #    tmp = query.filter(Wfrecord.traffic_sector_code.ilike(x))\
    #               .with_entities(func.count(Wfrecord.id)).scalar()
    #    time_total.append([v, tmp])
    if manual_check_status != 3:
        query = query.filter(Wfrecord.manual_check_status == manual_check_status)

    time_total = query.group_by(Wfrecord.correct_sector_code) \
        .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
        .offset(current).limit(pageSize) \
        .all()

    ana_total = query.filter(Wfrecord.check_status > 0) \
        .group_by(Wfrecord.correct_sector_code) \
        .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
        .offset(current).limit(pageSize) \
        .all()

    query = query.filter(Wfrecord.check_status == 2) \
        .filter(Wfrecord.sdk_reason_code > 0) \
        .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number)

    if not cons.NO_CAR_DISPLAY:
        query = query.filter(Wfrecord.sdk_reason_code != 5)

    # 通报只展示车牌更正
    # for i in csector_list:
    #    v = sector_map.get(i)
    #    x = "{}%".format(i)
    #    tmp = query.filter(Wfrecord.sdk_reason_code==1)\
    #               .filter(Wfrecord.traffic_sector_code.ilike(x))\
    #               .with_entities(func.count(Wfrecord.id)).scalar()
    #    err_total.append([v,tmp])
    err_total = query.filter(Wfrecord.sdk_reason_code == 1) \
        .group_by(Wfrecord.correct_sector_code) \
        .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
        .offset(current).limit(pageSize) \
        .all()

    m1_total = query \
        .filter(Wfrecord.sdk_reason_code == 1) \
        .filter(Wfrecord.manual_check_status == 1) \
        .group_by(Wfrecord.correct_sector_code) \
        .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
        .offset(current).limit(pageSize) \
        .all()

    m2_total = query \
        .filter(Wfrecord.sdk_reason_code == 1) \
        .filter(Wfrecord.manual_check_status == 2) \
        .group_by(Wfrecord.correct_sector_code) \
        .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
        .offset(current).limit(pageSize) \
        .all()

    total = len(db.session.query(distinct(Wfrecord.correct_sector_code)).all())

    # total = len(sector_list)
    # print time_total
    result = []
    t_map = {i[0]: i[1] for i in time_total}
    e_map = {i[0]: i[1] for i in err_total}
    a_map = {i[0]: i[1] for i in ana_total}

    m1_map = {i[0]: i[1] for i in m1_total}
    m2_map = {i[0]: i[1] for i in m2_total}

    inserts = 0
    errs = 0
    m1s = 0
    m2s = 0
    ana_counts = 0

    for k, v in t_map.items():
        result.append({"name": cons.SECTOR_MAP.get(k, "无名称或未录入"), "insert_count": v, "ana_count": a_map.get(k, 0),
                       "err_count": e_map.get(k, 0), "m1_count": m1_map.get(k, 0), "m2_count": m2_map.get(k, 0),
                       "m2_p": get_lv_bai(m2_map.get(k, 0), e_map.get(k, 0)),
                       "recall": get_lv(m2_map.get(k, 0), a_map.get(k, 0)), "jianchu": get_lv(e_map.get(k, 0), v)})
        inserts += v
        errs += e_map.get(k, 0)
        m1s += m1_map.get(k, 0)
        m2s += m2_map.get(k, 0)
        ana_counts += a_map.get(k, 0)

    result_data = {"result": result, "inserts": inserts, "ana_counts": ana_counts, "errs": errs, "m1s": m1s, "m2s": m2s,
                   "m2_p": get_lv_bai(m2s, errs), "recall": get_lv(m2s, inserts), "jianchu": get_lv(errs, inserts)}

    return result_data, total


def get_lv(a, b):
    if b == 0:
        return u'{:.1f}{}'.format(0, u'‱')
    return u'{:.1f}{}'.format(float(a)/float(b)*10000, u'‱')


def get_lv_bai(a, b):
    if b == 0:
        return '{:.1f}%'.format(0)
    return '{:.1f}%'.format(float(a)/float(b)*100)


# 导出统计
def create_results_info(start_time, end_time, name, manual_check_status, current=None, pageSize=None):
    # current = data.get('current', 1)
    # pageSize = data.get('pageSize', 24)
    # start_time = data.get('start_time', "")
    # end_time = data.get('end_time', "")
    # name = data.get("name", "")
    # manual_check_status = data.get('manual_check_status', [])

    query = db.session.query(Wfrecord.id, Wfrecord.src_record_id, Wfrecord.src_car_plate_type,
                             Wfrecord.src_car_plate_number, Wfrecord.sdk_car_plate_number,
                             Wfrecord.sdk_car_plate_type, Wfrecord.sdk_reason_code,
                             Wfrecord.snapshot_time, Wfrecord.car_num_pic_url, Wfrecord.car_num_pic_path,
                             Wfrecord.sdk_plate_rect, Wfrecord.manual_check_status,
                             Wfrecord.src_illegal_action, Wfrecord.sdk_recog_time, Wfrecord.recog_data,
                             Wfrecord.data_entry_time,
                             Wfrecord.data_entry_person, Wfrecord.traffic_sector_code)
    if start_time and end_time:
        query = query \
            .filter(Wfrecord.data_entry_time >= start_time) \
            .filter(Wfrecord.data_entry_time <= end_time)
    # 前页导出所有废片
    if not name:
        query = query.filter(Wfrecord.check_status == 2) \
            .filter(Wfrecord.sdk_reason_code > 0) \
            .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number) \
            .filter(Wfrecord.correct_sector_code.in_([v for _, v in cons.SECTOR_MAP.items()])) \
            .filter(Wfrecord.manual_check_status == 2)

    else:
        query = query.filter(Wfrecord.check_status == 2) \
            .filter(Wfrecord.sdk_reason_code > 0) \
            .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number) \
            .filter(Wfrecord.correct_sector_code == cons.SECTOR_MAP.get(name, None))
        # .filter(Wfrecord.traffic_sector_code.ilike("{}%".format(map_sector.get(name))))
    # 通报只展示车牌更正
    query = query.filter(Wfrecord.sdk_reason_code == 1)

    if not cons.NO_CAR_DISPLAY:
        query = query.filter(Wfrecord.sdk_reason_code != 5)

    if manual_check_status and name:
        query = query.filter(Wfrecord.manual_check_status.in_(manual_check_status))

    total = query.with_entities(func.count(Wfrecord.id)).scalar()

    if pageSize:
        records = query.offset(current).limit(pageSize).all()
    else:
        records = query.all()

    result = []
    for r in records:
        recog_data = json.loads(r[14])
        plate_scores = recog_data["PlateScores"]
        if not r[17]:
            s_m = 0
        else:
            s_m = r[17][0:4]

        result.append({
            'id': r[0],
            'src_record_id': r[1],
            'src_car_plate_type': r[2],
            'src_car_plate_number': r[3],
            'sdk_car_plate_number': r[4],
            'sdk_car_plate_type': r[5],
            'sdk_reason_code': r[6],
            'snapshot_time': r[7],
            'car_num_pic_url': r[8],
            'car_num_pic_path': get_image_path(r[9]),
            'sdk_plate_rect': r[10],
            'manual_check_status': r[11],
            'src_illegal_action': r[12],
            'sdk_recog_time': r[13],
            'data_entry_time': str(r[15]),
            'plate_scores': plate_scores,
            'data_entry_person': r[16],
            'traffic_sector_name': cons.SECTOR_MAP.get(s_m, ''),
        })
    result_data = {"result": result}
    return result_data, total


def get_image_path(file_name):
    return os.path.join(cons.IMAGE_PATH, file_name)
