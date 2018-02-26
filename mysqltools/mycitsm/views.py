# -*- coding: utf-8 -*- 
from commonconfig import *
from dbsize_viewss import *
from dbclear_viewss import *
from dns_viewss import *
from execute_viewss import *
from sqltoolsgrants import *
from updatesql_viewss import *

from django.contrib.auth.models import User
import ldap  

reload(sys)
sys.setdefaultencoding('UTF-8')


# 使用 django authenticate函数认证
def login(request):
    errors=[]
    if request.method=='POST':
        if not request.POST.get('username',''):
            errors.append('Enter username.')
        if not request.POST.get('password',''):
            errors.append('Enter password.')
        if not errors:
            user = auth.authenticate(username=request.POST.get('username'),password=request.POST.get('password'))
            if user is not None and user.is_active:
                auth.login(request,user)
                return HttpResponseRedirect("/")
            else:
                errors.append("Sorry, that's not a valid username or password.")
    return render_to_response('login.html',{
        'errors':errors,
        'username':request.POST.get('username',''),
        'password':request.POST.get('password',''),
        'title':"Login",
    })


# 登出
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/accounts/login/")

# 用户注册
def userreg(request):
    errors=[]
    if request.method=='POST':
        if not request.POST.get('username'):
            errors.append('Enter username.')
        if not request.POST.get('pwd'):
            errors.append('Enter password.')

        if not request.POST.get('email'):
            errors.append('Enter email.')
        if errors:    
            response = HttpResponse()
            response['Content-Type'] = "application/json"
            response.write(json.dumps(errors))

            return response

        if not errors:
            username = request.POST.get("username", "")
            email = request.POST.get("email", "")
            pwd = request.POST.get("pwd", "")
            try:
                user = User.objects.create_user(username, email, pwd)
                user.last_name = username
                user.first_name = username
                user.is_staff = 1
                user.save()
                errors = "用户注册成功： 用户名： %s  密码: %s" %(username, pwd)

            except Exception as e:
                errors = "用户注册失败： %s" %(e)
            
            response = HttpResponse()
            response['Content-Type'] = "application/json"
            response.write(json.dumps(errors))

            return response

    return render_to_response('userreg.html',{
        'errors':errors,
        'username':request.POST.get('username',''),
        'password':request.POST.get('password',''),
        'title':"用户注册",
    })



@login_required
def index(request):
    #if not request.user.is_authenticated():
    #    return HttpResponseRedirect("/login/")
    return render_to_response('index.html',{
        'user':request.user,
        'title':"Home",
    })

@login_required
def setpwd(request):
    retmsg = ""
    retno = 0
    pwd=request.POST.get('pwd','')
    muser=request.POST.get('user','')

    if muser == "":
        retmsg = "该用户不存在"
    else:
        try:        
            u = User.objects.get(username=muser)
            u.set_password(pwd)
            u.save()
            retno = 0
            retmsg = "重置完成"
        except Exception as e:
            retno = -1
            retmsg = "重置失败： %s" %(e)

    # message = {
    #         'returnno':retno,
    #         'content':retmsg
    #     }

    response = HttpResponse()
    response['Content-Type'] = "application/json"
    response.write(json.dumps(retmsg))

    return response

@login_required
def admin(request):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    return render_to_response('admin.html',{
        'user':request.user,
        'title':"Administration",
    })

def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]

def statusfetch(cursor):
    dict={} 
    for row in cursor.fetchall():
        dict[row[0]]=row[1]
    return dict


@login_required
def showuser(request):
    errors=[]
    if not request.user.is_superuser:
        cursor = connection.cursor()
        q=request.GET.get('q')
        if q:
            cursor.execute("select username,last_name as name,email,is_superuser,date_add(last_login,interval 8 hour) as last_login from auth_user where locate(%s,username)>0 and username = %s order by is_superuser desc,username",[q, request.user])
        else:
            cursor.execute('select username,last_name as name,email,is_superuser,date_add(last_login,interval 8 hour) as last_login from auth_user where username = %s order by is_superuser desc,username',[request.user])
        row_list=dictfetchall(cursor)
        paginator = Paginator(row_list, 25)
        page = request.GET.get('page')
        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)
        cursor.close()
        return render_to_response('showuser.html',{
            'user':request.user,
            'title':"Select user to change",
            'rows':rows,
            'username':q,
        })        
    #     errors.append('Sorry,only superusers are allowed to do this!')
    # if errors:
    #     return render_to_response('error.html',{
    #         'errors':errors,
    #         'user':request.user,
    #         'title':"Error"
    #     })
    else:
        cursor = connection.cursor()
        q=request.GET.get('q')
        if q:
            cursor.execute("select username,last_name as name,email,is_superuser,date_add(last_login,interval 8 hour) as last_login from auth_user where locate(%s,username)>0 order by is_superuser desc,username",[q])
        else:
            cursor.execute('select username,last_name as name,email,is_superuser,date_add(last_login,interval 8 hour) as last_login from auth_user order by is_superuser desc,username')
        row_list=dictfetchall(cursor)
        paginator = Paginator(row_list, 25)
        page = request.GET.get('page')
        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)
        cursor.close()
        return render_to_response('showuser.html',{
            'user':request.user,
            'title':"Select user to change",
            'rows':rows,
            'username':q,
        })

@login_required
def changeuser(request,username):
    errors=[]
    # if not request.user.is_superuser:
    #     errors.append('Sorry,only superusers are allowed to do this!')
    # if errors:
    #     return render_to_response('error.html',{
    #         'errors':errors,
    #         'user':request.user,
    #         'title':"Error"
    #     })

    cursor = connection.cursor()
    if request.method=='POST':
        is_superuser=request.POST.get('is_superuser','0')
        cursor.execute("update auth_user set is_superuser=%s, email= %s where username=%s",[is_superuser,request.POST.get('email',''),username])
        cursor.connection.commit()
        group_checkbox_list=request.POST.getlist('group_checkbox_list','')
        cursor.execute("select name from auth_group where is_userdef=1")
        group_list=cursor.fetchall()

        for groupname in group_list:
            if groupname[0] in group_checkbox_list:
                cursor.execute("call sp_user_group(%s,%s,1)",[username,groupname[0]])
                cursor.connection.commit()
            else:
                cursor.execute("call sp_user_group(%s,%s,0)",[username,groupname[0]])
                cursor.connection.commit()
        cursor.close()
        return HttpResponseRedirect("/admin/user/")

    cursor.execute("select is_superuser from auth_user where username=%s",[username])
    is_superuser=cursor.fetchone()
    cursor.execute("select g.name,g.is_userdef,case when t.id is null then 0 else 1 end as is_userin from auth_group g left join (select g.id from auth_user u join auth_user_groups ug on u.id=ug.user_id join auth_group g on ug.group_id=g.id where u.username=%s) t on g.id=t.id where g.is_userdef=1 or t.id is not null order by g.is_userdef,g.name",[username])
    group_list=dictfetchall(cursor)
    cursor.close()

    return render_to_response('changeuser.html',{
        'user':request.user,
        'title':"Change user",
        'username':username,
        'email':request.user.email,
        'is_superuser':request.user.is_superuser,
        'mis_superuser':is_superuser[0],
        'group_list':group_list,
    })

@login_required
def showgroup(request):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    q=request.GET.get('q')
    if q:
        cursor.execute("select name,is_userdef,description from auth_group where locate(%s,name)>0 order by is_userdef,name",[q])
    else:
        cursor.execute('select name,is_userdef,description from auth_group order by is_userdef,name')
    row_list=dictfetchall(cursor)
    paginator = Paginator(row_list, 25)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    cursor.close()
    return render_to_response('showgroup.html',{
        'user':request.user,
        'title':"Select group to change",
        'rows':rows,
        'groupname':q,
    })

@login_required
def changegroup(request,groupname):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    cursor = connection.cursor()

    if request.method=='POST':
        errorlist=[]
        cursor.execute("select is_userdef from auth_group where name=%s",[groupname])
        is_userdef=cursor.fetchone()
        new_groupname=request.POST.get('groupname',None)
        description=request.POST.get('description','')

        if new_groupname:
            cursor.execute("call sp_changegroup(%s,%s,%s)",[groupname,new_groupname,description])
        else:
            cursor.execute("call sp_changegroup(%s,null,%s)",[groupname,description])
        errorlist=cursor.fetchall()
        cursor.nextset()
        cursor.connection.commit()  
        for error in errorlist:
            errors.append(error[0])
        if errors:
            cursor.close()
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user,
                'title':"Change Group Error"
            })

        if is_userdef[0]==1:
            user_checkbox_list=request.POST.getlist('user_checkbox_list','')
            cursor.execute("select u.username from auth_user u join auth_user_groups ug on u.id=ug.user_id join auth_group g on ug.group_id=g.id where g.name=%s order by u.username",[groupname])
            user_list=cursor.fetchall()
            for username in user_list:
                if username[0] not in user_checkbox_list:
                    cursor.execute("call sp_user_group(%s,%s,0)",[username[0],groupname])
                    cursor.connection.commit()

        cursor.close()
        return HttpResponseRedirect("/admin/group/")

    cursor.execute("select name,is_userdef,description from auth_group where name=%s",[groupname])
    group=dictfetchall(cursor)
    cursor.execute("select u.username from auth_user u join auth_user_groups ug on u.id=ug.user_id join auth_group g on ug.group_id=g.id where g.name=%s order by u.username",[groupname])
    user_list=dictfetchall(cursor)
    cursor.close()
    return render_to_response('changegroup.html',{
        'user':request.user,
        'title':"Change group",
        'group':group[0],
        'user_list':user_list,
    })

@login_required
def addgroup(request):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    if request.method=='POST':
        errorlist=[]
        cursor = connection.cursor()
        groupname=request.POST.get('groupname','')
        description=request.POST.get('description','')
        cursor.execute("call sp_addgroup (%s,%s)",[groupname,description])
        errorlist=cursor.fetchall()
        cursor.nextset()
        cursor.connection.commit()
        cursor.close()
        for error in errorlist:
            errors.append(error[0])
        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user,
                'title':"Add Group Error"
            })
        return HttpResponseRedirect("/admin/group/")

    return render_to_response('addgroup.html',{
        'user':request.user,
        'title':"Add group",
    })

@login_required
def deletegroup(request,groupname):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    if request.method=='POST':
        errorlist=[]
        cursor = connection.cursor()
        cursor.execute("call sp_deletegroup (%s)",[groupname])
        errorlist=cursor.fetchall()
        cursor.nextset()
        cursor.connection.commit()
        cursor.close()
        for error in errorlist:
            errors.append(error[0])
        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user,
                'title':"Delete Group Error"
            })
        return HttpResponseRedirect("/admin/group/")

    
    return render_to_response('confirmation.html',{
        'user':request.user,
        'title':'Delete group confirmation',
        'confirmation':'Are you sure you want to delete the group:"'+groupname+'"?'
    })

@login_required
def addmember(request,groupname):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    if request.method=='POST':
        member_checkbox_list=request.POST.getlist('_selected_action','')
        for username in member_checkbox_list:
            cursor.execute("call sp_user_group(%s,%s,1)",[username,groupname])
            cursor.connection.commit()
        cursor.close()
        next='/admin/group/group='+groupname
        return HttpResponseRedirect(next)

    q=request.GET.get('q')
    if q:
        cursor.execute("select username,last_name as name,email,is_superuser from auth_user a where not exists (select 1 from  auth_user_groups ug join auth_group g on ug.group_id=g.id where g.name=%s and ug.user_id=a.id) and locate(%s,username)>0 order by is_superuser desc,username",[groupname,q])
    else:
        cursor.execute("select username,last_name as name,email,is_superuser from auth_user a where not exists (select 1 from  auth_user_groups ug join auth_group g on ug.group_id=g.id where g.name=%s and ug.user_id=a.id) order by is_superuser desc,username",[groupname])
    row_list=dictfetchall(cursor)
    paginator = Paginator(row_list, 15)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    cursor.close()
    return render_to_response('addmember.html',{
        'user':request.user,
        'title':'Select user to add to group ['+groupname+']',
        'rows':rows,
        'username':q,
    })

