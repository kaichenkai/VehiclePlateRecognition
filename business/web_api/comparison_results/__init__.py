# -*- coding:utf-8 -*-
from flask import Blueprint

comparison_results_blu = Blueprint("comparison_results", __name__, url_prefix="/api")

from . import views
