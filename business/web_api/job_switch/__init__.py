# -*- coding:utf-8 -*-
from flask import Blueprint

job_switch_blu = Blueprint("job_switch", __name__)

from . import views
