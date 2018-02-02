# -*- coding: utf-8 -*- 
from commonconfig import *
reload(sys)
sys.setdefaultencoding('UTF-8')




@login_required
def changedbinfo(request,dbname):
    errors=[]
    if not request.user.has_perm('mycitsm.changedbinfo'):
        errors.append('对不起，你没有权限进行此操作！')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
        

    #获取业务部门下拉列表
    conn = getConn('127.0.0.1', 3306, 'sqlmonitordb', 'sqlmonitor')
    conn.autocommit(1)
    cursor = conn.cursor()
    cursor.execute("select organization_name From sqlmonitordb.cf_organization")
    departmentList = dictfetchall(cursor)
    cursor.close()
    conn.close()

    cursor = connection.cursor()

    if request.method=='POST':
        description=request.POST.get('description','')
        owner=request.POST.get('owner','')
        department=request.POST.get('department','')
        isinwhitelist=request.POST.get('iswhite','')
        importance=request.POST.get('importance','')
        cursor.execute("replace into db_baseinfo values(%s,%s,%s,%s,%s)",[dbname,description,owner,department,importance])
        if isinwhitelist == '1':
            cursor.execute("replace into sqlreview_white_list(dbname) values(%s)",[dbname])
        elif isinwhitelist == '0':
            cursor.execute("delete from sqlreview_white_list where dbname = %s",[dbname])
        cursor.connection.commit()
        cursor.close()
        return HttpResponseRedirect("/dbmgmt/dblist/")

    cursor.execute("""select a.upload_dbname,ifnull(b.description,'') as description,ifnull(b.owner,'') as owner,department,importance
from Release_DBconfig a
left join db_baseinfo b on a.upload_dbname=b.dbname
where envid=4 and a.upload_dbname=%s""",[dbname])
    dbinfo=dictfetchall(cursor)
    cursor.execute("""select envt,host,port,dbuser,cast(aes_decrypt(Password,%s) as char(50)) as password
From db_conninfo where dbname=%s""",[mysql_aes_encrypt_key,dbname])
    dbconns=dictfetchall(cursor)
    cursor.close()
    cursorwhite=connection.cursor()
    cursorwhite.execute("select 1 from sqlreview_white_list where dbname = %s ",[dbname])
    iswhitesqlreviewdb=cursorwhite.fetchall()
    if len(iswhitesqlreviewdb) == 0:
        iswhite=0
    else:
        iswhite=1
    cursorwhite.close()
    return render_to_response('changedbinfo.html',{
        'user':request.user,
        'title':"修改数据库信息",
        'dbinfo':dbinfo[0],
        'dbconns':dbconns,
        'departmentList':departmentList,
        'showpass':request.user.has_perm('DBMgmt.viewconninfo'),
        'has_perm':request.user.has_perm('DBMgmt.editdbinfo'),
        'iswhite':iswhite
    })
    