@login_required
def showperm(request):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    q=request.GET.get('q')
    if q:
        cursor.execute("select name,description,case when exists (select 1 from auth_group_permissions where group_id=g.id) then 1 else 0 end as has_perm from auth_group g where locate(%s,name)>0 order by is_userdef,name",[q])
    else:
        cursor.execute("select name,description,case when exists (select 1 from auth_group_permissions where group_id=g.id) then 1 else 0 end as has_perm from auth_group g order by is_userdef,name")
    row_list=dictfetchall(cursor)
    paginator = Paginator(row_list, 25)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    cursor.close()
    return render_to_response('showperm.html',{
        'user':request.user,
        'title':"Select group to change",
        'rows':rows,
        'groupname':q,
    })

@login_required
def changeperm(request,groupname):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    cursor=connection.cursor()
    if request.method=='POST':
        perm_checkbox_list=request.POST.getlist('perm_checkbox_list','')
        cursor.execute("select convert(id,char(10)) from auth_permission")
        perm_list=cursor.fetchall()
        for perm in perm_list:
            if perm[0] in perm_checkbox_list:
                cursor.execute("call sp_group_perm(%s,%s,1)",[groupname,perm[0]])
                cursor.connection.commit()
            else:
                cursor.execute("call sp_group_perm(%s,%s,0)",[groupname,perm[0]])
                cursor.connection.commit()
        cursor.close()
        return HttpResponseRedirect("/admin/permission/")

    cursor.execute("select c.name as model,concat('[',c.model,'] ',p.name) as name,p.id,case when exists (select * from auth_group_permissions gp join auth_group g on gp.group_id=g.id where g.name=%s and gp.permission_id=p.id) then 1 else 0 end as has_perm from auth_permission p join django_content_type c on p.content_type_id=c.id order by c.app_label,p.id",[groupname])
    rows=dictfetchall(cursor)
    dict={}
    list=[]
    l_perm=[]
    for row in rows:
        if row['model']<>dict.get('model') and dict<>{}:
            list.append(dict)
            dict={}
            l_perm=[]
        dict={'model':row['model']}
        del row['model']
        l_perm.append(row)
        dict['permission']=l_perm
    list.append(dict)

    cursor.close()
    return render_to_response('changeperm.html',{
        'user':request.user,
        'title':'Change permission',
        'groupname':groupname,
        'list':list,
    })


@login_required
def dbmgmt(request):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    return render_to_response('dbmgmt.html',{
        'user':request.user,
        'title':"DB管理",
    })

@login_required
def dblist(request):
    errors=[]

    cursor = connection.cursor()
    q=request.GET.get('q')
    if q:
        cursor.execute("""select a.upload_dbname,ifnull(b.description,'') as description,ifnull(b.owner,'') as owner,department,a.host,importance
from Release_DBconfig a
left join db_baseinfo b on a.upload_dbname=b.dbname
where envid=4 and locate(%s,a.upload_dbname)>0
order by 1;""",[q])
    else:
        cursor.execute("""select a.upload_dbname,ifnull(b.description,'') as description,ifnull(b.owner,'') as owner,department,a.host,importance
from Release_DBconfig a
left join db_baseinfo b on a.upload_dbname=b.dbname
where envid=4
order by 1;""")
    row_list=dictfetchall(cursor)
    paginator = Paginator(row_list, 25)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    cursor.close()
    return render_to_response('dblist.html',{
        'user':request.user,
        'title':"数据库列表",
        'rows':rows,
        'dbname':q,
    })

 

@login_required
def serveradmin(request):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    return render_to_response('serveradmin.html',{
        'user':request.user,
        'title':"服务器管理",
    })

@login_required
def deal_unusedindex(request):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    sqlperfdb_conn=getConn('127.0.0.1',3306,'sqlperfdb')
    sqlperfdb_cursor=sqlperfdb_conn.cursor()
    q = request.GET.get('q','')
    q = q.strip()
    unusedindexinfoall={}
    if q == '':
        get_unusedindexinfo_sql="""select a.dbname,tablename,table_rows,indexname,colunname,b.Department,b.owner from 
            mysql_index_contact as a
            left join  mysqluploaddb.db_baseinfo as b on a.DBName=b.dbname            
            where concat(a.dbname,',',tablename,',',indexname) not in 
            (select concat(dbname,',',tablename,',',indexname) from mysql_index_usage_whitelists) 
            and concat(a.dbname,',',tablename,',',indexname) not in
            (select concat(dbname,',',tablename,',',indexname) from ready_dropindexlist)
            order by table_rows desc,dbname,tablename"""
        sqlperfdb_cursor.execute(get_unusedindexinfo_sql)
        unusedindexinfoall=dictfetchall(sqlperfdb_cursor)
    else:
        get_unusedindexinfo_sql="""
        select a.dbname,tablename,table_rows,indexname,colunname,b.Department,b.owner from 
            mysql_index_contact as a
            left join  mysqluploaddb.db_baseinfo as b on a.DBName=b.dbname            
            where concat(a.dbname,',',tablename,',',indexname) not in 
            (select concat(dbname,',',tablename,',',indexname) from mysql_index_usage_whitelists) 
            and concat(a.dbname,',',tablename,',',indexname) not in
            (select concat(dbname,',',tablename,',',indexname) from ready_dropindexlist)
            and
            (a.dbname like '%"""+q+"""%' or tablename like '%"""+q+"""%' or b.Department like '%"""+q+"""%' or b.owner like '%"""+q+"""%')
            order by table_rows desc,dbname,tablename
        """
        sqlperfdb_cursor.execute(get_unusedindexinfo_sql)
        unusedindexinfoall=dictfetchall(sqlperfdb_cursor)
    context = {
    'title':'数据库中表无效索引',
    'user':request.user,
    'unusedindexinfoall':unusedindexinfoall,
    }

    return render_to_response('unusedindex.html',context)

###将无效索引插入忽略处理表
@login_required
def insert_dealindex(request):
    response=HttpResponse()
    ret="1"
    errors=[]
    sqlperfdb_conn=getConn('127.0.0.1',3306,'sqlperfdb')
    sqlperfdb_cursor=sqlperfdb_conn.cursor()
    
    dbname=request.POST.get("dbname",'')
    tablename=request.POST.get("tablename",'')
    indexname=request.POST.get("indexname",'')
    type=request.POST.get("type",'')
    operator=request.user
    if type == "忽略":
        insert_ignoreindex_sql="insert into mysql_index_usage_whitelists(dbname,tablename,indexname,operator) select '%s','%s','%s','%s'" % (dbname,tablename,indexname,operator)
        sqlperfdb_cursor.execute(insert_ignoreindex_sql)
        sqlperfdb_cursor.connection.commit()
    elif type == "清除":
        insert_dropindex_sql="insert into ready_dropindexlist(dbname,tablename,indexname,operator) select '%s','%s','%s','%s'" % (dbname,tablename,indexname,operator)
        sqlperfdb_cursor.execute(insert_dropindex_sql)
        sqlperfdb_cursor.connection.commit()
    response.write(ret)
    return response



##serverinfonew添加dbmonitorconnection模块
def dbmonitorconnection(scan):
    scanmachines=[]
    ##切记修改连接串
    connection=getConn('127.0.0.1',3306,'sqlmonitordb','sqlmonitor')
    #connection=getConn('127.0.0.1',3306,'sqlmonitordb','')
    cursor=connection.cursor()
    if scan != '':
        cursor.execute("""select distinct(machine_name) from (select machine_name from cf_machine where (locate(%s,machine_name)>0 or locate(%s,ip_business)>0 or locate(%s,ip_backup)>0) and 
                        machine_owner='MySQL' 
                        union all 
                        select machine_name from cf_service where (locate(%s,service_name)>0 or locate(%s,dns)>0) and db_type in ('MySQL','MongoDB')
                        union all
                        select machine_name from cf_mysql_cluster where locate(%s,cluster_name)>0 or locate(%s,mastervip)>0
                        union all 
                        select machine_name from dic_mysql_database where locate(%s,database_name)>0
                        union all
                        select machine_name from cf_machine_remedy where locate(%s,located)>0 and service_type='OPS-IT基础架构-数据库'
                        ) as info""",[scan,scan,scan,scan,scan,scan,scan,scan,scan])
        for machine_name in cursor.fetchall():
            scanmachines.append(machine_name[0])
    return scanmachines
    cursor.connection.commit()
    cursor.close()


@login_required
def dbserverinfo(request):
    return render_to_response('dbserverinfo.html')

@login_required
def getdbserverinfo(request):
    errors=[]
    row_list={}
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    select = ("select DBType,a.Environment,AppName,\
            case when e.service_name is not null then '数据容灾' when f.cluster_name is not null then '容灾' when g.cluster_name is not null then '无需'\
            else  '无' end as isdr,\
            Approle,hostname,located,mysqlversion,ServerStatus,SlaveStatus,b.dnsall,c.dball,\
            case when serverstatus='Critical' or SlaveStatus='Critical' then 3 \
            when serverstatus='Fair' or SlaveStatus='Fair' then 2 when serverstatus='-' and a.Environment in ('生产','托管','内部/PRO','非生产/UAT','非生产/LPT','非生产/FAT')\
            then 1 else 0 END as statusorder\
            from mysql_serverstatus as a left join dic_mysql_dns as b on a.hostname=b.machine_name\
            left join dic_mysql_database as c on a.hostname=c.machine_name\
            left join environment_orderid as d on a.Environment=d.Environment\
            left join mysql_disaster_recovery as e on a.AppName=e.service_name\
            left join fulldr_clusterinfo as f on a.AppName=f.cluster_name\
            left join nodr_clusterinfoWhiteList as g on a.AppName=g.cluster_name\
            order by statusorder desc,d.id,AppName,Approle;")
    cursor.execute(select)
    row_list = json.dumps(dictfetchall(cursor))
    #cursor.close()
    #return render_to_response('dbserverinfo.html',{'data':row_list})
    paginator = Paginator(row_list, 1000)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    cursor.close()
    return HttpResponse(row_list, content_type='application/json')


@login_required
def adddbserverinfo(request):
    errors=[]
    if not request.user.has_perm('ServerAdmin.dbserverinfo'):
        errors.append('对不起，你没有权限进行此操作！')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor=connection.cursor()
    if request.method=='POST':
        dbtype=request.POST.get('dbtype')
        env=request.POST.get('env')
        schema_name=request.POST.get('schema_name')
        w_ip=request.POST.get('w_ip')
        r_ip=request.POST.get('r_ip')
        w_port=request.POST.get('w_port','')
        r_port=request.POST.get('r_port','')
        username=request.POST.get('username')
      #  dns=request.POST.get('dns','')
        appname=request.POST.get('appname','')
        vip=request.POST.get('vip','')
        if not schema_name:
            errors.append('必须提供数据库名。')
        if not w_ip:
            errors.append('必须至少提供写ip地址。')
        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user,
                'title':"插入新数据库报错"
            })
        if not w_port:
            w_port = 3306
        if not username:
            username = 'default_user'
        if not r_ip:
            r_ip = w_ip
            r_port = w_port
        if not r_port:
            r_port = 3306
