# -*- coding:utf-8 -*-
import time
import functools
import logging
from flask import request
from business import response


def error_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            start_time = time.time()
            ret = func(*args, **kwargs)
            logging.info('api:[{}], cost time:[{}]'.format(request.url, time.time()-start_time))
            return ret
        except Exception as err:
            logging.error('api:[{}], error:[{}]'.format(request.url, err))
            return response.server_error()
    #
    return wrapper


# 通过app.app_context().push()来推入一个上下文
def sqlalchemy_context(app):
    def add_context(func):
        @functools.wraps(func)
        def do_job(*args, **kwargs):
            app.app_context().push()
            result = func(*args, **kwargs)
            return result
        return do_job
    return add_context


# def user_login_data(f):
#     """装饰器"""
#     # 在flask中，一个路由对应一个函数
#     # 使用 functools.wraps 去装饰内层函数，可以保持当前装饰器去装饰的函数的 __name__ 属性值不变
#     @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         user_id = session.get("user_id", None)
#         user = None  # 设置 user 的初始值为 None，避免报错
#         if user_id:
#             # 尝试查询用户的模型
#             try:
#                 user = User.query.get(user_id)  # 根据id取出用户信息
#             except Exception as result:
#                 current_app.logger.error(result)
#         # 把查询出来的数据赋值给g变量
#         """这里必须要给g变量赋值，AttributeError: '_AppCtxGlobals' object has no attribute 'user'"""
#         g.user = user
#         return f(*args, **kwargs)
#     return wrapper
