# -*- coding:utf-8 -*-
from flask import Blueprint

report_statistics_blu = Blueprint("report_statistics", __name__, url_prefix="/api")

from . import views
