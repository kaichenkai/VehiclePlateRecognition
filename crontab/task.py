# -*- coding:utf-8 -*-
import os
import time
import datetime
import copy
import json
import base64
import logging
import requests
import threading
from sqlalchemy import func
from multiprocessing import Queue
from business import db, constants as cons, create_app
from business.models import Wfrecord, SectorDataCount
from manage import RUN_MODEL


img_counts = 0
today = time.strftime('%Y-%m-%d', time.localtime(time.time()))


# 请求分析服务接口
def sdk_request(a, b):
    app = create_app(RUN_MODEL)
    with app.app_context():
        # 一天限制40w数量图片
        global img_counts, today

        if today != time.strftime('%Y-%m-%d', time.localtime(time.time())):
            today = time.strftime('%Y-%m-%d', time.localtime(time.time()))
            img_counts = 0

        if img_counts >= cons.MAX_IMAGE_NUM:
            logging.info("image processing number reached 40w")
            print("image processing number reached 40w")
            # scheduler.pause_job('job2')
            return

        # query = s.query(Wfrecord.id, Wfrecord.src_car_plate_number, Wfrecord.car_num_pic_path, Wfrecord.src_illegal_action)\
        #            .filter(Wfrecord.check_status.in_((0,))).filter(Wfrecord.src_illegal_action.notin_(no_recog_action))
        # TODO 不过滤违法编码
        query = db.session.query(Wfrecord.id, Wfrecord.src_car_plate_number, Wfrecord.car_num_pic_path,
                                 Wfrecord.src_illegal_action) \
                          .filter(Wfrecord.check_status.in_((0,)))
        if cons.LIMIT_NUM:
            records = query.limit(cons.LIMIT_NUM).all()
        else:
            return
            # records = query.all()
        if not records:
            logging.info('no records to recog')
            print('no records to recog')
        else:
            tmp = []
            ex_tmp = []
            images = []
            cal_params = []

            queue = Queue()
            thred_list = []
            rs = []

            for i in range(int(cons.THREAD_NUM)):
                t = threading.Thread(target=process, args=(queue,))
                thred_list.append(t)

            for r in records:
                try:
                    # print '+++1',len(images)
                    image_path = os.path.join(cons.IMAGE_PATH, r[2])
                    with open(image_path, 'rb') as img_file:
                        img_data = img_file.read()
                    b64img = base64.b64encode(img_data)
                    cal_param = calc_param_patern.format(mode="0", srcplate=r[1].replace(".", ""))
                except Exception as e:
                    logging.exception('sdk_request{}'.format(e))

                    w_id = r[0]
                    w = db.session.query(Wfrecord).filter(Wfrecord.id == w_id).first()
                    # TODO 调用算法异常
                    w.check_status = 3
                    # db.session.add(w)
                    db.session.commit()
                    continue

                else:
                    if not b64img:
                        w_id = r[0]
                        w = db.session.query(Wfrecord).filter(Wfrecord.id == w_id).first()
                        # TODO 没有图片的情况
                        w.check_status = 4
                        # db.session.add(w)
                        db.session.commit()
                        continue
                    images.append(b64img)
                    cal_params.append(cal_param)
                    rs.append(r)

                if len(images) == 8:
                    images_fake = copy.deepcopy(images)
                    cal_fake = copy.deepcopy(cal_params)
                    rs_fake = copy.deepcopy(rs)

                    queue.put((images_fake, cal_fake, rs_fake))

                    del rs[:]
                    del images[:]
                    del cal_params[:]

                    img_counts += 1
                    # 一天限制40w数量图片
                    if img_counts >= cons.MAX_IMAGE_NUM:
                        logging.info("image processing number reached 40w")
                        print("image processing number reached 40w")
                        # scheduler.pause_job('job2')
                        break
            # 开启线程任务
            for t in thred_list:
                t.start()

            if images and img_counts < cons.MAX_IMAGE_NUM:
                queue.put((images, cal_params, rs))

            for t in thred_list:
                t.join()


