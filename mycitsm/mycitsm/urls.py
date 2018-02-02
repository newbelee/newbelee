#encoding:utf-8
from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

# urlpatterns = patterns('',
#     url(r'^accounts/login/$','django_cas.views.login'),
#     url(r'^accounts/logout/$','django_cas.views.logout'),
#     )
urlpatterns=patterns('')

urlpatterns += patterns('mycitsm.views',
    url(r'^accounts/login/$','login'),
    url(r'^accounts/logout/$','logout'),
    url(r'^setpwd/$','setpwd'),
    url(r'^userreg/$','userreg'),
    
    url(r'^$','index'),
    url(r'^admin/$','admin'),
    url(r'^admin/user/$','showuser'),
    url(r'^admin/user/user=([^/]+)/$','changeuser'),
    url(r'^admin/group/$','showgroup'),
    url(r'^admin/group/add/$','addgroup'),
    url(r'^admin/group/group=([^/]+)/$','changegroup'),
    url(r'^admin/group/group=([^/]+)/delete/$','deletegroup'),
    url(r'^admin/group/group=([^/]+)/addmember/$','addmember'),
    url(r'^admin/permission/$','showperm'),
    url(r'^admin/permission/group=([^/]+)/$','changeperm'),

    url(r'^dbmgmt/$','dbmgmt'),
    url(r'^dbmgmt/dblist/$','dblist'),
    url(r'^dbmgmt/dblist/executesql$','executesql'),

    url(r'^dbmgmt/sqltools/$','sqltoolsgrants'),
    url(r'^dbmgmt/sqltools/sqltoolsgrants$','sqltoolsgrants_edit'),
    url(r'^dbmgmt/sqltools/sqltoolsgrants_del$','sqltoolsgrants_del'),    
    url(r'^dbmgmt/sqltools/sqltoolsgrants_add$','sqltoolsgrants_add'),    

    url(r'^dbmgmt/onlinechange/$','updatesqlList'),
    url(r'^dbmgmt/onlinechange/updatesql_manage$','updatesql_manage'),

    url(r'^serveradmin/$','serveradmin'),
    url(r'^serveradmin/dbserverinfo/$','dbserverinfo'),
    url(r'^serveradmin/getdbserverinfo/$','getdbserverinfo'),

    url(r'^serveradmin/dbserverinfo/envtype=([^/]+)&host=([^/]+)&cluseraddress=([^/]+)/$','dbserverdetail'),
    url(r'^serveradmin/dbserverinfo/serverstatus/envtype=([^/]+)&host=([^/]+)/$','viewserverstatus'),
    url(r'^serveradmin/dbserverinfo/serverstatus/killprocessid/$','killprocessid'),
    url(r'^serveradmin/dbserverinfo/slavestatus/envtype=([^/]+)&host=([^/]+)/$','viewslavestatus'),
    url(r'^serveradmin/dbserverinfo/clusterstatus/envtype=([^/]+)&host=([^/]+)&cluseraddress=([^/]+)&clusername=([^/]+)/$','viewclusterstatus'),
    url(r'^serveradmin/dmlswitchlist/$','dmlswitchlist'),	
    url(r'^serveradmin/dbserverinfo/dmllogmonitor/host=([^/]+)/$','dmllogmonitor'),
    url(r'^serveradmin/dbserverinfo/dmllogmonitor/getDMLLogData$','getDMLLogData'),
    url(r'^serveradmin/dbserverinfo/serverstatus/envtype=([^/]+)&host=([^/]+)/mysqlexplain/dns=([^/]+)&dnsport=([^/]+)&db=([^/]+)&sqlinfo=([^/]+)/$','viewmysqlexplain'),
    
    url(r'^serveradmin/dbserverinfo/returnXls$','returnXls'),
    url(r'^serveradmin/slowlogmonitor/$','slowlogmonitor'),
    url(r'^serveradmin/slowlogmonitor/getSlowLogData$','getSlowLogData'),

    url(r'^dbmgmt/dbcapacitymonitor/$','dbcapacitymonitor'),
    url(r'^dbmgmt/dbcapacitymonitor/getSpecDbCapacityData$','getSpecDbCapacityData'),
    url(r'^dbmgmt/dbcapacitymonitor/getDbCapacityData$','getDbCapacityData'),
    url(r'^dbmgmt/dbcapacitymonitor/getDbCapacityDataDate$','getDbCapacityDataDate'),
    url(r'^dbmgmt/dbcapacitymonitor/getDBDbCapacityData$','getDBDbCapacityData'),
    url(r'^dbmgmt/dbcapacitymonitor/checkConn$','checkConn'),
    url(r'^dbmgmt/dbcapacitymonitor/getConnInfo$','getConnInfo'),
    url(r'^dbmgmt/dbcapacitymonitor/getTableNames$','getTableNames'),
    url(r'^dbmgmt/dbcapacitymonitor/getColumnNames$','getColumnNames'),
    url(r'^dbmgmt/dbcapacitymonitor/getColumnType$','getColumnType'),
    url(r'^dbmgmt/dbcapacitymonitor/getTableType$','getTableType'),

    url(r'^dbmgmt/dbcapacitymonitor/getAutoDataClearConfig$','getAutoDataClearConfig'),
    url(r'^dbmgmt/dbcapacitymonitor/setAutoDataClear$','setAutoDataClear'),
    url(r'^dbmgmt/dbcapacitymonitor/getAttachAutoDataClearConfig$','getAttachAutoDataClearConfig'),
    url(r'^dbmgmt/dbcapacitymonitor/setAttachAutoDataClear$','setAttachAutoDataClear'),
    url(r'^dbmgmt/dbcapacitymonitor/delAttachAutoDataClear$','delAttachAutoDataClear'),
    url(r'^dbmgmt/dbcapacitymonitor/delAutoDataClear$','delAutoDataClear'),
    url(r'^dbmgmt/dbcapacitymonitor/chainJoinKeyToTableName$','chainJoinKeyToTableName'),    
    
    url(r'^dbmgmt/dblist/dbname=([^/]+)/$','changedbinfo'),

    url(r'^i18n/i18n_javascript/$','i18n_javascript'),

         url(r'^serveradmin/dbserverinfo/parseDns$','parseDns'),
         url(r'^serveradmin/dbserverinfo/pingIP$','pingIP'),        

)

