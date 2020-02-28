# -*- coding:utf-8 -*-
import time


def main(start_time, end_time):
    format = '%Y-%m-%d'
    start_time = time.mktime(time.strptime(start_time, format))
    end_time = time.mktime(time.strptime(end_time, format))
    print(start_time)
    print(end_time)
    #
    sub_time = end_time - start_time
    day_num = int(sub_time / 3600 / 24)
    return day_num


if __name__ == '__main__':
    t = main("2020-02-01", "2020-03-01")
    print(t)