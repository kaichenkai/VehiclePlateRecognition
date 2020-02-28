# -*- coding:utf8 -*-
from flask import jsonify


def success(data=None, message=None, **kwargs):
    if not message:
        message = 'success'

    rsp = {
        'code': 200,
        'message': message,
        }

    if data is not None:
        rsp['data'] = data

    if kwargs:
        rsp.update(kwargs)

    return jsonify(rsp)


def add_success(data=None, message=None):
    if not message:
        message = 'success'

    rsp = {
        'code': 201,
        'message': message,
        }

    if data is not None:
        rsp['data'] = data

    return jsonify(rsp)


def invalid(message='invalid params'):
    rsp = {
        'code': 400,
        'message': message
        }

    return jsonify(rsp)


def server_error(message='server error'):
    rsp = {
        'code': 500,
        'message': message
        }

    return jsonify(rsp)


def success_with_pagenation(total, page, size, data):
    rsp = {
        'code': 200,
        'message': 'success',
        'total': total,
        'current': page,
        'pageSize': size,
        'data': data
        }

    return jsonify(rsp)


def log_timeout():
    data = {
        'code': 401,
        'message': '未登录'
    }

    return jsonify(data)


def login_error(message=None):
    if not message:
        message = 'invalid username or password'

    data = {
        'code': 400,
        'message': message
    }

    return jsonify(data)


def unauthorized():
    data = {
        'code': 403,
        'message': '你没有该操作权限'
    }

    return jsonify(data)
