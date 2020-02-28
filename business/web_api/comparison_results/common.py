# -*- coding:utf-8 -*-
import os
from business import constants as cons


def get_image_path(file_name):
    return os.path.join(cons.IMAGE_PATH, file_name)
