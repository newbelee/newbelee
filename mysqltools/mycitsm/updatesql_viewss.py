# -*- coding: utf-8 -*-
import sqlparse
from threading import Timer
from django import forms
import time
import signal
from commonconfig import *
from execute_viewss import *
import ConfigParser
import endecrypt
import os
from django.http import StreamingHttpResponse
import chardet
import MySQLdb
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger


limit_count = 10000
limit_time = 90

reload(sys)
sys.setdefaultencoding('utf-8')

config=ConfigParser.ConfigParser()
cfgfile=open('/var/www/site/mycitsm/mycitsm/login.cnf','r')

config.readfp(cfgfile)

product_user=config.get('mysqllogin','product_user').encode('utf-8')
product_passwd=endecrypt.decrypt(config.get('mysqllogin','product_passwd').encode('utf-8'))

statuslist = [["0", "未审批"], ["1", "正常"], ["2", "审批未通过"], ["3", "执行中"], ["4","执行完成"], ["5","执行失败"]]

# add at 20180201 audit select query function
########################################################
@login_required
def auditsqlList(request):
    errors=[]
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    upload_cur = connection.cursor()
    param = []
    if not request.user.is_superuser:
        db_list = get_dbowner(request.user.username,None)
        if db_list and db_list.get('result') == 0:
            param1 = str(db_list.get('db_list')).replace('[','(').replace(']',')').replace(' u\'','\'').replace('(u','(')
            sql = """
                     select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                         when status = 1 then '正常' 
                         when status = 2 then '未通过' 
                         when status = 3 then '执行中' 
                         when status = 4 then '执行完成' 
                     when status = 5 then '执行失败'
                    end as status_desc,status,
                    retmsg,DataChange_LastTime
                    from sqltools_selectsql_list where dbname in %s or username = %s
                    order by status, id desc limit 41
                  """ % ( param1,"'" + request.user.username + "'" )

        else:
            sql = """ 
                    select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                    	 when status = 1 then '正常' 
                	 when status = 2 then '未通过' 
                	 when status = 3 then '执行中' 
                	 when status = 4 then '执行完成' 
                     when status = 5 then '执行失败'
                    end as status_desc,status,
                    retmsg,DataChange_LastTime
                    from sqltools_selectsql_list where username = %s
                    order by status, id desc limit 41
                """
            param = [request.user.username]
    elif request.user.is_superuser:
        sql = """ 
                select id, dbname, username, `sql`,
                case when status = 0 then '未审批' 
                     when status = 1 then '正常' 
                     when status = 2 then '未通过' 
                     when status = 3 then '执行中' 
                     when status = 4 then '执行完成'
                     when status = 5 then '执行失败'
                end as status_desc,status,
                retmsg,DataChange_LastTime
                from sqltools_selectsql_list
                order by status, id desc limit 41
            """
    upload_cur.execute(sql, param)
    rows = dictFetchall(upload_cur)
    upload_cur.close()

    context = {
        'title':'数据查询',
        'is_superuser':request.user.is_superuser,
        'rows':rows
    }

    return render(request, 'auditsql.html',context)


@login_required
def selectsql_insert(request):
    chk_errors = []
    errors = []
    dblist = getdblist(request)
    dbname = request.POST.get("dbname")
    form = sqlreviewForm(request.POST)
    chk_errors = chk_sql_select(request)
    if chk_errors:
        context={'form':form,
               'title':'在线查询',
               'errorSqlList':chk_errors,
               'dblist':dblist,
               'databaseName': dbname
            }
        return render(request, 'auditsql_add.html',context)

    try:
        sql = """
            insert into sqltools_selectsql_list(dbname, username, `sql`, `status`, retmsg)
            values(%s, %s, %s, %s, %s);
        """ 
        param=[request.POST.get("dbname"), request.user.username, request.POST.get("sql"), 0, ""]

        upload_cur = connection.cursor()
        upload_cur.connection.autocommit(True)
        upload_cur.execute(sql, param)
        upload_cur.connection.commit()
        upload_cur.close()

        errors.append("操作成功")

    except Exception as e:
        errors.append("发生错误：%s" %(e))

    return render_to_response('error.html',{
        'errors':errors,
        'user':request.user.username,
        'title':"提示信息"
    })    