#        cursor.execute("""insert into dbserverlist(dbtype,environment,appname,mastervip,hostname,ip,backupip,dns,port)
#values(%s,%s,%s,%s,%s,%s,%s,%s,%s);""",[dbtype,env,appname,vip,hostname,ip,backupip,dns,port])
        cursor.execute("""insert into db_baseinfo(DBName, Description, Owner, Department, importance) 
values(%s, %s, '', '', 0);""",[schema_name, schema_name])
        cursor.execute("""insert into release_dbconfig(dbname, host, port, upload_dbname, active, EnvID) 
VALUES(%s, %s, %s, %s, '1', 4)""",[schema_name, w_ip, w_port, schema_name])
        cursor.execute("""insert into db_conninfo(dbname, envt, host, port, dbuser, password)
values(%s, '生产', %s, %s, %s, '')""", [schema_name, w_ip, w_port, username])
        cursor.execute("""insert into sqltools_db_conninfo(dbid, dbname, host, port, dbuser, type) 
select id, dbname, %s, %s, %s, %s from release_dbconfig where dbname  = %s """, [w_ip, w_port, username, "W", schema_name])
        cursor.execute("""insert into sqltools_db_conninfo(dbid, dbname, host, port, dbuser, type) 
select id, dbname, %s, %s, %s, %s from release_dbconfig where dbname  = %s """, [r_ip, r_port, username, "R", schema_name])

        cursor.connection.commit()
        cursor.close()
        return HttpResponseRedirect("/dbmgmt/dblist/")        

    cursor.execute("select name from release_environmentcfg order by levelid;")
    envlist=dictfetchall(cursor)
    cursor.close()
    return render_to_response('adddbserverinfo.html',{
        'user':request.user,
        'title':'增加新数据库服务器',
        'envlist':envlist,
    })

@login_required
def dbserverdetail(request,envtype,host,cluseraddress):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb')
    #dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb','')
    cursor=dbmonitorcon.cursor()
    cursor.execute("select replace(group_concat(concat(dns,':',dns_port),'\n' order by dns),',','') as dns from cf_service where machine_name=%s",[host])
    dnsinfo=dictfetchall(cursor)
    cursor.execute("select dns from cf_service where machine_name=%s and dns like '%%.com' order by dns",[host])
    dnsList=dictfetchall(cursor)
    cursor.execute("""select a.machine_name,b.ci_code,concat(cpu_logical_number,'(',cpu_number,')') as cpu,
                    b.cpu_model,a.mem_gb,b.physical_disk,a.logical_disk,b.located,a.ip_business,a.ip_backup,b.department,b.machine_function 
                    from cf_machine as a left join cf_machine_remedy as b on a.machine_name=b.machine_name where a.machine_name=%s""",[host])
    baseinfo=dictfetchall(cursor)
    cursor.execute("""select replace(group_concat(concat(database_name,' ',concat(round(`database_size(kb)`/1024,3),'M')),'\n' order by database_name),',','') as dbinfo 
                    from dic_mysql_dbsize where machine_name=%s and insert_timestamp=(select max(insert_timestamp)  
                    from dic_mysql_dbsize where machine_name=%s)""",[host,host])
    dbinfo=dictfetchall(cursor)
    cursor.execute("select cluster_name,mastervip from cf_mysql_cluster where machine_name=%s",[host])
    clusterinfo=dictfetchall(cursor)
    cursor.close()
    if clusterinfo == []:
        clusterinfo = ['None,None']
    #if cluseraddress == '':
    #    cluseraddress = 'None'
    return render_to_response('dbserverdetail.html',{
        'user':request.user,
        'title':'服务器'+host+'的基本信息',
        'dnsinfo':dnsinfo[0],
        'dnsList':dnsList,
        'baseinfo':baseinfo[0],
        'dbinfo':dbinfo[0],
        'clusterinfo':clusterinfo[0],
        'cluseraddress':cluseraddress
    })


@login_required
def servermonitor(request):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    dbtype=request.GET.get('dbtype','mysql')
    q=request.GET.get('q','')
    cursor.execute("""select HostName,case DNS when '' then AppName else left(DNS,locate('.',DNS,locate('.',DNS)+1)-1) end as DNS,Environment
,case CheckServer when 'T' then ServerStatus else '-' end as ServerStatus
,case CheckSlave when 'T' then SlaveStatus else '-' end as SlaveStatus
,case CheckPerf when 'T' then PerfStatus else '-' end as PerfStatus
from dbserverlist 
where DBType=%s and (locate(%s,hostname)>0 or locate(%s,ip)>0 or locate(%s,dns)>0)
order by 4,5,6,1;""",[dbtype,q,q,q])
    row_list=dictfetchall(cursor)
    paginator = Paginator(row_list, 500)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    cursor.close()
    return render_to_response('servermonitor.html',{
        'user':request.user,
        'title':"服务器监控",
        'rows':rows,
        'dbtype':dbtype,
        'keyword':q,
    })

@login_required
def changeservermonitor(request,dbtype,host):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor=connection.cursor()

    if request.method=='POST':
        CheckServer=request.POST.get('CheckServer','')
        CheckSlave=request.POST.get('CheckSlave','')
        CheckPerf=request.POST.get('CheckPerf','')
        cursor.execute("""update dbserverlist 
set CheckServer=%s,CheckSlave=%s,CheckPerf=%s
where DBType=%s and HostName=%s;""",[CheckServer,CheckSlave,CheckPerf,dbtype,host])
        cursor.connection.commit()
        cursor.close()
        return HttpResponseRedirect("/serveradmin/servermonitor/")

    cursor.execute("""select case CheckServer when 'T' then 'T' else 'F' end as CheckServer
,case CheckSlave when 'T' then 'T' else 'F' end as CheckSlave
,case CheckPerf when 'T' then 'T' else 'F' end as CheckPerf
from dbserverlist 
where DBType=%s and HostName=%s;""",[dbtype,host])
    status=dictfetchall(cursor)
    cursor.close()
    return render_to_response('changeservermonitor.html',{
        'user':request.user,
        'title':'服务器'+host+'的监控开关',
        'status':status[0],
        'has_perm':request.user.has_perm('ServerAdmin.servermonitor'),
    })

def ssh_out(ip,cmd):
    ssh=paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip,1022,username='op1')
    stdin,stdout,stderr=ssh.exec_command(cmd)
    output=stdout.readlines()
    return output
    ssh.close()

@login_required
def viewserverstatus(request,envtype,host):
    filterwarnings('ignore', category = MySQLdb.Warning)
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    status={}
    diskstatus=[]
    dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb')
    #dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb','')
    cursor=dbmonitorcon.cursor()
    cursor.execute("select dns,dns_port,db_type,ip_business from cf_service as a join cf_machine as b on a.machine_name=b.machine_name where a.machine_name=%s limit 1",[host])
    server=cursor.fetchone()
    db_type=server[2]
    cursor.close()


    rows={}
    tranrows={}
    text_scr=[]
    file_scr=[]
    disk_scr=[]

    if db_type == 'MySQL':
        conn=getConn(server[0],int(server[1]),'mysql','')
        cur=conn.cursor()
        cur.execute("""select * from information_schema.global_status
        where variable_name in ('Threads_connected','Open_files')
        union all
        select * from information_schema.global_variables
        where variable_name in ('max_connections','open_files_limit')
        union all
        select 'SYSTIME',now();""")
        status=statusfetch(cur)
        
        #cur.execute("""select proc.id,tx.trx_state,proc.user, left(proc.host,position(':' in proc.host)-1) as host,proc.DB, cast(tx.trx_started as char(20)) as trx_started,proc.TIME from information_schema.INNODB_TRX as tx join information_schema.processlist as proc on tx.trx_mysql_thread_id=proc.ID  where proc.COMMAND='Sleep' and proc.time>60 and proc.user not in ('system user','usvr_replication','usvr_serveroper','event_scheduler') order by proc.TIME desc""")
        cur.execute("""select proc.id,tx.trx_state,proc.user, left(proc.host,position(':' in proc.host)-1) as host,proc.DB, cast(tx.trx_started as char(20)) as trx_started,proc.TIME,sc.SQL_TEXT,left(sc.SQL_TEXT,60) as sqlsample from information_schema.INNODB_TRX as tx join information_schema.processlist as proc on tx.trx_mysql_thread_id=proc.ID join performance_schema.threads as th on proc.id=th.PROCESSLIST_ID join performance_schema.events_statements_current as sc on th.THREAD_ID=sc.THREAD_ID where proc.COMMAND='Sleep' and proc.time>60 and proc.user not in ('system user','usvr_replication','usvr_serveroper','event_scheduler') order by proc.TIME desc""")
        unclosetran=dictfetchall(cur)
        paginator = Paginator(unclosetran, 500)
        page = request.GET.get('page')
        try:
            tranrows = paginator.page(page)
        except PageNotAnInteger:
            tranrows = paginator.page(1)
        except EmptyPage:
            tranrows = paginator.page(paginator.num_pages)

	    cur.execute("""select proc.id,tx.trx_state,proc.user, left(proc.host,position(':' in proc.host)-1) as host,proc.DB, cast(tx.trx_started as char(20)) as trx_started,proc.TIME,info,left(info,60) as sqlsample from information_schema.INNODB_TRX as tx join information_schema.processlist as proc on tx.trx_mysql_thread_id=proc.ID where proc.COMMAND<>'Sleep' and trx_started<date_add(now(),interval -30 minute) and proc.user not in ('system user','usvr_replication','usvr_serveroper','event_scheduler') order by proc.TIME desc
        """)
        unclosegoingtran=dictfetchall(cur)
        paginator = Paginator(unclosegoingtran, 500)
        page = request.GET.get('page')
        try:
            goingtranrows = paginator.page(page)
        except PageNotAnInteger:
            goingtranrows = paginator.page(1)
        except EmptyPage:
            goingtranrows = paginator.page(paginator.num_pages)	

        
        # cur.execute("""
        #     select ID,USER,HOST,DB,COMMAND,TIME,ifnull(b.trx_state,'') as trx_state,STATE,left(INFO,70) as sqlsample,         
        #     (case when left(info,2)='/*' then ltrim(right(info,length(info)-(locate('*/',info)+1))) else info end) as sqlinfo ,         
        #     case when 
        #     ltrim(replace(replace((case when left(info,2)='/*' then ltrim(right(info,length(info)-(locate('*/',info)+1))) else info end),char(10),''),char(13),'')) like 'select%%' 
        #     or 
        #     ltrim(replace(replace((case when left(info,2)='/*' then ltrim(right(info,length(info)-(locate('*/',info)+1))) else info end),char(10),''),char(13),'')) like 'update%%'
        #     or 
        #     ltrim(replace(replace((case when left(info,2)='/*' then ltrim(right(info,length(info)-(locate('*/',info)+1))) else info end),char(10),''),char(13),''))  like 'delete%%'
        #     or 
        #     ltrim(replace(replace((case when left(info,2)='/*' then ltrim(right(info,length(info)-(locate('*/',info)+1))) else info end),char(10),''),char(13),''))  like 'insert%%'
        #     or 
        #     ltrim(replace(replace((case when left(info,2)='/*' then ltrim(right(info,length(info)-(locate('*/',info)+1))) else info end),char(10),''),char(13),''))  like 'replace%%'
        #     then 'T' else 'F' end descstatus         
        #     from information_schema.processlist as a left join information_schema.INNODB_TRX as b on a.id=b.trx_mysql_thread_id          
        #     where user not in ('system user','usvr_replication','usvr_serveroper','event_scheduler') and command not in ('killed','sleep')  order by time desc limit 20
        # """)
        cur.execute("""
			select ID,USER,HOST,DB,COMMAND,TIME,ifnull(b.trx_state,'') as trx_state,STATE,left(INFO,70) as sqlsample,         
            (case when left(replace(info,'\n',' '),2)='/*' then ltrim(right(replace(info,'\n',' '),length(replace(info,'\n',' '))-(locate('*/',replace(info,'\n',' '))+1))) else replace(info,'\n',' ') end) as sqlinfo ,         
            case when 
            ltrim(replace(replace((case when left(replace(info,'\n',' '),2)='/*' then ltrim(right(replace(info,'\n',' '),length(replace(info,'\n',' '))-(locate('*/',replace(info,'\n',' '))+1))) else replace(info,'\n',' ') end),char(10),''),char(13),'')) like 'select%%' 
            or 
            ltrim(replace(replace((case when left(replace(info,'\n',' '),2)='/*' then ltrim(right(replace(info,'\n',' '),length(replace(info,'\n',' '))-(locate('*/',replace(info,'\n',' '))+1))) else replace(info,'\n',' ') end),char(10),''),char(13),'')) like 'update%%'
            or 
            ltrim(replace(replace((case when left(replace(info,'\n',' '),2)='/*' then ltrim(right(replace(info,'\n',' '),length(replace(info,'\n',' '))-(locate('*/',replace(info,'\n',' '))+1))) else replace(info,'\n',' ') end),char(10),''),char(13),''))  like 'delete%%'
            or 
            ltrim(replace(replace((case when left(replace(info,'\n',' '),2)='/*' then ltrim(right(replace(info,'\n',' '),length(replace(info,'\n',' '))-(locate('*/',replace(info,'\n',' '))+1))) else replace(info,'\n',' ') end),char(10),''),char(13),''))  like 'insert%%'
            or 
            ltrim(replace(replace((case when left(replace(info,'\n',' '),2)='/*' then ltrim(right(replace(info,'\n',' '),length(replace(info,'\n',' '))-(locate('*/',replace(info,'\n',' '))+1))) else replace(info,'\n',' ') end),char(10),''),char(13),''))  like 'replace%%'
            then 'T' else 'F' end descstatus        
            from information_schema.processlist as a left join information_schema.INNODB_TRX as b on a.id=b.trx_mysql_thread_id          
            where user not in ('system user','usvr_serveroper','event_scheduler') and command not in ('killed','sleep')  order by time desc limit 20
        """)
        processlist=dictfetchall(cur)
        paginator = Paginator(processlist, 500)
        page = request.GET.get('page')
        try:
            rows = paginator.page(page)
        except PageNotAnInteger:
            rows = paginator.page(1)
        except EmptyPage:
            rows = paginator.page(paginator.num_pages)

        cur.close()
        text_scr=[]
        file_scr=[]
        disk_scr=[]


    return render_to_response('viewserverstatus.html',{
        'user':request.user,
        'title':'服务器'+host+'的状态',
        'dbtype':db_type,
        'status':status,
        'rows':rows,
        'tranrows':tranrows,
        'text_scr':text_scr,
        'file_scr':file_scr,
        'disk_scr':disk_scr,
        'serverinfo':server,
    })