def checkConn(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        DNS = postData.get('DNS','').strip()
        port = int(postData.get('port','').strip()) 
        DBName = postData.get('DBName','').strip()   

        canConn = True
        try:
            conn = getConn(DNS, port, DBName,'')
        except:
            canConn = False
        else:
            conn.close()

        message = {
            'canConn':canConn
        }
        
        response.write(json.dumps(message))
        return response


#从库容量表中获取数据库列表用于在下拉框中展示可选数据库        
@login_required
def dbcapacitymonitor(request):

    #构建至存储了DB,Table相关数据(预先计算好的，既便于提高运行速度)的数据库连接(mysqluploaddb)
    mysqluploadCursor = connection.cursor()

    #获取数据库列表以构建数据库选择下拉框
    getDatabaseNameSql = ("select distinct(database_name) as databaseName "
                          " from mysql_data_tablespace_growth_rate order by database_name")


    #获取主机列表以构建主机选择下拉框
    getMachineNameSql = ("select distinct(machine_name) as machineName "
                          " from mysql_data_tablespace_growth_rate order by machine_name")
    
    mysqluploadCursor.execute(getDatabaseNameSql)
    databaseNameList = dictfetchall(mysqluploadCursor)

    mysqluploadCursor.execute(getMachineNameSql)
    machineNameList = dictfetchall(mysqluploadCursor)

    mysqluploadCursor.close()

    context = {
       'title':'DB容量监控',
       'user':request.user,
       'databaseNameList':databaseNameList,
       'machineNameList':machineNameList,
    }

    return render_to_response('dbcapacitymonitor.html',context)


#从表容量表中获取目前最大的插入时间所在日期
@login_required
def getDbCapacityDataDate(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    if request.method == 'POST':
        #构建至存储了DB,Table相关数据的数据库连接(这里是存储了最近一天且包含计算出的增长率的数据库表)
        mysqluploadCursor = connection.cursor()

        #获取数据记录中最大的日期时间
        getMaxDateTimeSql = \
            (" select max(data_time) "
             " from mysql_data_tablespace_growth_rate")

        #获取库表中最近的日期
        mysqluploadCursor.execute(getMaxDateTimeSql)
        maxDateStr = mysqluploadCursor.fetchall()[0][0].strftime('%Y-%m-%d')
        mysqluploadCursor.close()

        message = {
                "dataDate":maxDateStr,
            }
    
        response.write(json.dumps(message))
        return response


#从库容量中获取绘制表格的数据（包含容量和增长率）
@login_required
def getDBDbCapacityData(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    if request.method == 'POST':
        postData = request.POST
        paramType = postData.get('paramType','')

        if paramType == 'DB':
            databaseNamesStr = postData.get('databaseName','')
    
            #解析ajax传过来的序列化后的参数
            #类似于databaseName=abtestdb&databaseName=actcommunitydb
            databaseNamesList = databaseNamesStr.split('&')
            databaseNames = []
            for item in databaseNamesList:
                databaseName = item[item.find('=') + 1 :]
                if databaseName:
                    databaseNames.append(databaseName)
   
            #将提交的数据库列表转换为MySQL SQL语句中IN子句可用的集合形式
            databaseNameSet = '(' + ','.join(['"'+ item + '"' for item in databaseNames]) + ')'

            whereCondition = " where database_name in %s " % databaseNameSet

        elif paramType == 'HOST':
            machineNamesStr = postData.get('machineName','')
            machineNamesList = machineNamesStr.split('&')
            machineNames = []
            for item in machineNamesList:
                machineName = item[item.find('=') + 1 :]
                if machineName:
                    machineNames.append(machineName)

            machineNameSet = '(' + ','.join(['"'+ item + '"' for item in machineNames]) + ')'

            whereCondition = " where machine_name in %s " % machineNameSet


        #构建至存储了DB,Table相关数据的数据库连接(这里是存储了最近一天且包含计算出的增长率的数据库表)
        mysqluploadCursor = connection.cursor() 

        #因为 mysql_data_tablespace_growth_rate 只存在生产环境表的容量数据，
        #而dic_mysql_dbsize_growth_rate存在各环境的库的容量数据，
        #而我们只需生产环境的数据
        getDatabaseInfoSql = \
                        (" select machine_name as machineName, "
                         " database_name as databaseName, "
                         " `database_size(kb)` as databaseSize, "
                         " database_size_growth_rate as databaseSizeGrowthRate "
                         " from dic_mysql_dbsize_growth_rate " 
                         +  whereCondition +
                         " and machine_name in (select distinct(machine_name) from mysql_data_tablespace_growth_rate)")

        mysqluploadCursor.execute(getDatabaseInfoSql)
        databaseInfoList =  dictfetchall(mysqluploadCursor)
        mysqluploadCursor.close()

        #构建dataT能够识别的数据格式
        data = []
        for item in databaseInfoList:
            newList = [
                item["machineName"],
                item["databaseName"],
                item["databaseSize"],
                str(item["databaseSizeGrowthRate"]) + '%',
            ]

            data.append(newList)

        message = {
                "data":data,
            }
    
        response.write(json.dumps(message))
        return response

        
#从库容量和表容量表中获取绘制表格的数据（包含容量和增长率）
@login_required
def getDbCapacityData(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    if request.method == 'POST':
        postData = request.POST

        # databaseNamesStr = postData.get('databaseName','')

        # #解析ajax传过来的序列化后的参数
        # #类似于databaseName=abtestdb&databaseName=actcommunitydb
        # databaseNamesList = databaseNamesStr.split('&')
        # databaseNames = []
        # for item in databaseNamesList:
        #     databaseName = item[item.find('=') + 1 :]
        #     if databaseName:
        #         databaseNames.append(databaseName)

        # #算是另一种形式的服务器端验证吧
        # #防止非法参数传入SQL语句，而已空结果的形式提醒用户没有选择数据库
        # if not databaseNames:
        #     message = {
        #         "data":[],
        #     }
      
        #     response.write(json.dumps(message))
        #     return response

        # #将提交的数据库列表转换为MySQL SQL语句中IN子句可用的集合形式
        # databaseNameSet = '(' + ','.join(['"'+ item + '"' for item in databaseNames]) + ')'

        databaseName = postData.get('databaseName','')
        machineName = postData.get('machineName','')

        #构建至存储了DB,Table相关数据的数据库连接(这里是存储了最近一天且包含计算出的增长率的数据库表)
        mysqluploadCursor = connection.cursor()
        
        #因为 mysql_data_tablespace_growth_rate 只存在生产环境表的容量数据，
        #而dic_mysql_dbsize_growth_rate存在各环境的库的容量数据，
        #因此join条件中药引入 a.machine_name = b.machine_name 这一限定条件
        getDatabaseInfoSql = \
                        (" select a.machine_name as machineName, "
                         " a.database_name as databaseName, "
                         " b.`database_size(kb)` as databaseSize, "
                         " b.database_size_growth_rate as databaseSizeGrowthRate, "
                         " a.table_name as tableName, "
                         " a.data_clear as dataClear, "
                         " a.row_count as rowCount, "
                         " a.row_count_growth_rate as rowCountGrowthRate, "
                         " a.reserved_kb as reservedKb, "
                         " a.reserved_kb_growth_rate as reservedKbGrowthRate "
                         " from mysql_data_tablespace_growth_rate as a "
                         " left join dic_mysql_dbsize_growth_rate as b "
                         " on a.database_name = b.database_name "
                         " and a.machine_name = b.machine_name "
                         " where a.database_name = '%s' "
                         " and a.machine_name = '%s' ") \
                          % (databaseName, machineName)

        # getDatabaseInfoSql = \
        #         (" select b.machine_name as machineName, "
        #             " b.database_name as databaseName, "
        #             " b.`database_size(kb)` as databaseSize, "
        #             " b.database_size_growth_rate as databaseSizeGrowthRate, "
        #             " a.table_name as tableName, "
        #             " a.data_clear as dataClear, "
        #             " a.row_count as rowCount, "
        #             " a.row_count_growth_rate as rowCountGrowthRate, "
        #             " a.reserved_kb as reservedKb, "
        #             " a.reserved_kb_growth_rate as reservedKbGrowthRate "
        #             " from dic_mysql_dbsize_growth_rate as b "
        #             " left join  mysql_data_tablespace_growth_rate as a "
        #             " on b.machine_name = a.machine_name"
        #             " and b.database_name = a.database_name "
        #             " where b.database_name in %s ") \
        #             % (databaseNameSet)
                    

        mysqluploadCursor.execute(getDatabaseInfoSql)
        databaseInfoList =  dictfetchall(mysqluploadCursor)
        mysqluploadCursor.close()

        #构建dataT能够识别的数据格式
        data = []
        for item in databaseInfoList:
            newList = [
                item["machineName"],
                item["databaseName"],
                item["databaseSize"],
                str(item["databaseSizeGrowthRate"]) + '%',
                item["tableName"],
                '否' if ( item["dataClear"] and int(item["dataClear"])) == 0 else '是',
                item["rowCount"],
                str(item["rowCountGrowthRate"]) + '%',
                item["reservedKb"],
                str(item["reservedKbGrowthRate"]) + '%',
            ]

            data.append(newList)

        message = {
                "data":data,
            }
    
        response.write(json.dumps(message))
        return response
 
#从库容量和表容量表中获取某个表/库相关的数据数据 
@login_required        
def getSpecDbCapacityData(request):
     response = HttpResponse()
     response['Content-Type'] = "application/json"
     
     if request.method == 'POST':
        postData = request.POST
        machineName = postData.get('machineName','')
        databaseName = postData.get('databaseName','')
        tableName = postData.get('tableName','')
        category = postData.get('category','')
      
        databaseSizeData = []
        rowCountData = []
        reservedKbData = []

        #取90天以内的数据
        today = datetime.date.today()
        timedelta = datetime.timedelta(days=-90)
        beginTime = (today + timedelta).strftime('%Y-%m-%d')

        #构建至存储了DB,Table相关数据的数据库连接(sqlmonitordb)
        sqlMonitorConn = getConn(sqlMonitorServer, sqlMonitorPort, sqlMonitorDb,'sqlmonitor')
        sqlMonitorCursor = sqlMonitorConn.cursor()

        #依据客户端提交的不同请求拉取不同的数据
        #dic_mysql_dbsize包含各环境的数据
        #要使用machine_name限定
        if category == 'databaseSize':
            sql = (" select `database_size(kb)` as databaseSize, "
                    " unix_timestamp(insert_timestamp)*1000 as `timeStamp` "
                    " from dic_mysql_dbsize "
                    " where machine_name=%s"
                    " and database_name=%s "
                    " and insert_timestamp>%s " )
            param = [machineName, databaseName, beginTime]

            sqlMonitorCursor.execute(sql, param)
            result = sqlMonitorCursor.fetchall()
            sqlMonitorCursor.close()
            sqlMonitorConn.close()

            for databaseSize, timeStamp in result:
                databaseSizeData.append([timeStamp, int(databaseSize)])

            #构建highchart能够使用的数据格式
            message = {
                'machineName':machineName,
                'databaseName':databaseName,
                'tableName': tableName,
                'category':category,
                'databaseSizeData':databaseSizeData,
            }
         
            response.write(json.dumps(message))
            return response

        #mysql_data_tablespace只存在生产环境表的容量数据
        ##无要使用machine_name限定
        elif category == 'rowCount':
            sql = (" select row_count as rowCount, "
                    " unix_timestamp(insert_timestamp)*1000 as `timeStamp` "
                    " from mysql_data_tablespace "
                    " where database_name=%s "
                    " and table_name=%s"
                    " and insert_timestamp>%s " )
            param = [databaseName, tableName, beginTime]

            sqlMonitorCursor.execute(sql, param)
            result = sqlMonitorCursor.fetchall()
            sqlMonitorCursor.close()
            sqlMonitorConn.close()

            for rowCount, timeStamp in result:
                rowCountData.append([timeStamp, int(rowCount)])

            message = {
                'machineName':machineName,
                'databaseName':databaseName,
                'tableName': tableName,
                'category':category,
                'rowCountData':rowCountData,
            }
         
            response.write(json.dumps(message))
            return response

        elif category == 'reservedKb':
            sql = (" select reserved_kb as reservedKb, "
                    " unix_timestamp(insert_timestamp)*1000 as `timeStamp` "
                    " from mysql_data_tablespace "
                    " where database_name=%s "
                    " and table_name=%s"
                    " and insert_timestamp>%s " )
            param = [databaseName, tableName, beginTime]

            sqlMonitorCursor.execute(sql, param)
            result = sqlMonitorCursor.fetchall()
            sqlMonitorCursor.close()
            sqlMonitorConn.close()

            for reservedKb, timeStamp in result:
                reservedKbData.append([timeStamp, int(reservedKb)])

            message = {
                'machineName':machineName,
                'databaseName':databaseName,
                'tableName': tableName,
                'category':category,
                'reservedKbData':reservedKbData,
            }
         
            response.write(json.dumps(message))
            return response