@login_required
def selectsql_getin_select_exec(request):
    param = []
    errors = []
    #取出可用数据库名和ID
    dblist = getdblist(request)

    mid = request.GET.get('id','')
    is_moduleuser = False
    upload_cur = connection.cursor()
    if not request.user.is_superuser:
        db_list = get_dbowner(request.user.username,None)
        if db_list and db_list.get('result') == 0:
            param1 = str(db_list.get('db_list')).replace('[','(').replace(']',')').replace(' u\'','\'').replace('(u','(')
            sql = """ 
                    select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                         when status = 1 then '正常' 
                         when status = 2 then '未通过' 
                         when status = 3 then '执行中' 
                         when status = 4 then '执行完成' 
                    end as status_desc,status,
                    retmsg, backinfo
                    from sqltools_selectsql_list where (dbname in %s or username = %s) and id = %s
                """ % (param1,"'" + request.user.username + "'",mid)
            is_moduleuser = True
        else:
            sql = """ 
                    select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                         when status = 1 then '正常' 
                         when status = 2 then '未通过' 
                         when status = 3 then '执行中' 
                         when status = 4 then '执行完成' 
                    end as status_desc,status,
                    retmsg, backinfo
                    from sqltools_selectsql_list where username = %s and id = %s
                """
            param = [request.user.username, mid]
    elif request.user.is_superuser:
        sql = """ 
                select id, dbname, username, `sql`,
                case when status = 0 then '未审批' 
                     when status = 1 then '正常' 
                     when status = 2 then '未通过' 
                     when status = 3 then '执行中' 
                     when status = 4 then '执行完成' 
                end as status_desc,status,
                retmsg, backinfo
                from sqltools_selectsql_list where id = %s
            """
        param = [mid]

    print(sql)
    upload_cur.execute(sql, param)
    updatesqlinfo = dictFetchall(upload_cur)
    upload_cur.close()

    if not updatesqlinfo:
        errors.append("该修改不存在，或者不是本人提交的")
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user.username,
            'title':"提示信息"
        })

    form = sqlreviewForm({'sql':updatesqlinfo[0]["sql"]})
    
    # 取执行结果
    upload_cur = connection.cursor()
    sql = """
        select `sql`, errormessage, backup_dbname, sequence, stagestatus
        from sqltools_updatesql_log where pid = %s
    """
    param = [mid]
    upload_cur.execute(sql, param)
    exec_result = dictFetchall(upload_cur)
    upload_cur.close()

    mretmsg = []
    mbackinfo = []
    for r in exec_result:
        mretmsg.append({"sql": r["sql"], "error":" [ RESULT ]: " + r["stagestatus"] + " [ ERRMSG ]: " +r["errormessage"]})
        mbackinfo.append([r["sql"], r["backup_dbname"] + "#" + r["sequence"]])

    action = request.GET.get("action")

    context = {
        'form':form, 
        'title':'在线修改',
        'dblist':dblist,
        'databaseName':updatesqlinfo[0]["dbname"],
        'statuslist':statuslist,
        'is_superuser':request.user.is_superuser,
        'is_moduleuser':is_moduleuser,
        'status':str(updatesqlinfo[0]["status"]).strip(),
        'action':action,
        'errorSqlList':mretmsg,
        'actionname':"修  改",
        'mid': updatesqlinfo[0]["id"]
    }
    return render(request, 'auditsql_add.html',context)    

def selectsql_upate(request):
    errors = []
    try:
        if not request.POST.get("dbname"):
            errors.append('请输入 dbname')
        if not request.POST.get("sql"):
            errors.append('请输入 sql')
        if not request.POST.get("mid"):
            errors.append('请输入 修改单号')

        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user.username,
                'title':"Error"
            })

        databaseName = ""

        if request.POST.get("status"):
            sql = """
                update sqltools_selectsql_list
                set dbname = %s, `sql` = %s, status = %s
                where id = %s
            """
            param=[request.POST.get("dbname"), request.POST.get("sql"), request.POST.get("status"), request.POST.get("mid")]
        else:
            sql = """
                update sqltools_selectsql_list
                set dbname = %s, `sql` = %s, status = 0
                where id = %s
            """
            param=[request.POST.get("dbname"), request.POST.get("sql"), request.POST.get("mid")]

        upload_cur = connection.cursor()
        upload_cur.connection.autocommit(True)
        upload_cur.execute(sql, param)
        upload_cur.connection.commit()
        upload_cur.close()

        errors.append("操作成功")

    except Exception as e:
        errors.append("发生错误：%s" %(e))

    return render_to_response('error.html',{
        'errors':errors,
        'user':request.user.username,
        'title':"提示信息"
    })