@login_required
def killprocessid(request):
    response=HttpResponse()
    ret="1"
    errors=[]
    if not request.user.has_perm('ServerAdmin.servermonitor'):
        errors.append('对不起，你没有权限进行此操作！')
        ret="2"
        response.write(ret)
        return response

    #response['Content-Type']="text/javascript" 
    id=request.POST.get("id",'')
    dns=request.POST.get("dns",'')
    port=request.POST.get("port",'')
    conn=getConn(dns,int(port),'mysql','')
    cur=conn.cursor()
    cur.execute("select @@hostname;")
    hostname=cur.fetchone()
    cur.execute("select concat('User:',ifnull(USER,''),',Host:',ifnull(host,''),',DB:',ifnull(db,''),',Command:',ifnull(command,''),',Time:',time,',State:',ifnull(state,''),',Info:',ifnull(info,'')) from information_schema.processlist where id="+id+";")
    row = cur.fetchone()
    os.system("echo `date -d '8 hour' +'%Y-%m-%d %H:%M:%S'` ' "+str(hostname[0])+" "+str(request.user)+" kill "+id+" "+str(row[0])+"' >> /home/op1/mysql_serveradmin_log/mysql_serveradmin_log.txt") 
    cur.execute("kill "+id+";")
    cur.connection.commit()
    response.write(ret)
    return response


@login_required
def viewmysqldisk(request,host):
    filterwarnings('ignore', category = MySQLdb.Warning)
    errors=[]
    if errors:
        return render_to_response('error.html',{
        'errors':errors,
        'user':request.user,
        'title':"Error"
        })
    dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb')
    cursor=dbmonitorcon.cursor()
    cursor.execute("select dns,dns_port,db_type,ip_business from cf_service as a join cf_machine as b on a.machine_name=b.machine_name where a.machine_name=%s limit 1",[host])
    server=cursor.fetchone()
    db_type=server[2]
    cursor.close()
    if request.method=='POST':
        if not request.user.has_perm('ServerAdmin.dbserverinfo'):
            errors.append('对不起，你没有权限进行此操作！')
        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user,
                'title':"Error"
            })

        filename=request.POST.getlist('filename','')
        for filekey in filename:
            #os.system("ssh -p 1022 "+server[3]+" sudo rm -rf "+filekey+"")
            iserror=ssh_out(server[3],"sudo rm -rf "+filekey+"")
            os.system("echo `date -d '8 hour' +'%Y-%m-%d %H:%M:%S'` ' "+host+" "+str(request.user)+" rm -rf "+filekey+"' >> /home/op1/mysql_serveradmin_log/mysql_serveradmin_log.txt")

    rows={}
    tranrows={}
    text_scr=[]
    file_scr=[]
    disk_scr=[]
	
    if db_type == 'MySQL':
        text_scr=[]
        file_scr=[]
        disk_scr=[]
        diskstatus=ssh_out(server[3],"df -Ph | awk 'BEGIN{OFS=\",\"}{print $6,$4,$5}' | sed '1d'")
        for diskone in diskstatus:
            diskdir=(diskone.strip().split(','))[0]
            diskall=(diskone.strip().split(','))[1]
            diskused=(diskone.strip().split(','))[2]
            disk_scr.append([diskdir,diskall,diskused])
        textall=ssh_out(server[3],"for file in `sudo find /tmp/ /data/ /home/op1/ /backup/mysql/ -maxdepth 1 -type f -size +1G`; do sudo du -L $file; done")
        for textone in textall:
            textsize=int(textone.split('\t')[0])
            textname=textone.split('\t')[1].strip('')
            if textsize/1024/1024 >= 1:
                textsize=str(textsize/1024/1024)+'G'
                text_scr.append([textname.strip(),textsize])
        filesizeall=ssh_out(server[3],"sudo du -L --max-depth=1 --exclude=binlog /backup/mysql/ | sort -rn | sed '1d';sudo du -L --max-depth=1 /tmp/ | sort -rn | sed '1d' | sed -n '1,10p';sudo du -L --max-depth=1  --exclude=mysql /var/lib/ | sort -rn | sed '1d' | sed -n '1,10p';sudo du -L --max-depth=1 --exclude=backupdir --exclude=mysql  --exclude=tmp /data/ | sort -rn | sed '1d' | sed -n '1,10p';sudo du -L --max-depth=1 --exclude=share /home/op1/ | sort -rn | sed '1d' | sed -n '1,10p';")
        for filesize in filesizeall:
            size=int(filesize.split('\t')[0])
            file=filesize.split('\t')[1].strip()
            if size/1024/1024 >= 1 :
                size=str(size/1024/1024)+'G'
                file_scr.append([file.strip(),size])
    return render_to_response('viewmysqldisk.html',{
    'user':request.user,
    'title':'服务器'+host+'的磁盘信息',
    'text_scr':text_scr,
    'file_scr':file_scr,
    'disk_scr':disk_scr,
    })



@login_required
def viewslavestatus(request,envtype,host):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    master=''
    s_status={}
    m_status={}
    showslavestatus={}
    rs_status={}

    dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb')
    #dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb','')
    cursor=dbmonitorcon.cursor()
    cursor.execute("select dns,dns_port,db_type from cf_service where machine_name=%s limit 1",[host])
    server=cursor.fetchone()
    db_type=server[2]
    cursor.close()
    if db_type == 'MySQL':
        conn=getConn(server[0],int(server[1]),'mysql','')
        cur=conn.cursor()
        cur.execute("show slave status;")
        showslavestatus=dictfetchall(cur)
        #showslavestatus=showslavestatus[0]
        #cursor.execute("select HostName from dbserverlist where DBType=%s and IP=%s;",[dbtype,showslavestatus['Master_Host']])
        #master=cursor.fetchone()
        m_file=showslavestatus[0]['Master_Log_File'].strip()
        master=m_file[0:m_file.find('-bin')]
        #master=master[0]
        cur.execute("""select *
        from information_schema.GLOBAL_STATUS
        where variable_name in ('SLAVE_RUNNING','RPL_SEMI_SYNC_SLAVE_STATUS')
        union all
        select 'HEARTBEAT',time
        from configdb.repl_heartbeat where hostname=%s;""",[master])
        s_status=statusfetch(cur)
        cur.close()
        m_conn=getConn(showslavestatus[0]['Master_Host'],int(showslavestatus[0]['Master_Port']),'mysql','')
        m_cur=m_conn.cursor()
        m_cur.execute("select * from information_schema.GLOBAL_STATUS where VARIABLE_NAME='RPL_SEMI_SYNC_MASTER_STATUS';")
        m_status=statusfetch(m_cur)
        m_cur.close()
    elif db_type == 'MongoDB':
        cursor.close()
        conn=pymongo.Connection(host=server[0],port=int(server[1]),network_timeout=3)
        admin=conn.admin
        rs_status=admin.command('replSetGetStatus')
        conn.close()
        for member in rs_status['members']:
            member['id']=member['_id']
            if member['stateStr'] != 'ARBITER':
                timestamp=int(member['optimeDate'].strftime('%s'))+28800
                member['optimeDate']=time.strftime( "%Y-%m-%d %H:%M:%S",time.localtime(timestamp))
            else:
                member['optimeDate']=''
    if showslavestatus == {}:
        showslavestatus=['']
    return render_to_response('viewslavestatus.html',{
        'user':request.user,
        'title':'服务器'+host+'的复制状态',
        'dbtype':db_type,
        'master':master,
        's_status':s_status,
        'm_status':m_status,
        'showslavestatus':showslavestatus[0],
        'rs_status':rs_status,
    })


@login_required
def viewclusterstatus(request,envtype,host,cluseraddress,clusername):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cluseraddress_host=cluseraddress.split('(')[1].split(')')[0]
    cursor = connection.cursor()
    cursor.execute("select ip from mhamanagerlist where hostname=%s",[cluseraddress_host])
    cluseraddress_ip=cursor.fetchone()
    ##切记修改日志名
    errorinfo=os.popen("ssh -l op1 -p 1022 "+cluseraddress_ip[0]+" cat /tmp/tmp_log_"+clusername+".err 2>/dev/null").readlines()
    #errorinfo=errorinfo[0].replace('\n','<br>')
    #os.system("echo '"+errorinfo+"' >/tmp/errorinfo_syj_tmp.txt")
    errornumall=[]
    for errorevery in errorinfo:
        erroreverynum=errorevery.find('[error]')
        errornumall.append(erroreverynum)
    #errorinfo=dict(zip(errorinfo,errornumall))
    errorinfo=zip(errorinfo,errornumall)
    paginator = Paginator(errorinfo, 500)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
    return render_to_response('viewclusterstatus.html',{
        'user':request.user,
        'title':'集群'+clusername+'的最新报错',
        'errorinfo':rows,
    })



