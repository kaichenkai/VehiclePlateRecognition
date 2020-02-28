# -*- coding:utf-8 -*-
import logging
from . import index_blu
from flask import render_template, current_app
from business.utils.decorator import error_handler


@index_blu.route("/")
@error_handler
def index():
    logging.info("index 被访问了")
    return render_template("index.html")


# 网站图标
@index_blu.route("/favicon.ico")
@error_handler
def favicon():
    return current_app.send_static_file("favicon.ico")