@login_required
def audit_manage(request):
    errors = []
    param = []
    dblist = getdblist(request)
                
    if request.method == "GET":
        action = request.GET.get("action", "")
        if action == "":
            errors.append('页面不存在！')
        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user.username,
                'title':"Error"
            })     

        if action == "add":            
            databaseName = request.GET.get('dbname','')
            form = sqlreviewForm()
            
            context = {
                'form':form, 
                'title':'在线修改',
                'dblist':dblist,
                'databaseName':databaseName,
                'statuslist':statuslist,
                'action':"add",
                'actionname':"增  加",
                'mid': 0,
                "status":"0"
            }
            return render(request, 'auditsql_add.html',context)
        elif action in ["edit", "exec"] :
            return selectsql_getin_select_exec(request) 
        else:
            errors.append('页面不存在！')
            if errors:
                return render_to_response('error.html',{
                    'errors':errors,
                    'user':request.user.username,
                    'title':"Error"
                }) 

    # POST
    elif request.method == 'POST':
        action = request.GET.get("action", "")
        retno = None
        retmsg = None
        sqlErrorDict={}
        exec_errors=[]
        field_desc=[]
        sqlResultDict=[]
        excel_name = ''
        errors=[]
        form = sqlreviewForm(request.POST)
        if request.POST.get('add'):
            return selectsql_insert(request)
        elif request.POST.get('edit'):
            return selectsql_upate(request)
        elif request.POST.get('exec'):
            chk_errors = chk_sql_select(request)
            if chk_errors:
                context={'form':form,
                         'title':'在线查询',
                         'errorSqlList':chk_errors,
                         'dbname':dblist
                }
                return render(request, 'auditsql_add.html',context)
            sql_id = request.POST.get('mid','')
            sql_check_dbname = """ 
                    select dbname, status from sqltools_selectsql_list  where id = %s """

            sql_check_conn = """select host,port,dbname
                from  sqltools_db_conninfo
                where dbname = %s and type = 'R';"""

            cursor = connection.cursor()
            cursor.execute(sql_check_dbname, [sql_id])
            dbname_info = dictFetchall(cursor)
            cursor.close()
            if len(dbname_info) == 1:
                db_name = dbname_info[0]['dbname']
                status = dbname_info[0]['status']
            else:
                errors.append('执行失败，请联系DBA')
            if errors:
                return render_to_response('error.html',{
                    'errors':errors,
                    'user':request.user.username,
                    'title':"Error"
                }) 

            cursor = connection.cursor()
            cursor.execute(sql_check_conn, [db_name])
            db_connstr = dictFetchall(cursor)
            cursor.close()
            if len(db_connstr) > 0:
                db_host = db_connstr[0]["host"]
                db_port = db_connstr[0]["port"]
                db_name = db_connstr[0]["dbname"]
            else:
                sqlErrorDict={}
                sqlErrorDict['sql']=""
                sqlErrorDict['error']="get dbconect failed: 未找到 db 连接串"
                exec_errors.append(sqlErrorDict)
                sqlResultDict=[]
                field_desc.append("error")   
                context={'form':form,
                         'title':'在线查询',
                         'errorSqlList':exec_errors,
                         'sqlResultDict':sqlResultDict,
                         'field_desc':field_desc,
                         'width':str(100/len(field_desc)) +'%',
                         'dblist':dblist,
                         'dbname': db_name
                }
                return render(request, 'auditsql_add.html',context)                

            # check top table privileges
            (retno, retmsg, tblist) = check_table_priv(request, db_name)
            if retno == -1:
                sqlErrorDict={}
                sqlErrorDict['sql']=""
                sqlErrorDict['error']="没有对象的查询权限: %s" %(tblist)

                exec_errors.append(sqlErrorDict)
                sqlResultDict=[]
                field_desc.append("error")

                context={'form':form,
                         'title':'在线查询',
                         'errorSqlList':exec_errors,
                         'sqlResultDict':sqlResultDict,
                         'field_desc':field_desc,
                         'width':str(100/len(field_desc)) +'%',
                         'dblist':dblist,
                         'dbname': db_name
                }
                return render(request, 'auditsql_add.html',context)

            (retno, retmsg, db_conn_exe) = getdbconnection(db_name,db_host, db_port, "0")
            if retno == -1:
                sqlErrorDict={}
                sqlErrorDict['sql']=""
                sqlErrorDict['error']="get dbconect failed: %s" %(retmsg)
                exec_errors.append(sqlErrorDict)
                sqlResultDict=[]
                field_desc.append("error")

                context={'form':form,
                         'title':'在线查询',
                         'errorSqlList':exec_errors,
                         'sqlResultDict':sqlResultDict,
                         'field_desc':field_desc,
                         'width':str(100/len(field_desc)) +'%',
                         'dblist':dblist,
                         'dbname': db_name
                }
                return render(request, 'auditsql_add.html',context)    
            else:
                db_conn_exe_id = db_conn_exe.thread_id()

            db_conn_kill = getConn(db_host, db_port,db_name)

            exec_errors = []
            field_desc = []
            sqlResultDict=[]           

            __result=None

            timer = ExecutionTime()
            # 调用execThread函数，此函数调用其它函数时，其他函数已写死返回行数为100，故已将那个函数增加一个参数，带默认值为100，不影响原来功能
            execThd = execThread(1,request,db_conn_exe, db_name, limit_count)
            execThd.setDaemon(True)
            execThd.start()          
            execThd.join(limit_time)

            __result = execThd.getResult()

            if len(__result["field_desc"]) > 0:
                exec_errors=__result["exec_errors"]
                sqlResultDict=__result["sqlResultDict"]
                field_desc=__result["field_desc"]
                excel_name = __result["excel_name"]
            else:
                error_mess = {"sql":"","error":"TIMEOUT: max execute time is : {0}s".format(limit_time)}
                exec_errors.append(error_mess)
                field_desc.append("error")
                if db_conn_exe_id > 0:
                    kill_dbconnection(db_conn_exe_id, db_conn_kill)

            if not db_conn_exe:              
                db_conn_exe.close()
            if not db_conn_kill:
                db_conn_kill.close()

            if len(sqlResultDict) == 0 and len(exec_errors) == 0:
               exec_errors.append({"sql":"","error":"没有满足条件的记录"})
               field_desc.append("info")
            # 修改执行过的sql为已完成
            sql_update = "update sqltools_selectsql_list set status=4 where id=%s"
            cursor = connection.cursor()
            cursor.connection.autocommit(True)
#            cursor.execute(sql_update, [sql_id])
            cursor.execute(sql_update, [10000])
            cursor.close()
            # 分页测试
            paginator = Paginator(sqlResultDict, 100)
            page = request.GET.get('page')
            try:
                sqlResultDict = paginator.page(page)
            except PageNotAnInteger:
                sqlResultDict = paginator.page(1)
            except EmptyPage:
                sqlResultDict = paginator.page(paginator.num_pages)
            xlsx_name = excel_name.split('/')[1]
            context={'form':form,
                     'title':'在线查询',
                     'errorSqlList':exec_errors,
                     'sqlResultDict':sqlResultDict,
                     'field_desc':field_desc,
                     'width':str(100/len(field_desc)) +'%',
                     'excel_name':xlsx_name,
                     'dblist':dblist,
                     'dbname': db_name,
                     'time': '{}'.format(round(timer.duration(), 2)),
                     'rowcount':len(sqlResultDict)
            }

            return render(request, 'auditsql_add.html',context)    

    
    context = {
        'form':form, 
        'title':'在线查询',
        'dblist':dblist,
        'dbname':db_name
    }

    return render(request, 'auditsql_add.html',context)
###############################################################################


##get shard dbname
def get_shard_db_name():
    sql = """select dbname from sqltools_db_conninfo where is_shard=1"""
    dbnames = []
    try:
        conn=MySQLdb.connect(host='127.0.0.1',user='root',passwd='8zlYg0Yamgl%qotnmlto',db='mysqluploaddb',port=3306)
        conn.set_character_set('utf8')
        cur=conn.cursor()
        ret=cur.execute(sql)
        result=cur.fetchall()
        for db in result:
            dbnames.append(db[0])
        cur.close()
        conn.close()
        return dbnames
    except MySQLdb.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
        return dbnames