@login_required
def viewmysqlexplain(request,envtype,host,dns,dnsport,db,sqlinfo):
    if dnsport == "3306":
        conn=getConn(dns,int(dnsport),db,'生产')
    else:
        conn=getConn(dns,int(dnsport),db,'dev')
    cur=conn.cursor()
    descsqlinfo='desc '+sqlinfo
    cur.execute(descsqlinfo)
    desclist=dictfetchall(cur)
    table_all=''
    indexlist={}
    columnlist={}
	
    for onedesc in desclist:
        if onedesc['id'] != None:
            table_cname=onedesc['table']
            if table_cname != None:
                exist=cur.execute("select * from information_schema.tables where TABLE_SCHEMA='"+db+"' and TABLE_NAME='"+table_cname+"'")
                if exist == 0:
                    sqlinfo=sqlinfo.replace('`','')
                    table_postion=sqlinfo.find(' '+table_cname+' ')
                    table_name=sqlinfo[0:table_postion].split(' ')[-1]
                    if table_name == 'as':
                        table_name=sqlinfo[0:table_postion].split(' ')[-2]
                    table_name=table_name.replace("'",'')				
                    table_all=table_all+"'"+table_name+"',"
            table_all=table_all+"'"+table_cname+"',"
    table_all=table_all.strip(',')
    if table_all != '':
        cur.execute("""
            select TABLE_NAME,NON_UNIQUE,INDEX_NAME,group_concat(COLUMN_NAME order by SEQ_IN_INDEX) as index_column,CARDINALITY from information_schema.STATISTICS 
            where TABLE_SCHEMA='"""+db+"""' and TABLE_NAME in ("""+table_all+""") group by TABLE_NAME,INDEX_NAME order by TABLE_NAME,NON_UNIQUE
            """)
        indexlist=dictfetchall(cur)
        cur.execute("""
            select TABLE_NAME,COLUMN_NAME,COLUMN_TYPE,IS_NULLABLE,COLUMN_KEY,COLUMN_DEFAULT,EXTRA,COLUMN_COMMENT from information_schema.COLUMNS
            where TABLE_SCHEMA='"""+db+"""' and TABLE_NAME in ("""+table_all+""") order by TABLE_NAME,ORDINAL_POSITION
            """)
        columnlist=dictfetchall(cur)

    paginator = Paginator(desclist, 500)
    page = request.GET.get('page')
    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    paginator = Paginator(indexlist, 500)
    page = request.GET.get('page')
    try:
        indexrows = paginator.page(page)
    except PageNotAnInteger:
        indexrows = paginator.page(1)
    except EmptyPage:
        indexrows = paginator.page(paginator.num_pages)

    paginator = Paginator(columnlist, 500)
    page = request.GET.get('page')
    try:
        columnrows = paginator.page(page)
    except PageNotAnInteger:
        columnrows = paginator.page(1)
    except EmptyPage:
        columnrows = paginator.page(paginator.num_pages)

    return render_to_response('viewmysqlexplain.html',{
        'user':request.user,
        'title':'数据库'+db+'中SQL语句执行计划',
        'rows':rows,
        'sqlinfo':sqlinfo,
        'indexrows':indexrows,
        'columnrows':columnrows,
    })



#截取字符串为固定长度
def truncateText(text,length):
    if len(text) < length:
        return text
    else:
        return text[0:length] + " ..." 

@login_required
def slowlogmonitor(request):
    errors=[]
    
    sqlPerfConn = getConn(sqlperfserver, sqlperfport, sqlperfdb,'')
    sqlPerfCursor = sqlPerfConn.cursor()

    #获取抓取了其慢日志的主机
    getHostSql = ("select distinct(hostname) as hostName "
                 " from slowlog_history ")
    
    sqlPerfCursor.execute(getHostSql)
    hostList = dictfetchall(sqlPerfCursor)
    
    #检查表单是否提交
    #并获取提交的表单值
    if request.GET:
        getData = request.GET
        topN = int(getData.get('topN',''))
        hostName = getData.getlist('hostName','')
        beginTime = getData.get('beginTime','')
        endTime = getData.get('endTime','')

        #服务器端验证时间值、时间范围是否合理
        dt = datetime.datetime
        dtBeginTime = dtEndTime = ''

        if beginTime and endTime:
            try:
                dtBeginTime = dt.strptime(beginTime,'%Y-%m-%d %H:%M')
            except:
                errors.append("开始时间'" + beginTime + "'格式错误！请使用'yyyy-mm-dd hh:mm'格式！")

            try:
                dtEndTime = dt.strptime(endTime,'%Y-%m-%d %H:%M')
            except:
                errors.append("结束时间'" + endTime + "'格式错误！请使用'yyyy-mm-dd hh:mm'格式！")

            if dtBeginTime and dtEndTime:
                if dtBeginTime >= dtEndTime:
                    errors.append("开始时间'" + beginTime + "'大于或等于结束时间'" + endTime + "'！")
        else:
            if not beginTime:
                errors.append("请输入开始时间！")
            if not endTime:
                errors.append("请输入结束时间！")

        #验证是否选择了数据库
        if not hostName:
            errors.append("请选择服务器！")

        if errors:
            sqlPerfCursor.close()
            sqlPerfConn.close()

            context = {
               'title':'慢日志监控',
               'user':request.user,
               'hostList':hostList,
               'hostName':hostName,
               'beginTime':beginTime,
               'endTime':endTime, 
               'topN':topN,
               'errors':errors,        
            }   
            
            return render_to_response('slowlogmonitor.html',context)

        #共通的查询内容
        queryContent =\
                (" hostname as hostName, "
                 " loginname as loginName, "
                 " hashcode as hashCode "
                 " from slowlog_history ")

        
        #共通的查询条件
        hostnameSet = '(' + ','.join(['"'+ item + '"' for item in hostName]) + ')'
        whereCondition = \
                (" where hostname in %s "
                 " and begin_time between '%s' and '%s' ") % \
                (hostnameSet, beginTime, endTime)


        #共通的分组条件
        groupByCondition = " group by hostName, loginName, hashCode "

        #获取前N个执行次数最多的慢语句
        getTopNCounts = \
                ("select sum(counts) as perCounts, "
                 + queryContent
                 + whereCondition 
                 + groupByCondition +
                 " order by perCounts desc "
                 " limit %s ")
  
        #获取前N个平均返回行数最多的慢语句
        getTopNAvgRows = \
                ("select round(sum(avgRows*counts)/sum(counts)) as perAvgRows, "
                 + queryContent
                 + whereCondition 
                 + groupByCondition +
                 " order by perAvgRows desc "
                 " limit %s ")

        #获取前N个平均实行时间最长的慢语句
        getTopNqueryTimeAvg = \
                ("select round(sum(query_time_avg*counts)/sum(counts),2) as perQueryTimeAvg, "
                 + queryContent
                 + whereCondition 
                 + groupByCondition +
                 " order by perQueryTimeAvg desc "
                 " limit %s ")
        
        #根据hostname,loginname,hashcode从slowlog_sql表中取sourcesql和sqltext
        getSqlTextAndSourceSql = \
                ("select sourcesql as sourceSql, "
                 " sqltext as sqlText, "
                 " loginip as loginIP "
                 " from slowlog_sql "
                 " where hostname=%s "
                 " and loginname=%s " 
                 " and hashcode=%s ")

        #设置将要显示前几个执行次数最多，总执行时间最久，平均执行时间最长的SQl语句以及语句截取长度
        truncateLenth = 5000
        topNParam = [topN,]
        nCounts = sqlPerfCursor.execute(getTopNCounts, topNParam)
        topNCounts =  dictfetchall(sqlPerfCursor)
        for item in topNCounts:
            param = [item['hostName'], item['loginName'], item['hashCode']]
            sqlPerfCursor.execute(getSqlTextAndSourceSql, param)
            result = dictfetchall(sqlPerfCursor)
            if result:
                item['sourceSql'] = truncateText(result[0]['sourceSql'], truncateLenth)
                item['sqlText'] = truncateText(result[0]['sqlText'], truncateLenth)
                item['loginIP'] = result[0]['loginIP']
            else:
                item['sourceSql'] = '!!!Record not found in sqlperfdb.slowlog_sql.'
                item['sqlText'] =  '!!!Record not found in sqlperfdb.slowlog_sql.'
                item['loginIP'] = 'Not found'
     
        nAvgRows = sqlPerfCursor.execute(getTopNAvgRows, topNParam)
        topNAvgRows =  dictfetchall(sqlPerfCursor)
        for item in topNAvgRows:
            param = [item['hostName'], item['loginName'], item['hashCode']]
            sqlPerfCursor.execute(getSqlTextAndSourceSql, param)
            result = dictfetchall(sqlPerfCursor)
            if result:
                item['sourceSql'] = truncateText(result[0]['sourceSql'], truncateLenth)
                item['sqlText'] = truncateText(result[0]['sqlText'], truncateLenth)
                item['loginIP'] = result[0]['loginIP']
            else:
                item['sourceSql'] = '!!!Record not found in sqlperfdb.slowlog_sql.'
                item['sqlText'] =  '!!!Record not found in sqlperfdb.slowlog_sql.'
                item['loginIP'] = 'Not found'
            
        nQueryTimeAvg  = sqlPerfCursor.execute(getTopNqueryTimeAvg, topNParam)
        topNqueryTimeAvg =  dictfetchall(sqlPerfCursor)
        for item in topNqueryTimeAvg:
            param = [item['hostName'], item['loginName'], item['hashCode']]
            sqlPerfCursor.execute(getSqlTextAndSourceSql, param)
            result = dictfetchall(sqlPerfCursor)
            if result:
                item['sourceSql'] = truncateText(result[0]['sourceSql'], truncateLenth)
                item['sqlText'] = truncateText(result[0]['sqlText'], truncateLenth)
                item['loginIP'] = result[0]['loginIP']
            else:
                item['sourceSql'] = '!!!Record not found in sqlperfdb.slowlog_sql.'
                item['sqlText'] =  '!!!Record not found in sqlperfdb.slowlog_sql.'
                item['loginIP'] = 'Not found'
        
        sqlPerfCursor.close()
        sqlPerfConn.close()
        
        context = {
           'title':'慢日志监控',
           'user':request.user,
           'hostList':hostList,
           'hostName':hostName,
           'topNCounts':topNCounts,
           'topNAvgRows':topNAvgRows,
           'topNqueryTimeAvg':topNqueryTimeAvg,
           'beginTime':beginTime,
           'endTime':endTime, 
           'topN':topN, 
           'nCounts':nCounts,
           'nAvgRows':nAvgRows, 
           'nQueryTimeAvg':nQueryTimeAvg,     
        }   
        
        return render_to_response('slowlogmonitor.html',context)
   
    sqlPerfCursor.close()
    sqlPerfConn.close()
    
    #构造默认开始时间和结束时间
    tz = SHTZ(8, 'Asia/Shanghai')
    timedelta = datetime.timedelta(days=-1)
    nowTime = datetime.datetime.now(tz)
    beginTime = (nowTime + timedelta).strftime('%Y-%m-%d %H:%M')
    endTime = nowTime.strftime('%Y-%m-%d %H:%M')


    context = {
       'title':'慢日志监控',
       'user':request.user,
       'hostList':hostList, 
       'beginTime':beginTime,
       'endTime':endTime, 
    }

    return render_to_response('slowlogmonitor.html',context)


def getSlowLogData(request):
    if request.method == 'POST':
        postData = request.POST
        hostName = postData.get('hostName','')
        loginName = postData.get('loginName','')
        hashCode = postData.get('hashCode','')
        # beginTime = postData.get('beginTime','')
        # endTime = postData.get('endTime','')     
        
        sql = ("select round(sum(query_time_avg*counts)/sum(counts),2) as queryTimeAvg, "
               " round(sum(avgRows*counts)/sum(counts)) as avgRows, "
               " sum(counts) as counts, "
               " unix_timestamp(begin_time)*1000 as `timeStamp` "
               " from slowlog_history "
               " where hostname=%s "
               " and loginName=%s "
               " and hashcode=%s " 
               " and begin_time>=%s "
               " and begin_time <=%s "
               " group by begin_time "
               " order by begin_time ")

        
        #取90天以内的数据
        tz = SHTZ(8, 'Asia/Shanghai')
        timedelta = datetime.timedelta(days=-30)
        nowTime = datetime.datetime.now(tz)
        beginTime = (nowTime + timedelta).strftime('%Y-%m-%d %H:%M:%S')
        endTime = nowTime.strftime('%Y-%m-%d %H:%M:%S')
        
        param = [hostName, loginName, hashCode, beginTime, endTime]

        sqlPerfConn = getConn(sqlperfserver, sqlperfport, sqlperfdb,'')
        sqlPerfCursor = sqlPerfConn.cursor()

        sqlPerfCursor.execute(sql, param)
        result = sqlPerfCursor.fetchall()
        
        sqlPerfCursor.close()
        sqlPerfConn.close()

        executionCountData = []
        avgRowsData = []
        queryTimeAvgData = []

        for queryTimeAvg, avgRows, counts, timeStamp in result:
            executionCountData.append([timeStamp, int(counts)])
            avgRowsData.append([timeStamp, int(avgRows)])
            queryTimeAvgData.append([timeStamp, queryTimeAvg])        
       
        message = {
            'hostName':hostName,
            'loginName':loginName,
            'hashCode': hashCode,
            # 'beginTime':beginTime,
            # 'endTime':endTime,
            'executionCountData':executionCountData,
            'avgRowsData':avgRowsData,
            'queryTimeAvgData':queryTimeAvgData
        }
        
        response = HttpResponse()
        response['Content-Type'] = "application/json"
        response.write(json.dumps(message))

        return response


