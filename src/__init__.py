import re
import os
import csv
import sys
import time
import json
import xlwt
import sqlite3
import shutil
import codecs
import socket
import random
import datetime
import threading
import platform
import argparse
import requests
import subprocess
import configparser
import urllib3
from urllib3.exceptions import InsecureRequestWarning
from monster.dirsearch import dirsearch
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
# from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 项目绝对路径/当前操作系统
path = os.path.dirname(os.path.split(os.path.realpath(__file__))[0])
OS = platform.system()
# 全局配置读取
cf = configparser.ConfigParser()
cf.read("./suturemonster.yml", encoding='UTF-8')
# global
proxy_addr = cf.get("global", "proxy_addr")
# oneforall
ofa_port = cf.get("oneforall", "ofa_port")
ofa_alive = cf.get("oneforall", "ofa_alive")
ofa_path = cf.get("oneforall", "ofa_path")
ofa_flag = int(cf.get("oneforall", "ofa_flag"))
# jsfinder
jf_path = cf.get("jsfinder", "jf_path")
jf_cookie = cf.get("jsfinder", "jf_cookie")
# dirsearch
ds_extensions = cf.get("dirsearch", "ds_extensions")
ds_threads = cf.get("dirsearch", "ds_threads")
ds_exclude_status_code = cf.get("dirsearch", "ds_exclude_status_code")
ds_exclude_regex = cf.get("dirsearch", "ds_exclude_regex")
# hostsurvey
hs_mod = cf.get("hostsurvey", "hs_mod")
hs_port = cf.get("hostsurvey", "hs_port")
hs_ping = int(cf.get("hostsurvey", "hs_ping"))
hs_timeout = cf.get("hostsurvey", "hs_timeout")
# nmap
n_flag = int(cf.get("nmap", "n_flag"))
n_scan_flag = cf.get("nmap", "n_scan_flag")
n_hostgroup = cf.get("nmap", "n_hostgroup")
n_parallelism = cf.get("nmap", "n_parallelism")
n_timeout = cf.get("nmap", "n_timeout")
n_seq = cf.get("nmap", "n_seq")
# xray
xray_model = int(cf.get("xray", "xray_model"))
xray_proxy_addr = cf.get("xray", "xray_proxy_addr")
xray_proxy_port = cf.get("xray", "xray_proxy_port")
xray_path = cf.get("xray", "xray_path")
# awvs
awvs_url = cf.get("awvs", "awvs_url")
scan_speed = cf.get("awvs", "scan_speed")
awvs_model = cf.get("awvs", "awvs_model")
awvs_proxy = int(cf.get("awvs", "awvs_proxy"))
awvs_proxy_addr = cf.get("awvs", "awvs_proxy_addr")
awvs_proxy_port = cf.get("awvs", "awvs_proxy_port")
apikey = cf.get("awvs", "apikey")
# hydra
hy_thread = cf.get("hydra", "hy_thread")
hy_flag = int(cf.get("hydra", "hy_flag"))
hy_dictName = os.path.join(path, 'dictionary', cf.get("hydra", "hy_dictName"))
hy_userDictPath = os.path.join(path, 'dictionary', cf.get("hydra", "hy_userDict"))
hy_passDictPath = os.path.join(path, 'dictionary', cf.get("hydra", "hy_passDict"))
