import endecrypt
import ConfigParser


config=ConfigParser.ConfigParser()
cfgfile=open('/var/www/site/mycitsm/mycitsm/login.cnf','r')
config.readfp(cfgfile)
product_user=config.get('mysqllogin','product_user').encode('utf-8')
product_passwd=endecrypt.decrypt(config.get('mysqllogin','product_passwd').encode('utf-8'))
#product_user='root'
#product_passwd='123'
print product_user,product_passwd