###获取dml日志相关信息
@login_required
def dmllogmonitor(request,host):
    errors=[]

    sqlPerfConn = getConn(sqlperfserver, sqlperfport, sqlperfdb,'')
    sqlPerfCursor = sqlPerfConn.cursor()

    #获取抓取了其慢日志的主机
    getdblistSql = ("select distinct(SCHEMA_NAME) as dbName "
        " from dmlsql_sample where hostname='"+host+"' ")

    getsqltypesql = ("select distinct(SQL_Type) as SqlType "
        " from dmlsql_sample where hostname='"+host+"' ")
    sqlPerfCursor.execute(getdblistSql)
    DBList = dictfetchall(sqlPerfCursor)

    sqlPerfCursor.execute(getsqltypesql)
    SqlTypeList = dictfetchall(sqlPerfCursor)
    #SqlTypeList = [{'SqlType':'select'},{'SqlType':'insert'},{'SqlType':'update'},{'SqlType':'delete'}] 

    #检查表单是否提交
    #并获取提交的表单值
    if request.GET:
        getData = request.GET
        topN = int(getData.get('topN',''))
        DBName = getData.getlist('DBName','')
        SqlType = getData.getlist('SqlType','')
        beginTime = getData.get('beginTime','')
        endTime = getData.get('endTime','')

        #服务器端验证时间值、时间范围是否合理
        dt = datetime.datetime
        dtBeginTime = dtEndTime = ''

        if beginTime and endTime:
            try:
                dtBeginTime = dt.strptime(beginTime,'%Y-%m-%d %H:%M')
            except:
                errors.append("开始时间'" + beginTime + "'格式错误！请使用'yyyy-mm-dd hh:mm'格式！")

            try:
                dtEndTime = dt.strptime(endTime,'%Y-%m-%d %H:%M')
            except:
                errors.append("结束时间'" + endTime + "'格式错误！请使用'yyyy-mm-dd hh:mm'格式！")

            if dtBeginTime and dtEndTime:
                if dtBeginTime >= dtEndTime:
                    errors.append("开始时间'" + beginTime + "'大于或等于结束时间'" + endTime + "'！")
        else:
            if not beginTime:
                errors.append("请输入开始时间！")
            if not endTime:
                errors.append("请输入结束时间！")

        #验证是否选择了数据库
        if not DBName:
            errors.append("请选择数据库！")
        if not SqlType:
            errors.append("请选择SQL类型！")
        if errors:
            sqlPerfCursor.close()
            sqlPerfConn.close()

            context = {
                'title':'DMLSQL日志监控',
                'user':request.user,
                'DBList':DBList,
                'SqlTypeList':SqlTypeList,
                'DBName':DBName,
                'SqlType':SqlType,
                'beginTime':beginTime,
                'endTime':endTime,
                'topN':topN,
                'errors':errors,
            }

            return render_to_response('DMLlogmonitor.html',context)

		#共通的查询内容
        queryContent ="""case when b.SqlText<>'' then b.SqlText else b.DIGEST_TEXT end as sqlinfo,a.HostName,a.SCHEMA_NAME,a.DIGEST
            from dmlsql_history as a join dmlsql_sample as b on a.HostName=b.HostName and a.SCHEMA_NAME=b.SCHEMA_NAME and a.DIGEST=b.DIGEST
            """


        #共通的查询条件
        DBnameSet = '(' + ','.join(['"'+ item + '"' for item in DBName]) + ')'
        SqlTypeSet = '(' + ','.join(['"'+ item + '"' for item in SqlType]) + ')'
        whereCondition = \
            (" where a.HostName='%s' and a.SCHEMA_NAME in %s and b.SQL_Type in %s "
            " and a.Data_Time between '%s' and '%s' ") % \
            (host, DBnameSet, SqlTypeSet,beginTime, endTime)


        #共通的分组条件
        groupByCondition = " group by a.HostName,a.SCHEMA_NAME,a.DIGEST "

        #获取前N个执行次数最多的慢语句
        getTopNCounts = \
            ("select sum(COUNT_STAR) as perCounts, "
            + queryContent
            + whereCondition
            + groupByCondition +
            " order by perCounts desc "
            " limit %s ")

        #获取前N个平均扫描行数最多的慢语句
        getTopNAvgRows = \
            ("select round(sum(SUM_ROWS_EXAMINED)/sum(COUNT_STAR)) as perAvgRows, "
            + queryContent
            + whereCondition
            + groupByCondition +
            " order by perAvgRows desc "
            " limit %s ")
	
		#获取前N个平均实行时间最长的慢语句
        getTopNqueryTimeAvg = \
            ("select round(avg(AVG_TIMER_WAIT)/1000000000) as perQueryTimeAvg, "
            + queryContent
            + whereCondition
            + groupByCondition +
            " order by perQueryTimeAvg desc "
            " limit %s ")

        #最近一段时间新上线的SQL，按照执行时间进行排序
        newreleasesql = """ and b.DataChange_LastTime between '%s' and '%s' """ % (beginTime,endTime)
        getTopNnewreleaseSQL = \
            ("select  round(avg(AVG_TIMER_WAIT)/1000000000) as newperQueryTimeAvg, "
            "case when b.SqlText<>'' then b.SqlText else b.DIGEST_TEXT end as sqlinfo,a.HostName,a.SCHEMA_NAME,a.DIGEST"
            " from dmlsql_history as a join dmlsql_sample as b "
            "on a.HostName=b.HostName and a.SCHEMA_NAME=b.SCHEMA_NAME and a.DIGEST=b.DIGEST"
            + whereCondition
            + newreleasesql
            + groupByCondition +
            " order by newperQueryTimeAvg desc "
            " limit %s ")


        #设置将要显示前几个执行次数最多，总执行时间最久，平均执行时间最长的SQl语句以及语句截取长度
        truncateLenth = 1000
        topNParam = [topN,]
        nCounts = sqlPerfCursor.execute(getTopNCounts, topNParam)
        topNCounts =  dictfetchall(sqlPerfCursor)

        nAvgRows = sqlPerfCursor.execute(getTopNAvgRows, topNParam)
        topNAvgRows =  dictfetchall(sqlPerfCursor)

        nQueryTimeAvg  = sqlPerfCursor.execute(getTopNqueryTimeAvg, topNParam)
        topNqueryTimeAvg =  dictfetchall(sqlPerfCursor)

        nNewRelease = sqlPerfCursor.execute(getTopNnewreleaseSQL,  topNParam)
        topNnewRelease = dictfetchall(sqlPerfCursor)

        if nNewRelease == 0:
            topNnewRelease=[{'newperQueryTimeAvg':0,'sqlinfo':'','HostName':'','SCHEMA_NAME':'','DIGEST':''}]

        sqlPerfCursor.close()
        sqlPerfConn.close()


        context = {
            'title':'DMLSQL日志监控',
            'user':request.user,
            'DBList':DBList,
            'DBName':DBName,
            'SqlTypeList':SqlTypeList,
            'SqlType':SqlType,
            'topNCounts':topNCounts,
            'topNAvgRows':topNAvgRows,
            'topNqueryTimeAvg':topNqueryTimeAvg,
            'topNnewRelease':topNnewRelease,
            'beginTime':beginTime,
            'endTime':endTime,
            'topN':topN,
            'nCounts':nCounts,
            'nAvgRows':nAvgRows,
            'nQueryTimeAvg':nQueryTimeAvg,
            'nNewRelease':nNewRelease,
        }


        return render_to_response('DMLlogmonitor.html',context)

	#构造默认开始时间和结束时间
    tz = SHTZ(8, 'Asia/Shanghai')
    timedelta = datetime.timedelta(days=-1)
    nowTime = datetime.datetime.now(tz)
    beginTime = (nowTime + timedelta).strftime('%Y-%m-%d %H:%M')
    endTime = nowTime.strftime('%Y-%m-%d %H:%M')


    context = {
        'title':'DMLSQL日志监控',
        'user':request.user,
        'DBList':DBList,
        'SqlTypeList':SqlTypeList,
        'beginTime':beginTime,
        'endTime':endTime,
    }
    return render_to_response('DMLlogmonitor.html',context)


def getDMLLogData(request):
    if request.method == 'POST':
        postData = request.POST
        hostName = postData.get('HostName','')
        DBName = postData.get('SCHEMA_NAME','')
        hashCode = postData.get('DIGEST','')


        sql = """
          select sum(COUNT_STAR),round(AVG_TIMER_WAIT/1000000000) as AVG_TIME,
          round(SUM_ROWS_SENT/COUNT_STAR) as AVG_ROWS_SENT,
          round(SUM_ROWS_EXAMINED/COUNT_STAR) as AVG_ROWS_EXAMINED,
          SUM_ERRORS,
          unix_timestamp(Data_Time)*1000 as `timeStamp`  
          from dmlsql_history 
          where HostName=%s
          and SCHEMA_NAME=%s
          and DIGEST=%s 
          and Data_Time between %s and %s
          and COUNT_STAR<>0
          group by Data_Time
          order by Data_Time 
          """

    #取90天以内的数据
    tz = SHTZ(8, 'Asia/Shanghai')
    timedelta = datetime.timedelta(days=-30)
    nowTime = datetime.datetime.now(tz)
    beginTime = (nowTime + timedelta).strftime('%Y-%m-%d %H:%M:%S')
    endTime = nowTime.strftime('%Y-%m-%d %H:%M:%S')

    param = [hostName, DBName, hashCode, beginTime, endTime]

    sqlPerfConn = getConn(sqlperfserver, sqlperfport, sqlperfdb,'')
    sqlPerfCursor = sqlPerfConn.cursor()

    sqlPerfCursor.execute(sql, param)
    result = sqlPerfCursor.fetchall()

    sqlPerfCursor.close()
    sqlPerfConn.close()

    executionCount = []
    avgRowssent = []
    avgRowsexamined = []
    queryTime = []
    sumerrors = []



    for COUNT_STAR, AVG_TIME, AVG_ROWS_SENT,AVG_ROWS_EXAMINED,SUM_ERRORS,timeStamp in result:
        executionCount.append([timeStamp, int(COUNT_STAR)])
        avgRowssent.append([timeStamp, int(AVG_ROWS_SENT)])
        avgRowsexamined.append([timeStamp, int(AVG_ROWS_EXAMINED)])
        queryTime.append([timeStamp, int(AVG_TIME)])
        sumerrors.append([timeStamp, int(SUM_ERRORS)])

    message = {
        'hostName':hostName,
        'DBName':DBName,
        'hashCode': hashCode,
        # 'beginTime':beginTime,
        # 'endTime':endTime,
        'executionCount':executionCount,
        'queryTime':queryTime,
        'avgRowssent':avgRowssent,
        'avgRowsexamined':avgRowsexamined,
        'sumerrors':sumerrors,
    }

    response = HttpResponse()
    response['Content-Type'] = "application/json"
    response.write(json.dumps(message))

    return response

