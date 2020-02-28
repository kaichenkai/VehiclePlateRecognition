# -*- coding:utf-8 -*-
from datetime import datetime
from business import db


class BaseModel(object):
    """模型基类"""
    create_time = db.Column(db.DateTime, default=datetime.now)
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


class Wfrecord(db.Model):
    __tablename__ = 'wf_record'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    src_record_id = db.Column(db.String)
    src_car_plate_number = db.Column(db.String)
    src_car_plate_type = db.Column(db.String)

    snapshot_time = db.Column(db.Integer)

    sdk_car_plate_number = db.Column(db.String)
    sdk_car_plate_type = db.Column(db.Integer)
    sdk_reason_code = db.Column(db.Integer)

    car_num_pic_url = db.Column(db.String)
    car_num_pic_path = db.Column(db.String)

    check_status = db.Column(db.Integer)

    sdk_plate_rect = db.Column(db.String)
    manual_check_status = db.Column(db.Integer)
    src_illegal_action = db.Column(db.String)

    recog_data = db.Column(db.Text)
    sdk_recog_time = db.Column(db.Integer)
    plate_head_score = db.Column(db.Integer)

    traffic_sector_name = db.Column(db.String)
    traffic_sector_code = db.Column(db.String)

    data_entry_time = db.Column(db.DateTime)

    data_entry_person = db.Column(db.String)
    correct_sector_code = db.Column(db.String)

    modified_column = ('manual_check_status', 'sdk_plate_rect', 'sdk_car_plate_number', 'sdk_reason_code',
                       'sdk_car_plate_type', 'check_status')


class SectorDataCount(db.Model):
    __tablename__ = 'sector_date_count'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sector_code = db.Column(db.String)
    date = db.Column(db.String)
    manual_check_status = db.Column(db.Integer)
    insert_count = db.Column(db.Integer)
    ana_count = db.Column(db.Integer)
    err_count = db.Column(db.Integer)
    m1_count = db.Column(db.Integer)
    m2_count = db.Column(db.Integer)
