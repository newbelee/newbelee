# -*- coding: utf-8 -*- 
from commonconfig import *
reload(sys)
sys.setdefaultencoding('UTF-8')


############################################
###
############################################
@login_required
def getAutoDataClearConfig(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        databaseName = postData.get('databaseName','')
        tableName = postData.get('tableName','')

        #构建至存储了数据库表自动清理配置的数据库连接(VMS0170-autodatacleardb)
        autoDataClearConn = getConn(autoDataClearServer, autoDataClearPort, autoDataClearDB,'')
        autoDataClearCursor = autoDataClearConn.cursor()

        #获取指定的数据库.数据表的清理配置
        getAutoClearSettingSql = \
            ("select "
            " id, "
            " dns, "
            " port, "
            " priority, "
            " type, "
            " dbname, "
            " tbname, "
            " colname, "
            " keep_days, "
            " del_time_step, "
            " tstep_type, "
            " del_row_step, "
            " punit, "
            " pkeepcnt, "
            " pprecnt, "
            " pperunit, "
            " clearwindow_start, "
            " clearwindow_end, "
            " run_sleep, "
            " status, "
            " lastsuccess_time, "
            " mintime, "
            " join_key, "
            " timeunit, "
            " batchid "
            " from autoclear_setting "
            " where dbname=%s "
            " and tbname=%s "
            " limit 1")

        param = [databaseName, tableName]
        autoDataClearCursor.execute(getAutoClearSettingSql, param)
        autoClearSetting = autoDataClearCursor.fetchall()
        autoDataClearCursor.close()
        autoDataClearConn.close()

        if autoClearSetting:
            for (id, dns, port, priority, type, dbname, tbname, colname, 
                keep_days, del_time_step, tstep_type, del_row_step, punit, 
                pkeepcnt, pprecnt, pperunit, clearwindow_start, clearwindow_end, 
                run_sleep, status, lastsuccess_time, mintime, join_key, timeunit, batchid) in autoClearSetting:

                message = {
                    'hasAutoClearSetting':True,
                    'ID':id,
                    'DNS':dns,
                    'port':port,
                    'priority':priority,
                    'type':type,
                    'DBName':dbname,
                    'tableName':tbname,
                    'columnName':colname,
                    'keepDays':keep_days,
                    'delTimeStep':del_time_step,
                    'timeStepType':tstep_type,
                    'delRowStep':del_row_step,
                    'partitionUnit':punit,
                    'partitionKeepCount':pkeepcnt,
                    'partitionPreCount':pprecnt,
                    'partitionPerUnit':pperunit,
                    'clearWindowStart':str(clearwindow_start),
                    'clearWindowEnd':str(clearwindow_end),
                    'runSleep':run_sleep,
                    'status':status,
                    'lastSuccessTime':str(lastsuccess_time),
                    'minTime':str(mintime),
                    'joinKey':join_key,
                    'timeUnit':timeunit,
                    'batchID':batchid
                }

        else: 
            message = {
                'hasAutoClearSetting':False,
            }
    
        response.write(json.dumps(message))
        return response

@login_required
def setAutoDataClear(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    hasPerm = request.user.has_perm('DBMgmt.set_auto_data_clear')
    if not hasPerm:
        message = {
            'hasPerm':hasPerm,
        }    
        response.write(json.dumps(message))
        return response
    
    if request.method == 'POST':
        postData = request.POST
        
        hasAutoClearSetting = postData.get('hasAutoClearSetting','')
        ID = int(postData.get('ID').strip()) if postData.get('ID') else ''
        DNS = postData.get('DNS','').strip() 
        port = int(postData.get('port',''))
        priority = int(postData.get('priority',''))
        type = int(postData.get('type',''))
        DBName = postData.get('DBName','')
        tableName = postData.get('tableName','')
        columnName = postData.get('columnName','')

        ##添加cluster##
        tmpconn = getConn(DNS,port,DBName, '')
        tmpconn.autocommit(1)
        tmpcursor = tmpconn.cursor()
        sql="select @@hostname"
        tmpcursor.execute(sql)
        tempmachinename=tmpcursor.fetchall()[0][0]
        tmpcursor.close()
        tmpconn.close()        
        tmpconn = getConn('127.0.0.1', 3306, 'sqlmonitordb', 'sqlmonitor')
        tmpconn.autocommit(1)
        tmpcursor = tmpconn.cursor()
        sql="select cluster_name from cf_mysql_cluster where machine_name='%s' limit 1" % (tempmachinename)
        tmpcursor.execute(sql)
        tempclustername=tmpcursor.fetchall()[0][0]
        tmpcursor.close()
        tmpconn.close()
        ###############

        keepDays = int(postData.get('keepDays')) if postData.get('keepDays') else None
        delTimeStep = int(postData.get('delTimeStep')) if postData.get('delTimeStep') else None
        timeStepType = postData.get('timeStepType',None)
        delRowStep = int(postData.get('delRowStep')) if postData.get('delRowStep') else None
        joinKey = postData.get('joinKey',None)
        timeUnit = postData.get('timeUnit',None)

        partitionUnit = postData.get('partitionUnit',None)
        partitionKeepCount = int(postData.get('partitionKeepCount')) if postData.get('partitionKeepCount') else None
        partitionPreCount = int(postData.get('partitionPreCount')) if postData.get('partitionPreCount') else None
        partitionPerUnit = postData.get('partitionPerUnit',None)

        clearWindowStart = postData.get('clearWindowStart','').strip()
        clearWindowEnd = postData.get('clearWindowEnd','').strip()
        batchID = int(postData.get('batchID',''))
        runSleep = int(postData.get('runSleep',''))
        status = int(postData.get('status',''))
          
        #构建至存储了数据库表自动清理配置的数据库连接(VMS0170-autodatacleardb)
        autoDataClearConn = getConn(autoDataClearServer, autoDataClearPort, autoDataClearDB,'')
        autoDataClearCursor = autoDataClearConn.cursor()
        autoDataClearConn.autocommit(0)

        #获取指定的数据库.数据表的附表清理配置
        getAttachAutoClearSettingSql = \
            (" select id "
             " from autoclear_attach_setting "
             " where pid=%s")

        updateAutoClearSettingSql = \
            (" update autoclear_setting "
            " set dns=%s, "
            " port=%s, "
            " priority=%s, "
            " type=%s, "
            " colname=%s, "
            " keep_days=%s, "
            " del_time_step=%s, "
            " tstep_type=%s, "
            " del_row_step=%s, "
            " punit=%s, "
            " pkeepcnt=%s, "
            " pprecnt=%s, "
            " pperunit=%s, "
            " clearwindow_start=%s, "
            " clearwindow_end=%s, "
            " run_sleep=%s, "
            " status=%s, "
            " join_key=%s, "
            " timeunit=%s, "
            " batchid=%s "
            " where id=%s ")

        insertAutoClearSettingSql = \
           (" insert into autoclear_setting "
            " (dns, "
            " port, "
            " priority, "
            " type, "
            " dbname, "
            " tbname, "
            " colname, "
            " keep_days, "
            " del_time_step, "
            " tstep_type, "
            " del_row_step, "
            " punit, "
            " pkeepcnt, "
            " pprecnt, "
            " pperunit, "
            " clearwindow_start, "
            " clearwindow_end, "
            " run_sleep, "
            " status, "
            " join_key, "
            " timeunit, "
            " batchid, "
            " cluster) values "
            " (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")


        #依据获取的表单数据删除配置
        #先判断是否存在附表的配置，若存在则需先通知删除附表配置
        param = [ID,]
        attachAutoClearSettingCnt = autoDataClearCursor.execute(getAttachAutoClearSettingSql, param)

        if not joinKey and attachAutoClearSettingCnt > 0:
            message = {
                'hasPerm':hasPerm,
                'hasAutoClearSetting':hasAutoClearSetting,
                'hasAttachAutoClearSetting':True,
            }

            response.write(json.dumps(message))
            return response


        #依据获取的表单数据更新或者插入配置
        n = 0
        insertID = 0
        if hasAutoClearSetting == "true"  and ID:
            opType = "update"
            param = [DNS,port,priority,type,columnName,
                keepDays,delTimeStep,timeStepType,delRowStep,partitionUnit,
                partitionKeepCount,partitionPreCount,partitionPerUnit,clearWindowStart,
                clearWindowEnd,runSleep,status,joinKey,timeUnit,batchID,ID]
            
            n =autoDataClearCursor.execute(updateAutoClearSettingSql, param)
              
        elif hasAutoClearSetting == "false" and not ID:
            opType = "insert"
            param = [DNS,port,priority,type,DBName,tableName,columnName,
                keepDays,delTimeStep,timeStepType,delRowStep,partitionUnit,
                partitionKeepCount,partitionPreCount,partitionPerUnit,clearWindowStart,
                clearWindowEnd,runSleep,status,joinKey,timeUnit,batchID,tempclustername]
            
            n =autoDataClearCursor.execute(insertAutoClearSettingSql, param)
            insertID = int(autoDataClearCursor.lastrowid)
        
        if n == 1:
            autoDataClearConn.commit()
            #同时更新mysql_data_tablespace_growth_rate表中的data_clear字段
            cursor=connection.cursor()
            sql = "update mysql_data_tablespace_growth_rate set data_clear = 1 where database_name=%s and table_name=%s"
            param = [DBName, tableName]      
            cursor.execute(sql, param)
            cursor.connection.commit()
            cursor.close()

        else:
            autoDataClearConn.rollback()

        autoDataClearCursor.close()
        autoDataClearConn.close()

        message = {
                'hasPerm':hasPerm,
                'hasAutoClearSetting':hasAutoClearSetting,
                'hasAttachAutoClearSetting':False,
                'opType':opType,
                'status':n,
                'insertID':insertID 
            }

        response.write(json.dumps(message))
        return response

@login_required
def delAutoDataClear(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    hasPerm = request.user.has_perm('DBMgmt.set_auto_data_clear')
    if not hasPerm:
        message = {
            'hasPerm':hasPerm,
        }    
        response.write(json.dumps(message))
        return response
    
    if request.method == 'POST':
        postData = request.POST  
        ID = int(postData.get('ID','').strip()) if postData.get('ID','') else postData.get('ID','')
        DBName = postData.get('DBName','')
        tableName = postData.get('tableName','')
       
        #构建至存储了数据库表自动清理配置的数据库连接(VMS0170-autodatacleardb)
        autoDataClearConn = getConn(autoDataClearServer, autoDataClearPort, autoDataClearDB,'')
        autoDataClearCursor = autoDataClearConn.cursor()
        autoDataClearConn.autocommit(0)

        #获取指定的数据库.数据表的附表清理配置
        getAttachAutoClearSettingSql = \
            (" select id "
             " from autoclear_attach_setting "
             " where pid=%s")

        deleteAutoClearSettingSql = \
            (" delete from autoclear_setting "
             " where id=%s ")

        #依据获取的表单数据删除配置
        #先判断是否存在附表的配置，若存在则需先通知删除附表配置
        status = 0
        param = [ID,]
        attachAutoClearSettingCnt = autoDataClearCursor.execute(getAttachAutoClearSettingSql, param)

        if attachAutoClearSettingCnt <= 0:  
            status = autoDataClearCursor.execute(deleteAutoClearSettingSql, param)

            if status == 1:
                autoDataClearConn.commit()
                #同时更新mysql_data_tablespace_growth_rate表中的data_clear字段
                cursor=connection.cursor()
                sql = "update mysql_data_tablespace_growth_rate set data_clear = 0 where database_name=%s and table_name=%s"
                param = [DBName, tableName]      
                cursor.execute(sql, param)
                cursor.connection.commit()
                cursor.close()
            else:
                autoDataClearConn.rollback()

            autoDataClearCursor.close()
            autoDataClearConn.close()

            message = {
                    'hasPerm':hasPerm,
                    'status':status,
                    'attachAutoClearSettingCnt':attachAutoClearSettingCnt,
                }
                
        message = {
                    'hasPerm':hasPerm,
                    'status':status,
                    'attachAutoClearSettingCnt':attachAutoClearSettingCnt,
                }
                
        response.write(json.dumps(message))
        return response
        
@login_required
def getAttachAutoDataClearConfig(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST

        PID = int(postData.get('PID','').strip()) if postData.get('PID','') else postData.get('PID','')    
        
        #构建至存储了数据库表自动清理配置及相关附表配置的数据库连接(VMS0170-autodatacleardb)
        autoDataClearConn = getConn(autoDataClearServer, autoDataClearPort, autoDataClearDB,'')
        autoDataClearCursor = autoDataClearConn.cursor()

        #获取指定的数据库.数据表的清理配置
        getAttachAutoClearSettingSql = \
            (" select id, "
             " dbname, "
             " tbname, "
             " pid, "
             " join_key "
             " from autoclear_attach_setting "
             " where pid=%s")

        param = [PID,]
        autoDataClearCursor.execute(getAttachAutoClearSettingSql, param)
        attachAutoClearSetting = autoDataClearCursor.fetchall()
    
        autoDataClearCursor.close()
        autoDataClearConn.close()

        attachAutoClearSettingList = []
        if attachAutoClearSetting:
            for id, dbname, tbname, pid, join_key in attachAutoClearSetting:
                attachAutoClearSettingItem = {
                    'ID':id,
                    'DBName':dbname,
                    'tableName':tbname,
                    'PID':pid,
                    'joinKey':join_key,
                }

                attachAutoClearSettingList.append(attachAutoClearSettingItem)
            message = {
                    'hasAttachAutoClearSetting':True,
                    'attachAutoClearSettingList':attachAutoClearSettingList,              
            }    

        else: 
            message = {
                'hasAttachAutoClearSetting':False,
            }
    
        response.write(json.dumps(message))
        return response

@login_required
def setAttachAutoDataClear(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    hasPerm = request.user.has_perm('DBMgmt.set_auto_data_clear')
    if not hasPerm:
        message = {
            'hasPerm':hasPerm,
        }    
        response.write(json.dumps(message))
        return response
    
    if request.method == 'POST':
        postData = request.POST
        
        hasAttachAutoClearSetting = postData.get('hasAttachAutoClearSetting','')
        ID = int(postData.get('ID','').strip()) if postData.get('ID','') else postData.get('ID','')
        PID = int(postData.get('PID','').strip()) if postData.get('PID','') else postData.get('PID','')
        DBName = postData.get('DBName','').strip()
        tableName = postData.get('tableName','').strip()
        joinKey = postData.get('joinKey','').strip()
        
        #构建至存储了数据库表自动清理配置的数据库连接(VMS0170-autodatacleardb)
        autoDataClearConn = getConn(autoDataClearServer, autoDataClearPort, autoDataClearDB,'')
        autoDataClearCursor = autoDataClearConn.cursor()
        autoDataClearConn.autocommit(0)

        updateAttachAutoClearSettingSql = \
            (" update autoclear_attach_setting "
            " set dbname=%s, "
            " tbname=%s, "
            " join_key=%s "
            " where id=%s ")

        insertAttachAutoClearSettingSql = \
           (" insert into autoclear_attach_setting "
            " (dbname, "
            " tbname, "
            " pid, "
            " join_key) values "
            " (%s, %s, %s, %s)")


        #依据获取的表单数据更新或者插入配置
        status = 0
        insertID = 0
        if ID:
            opType = "update"
            param = [DBName, tableName, joinKey, ID]    
            status = autoDataClearCursor.execute(updateAttachAutoClearSettingSql, param)
        elif not ID:
            opType = "insert"
            param = [DBName, tableName, PID, joinKey]          
            status =autoDataClearCursor.execute(insertAttachAutoClearSettingSql, param)
            insertID = int(autoDataClearCursor.lastrowid)

        if status == 1:
            autoDataClearConn.commit()
        else:
            autoDataClearConn.rollback()

        autoDataClearCursor.close()
        autoDataClearConn.close()

        message = {
                'hasPerm':hasPerm,
                'hasAttachAutoClearSetting':hasAttachAutoClearSetting,
                'opType':opType,
                'status':status,
                'insertID':insertID 
            }
            
        response.write(json.dumps(message))
        return response

@login_required
def delAttachAutoDataClear(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"

    hasPerm = request.user.has_perm('DBMgmt.set_auto_data_clear')
    if not hasPerm:
        message = {
            'hasPerm':hasPerm,
        }    
        response.write(json.dumps(message))
        return response

    if request.method == 'POST':
        postData = request.POST
        
        ID = int(postData.get('ID','').strip()) if postData.get('ID','') else postData.get('ID','')
        PID = int(postData.get('PID','').strip()) if postData.get('PID','') else postData.get('PID','')
       
        #构建至存储了数据库表自动清理配置的数据库连接(VMS0170-autodatacleardb)
        autoDataClearConn = getConn(autoDataClearServer, autoDataClearPort, autoDataClearDB,'')
        autoDataClearCursor = autoDataClearConn.cursor()
        autoDataClearConn.autocommit(0)

        #获取指定的数据库.数据表的清理配置
        getAttachAutoClearSettingSql = \
            (" select id "
             " from autoclear_attach_setting "
             " where pid=%s")

        deleteAttachAutoClearSettingSql = \
            (" delete from autoclear_attach_setting "
             " where id=%s ")

        #依据获取的表单数据删除配置
        status = 0
        param = [ID,]    
        status = autoDataClearCursor.execute(deleteAttachAutoClearSettingSql, param)

        param = [PID,]
        attachAutoClearSettingCnt = 0
        attachAutoClearSettingCnt = autoDataClearCursor.execute(getAttachAutoClearSettingSql, param)
        attachAutoClearSetting = autoDataClearCursor.fetchall()

        if status == 1:
            autoDataClearConn.commit()
        else:
            autoDataClearConn.rollback()

        autoDataClearCursor.close()
        autoDataClearConn.close()

        message = {
                'hasPerm':hasPerm,
                'status':status,
                'attachAutoClearSettingCnt':attachAutoClearSettingCnt 
            }
            
        response.write(json.dumps(message))
        return response