@login_required
def dmlswitchlist(request):
    errors=[]
    row_list={}
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    dbmonitorcon=getConn('127.0.0.1',3306,'sqlmonitordb')
    cursor=dbmonitorcon.cursor()
    q = request.GET.get('q','')
    machines=''
    qmachine=dbmonitorconnection(q)
    for row in qmachine:
        machines=machines+"'"+row+"',"
    machines=machines.strip(',')
    if machines == '' and q != '':
        machines="'"+q+"'"
    if machines == '' and q == '':
        cursor.execute("""select service_name,machine_name,env_type,case when perf_status=0 then 0 else monitor_status end as monitor_status ,perf_slowsql,collect_dmv,collect_trace from serverlist 
            where db_type='MySQL' and dns not like 'DWInfobright%'  order by env_type,monitor_status""")
        getdmlswitchlist = dictfetchall(cursor)
    else:
        cursor.execute("""select service_name,machine_name,env_type,case when perf_status=0 then 0 else monitor_status end as monitor_status,perf_slowsql,collect_dmv,collect_trace from serverlist 
            where db_type='MySQL' and dns not like 'DWInfobright%' and machine_name in ("""+machines+""")  order by env_type,monitor_status""")
        getdmlswitchlist = dictfetchall(cursor)

    if request.method=='POST':
        if not request.user.has_perm('ServerAdmin.dbserverinfo'):
            errors.append('对不起，你没有权限进行此操作！')
        if errors:
            return render_to_response('error.html',{
                'errors':errors,
                'user':request.user,
                'title':"Error"
        })
        for key in request.POST:
            value= request.POST.getlist(key)
            switch_status=value[0].split('_')[0]
            switch_operation=value[0].split('_')[1]
            if (switch_status == '1' and switch_operation == 'off') or (switch_status == '0' and switch_operation == 'on'):
                machine_name = key.split('_')[2]
                switch_type  = key.split('_')[0]

                if switch_type == 'monitor':
                    property='monitor_status'
                    serverlist_property='monitor_status'
                elif switch_type == 'slowlog':
                    property='perf_slowsql'
                    serverlist_property='perf_slowsql'
                elif switch_type == 'dmv':
                    property='monitor_dmv'
                    serverlist_property='collect_dmv'
                elif switch_type == 'trace':
                    property='monitor_trace'
                    serverlist_property='collect_trace'

                if switch_operation == 'on':
                    property_value=1
                elif switch_operation == 'off':
                    property_value=0

                updatesql_control="""update control_machine_monitorstatus 
                                    set property_value="""+str(property_value)+""",expire_time=null where machine_name='"""+machine_name+"""' and property='"""+property+"""'"""
                updatesql_serverlist="""update serverlist set """+serverlist_property+"""="""+str(property_value)+""" where machine_name='"""+machine_name+"""'"""

                cursor.execute(updatesql_control)
                cursor.execute(updatesql_serverlist)
                cursor.connection.commit()
    context = {
        'title':'服务器监控开关管理',
        'user':request.user,
        'getdmlswitchlist':getdmlswitchlist,
    }

    return render_to_response('dmlswitchlist.html',context)

@login_required
def disaster_recovery_serverlist(request):
    errors=[]
    row_list={}
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    q = request.GET.get('q','')
    machines=''
    row_list={}

    if request.method=='POST':
        add_clustername=request.POST.get('add_clustername','')
        add_clusterip=request.POST.get('add_clusterip','')
        drstorage_choice=request.POST.get('drstorage_choice','')
        master_host=drstorage_choice.split('(')[0].strip()
        mysqlupload_con=getConn('127.0.0.1',3306,'mysqluploaddb')
        mysqlupload_cursor=mysqlupload_con.cursor()

        insert_mysql_disaster_recovery="""insert into mysql_disaster_recovery(master_host,service_name,
        service_ip,service_port,server_status,slave_status,masterhost_monitorswitch,dr_monitorswitch)
        select '%s','%s','%s',3306,'Good','Good','T','T'""" % (master_host,add_clustername,add_clusterip)
        mysqlupload_cursor.execute(insert_mysql_disaster_recovery)
        mysqlupload_cursor.connection.commit()

    cursor.execute("""select concat(machine_name,' (所在地:',machine_local,' 已有',clustercounts,'个节点)') as info from mysql_disaster_bakpools""")
    machinepoolrows=dictfetchall(cursor)
    cursor.execute("""select distinct(master_host) from mysql_disaster_recovery where locate(%s,service_name)>0 
            union all
            select distinct(master_host) from mysql_disaster_recovery where locate(%s,master_host)>0 
            """,[q,q])
    for machine_name in cursor.fetchall():
        machines=machines+"'"+machine_name[0]+"',"
    machines=machines.strip(',')
    if q == '':
        cursor.execute("""select concat(master_host,'[',pool.machine_local,']') as master_host, concat(service_name,'[',my.located,']') as service_name,
service_ip,service_port,server_status,slave_status 
from mysql_disaster_recovery as info left join mysql_disaster_bakpools as pool 
on info.master_host=pool.machine_name left join (select AppName,located from mysql_serverstatus group by AppName) as my 
on info.service_name=my.AppName order by server_status,slave_status,master_host""")
        row_list=dictfetchall(cursor)
    else:
        if machines != "":
            cursor.execute("""
        select concat(master_host,'[',pool.machine_local,']') as master_host, concat(service_name,'[',my.located,']') as service_name,
        service_ip,service_port,server_status,slave_status from mysql_disaster_recovery as info left join mysql_disaster_bakpools as pool 
        on info.master_host=pool.machine_name left join (select AppName,located from mysql_serverstatus group by AppName) as my 
        on info.service_name=my.AppName 
        where master_host in ("""+machines+""") order by server_status,slave_status,master_host""")
            row_list=dictfetchall(cursor)
    paginator = Paginator(row_list, 500)
    page = request.GET.get('page')

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)
   

    return render_to_response('disaster_recovery_serverlist.html',{
        'user':request.user,
        'title':"MySQL异地容灾服务器信息",
        'rows':rows,
        'machinepoolrows':machinepoolrows,
    })


##获取dr节点 服务器复制状况
def viewdrslavestatus(request,drip,drport,drclustername):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })

    master=''
    s_status={}
    m_status={}
    showslavestatus={}
    rs_status={}

    conn=getConn(drip,int(drport),'mysql','')
    cur=conn.cursor()
    cur.execute("show slave status;")
    showslavestatus=dictfetchall(cur)
    m_file=showslavestatus[0]['Master_Log_File'].strip()
    master=m_file[0:m_file.find('-bin')]
    cur.execute("""select *
    from information_schema.GLOBAL_STATUS
    where variable_name in ('SLAVE_RUNNING','RPL_SEMI_SYNC_SLAVE_STATUS')
    union all
    select 'HEARTBEAT',time
    from configdb.repl_heartbeat where hostname=%s;""",[master])
    s_status=statusfetch(cur)
    cur.close()
    m_conn=getConn(showslavestatus[0]['Master_Host'],int(showslavestatus[0]['Master_Port']),'mysql','')
    m_cur=m_conn.cursor()
    m_cur.execute("select * from information_schema.GLOBAL_STATUS where VARIABLE_NAME='RPL_SEMI_SYNC_MASTER_STATUS';")
    m_status=statusfetch(m_cur)
    m_cur.close()

    if showslavestatus == {}:
        showslavestatus=['']
    return render_to_response('viewdrslavestatus.html',{
        'user':request.user,
        'title':drclustername+'DR节点复制状态',
        'dbtype':'MySQL',
        'master':master,
        's_status':s_status,
        'm_status':m_status,
        'showslavestatus':showslavestatus[0],
        'rs_status':rs_status,
    })


def drcontrol(request,drmaster_host):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    drmaster_host=drmaster_host[0:drmaster_host.find('[')]
    cursor.execute("select masterhost_monitorswitch from mysql_disaster_recovery where master_host='"+drmaster_host+"' limit 1")
    masterhost_monitorswitch=cursor.fetchone()[0]
    if request.method=='POST':
        drswitch=request.POST.get('drmasterswitch','')
        drmaster_closedescription=request.POST.get('drmaster_closedescription','')
        cursor.execute("update mysql_disaster_recovery set masterhost_monitorswitch='"+drswitch+"' where master_host='"+drmaster_host+"'")
        cursor.connection.commit()
        cursor.execute("insert into drmonitorswitchlog(drswitch_type,servername,drswitch_status,operator,Operation_reason) select 'masterhost_monitorswitch','"+drmaster_host+"','"+drswitch+"','"+str(request.user)+"','"+drmaster_closedescription+"'")
        cursor.connection.commit()
    return render_to_response('viewdrcontrol.html',{
        'user':request.user,
        'title':'DR节点'+drmaster_host+'信息管理',
        'masterhost_monitorswitch':masterhost_monitorswitch,
        'drmaster_host':drmaster_host,
    })

@login_required
def smoking_show(request):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    q = request.GET.get('q','')
    machines=''
    row_list={}
    if request.method=='POST':
        add_ignore_machine=request.POST.get('add_ignore_machine','')
        add_ignore_reason=request.POST.get('add_ignore_reason','')
        mysqlupload_con=getConn('127.0.0.1',3306,'sqlperfdb')
        mysqlupload_cursor=mysqlupload_con.cursor()
        insert_ignore_mysql_cpu="insert into ignore_mysql_cpu(machine_name,ignore_reason,operator) select '%s','%s','%s'" % (add_ignore_machine,add_ignore_reason,str(request.user))
        mysqlupload_cursor.execute(insert_ignore_mysql_cpu)
        mysqlupload_cursor.connection.commit()

    cursor = connection.cursor()
    if q == '':
        cursor.execute("""select id,a.machine_name,dns,case when b.machine_name is null then '非关键' else '关键' end as importance,ObjectName,
        CounterValue,top_info,'show processlist' as proc,'show engine innodb stauts' as engine,a.insert_time from sqlperfdb.smoking_mysql_cpu as a
        left join sqlperfdb.mysql_importance_machine as b on a.machine_name=b.machine_name
        order by id desc""")
        row_list=dictfetchall(cursor)
    else:
        count=cursor.execute("""select distinct(machine_name) from sqlperfdb.smoking_mysql_cpu where locate(%s,machine_name)>0""",[q])
        if count > 0:
            for machine_name in cursor.fetchall():
                machines=machines+"'"+machine_name[0]+"',"
            machines=machines.strip(',')
        if machines != "":
            cursor.execute("""select id,a.machine_name,dns,case when b.machine_name is null then '非关键' else '关键' end as importance,ObjectName,
            CounterValue,top_info,'show processlist' as proc,'show engine innodb stauts' as engine,a.insert_time from sqlperfdb.smoking_mysql_cpu as a
            left join sqlperfdb.mysql_importance_machine as b on a.machine_name=b.machine_name where a.machine_name in ("""+machines+""")
            order by id desc;""")
            row_list=dictfetchall(cursor)
        else:
            cursor.execute("""select id,a.machine_name,dns,case when b.machine_name is null then '非关键' else '关键' end as importance,ObjectName,       
            CounterValue,top_info,'show processlist' as proc,'show engine innodb stauts' as engine,a.insert_time from sqlperfdb.smoking_mysql_cpu as a
            left join sqlperfdb.mysql_importance_machine as b on a.machine_name=b.machine_name
            order by id desc""")
            row_list=dictfetchall(cursor)
        
        
    paginator = Paginator(row_list, 500)
    page = request.GET.get('page')

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    return render_to_response('smoking_show.html',{
        'user':request.user,
        'title':"MySQL Smoking Info",
        'rows':rows,
    })

@login_required
def smoking_show_processlist(request,id):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    
    cursor = connection.cursor()
    cursor.execute("select proc_info from sqlperfdb.smoking_mysql_cpu where id="+id+"")
    proc_status=dictfetchall(cursor)
    return render_to_response('smoking_show_processlist.html',{
        'user':request.user,
        'title':'数据库中抓取的进程信息',
        'proc_status':proc_status[0],
    })

@login_required
def smoking_show_engine(request,id):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    cursor = connection.cursor()
    cursor.execute("select replace(engine_info,'\n','<br />') as engine_info from sqlperfdb.smoking_mysql_cpu where id="+id+"")
    engine_status=dictfetchall(cursor)
    return render_to_response('smoking_show_engine.html',{
        'user':request.user,
        'title':'MySQL Innodb 引擎状况',
        'engine_status':engine_status[0],
    })


