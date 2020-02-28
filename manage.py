# -*- coding:utf-8 -*-
from business import create_app
from flask_script import Manager

# 程序运行模式
RUN_MODEL = "prod"

# 从自定义方法中创建 app, 传入环境配置选项
app = create_app(RUN_MODEL)
manager = Manager(app)


if __name__ == "__main__":
    manager.run()
