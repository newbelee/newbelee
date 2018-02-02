# -*- coding: utf-8 -*- 

from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib import auth
from django.db import connection
from django.db.utils import DatabaseError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from mycitsm.dbconn import getConn
from mycitsm.sendmsg import sendmail
from dbconn import mysql_aes_encrypt_key
from mycitsm.mssqlconn import getmssqlconn
from _mysql_exceptions import *
import pymongo
import random, string
import time
import sys
import re
from django.conf import settings
import urllib
import urllib2
import threading
import time
from random import choice
import string
import json
import datetime
import os
import paramiko
from warnings import filterwarnings
import MySQLdb
import re
import dns.resolver
import commands
import xlwt

from django.template import RequestContext
from dbhelper import Connection
import requests
from croncontrolcenter import *
from django.shortcuts import render
from django.shortcuts import render_to_response
import ConfigParser
import endecrypt

reload(sys)
sys.setdefaultencoding('UTF-8')


devhost='127.0.0.1'
devport=3306

sqlperfserver='127.0.0.1'
sqlperfport=3306
sqlperfdb='sqlperfdb'

autoDataClearServer = "127.0.0.1"
autoDataClearPort = 3306
autoDataClearDB = 'autodatacleardb'

sqlMonitorServer = '127.0.0.1'
sqlMonitorPort = 3306
sqlMonitorDb = 'sqlmonitordb'

mysqluploadServer="127.0.0.1"
mysqluploadPort=3306


#regular expression to match an ip address
ip_patt = ('^([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])\.'
           '([01]?\d\d?|2[0-4]\d|25[0-5])\.([01]?\d\d?|2[0-4]\d|25[0-5])$')
#compiled regular expression 
ip_prog = re.compile(ip_patt)

class ExecutionTime:
    def __init__(self):
        self.start_time = time.time()

    def duration(self):
        return time.time() - self.start_time

#定义时区类
class SHTZ(datetime.tzinfo):
    """Fixed offset in hours east from UTC."""
    def __init__(self, offset, name):
        self.__offset = datetime.timedelta(hours = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta(0)

#用以产生随机密码
def genPasswd(length=16, chars=string.letters + string.digits):
    return ''.join([choice(chars) for i in range(length)])

def i18n_javascript(request):
        """
        Displays the i18n JavaScript that the Django admin requires.

        This takes into account the USE_I18N setting. If it's set to False, the
        generated JavaScript will be leaner and faster.
        """
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog
        return javascript_catalog(request, packages=['django.conf', 'django.contrib.admin'])

def dictFetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

# 数据库操作
def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
    
# 读取文件
def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break