###获取到全备份的日志信息
def backupalllog_show(request):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    dbmonitor=getConn('127.0.0.1',3306,'sqlmonitordb')
    cursor=dbmonitor.cursor()
    
    q = request.GET.get('q','')
    cluster=''
    row_list={}
    if q == '':
        cursor.execute("""select a.machine_name,b.cluster_name,ifnull(a.backup_start_time,'') as backup_start_time,ifnull(a.backup_end_time,'') as 'last_backuptime',
        ifnull(a.ftp_end_time,'') as ftp_end_time,
        case when (errorinfo='' or errorinfo is null) and backup_end_time>=date_add(date(now()),interval -3 day) then 'Good' 
        when b.backupall_swtich=0 then 'Closed'
        else 'Failed' end as backupstatus,'info'
        from mysql_data_backupallinfo as a join
        mycrond_control as b on a.machine_name=b.machine_name order by backupstatus""")
        row_list=dictfetchall(cursor)
    else:
        count=cursor.execute("""select distinct(cluster_name) from mycrond_control where locate(%s,cluster_name)>0""",[q])
        if count > 0:
            for cluster_name in cursor.fetchall():
                cluster=cluster+"'"+cluster_name[0]+"',"
                cluster=cluster.strip(',')
        if cluster != "":
            cursor.execute("""select a.machine_name,b.cluster_name,ifnull(a.backup_start_time,'') as backup_start_time,ifnull(a.backup_end_time,'') as 'last_backuptime',
            ifnull(a.ftp_end_time,'') as ftp_end_time,
            case when (errorinfo='' or errorinfo is null) and backup_end_time>=date_add(date(now()),interval -3 day) then 'Good' 
            when b.backupall_swtich=0 then 'Closed'
            else 'Failed' end as backupstatus,'info'
            from mysql_data_backupallinfo as a join
            mycrond_control as b on a.machine_name=b.machine_name 
            where b.cluster_name in ("""+cluster+""")
            order by backupstatus""")
            row_list=dictfetchall(cursor)

        else:
            cursor.execute("""select a.machine_name,b.cluster_name,ifnull(a.backup_start_time,'') as backup_start_time,ifnull(a.backup_end_time,'') as 'last_backuptime',
            ifnull(a.ftp_end_time,'') as ftp_end_time,
            case when (errorinfo='' or errorinfo is null) and backup_end_time>=date_add(date(now()),interval -3 day) then 'Good' 
            when b.backupall_swtich=0 then 'Closed'
            else 'Failed' end as backupstatus,'info'
            from mysql_data_backupallinfo as a join
            mycrond_control as b on a.machine_name=b.machine_name order by backupstatus""")
            row_list=dictfetchall(cursor)
            
    paginator = Paginator(row_list, 500)
    page = request.GET.get('page')

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    return render_to_response('backupalllog_show.html',{
        'user':request.user,
        'title':"MySQL BackupLog Info",
        'rows':rows,
    })
@login_required
def backupalllog_errorinfo(request,machine_name):
    errors=[]
#    if not request.user.is_superuser:
#        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
            'errors':errors,
            'user':request.user,
            'title':"Error"
        })
    
    dbmonitor=getConn('127.0.0.1',3306,'sqlmonitordb')
    cursor=dbmonitor.cursor()
    cursor.execute("select errorinfo from mysql_data_backupallinfo where machine_name='"+machine_name+"'")
    proc_status=dictfetchall(cursor)
    return render_to_response('backupalllog_errorinfo.html',{
        'user':request.user,
        'title':'全备份报错信息',
        'proc_status':proc_status[0],
    })

@login_required
def chainJoinKeyToTableName(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'GET':
        getData = request.GET.copy()

        DNS = getData.pop("DNS")[0].strip()
        port = int(getData.pop("port")[0].strip())
        DBName = getData.pop("DBName")[0].strip()
        tableName = getData.values()[0].strip()
        
        getKeyColumnSql = \
                (" select COLUMN_NAME,  "
                 " COLUMN_TYPE"
                 " from COLUMNS  " 
                 " where TABLE_SCHEMA=%s "
                 " and TABLE_NAME=%s" 
                 " and COLUMN_KEY<>''")
        

        conn = getConn(DNS, port, 'information_schema','')
        cursor = conn.cursor()

        param = [DBName, tableName]
        cursor.execute(getKeyColumnSql, param)
        keyColumns = cursor.fetchall()

        message = [[""," -- "]]
        for columnName,columnType in keyColumns:
            message.append([columnName, columnName + " " +  columnType])
        
        response.write(json.dumps(message))
        return response


@login_required
def getConnInfo(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        DBName = postData.get('DBName','').strip()
    
        connInfoList = []

        getConnInfoSql = \
                (" select Host, Port, EnvID"
                 " from release_dbconfig "
                 " where Upload_DBName=%s")
        
        cursor = connection.cursor()
        
        param = [DBName,]
        cursor.execute(getConnInfoSql, param)
        connInfos = cursor.fetchall()

        for host, port, envID in connInfos:
            connInfoDict = {"host":host, "port":port, "envID":envID}
            if int(envID) == 4:
                connInfoList.insert(0, connInfoDict)
            else:
                connInfoList.append(connInfoDict) 

        cursor.close()

        message = {
            'connInfoList':connInfoList
        }
        
        response.write(json.dumps(message))
        return response

@login_required
def getTableNames(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        DNS = postData.get('DNS','').strip()
        port = int(postData.get('port','').strip())
        DBName = postData.get('DBName','').strip()
    
        tableNameList = []

        getTablesSql = \
                (" select TABLE_NAME "
                 " from TABLES "
                 " where TABLE_SCHEMA=%s")

        conn = getConn(DNS, port, 'information_schema','')
        cursor = conn.cursor()
        
        param = [DBName,]
        cursor.execute(getTablesSql, param)
        tableNames = cursor.fetchall()

        for item, in tableNames:
            tableNameList.append(item) 

        cursor.close()
        conn.close()

        message = {
            'tableNameList':tableNameList
        }
        
        response.write(json.dumps(message))
        return response
    
def getTableTypeFunc(dns, port, dbName, tableName):
    tableType = ''
    tableNoExist = False

    getTableTypeSql = \
            ("select PARTITION_NAME, PARTITION_EXPRESSION "
                " from PARTITIONS "
                " where TABLE_SCHEMA=%s "
                " and TABLE_NAME=%s "
                " limit 1")

    conn = getConn(dns, port, 'information_schema','')
    cursor = conn.cursor()
    
    param = [dbName,tableName]
    cursor.execute(getTableTypeSql, param)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    if result:
        for partitionName, partitionExpression in result:
            if partitionName:
                tableType = 1 #分区表
            else:
                tableType = 2 #普通表
        
        tableNoExist = True

    return (tableNoExist, tableType)


@login_required
def getTableType(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        DNS = postData.get('DNS','').strip()
        port = int(postData.get('port','').strip())
        DBName = postData.get('DBName','').strip()
        tableName = postData.get('tableName','').strip()
    
        (tableNoExist, tableType) = getTableTypeFunc(DNS, port, DBName, tableName)

        message = {
            'tableNoExist':tableNoExist,
            'tableType':tableType
        }
        
        response.write(json.dumps(message))
        return response  
    
@login_required
def getColumnNames(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        DNS = postData.get('DNS','').strip()
        port = int(postData.get('port','').strip())
        DBName = postData.get('DBName','').strip()
        tableName = postData.get('tableName','').strip()
    
        keyColumnList = []
        timeColumnList = []

        (tableNoExist, tableType) = getTableTypeFunc(DNS, port, DBName, tableName)

        if tableType == 1:
            dataTypeSet = ('DATETIME','TIMESTAMP','DATE')
        elif tableType == 2:
            dataTypeSet = ('INTEGER','INT','SMALLINT','TINYINT','MEDIUMINT','BIGINT','DATETIME','TIMESTAMP','DATE')

        getKeyColumnSql = \
                ("select COLUMN_NAME, COLUMN_TYPE "
                    " from COLUMNS "
                    " where TABLE_SCHEMA='%s' "
                    " and TABLE_NAME='%s' "
                    " and COLUMN_KEY <> ''") % (DBName,tableName)

        getTimeColumnSql = \
                ("select COLUMN_NAME,COLUMN_TYPE  "
                    " from COLUMNS "
                    " where TABLE_SCHEMA='%s' "
                    " and TABLE_NAME='%s' "
                    " and  DATA_TYPE in %s") % (DBName, tableName, str(dataTypeSet))

           
        conn = getConn(DNS, port, 'information_schema','')
        cursor = conn.cursor()
        
        cursor.execute(getKeyColumnSql)
        keyColumns = cursor.fetchall()

        for columnName,columnType in keyColumns:
            keyColumnList.append({"columnName":columnName,"columnType":columnType})

        cursor.execute(getTimeColumnSql)
        timeColumns = cursor.fetchall()

        for columnName,columnType in timeColumns:
            timeColumnList.append({"columnName":columnName,"columnType":columnType})

        cursor.close()
        conn.close()

        message = {
            'keyColumnList':keyColumnList,
            'timeColumnList':timeColumnList
        }
        
        response.write(json.dumps(message))
        return response

@login_required
def getColumnType(request):
    response = HttpResponse()
    response['Content-Type'] = "application/json"
    
    if request.method == 'POST':
        postData = request.POST
        DNS = postData.get('DNS','').strip()
        port = int(postData.get('port','').strip())
        DBName = postData.get('DBName','').strip()
        tableName = postData.get('tableName','').strip()
        columnName = postData.get('columnName','').strip()
    
        getColumnTypeSql = \
                ("select DATA_TYPE "
                    " from COLUMNS "
                    " where TABLE_SCHEMA=%s "
                    " and TABLE_NAME=%s "
                    " and COLUMN_NAME=%s ")
        
        conn = getConn(DNS, port, 'information_schema','')
        cursor = conn.cursor()
        
        param = [DBName,tableName,columnName]
        cursor.execute(getColumnTypeSql, param)
        columnType = cursor.fetchall()

        if columnType:
            for item, in columnType:
                message = {
                'columnType':item,
            }
        else:
            message = {
             'columnType':'',
            }
            
        cursor.close()
        conn.close()
        
        response.write(json.dumps(message))
        return response

def showprocessresult(request):
    print 111
    batch_id=0
    if request.method=='POST':
        batch_id=request.POST.getlist('batch_id')[0]
    batch_id=str(batch_id)
    #batch_id=78
    db=connection.cursor()
    sql="select jid from salt_verify_hostname where batch_id=%s and jid !='' limit 1" %(batch_id)
    db.execute(sql)
    jid= db.fetchall()
    if jid!=():
        jid=jid[0][0]
    else:
        jid=0
    print jid
    sql="select shortci,web_ip,targetip,reuslt,status from mysqluploaddb.salt_verify_hostname where jid='%s'" % (jid)
    # sql="select service_name,web_ip,if(locate('Successfully connected to',result)>0,'successful','Fail') as result_simple,target_ip,result from salt_verify_result where  batch_id=%s order by result_simple asc" % (batch_id)
    db.execute(sql)
    results = db.fetchall()
    havedonenum = 0
    message={"results":results,"havedonenum":havedonenum}
    json=simplejson.dumps(message,ensure_ascii = False)
    return HttpResponse(json,mimetype='application/json')


def viewscronlist(request):
    errors=[]
    if not request.user.is_superuser:
        errors.append('Sorry,only superusers are allowed to do this!')
    if errors:
        return render_to_response('error.html',{
        'errors':errors,
        'user':request.user,
        'title':"Error"
        })
    serverlistmeta = Serverlist("mysql")
    pool = Pool(20)
    serverlist = pool.map(servercroninit,serverlistmeta.serverlist)
    pool.close()
    pool.join()
    cronhandler = Cronhandler()
    for server in serverlist:
        cronhandler.getcronstatus(server)
    serverlist.sort(key = lambda x:x.cronstatus)
    return render_to_response( 'cronlist.html',{
        'serverlist':serverlist,
    })


