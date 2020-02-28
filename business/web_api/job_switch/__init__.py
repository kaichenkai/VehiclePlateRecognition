# -*- coding:utf-8 -*-
from flask import Blueprint

job_switch_blu = Blueprint("job_switch", __name__, url_prefix="/api")

from . import views
