# -*- coding: utf-8 -*-
# import redis
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler


# 数据库
db = SQLAlchemy()
redis_store = None

# 进程任务调度
flask_scheduler = APScheduler()


def create_app(config_name):
    """通过不同的配置名称， 初始化其对应配置的应用实例"""
    #
    from config import config_dict  #
    config = config_dict[config_name]
    # 配置项目日志
    # setup_log(config)
    # 创建 web 应用
    app = Flask(__name__, static_folder="static/", template_folder="static/")
    # 从 object 中加载配置
    app.config.from_object(config)
    # 初始化 mysql
    global db
    db.init_app(app)
    # 连接 redis
    global redis_store
    # redis_store = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT)

    # 注册，开启任务调度
    global flask_scheduler
    if not flask_scheduler.running:  # 初始化时为 False
        flask_scheduler.init_app(app)
        flask_scheduler.start()
        # 配置项目日志(仅配置一次，生成一个日志对象)
        setup_log(config)

        # 注册蓝图
        from business.web_api.index import index_blu
        app.register_blueprint(index_blu)
        from business.web_api.comparison_results import comparison_results_blu
        app.register_blueprint(comparison_results_blu)
        from business.web_api.report_statistics import report_statistics_blu
        app.register_blueprint(report_statistics_blu)
        from business.web_api.job_switch import job_switch_blu
        app.register_blueprint(job_switch_blu)
    #
    return app


def setup_log(config):
    """配置日志"""
    # 设置日志的记录等级
    logging.basicConfig(level=config.LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小(5个G)、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 5, backupCount=10)
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
