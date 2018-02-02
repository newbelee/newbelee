#!/usr/bin/env python
# encoding: utf-8
import MySQLdb
import ConfigParser
import endecrypt

config = ConfigParser.ConfigParser()
cfgfile = open('/var/www/site/mycitsm/mycitsm/login.cnf', 'r')
config.readfp(cfgfile)
admin_user = config.get('mysqllogin', 'admin_user')
admin_passwd = endecrypt.decrypt(config.get('mysqllogin', 'admin_passwd'))
product_user = config.get('mysqllogin', 'product_user')
product_passwd = endecrypt.decrypt(config.get('mysqllogin', 'product_passwd'))
mysqluploaddb_site_user = config.get('mysqllogin', 'mysqluploaddb_site_user')
mysqluploaddb_site_passwd = endecrypt.decrypt(config.get('mysqllogin', 'mysqluploaddb_site_passwd'))
sqlmonitordb_user = config.get('mysqllogin', 'sqlmonitordb_user')
sqlmonitordb_passwd = endecrypt.decrypt(config.get('mysqllogin', 'sqlmonitordb_passwd'))
mysql_aes_encrypt_key = endecrypt.decrypt(config.get('key', 'mysql_aes_encrypt_key'))


def getConn(host, port, dbname, env = ''):
    conn = ''
    if env == '':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = admin_user, passwd = admin_passwd, charset = 'utf8', connect_timeout = 3)
    elif env == 'dev':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = dev_user, passwd = dev_passwd, charset = 'utf8')
    elif env == '测试':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = test_user, passwd = test_passwd, charset = 'utf8')
    elif env == 'UAT':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = uat_user, passwd = uat_passwd, charset = 'utf8')
    elif env == '生产':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = product_user, passwd = product_passwd, charset = 'utf8')
    elif env == 'mysqlupload':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = mysqluploaddb_site_user, passwd = mysqluploaddb_site_passwd, charset = 'utf8')
    elif env == 'sqlmonitor':
        conn = MySQLdb.connect(host = host, port = port, db = dbname, user = sqlmonitordb_user, passwd = sqlmonitordb_passwd, charset = 'utf8')
    else:
        conn = ''
    return conn

