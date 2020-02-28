# -*- coding:utf-8 -*-
from . import job_switch_blu
from business import response, flask_scheduler
from business.utils.decorator import error_handler


@job_switch_blu.route('/pause/job', methods=['GET'])
@error_handler
def pause_job():
    flask_scheduler.pause_job('job2')
    return response.success()


@job_switch_blu.route('/restart/job', methods=['GET'])
@error_handler
def start_job():
    flask_scheduler.resume_job('job2')
    return response.success()
