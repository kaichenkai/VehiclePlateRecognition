# -*- coding:utf-8 -*-
import time

default_format = "%Y-%m-%d %H:%M:%S"
seconds_per_day = 24 * 3600


def timestamp2str(timestamp, format=default_format):
    return time.strftime(format, time.localtime(int(timestamp)))


def mstime2str(mstimestamp, format=default_format):
    return time.strftime(format, time.localtime(int(mstimestamp) / 1000))


def str2timestamp(string, format=default_format):
    return int(time.mktime(time.strptime(string, format)))


def to_mstimestamp(string, format=default_format):
    return int(time.mktime(time.strptime(string, format))) * 1000


def today(format='%Y-%m-%d'):
    return timestamp2str(time.time(), format)


def date_interval(start_time, end_time, format=default_format):
    start_time = time.mktime(time.strptime(start_time, format))
    end_time = time.mktime(time.strptime(end_time, format))
    #
    sub_time = end_time - start_time
    day_num = int(sub_time / 3600 / 24)
    return day_num


if __name__ == '__main__':
    t = to_mstimestamp("2020-02-10 10:10:10")
    print(t)
    t2 = mstime2str(t)
    print(t2)