# 识别线程任务
def process(queue):
    while True:
        try:
            d = queue.get(True, 1)
        except Exception as e:
            logging.error(e)
            break

        try:
            ex_tmp = []
            tmp = []
            rs = d[2]
            post_data = dict(
                images=d[0],
                calc_param_list=d[1]
            )
            rsp = requests.post(cons.SDK_API, json.dumps(post_data))

            # print rsp.content

            # rsp_json = json.loads(unicode(rsp.content, errors='ignore'))
            try:
                rsp_json = json.loads(rsp.content)
            except Exception as e:
                logging.error(e)
                print(rsp.content)
                break

            if rsp_json['Code'] != 0:
                for r in rs:
                    ex_tmp.append(r[0])
                continue

            result_datas = rsp_json["Results"]
            for result_data in result_datas:
                index = result_datas.index(result_data)
                recog_plate_number = result_data['Licence']
                reason_code = result_data['EvenCode']

                if reason_code == -1:
                    ex_tmp.append(rs[index][0])
                    continue

                # 录入尾号不是汉字，sdk识别是汉字放入正片
                if recog_plate_number:
                    if rs[index][1][-1] not in ('学', '警'):
                        if recog_plate_number[-1] in ('学', '警'):
                            reason_code = 0

                # 首字识别一致，后六位不一致算车牌更正 reason_code = 3 否则为0
                if recog_plate_number and reason_code == 1:
                    # 替换点再比较
                    # rs[index][1] = rs[index][1].replace(".", "")

                    if rs[index][1][0] == recog_plate_number[0] and rs[index][1][1:] != recog_plate_number[1:]:
                        reason_code = 1
                    else:
                        reason_code = 0

                    # 车牌更正,任意一位得分低于90放入疑似
                    p_s = result_data['PlateScores']
                    if p_s:
                        for i in p_s:
                            if i < 90:
                                reason_code = 2
                                break

                    # 车牌更正,识别不同的号码得分小于70，放入疑似
                    # p_s = result_data['PlateScores']
                    # if p_s:
                    #    for i in range(1, len(p_s)):
                    #        try:
                    #            tmp_sr = rs[index][1][i]
                    #        except:
                    #            tmp_sr = ''
                    #        try:
                    #            tmp_re = recog_plate_number[i]
                    #        except:
                    #            tmp_re = ''
                    #        if p_s[i] < 70 and tmp_sr != tmp_re:
                    #            reason_code = 2
                    #            break

                recog_plate_type = result_data['PlateType']
                plate_rect = result_data['PlateRect']
                if result_data['PlateScores']:
                    plate_head_score = result_data['PlateScores'][0]
                else:
                    plate_head_score = 0

                tmp.append({'id': rs[index][0],
                            'plate_number': recog_plate_number,
                            'plate_type': recog_plate_type,
                            'reason_code': reason_code,
                            'plate_rect': plate_rect,
                            'head_score': plate_head_score,
                            'recog_data': json.dumps(result_data, ensure_ascii=False),
                            })

        except Exception as e:
            logging.exception('sdk_request{}'.format(e))
            for r in rs:
                ex_tmp.append(r[0])

        add_data(tmp, ex_tmp)


def add_data(tmp, ex_tmp):
    adds = []
    # ex_adds = []
    for t in tmp:
        w_id = t["id"]
        w = db.session.query(Wfrecord).filter(Wfrecord.id == w_id).first()
        w.sdk_car_plate_number = t["plate_number"]
        w.sdk_car_plate_type = t["plate_type"]
        w.sdk_reason_code = t["reason_code"]
        w.sdk_plate_rect = json.dumps(t["plate_rect"])
        w.check_status = 2
        w.recog_data = t['recog_data']
        w.plate_head_score = t['head_score']
        w.sdk_recog_time = int(time.time() * 1000)
        adds.append(w)

    # db.session.bulk_save_objects(adds)
    db.session.add_all(adds)

    for t in ex_tmp:
        w_id = t
        w = db.session.query(Wfrecord).filter(Wfrecord.id == w_id).first()
        w.check_status = 3  # 会自动 commit()