@login_required
def updatesqlList(request):
    errors=[]
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    upload_cur = connection.cursor()
    param = []
    if not request.user.is_superuser:
        db_list = get_dbowner(request.user.username,None)
        if db_list and db_list.get('result') == 0:
            param1 = str(db_list.get('db_list')).replace('[','(').replace(']',')').replace(' u\'','\'').replace('(u','(')
            sql = """
                     select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                         when status = 1 then '正常' 
                         when status = 2 then '未通过' 
                         when status = 3 then '执行中' 
                         when status = 4 then '执行完成' 
                     when status = 5 then '执行失败'
                    end as status_desc,status,
                    retmsg,DataChange_LastTime
                    from sqltools_updatesql_list where dbname in %s or username = %s
                    order by status, id desc limit 41
                  """ % ( param1,"'" + request.user.username + "'" )

        else:
            sql = """ 
                    select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                    	 when status = 1 then '正常' 
                	 when status = 2 then '未通过' 
                	 when status = 3 then '执行中' 
                	 when status = 4 then '执行完成' 
                     when status = 5 then '执行失败'
                    end as status_desc,status,
                    retmsg,DataChange_LastTime
                    from sqltools_updatesql_list where username = %s
                    order by status, id desc limit 41
                """
            param = [request.user.username]
    elif request.user.is_superuser:
        sql = """ 
                select id, dbname, username, `sql`,
                case when status = 0 then '未审批' 
                     when status = 1 then '正常' 
                     when status = 2 then '未通过' 
                     when status = 3 then '执行中' 
                     when status = 4 then '执行完成'
                     when status = 5 then '执行失败'
                end as status_desc,status,
                retmsg,DataChange_LastTime
                from sqltools_updatesql_list
                order by status, id desc limit 41
            """
    upload_cur.execute(sql, param)
    rows = dictFetchall(upload_cur)
    upload_cur.close()

    context = {
        'title':'数据操作',
        'is_superuser':request.user.is_superuser,
        'rows':rows
    }

    return render(request, 'modifysql.html',context)

@login_required
def getdblist(request):
    envId = 4
    cursor = connection.cursor()

    param = []
    #取出可用数据库名和ID
    if request.user.is_superuser:
        sql = """
                select id,  Upload_DBName from  
                    release_dbconfig 
                """
    else:
        db_list = get_dbowner(request.user.username,None)
        if db_list and db_list.get('result') == 0:
            param1 = str(db_list.get('db_list')).replace('[','(').replace(']',')').replace(' u\'','\'').replace('(u','(')
            sql = """
                select distinct dbid as id, dbname as Upload_DBName from  
                    sqltools_user_db 
                    where  dbname in %s or ( username = %s and status = 1 )
                """ % (param1, "'" + request.user.username + "'")
        else:

            sql = """
                select dbid as id, dbname as Upload_DBName from  
                    sqltools_user_db 
                    where username = %s and status = 1
                """
            param = [request.user.username]
    cursor.execute(sql, param)
    dblist = dictFetchall(cursor)
    cursor.close()

    return dblist

@login_required
def updatesql_manage(request):
    errors = []
    param = []
    #取出可用数据库名和ID
    dblist = getdblist(request)

    if request.method == "GET":
        action = request.GET.get("action", "")
        if action == "":
            errors.append('页面不存在！')

        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user.username,
                'title':"Error"
            })        
        if action == "add":            
            databaseName = request.GET.get('databaseName','')
            form = sqlreviewForm()
            
            context = {
                'form':form, 
                'title':'在线修改',
                'dblist':dblist,
                'databaseName':databaseName,
                'statuslist':statuslist,
                'action':"add",
                'actionname':"增  加",
                'mid': 0,
                "status":"0"
            }
            return render(request, 'updatesql_add.html',context)
        elif action in ["edit", "exec"] :
            return updatesql_getin_update_exec(request)
        elif action == "getbk":
            mid = request.GET.get("id", "")
            filename = ""
            retno = 0
            retmsg = ""

            if mid == "":
                errors.append("该记录不存在")
            if errors:
                return render_to_response('error.html',{
                    'errors':errors,
                    'user':request.user.username,
                    'title':"提示信息"
                })
            (retno, retmsg, filename) = gen_backfile(request)
            if retno != 0:
                errors.append("发生错误：" + retmsg)
            if errors:
                return render_to_response('error.html',{
                    'errors':errors,
                    'user':request.user.username,
                    'title':"提示信息"
                })
            
            content = open(filename, "r").read()

            response = StreamingHttpResponse(file_iterator(filename))
            response['Content-Type'] = 'application/octet-stream'
            response['Content-Disposition'] = 'attachment;filename="{0}"'.format(filename)        
            return response
        else:
            errors.append('页面不存在！')
            if errors:
                return render_to_response('error.html',{
                    'errors':errors,
                    'user':request.user.username,
                    'title':"Error"
                }) 
            
    elif request.method == "POST":
        if request.POST.get('chksql'):
            dblist = getdblist(request)
            databaseName = ""
            (retno, retmsg, databaseName) = chk_sql(request)

            form = sqlreviewForm({'sql':request.POST.get("sql", "")})
            mid = request.GET.get("id", "")
            action = request.GET.get("action", "")

            actionname = ""
            status = "0"
            if action == "add":
                actionname = "增  加"
            elif action in ["edit", "exec"]:
                upload_cur = connection.cursor()
                param = []
                actionname = "修  改"
                sql = """ 
                        select id, dbname, username, `sql`,
                        case when status = 0 then '未审批' 
                             when status = 1 then '正常' 
                             when status = 2 then '未通过' 
                             when status = 3 then '执行中' 
                             when status = 4 then '执行完成' 
                        end as status_desc,status,
                        retmsg, backinfo
                        from sqltools_updatesql_list where id = %s
                    """
                param = [mid]

                upload_cur.execute(sql, param)
                updatesqlinfo = dictFetchall(upload_cur)
                upload_cur.close()
                if len(updatesqlinfo) >0:
                    status = str(updatesqlinfo[0]["status"]).strip()

            context={'form':form,
                     'title':'在线查询',
                     'is_superuser':request.user.is_superuser,
                     'errorSqlList':retmsg,
                     'dblist':dblist,
                     'statuslist':statuslist,
                     'mid': request.POST.get("mid"),
                     'action': action,
                     'status':status,
                     'actionname': actionname,
                     'databaseName': databaseName
            }
            return render(request, 'updatesql_add.html',context)
        elif request.POST.get('add'):
            return updatesql_insert(request)
        elif request.POST.get('edit'):
            return updatesql_upate(request)
        elif request.POST.get('exec'):
            return updatesql_execute(request)
        elif request.POST.get('delete'):
            return updatesql_delete(request)            

