# -*- coding:utf-8 -*-
import logging
from business import constants as cons
from crontab.task import sdk_request, all_date_count, yesterday_count


class CrontabConfig(object):  # 创建配置，用类
    # 任务列表
    JOBS = [
        {
            'id': 'job2',
            'func': sdk_request,  # 方法名
            'args': (1, 2),  # 入参
            'trigger': 'interval',  # interval表示循环任务
            'seconds': cons.time_interval,
        },
        {
            'id': 'all_date_count',
            'func': all_date_count,  # 方法名
            'args': (1, 2),  # 入参
            'trigger': 'date',  # date表示一次任务
            # 'run_date': datetime.datetime.now(),
        },
        {
            'id': 'yesterday_count',
            'func': yesterday_count,  # 方法名
            'args': (1, 2),  # 入参
            'trigger': 'cron',  # cron表示定时任务
            'hour': 0,
            'minute': 1
        }
    ]


class BasicConfig(CrontabConfig):
    """项目配置信息"""
    DEBUG = True

    # 支持 JSON 显示中文
    JSON_AS_ASCII = False

    # mysql 配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:123456@127.0.0.1:3306/geo_explor"
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 设置为数据库不跟踪
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True  # 在请求结束时，SQLAlchemy 会自动执行一次 db.session.commit()操作

    # redis 配置
    # REDIS_HOST = "127.0.0.1"
    # REDIS_PORT = 6379

    # session 配置
    SECRET_KEY = "EjpNVSNQTyGi1VvWECj9TvC/+kq3oujee2kTfQUs8yCM6xX9Yjq52v54g+HVoknA"
    SESSION_USE_SIGNER = True  # 让 cookie 中的 session_id 被加密签名处理
    # SESSION_TYPE = ""

    # 默认日志等级
    LOG_LEVEL = logging.DEBUG  # 默认为DEBUG


class Dev(BasicConfig):
    """开发环境配置"""
    pass


class Prod(BasicConfig):
    """生产环境配置"""
    DEBUG = False

    # 日志等级
    LOG_LEVEL = logging.INFO


class Test(BasicConfig):
    """单元测试环境下的配置"""
    # TESTING开启之后，当被测试代码保措时，会输出错误在哪一行
    TESTING = True


# 定义配置字典
config_dict = {
    "dev": Dev,
    "prod": Prod,
    "test": Test
}