def all_date_count(a, b):
    app = create_app(RUN_MODEL)
    with app.app_context():
        record = db.session.query(Wfrecord).first()
        first_time = record.data_entry_time.strftime("%Y-%m-%d")
        next_day = first_time
        today = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")

        print('+++++++++ all_date_count', today, next_day)
        while today != next_day:
            result = get_count(next_day)
            insert_date_count(result)
            next_day = (datetime.datetime.strptime(next_day, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

            # print '+++++++++ all_date_count', today, next_day


def yesterday_count(a, b):
    app = create_app(RUN_MODEL)
    with app.app_context():
        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        result = get_count(yesterday)
        insert_date_count(result)


def get_count(date):
    result = {}

    start_time = date + ' 00:00:00'
    end_time = \
        (datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)).strftime(
            "%Y-%m-%d") + ' 00:00:00'

    result['date'] = date

    for manual_check_status in (3, 2, 1):
        query = db.session.query(Wfrecord)

        query = query \
            .filter(Wfrecord.data_entry_time >= start_time) \
            .filter(Wfrecord.data_entry_time < end_time)

        if manual_check_status != 3:
            query = query.filter(Wfrecord.manual_check_status == manual_check_status)

        time_total = query.group_by(Wfrecord.correct_sector_code) \
            .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
            .all()

        ana_total = query.filter(Wfrecord.check_status > 0) \
            .group_by(Wfrecord.correct_sector_code) \
            .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
            .all()

        query = query.filter(Wfrecord.check_status == 2) \
            .filter(Wfrecord.sdk_reason_code > 0) \
            .filter(Wfrecord.src_car_plate_number != Wfrecord.sdk_car_plate_number)

        if not cons.NO_CAR_DISPLAY:
            query = query.filter(Wfrecord.sdk_reason_code != 5)

        # 通报只展示车牌更正
        err_total = query.filter(Wfrecord.sdk_reason_code == 1) \
            .group_by(Wfrecord.correct_sector_code) \
            .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
            .all()

        m1_total = query \
            .filter(Wfrecord.sdk_reason_code == 1) \
            .filter(Wfrecord.manual_check_status == 1) \
            .group_by(Wfrecord.correct_sector_code) \
            .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
            .all()

        m2_total = query \
            .filter(Wfrecord.sdk_reason_code == 1) \
            .filter(Wfrecord.manual_check_status == 2) \
            .group_by(Wfrecord.correct_sector_code) \
            .with_entities(Wfrecord.correct_sector_code, func.count(Wfrecord.id)) \
            .all()

        result.setdefault(manual_check_status, [])

        t_map = {i[0]: i[1] for i in time_total}
        a_map = {i[0]: i[1] for i in ana_total}
        e_map = {i[0]: i[1] for i in err_total}

        m1_map = {i[0]: i[1] for i in m1_total}
        m2_map = {i[0]: i[1] for i in m2_total}

        result[manual_check_status].extend([t_map, a_map, e_map, m1_map, m2_map])
    return result


def insert_date_count(result):
    for m in (3, 2, 1):
        for k in cons.SECTOR_MAP:
            tmp = db.session.query(SectorDataCount)\
                            .filter(SectorDataCount.manual_check_status==m)\
                            .filter(SectorDataCount.sector_code==k)\
                            .filter(SectorDataCount.date==result['date'])\
                            .first()
            if tmp:
                continue
            if result.get(m, [])[0].get(k, 0) == 0:
                continue
            sd = SectorDataCount()
            sd.sector_code = k
            sd.manual_check_status = m
            sd.insert_count = result.get(m, [])[0].get(k, 0)
            sd.ana_count = result.get(m, [])[1].get(k, 0)
            sd.err_count = result.get(m, [])[2].get(k, 0)
            sd.m1_count = result.get(m, [])[3].get(k, 0)
            sd.m2_count = result.get(m, [])[4].get(k, 0)
            sd.date = result['date']
            db.session.add(sd)


calc_param_patern = """
{{
    "Detect": {{
        "IsDet":true, 
        "Mode": {mode},
        "PlateNum": "{srcplate}"
    }},
    "Recognize" : {{
      "Color" : {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Type" : {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Brand" : {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Belt": {{
        "IsRec" :true 
      }},
      "Call": {{
        "IsRec" :true
      }},
      "Crash": {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Danger": {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Plate": {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Similar": {{
        "IsRec" : false,
        "Mode" : {mode}
      }},
      "Marker": {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Face": {{
        "IsRec" : true,
        "Mode" : {mode}
      }},
      "Slag": {{
        "IsRec" : true,
        "Mode" : {mode}
      }}
    }}
}}
"""