@login_required
def updatesql_delete(request):
    errors = []
    try:
        if not request.POST.get("id"):
            errors.append('请输入 修改单号')
        if not request.POST.get("status"):
            errors.append('请输入 状态')                    

        if int(request.POST.get("status")) not in [0, 2]:
            errors.append('只有未审批和审批通过记录才能删除')

        if errors:
            response = HttpResponse()
            response['Content-Type'] = "application/json"
            response.write(json.dumps(errors))

            return response

        sql = """
            delete from sqltools_updatesql_list
            where id = %s
        """ 
        param=[str(request.POST.get("id")).strip()]

        upload_cur = connection.cursor()
        upload_cur.connection.autocommit(True)
        upload_cur.execute(sql, param)
        upload_cur.connection.commit()
        upload_cur.close()

        retmsg = "操作成功"

    except Exception as e:
        retmsg = "发生错误：%s" %(e)

    response = HttpResponse()
    response['Content-Type'] = "application/json"
    response.write(json.dumps(retmsg))

    return response

@login_required
def updatesql_execute(request):
    backinfo = []
    upstatus = 0
    errors = []

    sql = """
            select dbname, status from sqltools_updatesql_list  where id = %s
        """
    param = [request.POST.get("mid")]
    upload_cur = connection.cursor()
    upload_cur.execute(sql, param)
    dbinfo = dictFetchall(upload_cur)
    upload_cur.close()
    if len(dbinfo) == 0:                
        errors.append("请输入 db name")

        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user.username,
            'title':"提示信息"
        })

    upstatus = str(dbinfo[0]["status"])
    if upstatus != "1":
        errors.append("该记录不是 [ 正常 ] 状态")

        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user.username,
            'title':"提示信息"
        })

    dblist = getdblist(request)
    databaseName = "" #dbinfo[0]["dbname"]

    (retno, retmsg, databaseName) = chk_sql(request)

    if retno == 0:
        # 执行 sql 
        (retno, retmsg, backinfo) = exec_sql(request, databaseName)
        upload_cur = connection.cursor()
        status = 0
        if retno == 0:
            status = 4
        else:
            status = 5

        sql = """
                update sqltools_updatesql_list set `status` = %s, retmsg = %s, backinfo = %s where id = %s
            """

        mretmsg = ""
        for msg in retmsg:
            mretmsg = mretmsg + "sql: " + msg["sql"] + " -- " + msg["error"] + "\n"
        mbackinfo = ""
        for msg in backinfo:
            mbackinfo = mbackinfo + "sql: " + msg[0] + " -- " + msg[1] + "\n"


        param = [status, mretmsg, mbackinfo, request.POST.get("mid")]
        upload_cur.execute(sql, param)
        upload_cur.connection.commit()
        upload_cur.close()

    dblist = getdblist(request)
    form = sqlreviewForm({'sql':request.POST.get("sql", "")})
    
    context={'form':form,
             'title':'在线查询',
             'errorSqlList':retmsg,
             'dblist':dblist,
             'statuslist':statuslist,
             'mid': request.POST.get("mid"),
             'action':"exec",
             'backinfo':backinfo,
             'actionname':"修  改",
             'databaseName': databaseName
    }
    return render(request, 'updatesql_add.html',context)        

@login_required
def updatesql_getin_update_exec(request):
    param = []
    errors = []
    #取出可用数据库名和ID
    dblist = getdblist(request)

    mid = request.GET.get('id','')
    is_moduleuser = False
    upload_cur = connection.cursor()
    if not request.user.is_superuser:
        db_list = get_dbowner(request.user.username,None)
        if db_list and db_list.get('result') == 0:
            param1 = str(db_list.get('db_list')).replace('[','(').replace(']',')').replace(' u\'','\'').replace('(u','(')
            sql = """ 
                    select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                         when status = 1 then '正常' 
                         when status = 2 then '未通过' 
                         when status = 3 then '执行中' 
                         when status = 4 then '执行完成' 
                    end as status_desc,status,
                    retmsg, backinfo
                    from sqltools_updatesql_list where (dbname in %s or username = %s) and id = %s
                """ % (param1,"'" + request.user.username + "'",mid)
            is_moduleuser = True
        else:
            sql = """ 
                    select id, dbname, username, `sql`,
                    case when status = 0 then '未审批' 
                         when status = 1 then '正常' 
                         when status = 2 then '未通过' 
                         when status = 3 then '执行中' 
                         when status = 4 then '执行完成' 
                    end as status_desc,status,
                    retmsg, backinfo
                    from sqltools_updatesql_list where username = %s and id = %s
                """
            param = [request.user.username, mid]
    elif request.user.is_superuser:
        sql = """ 
                select id, dbname, username, `sql`,
                case when status = 0 then '未审批' 
                     when status = 1 then '正常' 
                     when status = 2 then '未通过' 
                     when status = 3 then '执行中' 
                     when status = 4 then '执行完成' 
                end as status_desc,status,
                retmsg, backinfo
                from sqltools_updatesql_list where id = %s
            """
        param = [mid]

    print(sql)
    upload_cur.execute(sql, param)
    updatesqlinfo = dictFetchall(upload_cur)
    upload_cur.close()

    if not updatesqlinfo:
        errors.append("该修改不存在，或者不是本人提交的")
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user.username,
            'title':"提示信息"
        })

    form = sqlreviewForm({'sql':updatesqlinfo[0]["sql"]})
    
    # 取执行结果
    upload_cur = connection.cursor()
    sql = """
        select `sql`, errormessage, backup_dbname, sequence, stagestatus
        from sqltools_updatesql_log where pid = %s
    """
    param = [mid]
    upload_cur.execute(sql, param)
    exec_result = dictFetchall(upload_cur)
    upload_cur.close()

    mretmsg = []
    mbackinfo = []
    for r in exec_result:
        mretmsg.append({"sql": r["sql"], "error":" [ RESULT ]: " + r["stagestatus"] + " [ ERRMSG ]: " +r["errormessage"]})
        mbackinfo.append([r["sql"], r["backup_dbname"] + "#" + r["sequence"]])

    action = request.GET.get("action")

    context = {
        'form':form, 
        'title':'在线修改',
        'dblist':dblist,
        'databaseName':updatesqlinfo[0]["dbname"],
        'statuslist':statuslist,
        'is_superuser':request.user.is_superuser,
        'is_moduleuser':is_moduleuser,
        'status':str(updatesqlinfo[0]["status"]).strip(),
        'action':action,
        'errorSqlList':mretmsg,
        'backinfo':mbackinfo,
        'actionname':"修  改",
        'mid': updatesqlinfo[0]["id"]
    }
    print(context)
    return render(request, 'updatesql_add.html',context)    

