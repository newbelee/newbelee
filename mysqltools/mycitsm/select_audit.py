limit_count = 10000
limit_time = 90

# sqltools_selectsql_list新表，需要创建，存放需审核已经审核通过的select类型sql
# connection为其他地方导入的函数，有默认值



# 需要审核的页面显示,只显示5页，41条(不需要太多)，提交需要审核的select类型sql也从次页面提交
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





# 对查询的sql进行审核，使用chk_sql_select函数拆分sql判断是否合法(非dml都为通过，是否语义错误之类，执行时才显示)

@login_required
def selectsql_insert(request):
    chk_errors = []
    errors = []
    dbname = request.POST.get("dbname")
    form = sqlreviewForm(request.POST)
    chk_errors = chk_sql_select(request)
    if chk_errors:
        context={'form':form,
               'title':'在线查询',
               'errorSqlList':chk_errors,
               'dblist':dbname,
               'databaseId': dbname
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




# request.method == "GET"时，点击编辑或者修改进入的页面 

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


# 需审核的sql，根据提交的状态更新到审核表中

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



#审核管理以及最终执行函数,执行前会再检查一遍sql，防止审核时误操作

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

            context={'form':form,
                     'title':'在线查询',
                     'errorSqlList':exec_errors,
                     'sqlResultDict':sqlResultDict,
                     'field_desc':field_desc,
                     'width':str(100/len(field_desc)) +'%',
                     'dblist':dblist,
                     'dbname': db_name,
                     'time': '{}'.format(round(timer.duration(), 2)),
                     'rowcount':len(sqlResultDict)
            }

            return render(request, 'auditsql_add.html',context)    

    form = sqlreviewForm()
    
    context = {
        'form':form, 
        'title':'在线查询',
        'dblist':dblist,
        'dbname':db_name
    }

    return render(request, 'auditsql_add.html',context)




# 另外增加次功能导致其他需要修改的函数如下：

#执行线程
class execThread(threading.Thread):
    __result = {}
    __result['exec_errors'] = []
    __result['sqlResultDict'] = []
    __result['field_desc'] = []
    
    # 初始化时，原来没有limit_count参数，此处为新加，真正执行失去了是do_execute函数，所以do_execute增加了一个参数
    def __init__(self, thread_id,request, db_conn, db_name, limit_count=100):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.request=request
        self.db_conn = db_conn
        self.db_name = db_name
        self.limit_count = limit_count

    def run(self):
        self.__result =  do_execute(self.request,self.db_conn, self.db_name, self.limit_count)
    def getResult(self):
        return self.__result



# 真正执行sql的函数，增加了limit_count

@login_required
def do_execute(request, db_conn, db_name, limit_count):
    try:
        returncount = 0

        __result = {}
        __result['exec_errors'] = []
        __result['sqlResultDict'] = []
        __result['field_desc'] = []

        result_item = []
        sqlErrorDict={}
        sqlResultDict=[]
        exec_errors = []
        field_desc=[]

        db_conn.autocommit(0)
        db_cur = db_conn.cursor()
        db_cur.connection.autocommit(0)

        sql_parse = sqlparse.parse(request.POST.get('sql',''))        
        sql_item=""
        sql_item = sql_parse[0]
        sql = str(sql_item)

        # 处理 sql 的 limit
        isExistsLimit = 0
        dosql= ""
        islimit = 0
        limit_begin = 0
        limit_end = 0
        idx = 0
        num = ""
        for item in sql_item:     
            if str(item).lower() == "limit":
                islimit = 1
                idx = idx + 1
                continue
            if islimit == 1 and str(item).strip() != ";":
                if str(item).strip() == "":
                    continue
                else:
                    num = str(item).strip().replace(" ", "")
            else:
                dosql = dosql + str(item)        

        if num != "":
            if len(num.split(",")) == 2:
                limit_begin = int(num.split(",")[0])
                limit_end = int(num.split(",")[1])
            else:
                limit_begin = 0
                limit_end = int(num.split(",")[0])

            if int(limit_end) > limit_count:
                limit_end = limit_count            
        else:
            limit_begin = 0
            limit_end = limit_count

        # 去掉结尾的 ; 
        if dosql[-1] == ";":
            dosql = dosql[:-1]

        if sql_item.get_type() == "SELECT":
            dosql = dosql + " limit " + str(limit_begin) + "," + str(limit_end)

        returncount = db_cur.execute(dosql)

        for desc in db_cur.description:
            field_desc.append(desc[0])

        rows = db_cur.fetchall()
        for row in rows:
            line = []
            for i in range(0, len(row)):
                if row[i] ==None:
                    line.append("NULL")
                else:
                    line.append(str(row[i]))
            result_item.append(line)


        sqlResultDict = result_item

        db_conn.rollback()
        db_cur.close()

    except Exception as e:
        field_desc.append("error")
        sqlErrorDict={}
        sqlErrorDict['sql']=str(sql_item)
        sqlErrorDict['error']="execute failed: %s" %(e)
        exec_errors.append(sqlErrorDict)

    
    __result['exec_errors'] = exec_errors
    __result['sqlResultDict'] = sqlResultDict
    __result['field_desc'] = field_desc

    # log
    try:
        upload_cur = connection.cursor()
        sqlstr = """
            insert into sqltools_sqlqry_log(dbid, dbname, username, `sql`, returncount) 
                values(%s, %s, %s, %s, %s)
        """
        param = [request.POST.get('databaseId',''), db_name, request.user.username, str(sql_item), returncount ]
        upload_cur.execute(sqlstr, param)
        upload_cur.connection.commit()
        upload_cur.close()
    except Exception as e:
        upload_cur.close()

    return __result