@login_required
def updatesql_upate(request):
    errors = []
    try:
        if not request.POST.get("dbname"):
            errors.append('请输入 dbname')
        if not request.POST.get("sql"):
            errors.append('请输入 sql')
        if not request.POST.get("mid"):
            errors.append('请输入 修改单号')

        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user.username,
                'title':"Error"
            })

        databaseName = ""
        (retno, retmsg, databaseName) = chk_sql(request)
        if retno != 0:
            dblist = getdblist(request)
            form = sqlreviewForm({'sql':request.POST.get("sql", "")})
            context={'form':form,
                     'title':'在线查询',
                     'errorSqlList':retmsg,
                     'dblist':dblist,
                     'statuslist':statuslist,
                     'mid': request.POST.get("mid"),
                     'action':"edit",
                     'actionname':"修  改",
                     'databaseName': databaseName
            }
            return render(request, 'updatesql_add.html',context)   

        if request.POST.get("status"):
            sql = """
                update sqltools_updatesql_list
                set dbname = %s, `sql` = %s, status = %s
                where id = %s
            """
            param=[request.POST.get("dbname"), request.POST.get("sql"), request.POST.get("status"), request.POST.get("mid")]
        else:
            sql = """
                update sqltools_updatesql_list
                set dbname = %s, `sql` = %s, status = 0
                where id = %s
            """
            param=[request.POST.get("dbname"), request.POST.get("sql"), request.POST.get("mid")]

        upload_cur = connection.cursor()
        upload_cur.connection.autocommit(True)
        upload_cur.execute(sql, param)
        upload_cur.connection.commit()
        upload_cur.close()

        errors.append("操作成功")

    except Exception as e:
        errors.append("发生错误：%s" %(e))

    return render_to_response('error.html',{
        'errors':errors,
        'user':request.user.username,
        'title':"提示信息"
    })
@login_required
def updatesql_insert(request):
    errors = []
    try:
        databaseName = ""
        (retno, retmsg, databaseName) = chk_sql(request)
        if retno != 0:
            dblist = getdblist(request)
            form = sqlreviewForm({'sql':request.POST.get("sql", "")})
            context={'form':form,
                     'title':'在线查询',
                     'errorSqlList':retmsg,
                     'dblist':dblist,
                     'statuslist':statuslist,
                     'mid': request.POST.get("mid"),
                     'action':"add",
                     'status':"0",
                     'actionname':"增  加",
                     'databaseName': databaseName
            }   
            return render(request, 'updatesql_add.html',context)   

        sql = """
            insert into sqltools_updatesql_list(dbname, username, `sql`, `status`, retmsg)
            values(%s, %s, %s, %s, %s);
        """ 
        param=[request.POST.get("dbname"), request.user.username, request.POST.get("sql"), 0, ""]

        upload_cur = connection.cursor()
        upload_cur.connection.autocommit(True)
        upload_cur.execute(sql, param)
        upload_cur.connection.commit()
        upload_cur.close()

        errors.append("操作成功")

    except Exception as e:
        errors.append("发生错误：%s" %(e))

    return render_to_response('error.html',{
        'errors':errors,
        'user':request.user.username,
        'title':"提示信息"
    })    

# 检查字符集，将非 utf8 的转换成 utf8
def convertCharactSet(s_str):
    charact_type=chardet.detect(s_str)["encoding"]
    return s_str.decode(charact_type, 'ignore').encode('utf-8')

#
# 检查 sql: 1. 语法是否有错; 2. 影响行数, 单条影响超过 1000 行; 3. 执行的 sql 数不能超过  500
#

@login_required
def chk_sql(request):
    errors = []
    sqlErrorDict={}
    chk_errors = []
    sql_item = []
    retno = 0
    action = request.GET.get("action", "")
    mid = ""
    param = []
    if action == "add":
        if not request.POST.get("dbname", ""):
            sqlErrorDict={}
            sqlErrorDict['sql']=""
            sqlErrorDict['error']="请输入 db name"
            chk_errors.append(sqlErrorDict)
        
        dbname = str(request.POST.get("dbname", ""))
        print dbname
    elif action in ["edit", "exec"]:
        mid = request.GET.get("id", "")
        upload_cur = connection.cursor()
        sql = """
            select dbname from sqltools_updatesql_list  where id = %s
        """
        param = [mid]
        upload_cur.execute(sql, param)
        updatedbinfo = dictFetchall(upload_cur)
        upload_cur.close()

        if len(updatedbinfo) == 0:
            sqlErrorDict={}
            sqlErrorDict['sql']=""
            sqlErrorDict['error']="请输入 db name"
            chk_errors.append(sqlErrorDict)
        else:
            dbname = str(updatedbinfo[0]["dbname"])

    if len(chk_errors) > 0:
        return -1, chk_errors, ""

    try:
        sql = request.POST.get('sql','')
        sql_parse = sqlparse.parse(str(sql).strip())        

        if len(sql_parse) > 200:
            sqlErrorDict={}
            sqlErrorDict['sql']=""
            sqlErrorDict['error']="一次只能查询 200条 sql"
            chk_errors.append(sqlErrorDict)
            return (-1, chk_errors, dbname)

        sql = """
                select b.host, b.port
                from db_conninfo a 
                left join sqltools_db_conninfo b on a.dbname = b.dbname and envt = "生产" and a.dbuser = b.dbuser 
                and type = 'W'
                where b.dbname = %s 
            """

        param = [dbname]
        upload_cur=connection.cursor()
        upload_cur.execute(sql, param)
        dbconn = dictfetchall(upload_cur)
        upload_cur.close()

        if not dbconn:
            sqlErrorDict={}
            sqlErrorDict['sql']=""
            sqlErrorDict['error']="未找到该 db 的连接信息"
            chk_errors.append(sqlErrorDict)
            return (-1, chk_errors, dbname)

        exec_sql="/*--user=%s;--password=%s; --enable-check;--host=%s;--port=%s;*/\
                    inception_magic_start;\
                    use %s;" %(product_user, product_passwd, 
                        str(dbconn[0]["host"]), str(dbconn[0]["port"]), dbname)
        otherdb_error = 0
        for sql_item in sql_parse:
            dblist, tblist = getTbName(request, str(sql_item))
            otherdb_error = 0

            for dbitemname in dblist:
                if dbitemname.lower() != dbname.lower():
                    otherdb_error = 1
                    sqlErrorDict={}
                    sqlErrorDict['sql']=str(sql_item)
                    sqlErrorDict['error']="不允许跨库操作 [ %s ]" %(dbitemname)
                    chk_errors.append(sqlErrorDict)
                    continue           

            if otherdb_error == 0:
                if sql_item.get_type() not in ["INSERT", "UPDATE", "DELETE"]:
                    sqlErrorDict={}
                    sqlErrorDict['sql']=str(sql_item)
                    sqlErrorDict['error']="SQL must be in [ INSERT, UPDATE, DELETE ]"
                    chk_errors.append(sqlErrorDict)                
                else:
                    if str(sql_item).strip()[-1:] != ";":
                        exec_sql = exec_sql + str(sql_item).strip() + ";" 
                    else:
                        exec_sql = exec_sql + str(sql_item).strip()
                

        if len(chk_errors) > 0:
            return (-1, chk_errors, dbname)

        exec_sql = exec_sql + "inception_magic_commit;"
        ince_conn=MySQLdb.connect(host='127.0.0.1',user='',passwd='',db='',port=6669,charset='utf8')
        ince_conn.set_character_set('utf8')
        ince_cur=ince_conn.cursor()
        
        exec_sql = convertCharactSet(exec_sql)

        ret=ince_cur.execute(exec_sql)
        result= dictFetchall(ince_cur)
        ince_cur.close()
        ince_conn.close()
        # check result
        chk_errors = []
     #   if dbname != "credit_center" and dbname != "order_db_shard" and dbname != 'shop_price_center' and dbname != '':
        shard_dbs = get_shard_db_name() 
        if dbname not in shard_dbs:
            for r in result:
                if int(r["errlevel"]) > 0:
                    sqlErrorDict={}
                    sqlErrorDict['sql']=str(r["SQL"])
                    sqlErrorDict['error']="check 失败： %s" %(str(r["errormessage"]))
                    chk_errors.append(sqlErrorDict)
                    retno = -1
                    continue

                if int(r["Affected_rows"]) > 2000:                
                    sqlErrorDict={}
                    sqlErrorDict['sql']=str(r["SQL"])
                    sqlErrorDict['error']="该 sql 影响行数可能超过 2000 ，请转给 dba 手工操作"
                    chk_errors.append(sqlErrorDict)
                    retno = -1

    except Exception as e:
        sqlErrorDict={}
        sqlErrorDict['sql']=str(sql_item)
        sqlErrorDict['error']="sql format failed: %s" %(e)
        chk_errors.append(sqlErrorDict)
        retno = -1
        print chk_errors

    if not chk_errors:
        sqlErrorDict={}
        sqlErrorDict['sql']=""
        sqlErrorDict['error']="check 通过"
        chk_errors.append(sqlErrorDict)

    return (retno, chk_errors, dbname)

#
# 执行 sql
# 返回： retno / retmsg / retBack
#
@login_required
def exec_sql(request, dbname):
    errors = []
    sqlErrorDict={}
    chk_errors = []
    sql_item = []
    retno = 0
    backupinfo = []

    try:
        sql = request.POST.get('sql','')
        sql_parse = sqlparse.parse(str(sql).strip())        

        if len(sql_parse) > 200:
            sqlErrorDict['sql']=""
            sqlErrorDict['error']="一次只能查询 200条 sql"
            chk_errors.append(sqlErrorDict)
            return (-1, chk_errors, [])
        
        sql = """
                select b.host, b.port
                from db_conninfo a 
                left join sqltools_db_conninfo b on a.dbname = b.dbname and envt = "生产" and a.dbuser = b.dbuser 
                and type = 'W'
                where b.dbname = %s 
            """

        param = [dbname]
        upload_cur=connection.cursor()
        upload_cur.execute(sql, param)
        dbconn = dictfetchall(upload_cur)
        upload_cur.close()

        if not dbconn:
            sqlErrorDict['sql']=""
            sqlErrorDict['error']="未找到该 db 的连接信息"
            chk_errors.append(sqlErrorDict)
            return (-1, chk_errors, [])

#        if dbname == 'credit_center' or dbname == 'order_db_shard':
        shard_dbs = get_shard_db_name()
        if dbname in shard_dbs:
            for sql_item in sql_parse:
                if sql_item.get_type() not in ["INSERT", "UPDATE", "DELETE"]:
                    sqlErrorDict['sql']=str(sql_item)
                    sqlErrorDict['error']="SQL must be in [ INSERT, UPDATE, DELETE ]"
                    chk_errors.append(sqlErrorDict)   
                    return (-1, chk_errors, [])             
                else:
                    if str(sql_item).strip()[-1:] != ";":
                        exec_sql = str(sql_item).strip() + ";"
                    else:
                        exec_sql = str(sql_item).strip()
                    ince_conn=MySQLdb.connect(host=str(dbconn[0]["host"]), user=product_user, passwd=product_passwd, db=dbname, port=int(dbconn[0]["port"]), charset='utf8')
                    ince_conn.set_character_set('utf8')
                    ince_cur=ince_conn.cursor()
                    ret=ince_cur.execute(exec_sql)
                    ince_conn.commit()
                    ince_cur.close()
                    ince_conn.close()                
           
        else:
            exec_sql="/*--user=%s;--password=%s; --enable-execute;--host=%s;--port=%s;*/\
                        inception_magic_start;\
                        use %s;" %(
                            product_user, product_passwd, str(dbconn[0]["host"]), 
                            str(dbconn[0]["port"]), dbname)
        
            for sql_item in sql_parse:
                if sql_item.get_type() not in ["INSERT", "UPDATE", "DELETE"]:
                    sqlErrorDict['sql']=str(sql_item)
                    sqlErrorDict['error']="SQL must be in [ INSERT, UPDATE, DELETE ]"
                    chk_errors.append(sqlErrorDict)                
                else:
                    if str(sql_item).strip()[-1:] != ";":
                        exec_sql = exec_sql + str(sql_item).strip() + ";"
                    else:
                        exec_sql = exec_sql + str(sql_item).strip()

            if len(chk_errors) > 0:
                return (-1, chk_errors, [])

            exec_sql = exec_sql + "inception_magic_commit;" 

            ince_conn=MySQLdb.connect(host='127.0.0.1',user='',passwd='',db='',port=6669,charset='utf8')
            ince_conn.set_character_set('utf8')

            ince_cur=ince_conn.cursor()

            ret=ince_cur.execute(exec_sql)
            result= dictFetchall(ince_cur)
            ince_cur.close()
            ince_conn.close()

            # get result, 并写日志表 sqltools_updatesql_log
            upload_cur = connection.cursor()
            pid = request.POST.get("mid", "0")
            username = request.user.username

            sql = """
                insert into sqltools_updatesql_log(
                    pid, dbname, username, stage, errlevel, stagestatus, errormessage, `sql`, affected_rows,
                    sequence, backup_dbname, execute_time, SQLSHA1
                )
                values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
            for r in result:            
                if int(r["errlevel"]) > 0:
                    sqlErrorDict['sql']=str(r["SQL"])
                    sqlErrorDict['error']="执行失败： %s" %(str(r["errormessage"]))
                    chk_errors.append(sqlErrorDict)
                    retno = -1
                else:
                    backupinfo.append([str(r["SQL"]), str(r["backup_dbname"]) + "#" + str(r["sequence"]) ])
                param=[pid, dbname, username, str(r["stage"]), str(r["errlevel"]), str(r["stagestatus"]), 
                        str(r["errormessage"]), str(r["SQL"]), str(r["Affected_rows"]), str(r["sequence"]), 
                        str(r["backup_dbname"]), str(r["execute_time"]), str(r["sqlsha1"])]

                upload_cur.execute(sql,param)
                upload_cur.connection.commit()

            upload_cur.close()

    except Exception as e:        
        sqlErrorDict['sql']=str(sql_item)
        sqlErrorDict['error']="sql format failed: %s" %(e)
        chk_errors.append(sqlErrorDict)
        retno = -1

    if not chk_errors:
        sqlErrorDict['sql']=""
        sqlErrorDict['error']="执行成功"
        chk_errors.append(sqlErrorDict)

    return (retno, chk_errors, backupinfo)

#
# 生成备份文件
# 返回： retno / retmsg / filename
#
@login_required
def gen_backfile(request):
    try:
        mid = request.GET.get("id", "")
        filename = ""
        sql = """
            select dbname, backup_dbname, replace(sequence, "'", "") as sequence
            from sqltools_updatesql_log
            where pid = %s and stage = "EXECUTED"
        """
        param = [mid]
        upload_cur = connection.cursor()
        upload_cur.execute(sql, param)
        exec_result = dictFetchall(upload_cur)
        upload_cur.close()
        filename = "/tmp/tmp_down/" + str(mid) + "_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"

        if len(exec_result) == 0:
            fo = open(filename, "w")
            fo.close()
            return 0, "ok", filename

        back_conn=MySQLdb.connect(host='127.0.0.1',user=product_user,passwd=product_passwd,db=exec_result[0]["backup_dbname"],port=3306,charset='utf8')
        back_cur=back_conn.cursor()

        strwhere = '(' + ','.join(['"'+ item["sequence"] + '"' for item in exec_result]) + ')'

        # get tbname
        sql = """
            select distinct tablename from $_$inception_backup_information$_$
            where opid_time in 
        """
        param = [strwhere]
        back_cur.execute(sql + strwhere)
        tblist = dictFetchall(back_cur)

        fo = open(filename, "w")
        for tbname in tblist:
            back_cur.execute("select rollback_statement from "+ tbname["tablename"] +" where opid_time in " + strwhere)
            backsql = dictFetchall(back_cur)
            for msql in backsql:
                fo.write(str(msql["rollback_statement"]+"\n"))
        fo.close()
        back_cur.close()
        back_conn.close()

        return 0, "ok", filename

    except Exception as e:
        return -1, str(e), filename
