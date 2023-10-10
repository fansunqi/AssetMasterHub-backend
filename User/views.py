import json
import math
from django.http import HttpRequest,JsonResponse
from utils.config import *
from User.models import *
from Asset.models import *
from utils.utils_request import BAD_METHOD, request_failed, request_success, return_field
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require
from utils.sessions import *
from utils.model_date import *
# from utils.manipulate_database import *
from rest_framework.request import Request
import requests
from utils.utils_other import *
from utils.utils_add_data import *
from utils.utils_asset import *
import hashlib
import base64
import time
import datetime as dt
from Crypto.Cipher import AES


def check_for_user_data(body):
    name = require(body, "UserName", "string",
                   err_msg="Missing or error type of name")
    hashed_password = require(body, "Password", "string",
                              err_msg="Missing or error type of password")
    assert 0 < len(name) <= 128, "Bad length of name"
    assert 0 < len(hashed_password) <= 32, "Bad length of password"
    return name, hashed_password


@CheckRequire
def login(req: Request):
    if req.method == 'POST':
        # 约定：同一用户可以同时在第二个设备上可以成功登录，但会顶掉第一个设备上的sessionid
        tmp_body = req.body.decode("utf-8")
        try:
            body = json.loads(tmp_body)
        except BaseException as error:
            print(error, tmp_body)

        name, hashed_password = check_for_user_data(body)

        # 再进行sha256加密
        sha_hashed_password = sha256(hashed_password)

        user = User.objects.filter(name=name).first()
        if not user:
            return request_failed(2, "用户名或密码错误")
        else:
            if user.Is_Locked:
                Log.objects.create(type=IN_OUT,user_name=user.name,entity_name=user.entity.name,is_succ=0,
                                   more_info=user.name + " 尝试登录系统，但该用户已被锁定")
                return request_failed(1,"用户已被锁定")
            elif user.password == sha_hashed_password:
                SessionPool.objects.filter(user=user).all().delete()
                session_id = get_session_id(req)
                bind_session_id(sessionId=session_id, user=user)
                print("successfully bind session id!")
                if user.super_administrator == 1:
                    Log.objects.create(type=IN_OUT,user_name=user.name,more_info=user.name + " 登录系统")
                else:
                    Log.objects.create(type=IN_OUT,user_name=user.name,entity_name=user.entity.name,more_info=user.name + " 登录系统")
                return request_success()
            else:
                if user.super_administrator == 1:
                    Log.objects.create(type=IN_OUT,user_name=user.name,is_succ=0,
                                       more_info=user.name + " 尝试登录系统，但密码错误")
                else:
                    Log.objects.create(type=IN_OUT,user_name=user.name,entity_name=user.entity.name,is_succ=0,
                                       more_info=user.name + " 尝试登录系统，但密码错误")
                return request_failed(3, "用户名或密码错误")
    else:
        return BAD_METHOD


def logout(req: Request):
    if req.method == 'POST':
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            user = sessionRecord.user
            disable_session_id(sessionId=session_id)
            if user.super_administrator == 1:
                Log.objects.create(type=IN_OUT,user_name=user.name,more_info=user.name + " 登出系统")
            else:
                Log.objects.create(type=IN_OUT,user_name=user.name,entity_name=user.entity.name,more_info=user.name + " 登出系统")
            return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def user_info(req: Request, sessionId: str):
    print("调用了user_info函数", sessionId)
    if req.method == 'GET':
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                usr = sessionRecord.user
                usr_info = {}
                usr_info["ID"] = usr.id
                usr_info["UserName"] = usr.name
                try:
                    usr_info["Entity"] = usr.entity.name
                except:
                    usr_info["Entity"] = None
                try:
                    usr_info["Department"] = usr.department.name
                except: 
                    usr_info["Department"] = None
                try:
                    usr_info["Mobile"] = usr.mobile[3:]
                except:
                    usr_info["Mobile"] = None
                usr_info["UserApp"] = usr.function_string
                usr_info["TODO"] = False
                usr_info["TOREAD"] = False
                if usr.super_administrator == 1:
                    usr_info["Authority"] = 0
                elif usr.system_administrator == 1:
                    usr_info["Authority"] = 1
                else:
                    toread_responses = list(PendingResponse.objects.filter(employee=usr,is_read=False).all()) 
                    toread_num = len(toread_responses)
                    if toread_num > 0:
                        usr_info["TOREAD"] = True 
                    if usr.asset_administrator == 1:
                        usr_info["Authority"] = 2
                        todo_requests = list(PendingRequests.objects.filter(asset_admin=usr,result=PENDING).all())
                        todo_num = len(todo_requests)
                        if todo_num > 0:
                            usr_info["TODO"] = True
                    else:
                        usr_info["Authority"] = 3                       
                return request_success(usr_info)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def get_all_member(req: Request, sessionId: str,page_id:str,search_name:str,search_dep:str,search_auth:str):
    print("调用了get_all_member函数", sessionId)
    if req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 1:
                    return request_failed(1, "无权限操作")
                else:
                    e1 = user.entity
                    return_data = {}              
                    search_name = search_name[5:]
                    search_dep = search_dep[11:]
                    search_auth = search_auth[10:]
                    member_list = []
                    if search_auth == "":
                        search_auth = "-1"
                    search_auth = int(search_auth)
                    if search_name != "":
                        member = User.objects.filter(name=search_name,entity=e1,system_administrator=0).first()
                        if member:
                            if search_dep != "":
                               if member.department.name == search_dep:
                                    member_list = [member]
                               else:
                                   member_list = []
                            else:
                                member_list = [member]
                        else:
                            member_list = []
                    else:
                        if search_dep != "":
                            d1 = Department.objects.filter(name=search_dep,entity=e1).first()
                            if d1:
                                member_list = list(User.objects.filter(department=d1).all())
                            else:
                                member_list = []
                        else:
                            member_list = list(User.objects.filter(entity=e1,system_administrator=0).all())            
                    if search_auth != -1 and search_auth != 2 and search_auth != 3:
                        return request_failed(1,"要搜索的authority不合法")
                    elif search_auth == 2:
                        member_list = [member for member in member_list if member.asset_administrator == 1]
                    elif search_auth == 3:
                        member_list = [member for member in member_list if member.asset_administrator == 0]
                    page = int(page_id)
                    member_num = len(member_list)
                    page_num = math.ceil(member_num / 20)
                    return_data["TotalNum"] = member_num
                    return_data["TotalPage"] = page_num
                    tmp_list : list[User] = []
                    # 访问不存在的页时，返回空
                    if 20 * (page - 1) + 1 > member_num:
                        tmp_list = []
                    # 能够完整返回20条信息
                    elif 20 * page <= member_num:
                        tmp_list = member_list[20 * (page - 1): 20 * page]
                    # 返回的信息不足20条
                    else:
                        tmp_list = member_list[20 * (page - 1):]
                    return_data["member"] = [return_field(member.serialize(),["Name","Department","Authority","lock"])
                                            for member in tmp_list]
                    return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def add_member(req: Request):
    print("调用了add_member函数")
    if req.method == "POST":
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    member_name = require(body, "UserName", "string",
                                          err_msg="Missing or error type of UserName")
                    department_path = require(body, "Department","string",
                                              err_msg="Missing or error type of Department")
                    if len(member_name) == 0 or len(member_name) >128:
                        return(1,"用户名长度不合规范")
                    for ch in member_name:
                        if ch == ' ' or ch == '/' or ch =='\\':
                            return request_failed(1,"存在非法字符")
                    member1 = User.objects.filter(name=member_name).first()
                    if member1:
                        return request_failed(1,"用户名已存在")
                    d1 = Department.objects.filter(path=department_path,entity=e1).first()
                    if not d1:
                        return request_failed(4,"部门不存在")
                    else:
                        if len(parse_children(d1.children)) != 0:
                            return request_failed(4,"不是叶子部门")
                        else:
                            User.objects.create(name=member_name,password=sha256(MD5("yiqunchusheng")),
                                                entity=e1,department=d1,
                                                super_administrator=0,system_administrator=0,asset_administrator=0,
                                                function_string="1111100000000000000000")
                            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                               more_info="系统管理员 " + user.name + " 在部门 " + d1.name + " 下创建了员工 " + member_name)
                            return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def remove_member(req:Request, sessionId:str, UserName:str):
    print("调用了remove_member函数")
    if req.method == "DELETE":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    member1 = User.objects.filter(name=UserName,entity=e1).first()
                    if not member1:
                        return request_failed(1,"用户不存在")
                    elif member1.system_administrator == 1:
                        return request_failed(1,"不能删除系统管理员")
                    # 还有资产则不能转移
                    a1 = Asset.objects.filter(user=member1).first()
                    if a1:
                        return request_failed(1,"用户还有资产，不能删除")
                    else:
                        if member1.asset_administrator == 1:
                            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                            more_info="系统管理员 " + user.name + " 删除了资产管理员 " + member1.name)
                        else:
                            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                            more_info="系统管理员 " + user.name + " 删除了员工 " + member1.name)
                        member1.delete()                    
                        return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def lock_member(req:Request):
    print("调用了lock_member函数")
    if req.method == "PUT":
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    member_name = require(body, "UserName", "string",
                                          err_msg="Missing or error type of UserName")
                    if len(member_name) == 0 or len(member_name) >128:
                        return(1,"用户名长度不合规范")
                    for ch in member_name:
                        if ch == ' ' or ch == '/' or ch =='\\':
                            return request_failed(1,"存在非法字符")
                    member = User.objects.filter(name=member_name,entity=e1).first()
                    if not member:
                        return request_failed(1,"用户不存在")
                    else:
                        if member.system_administrator == 1:
                            return request_failed(1,"不能更改系统管理员的锁定状态")
                        else:
                            member.Is_Locked = not member.Is_Locked
                            member.save()
                            if member.Is_Locked == True:
                                if member.asset_administrator == 1:
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                more_info="系统管理员 " + user.name + " 锁定了资产管理员 " + member.name)
                                else:
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                more_info="系统管理员 " + user.name + " 锁定了员工 " + member.name)
                            else:
                                if member.asset_administrator == 1:
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                more_info="系统管理员 " + user.name + " 解锁了资产管理员 " + member.name)
                                else:
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                more_info="系统管理员 " + user.name + " 解锁了员工 " + member.name)
                            SessionPool.objects.filter(user=member).all().delete()
                            return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def change_authority(req:Request):
    print("调用了change_authority函数")
    if req.method == "PUT":
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    member_name = require(body, "UserName", "string",
                                          err_msg="Missing or error type of UserName")
                    if len(member_name) == 0 or len(member_name) >128:
                        return(1,"用户名长度不合规范")
                    for ch in member_name:
                        if ch == ' ' or ch == '/' or ch =='\\':
                            return request_failed(1,"存在非法字符")
                    authority = require(body,"Authority","int",
                                        err_msg="Missing or error type of Authority")
                    member = User.objects.filter(name=member_name,entity=e1).first()
                    if not member:
                        return request_failed(1,"用户不存在")
                    else:
                        if member.system_administrator == 1:
                            return request_failed(1,"不能更改系统管理员的权限")
                        else:
                            if authority == 2:
                                if member.asset_administrator == 1:
                                    return request_success()
                                else:
                                    d1 = member.department
                                    member2 = User.objects.filter(department=d1,asset_administrator=1).first()
                                    if member2:
                                        return request_failed(4,"不能同时存在两个资产管理员")
                                    else:
                                        member.super_administrator = 0
                                        member.system_administrator = 0
                                        member.asset_administrator = 1
                                        member.function_string = "0000011111111100000000"
                                        member.save()
                                        Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                            more_info="系统管理员 " + user.name + " 将部门 " + d1.name + " 下的员工 " + member.name + " 提拔为资产管理员")
                                        SessionPool.objects.filter(user=member).all().delete()
                                        return request_success()
                            elif authority == 3:
                                if member.asset_administrator == 0:
                                    return request_success()
                                else:
                                    # 还有资产则不能罢黜
                                    a1 = Asset.objects.filter(user=member).first()
                                    if a1:
                                        return request_failed(1,"用户还有资产，不能删除")
                                    # 将资产管理员罢黜后，需要删除所有正在等待的pending request
                                    PendingRequests.objects.filter(asset_admin=member,result=PENDING).all().delete()
                                    # 更改权限
                                    member.super_administrator = 0
                                    member.system_administrator = 0
                                    member.asset_administrator = 0
                                    member.function_string = "1111100000000000000000"
                                    member.save()
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                            more_info="系统管理员 " + user.name + " 将部门 " + member.department.name + " 下的资产管理员 " + member.name + " 罢黜为员工")
                                    SessionPool.objects.filter(user=member).all().delete()
                                    return_data = {
                                        "important_message": "当前部门缺少资产管理员，请尽快添加",
                                    }
                                    return request_success(return_data)
                            else:
                                return request_failed(2,"无权更改为其他身份")
                            
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def remake_password(req:Request):
    print("调用了remake_password函数")
    if req.method == "POST":
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    member_name = require(body, "UserName", "string",
                                          err_msg="Missing or error type of UserName")
                    if len(member_name) == 0 or len(member_name) >128:
                        return(1,"用户名长度不合规范")
                    for ch in member_name:
                        if ch == ' ' or ch == '/' or ch =='\\':
                            return request_failed(1,"存在非法字符")
                    member = User.objects.filter(name=member_name,entity=e1).first()
                    if not member:
                        return request_failed(1,"用户不存在")
                    else:
                        if member.system_administrator == 1:
                            return request_failed(1,"不能重置系统管理员的密码")
                        else:
                            member.password = sha256(MD5("yiqunchusheng"))
                            member.save()
                            if member.asset_administrator == 1:
                                Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                            more_info="系统管理员 " + user.name + " 重置了资产管理员 " + member.name + " 的密码")
                            else:
                                Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                            more_info="系统管理员 " + user.name + " 重置了员工 " + member.name + " 的密码")
                            SessionPool.objects.filter(user=member).all().delete()
                            return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def get_subtree(dep:Department):
    nodeData = {}
    nodeData['title'] = dep.name
    # 解析出children_list
    children_list = parse_children(dep.children)
    # 如果这个asset_class没有children, 直接返回nodeData
    if len(children_list)==0:
        return nodeData 
    # 如果这个asset_class有children
    children = []
    for child_id in children_list:
        child_dep = Department.objects.filter(id=child_id).first()
        children.append(get_subtree(child_dep))
    nodeData["children"] = children
    return nodeData


def get_tree(req:Request,sessionId:str):
    if req.method == 'GET':
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    treeData = {}
                    treeData['title'] = e1.name + " 业务实体部门树"
                    children = []
                    children_list = list(Department.objects.filter(parent=None,entity=e1).all().order_by("path"))
                    for child in children_list:
                        children.append(get_subtree(child))
                    treeData['children'] = children
                    return request_success({"treeData":[treeData]})
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def add_department(req: Request):
    print("调用了add_department函数")
    if req.method == "POST":
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(4, "无权限操作")
                else:
                    e1 = user.entity
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    DepartmentPath = require(body, "DepartmentPath", "string",
                                             err_msg="Missing or error type of DepartmentPath")
                    DepartmentName = require(body, "DepartmentName", "string",
                                             err_msg="Missing or error type of DepartmentName")
                    if len(DepartmentName) == 0 or len(DepartmentName) >128:
                        return(1,"部门名长度不合规范")
                    for ch in DepartmentName:
                        if ch == ' ' or ch == '/' or ch =='\\':
                            return request_failed(1,"存在非法字符")
                    d1 = Department.objects.filter(name=DepartmentName,entity=e1).first()
                    if d1:
                        return request_failed(1, "部门名已存在")
                    # 如果要创建根部门
                    elif DepartmentPath == '000000000':
                        root_num = len(Department.objects.filter(parent=None,entity=e1).all())
                        if root_num >= 9:
                            return request_failed(3, "部门数已达到上限")
                        else:
                            new_departmentpath = DepartmentPath
                            tmp_list = list(new_departmentpath)
                            tmp_list[0] = str((1 + root_num))
                            new_departmentpath = ''.join(tmp_list)
                            new_d = Department.objects.create(entity=e1, 
                                                              name=DepartmentName,
                                                              path=new_departmentpath)
                            # 创建该部门的资产分类树
                            ac1 = AssetClass.objects.create(department=new_d, name=new_d.name + " 资产分类树", children="", property=0)
                            ac2 = AssetClass.objects.create(department=new_d, name="条目型资产", parent=ac1, children="", property=3)
                            ac3 = AssetClass.objects.create(department=new_d, name="数量型资产", parent=ac1, children="", property=4)
                            ac1.children = "$" + str(ac2.id) + "$" + str(ac3.id)
                            ac1.save()
                            return_data = {
                                    "department_path" : new_departmentpath
                                }
                            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                               more_info="系统管理员 " + user.name + " 创建了根部门 " + new_d.name)
                            return request_success(return_data)
                    # 不是根部门
                    else:
                        d2 = Department.objects.filter(path=DepartmentPath,entity=e1).first()
                        if not d2:
                            return request_failed(2, "部门路径无效")
                        elif DepartmentPath[-1] != '0':
                            return request_failed(2,"部门层数达到上限")
                        else:
                            # 就要判断有几个孩子
                            children_list = parse_children(d2.children)
                            child_num = len(children_list)
                            # 孩子太多塞不下
                            if child_num >= 9:
                                return request_failed(3, "部门数已达到上限")
                            # 能创建先创建
                            else:
                                new_departmentpath = DepartmentPath
                                for i in range(0, len(new_departmentpath)):
                                    if new_departmentpath[i] != '0':
                                        continue
                                    else:
                                        index = i
                                        break
                                tmp_list = list(new_departmentpath)
                                tmp_list[index] = str((1 + child_num))
                                new_departmentpath = ''.join(tmp_list)
                                new_d = Department.objects.create(parent=d2, entity=e1, 
                                                                  name=DepartmentName,
                                                                  path=new_departmentpath)
                                return_data = {
                                    "department_path" : new_departmentpath
                                }
                                # 如果是叶子部门,则要转移员工\资产分类树
                                if child_num == 0:
                                    d2.children = '$' + str(new_d.id)
                                    d2.save()
                                    member_list = list(User.objects.filter(department=d2).all())
                                    for member in member_list:
                                        member.department = new_d
                                        member.save()
                                    # 转移资产分类树时，根节点的名字要对应变化
                                    root_assetclass = AssetClass.objects.filter(department=d2,property=0).first()
                                    root_assetclass.name = new_d.name + "资产分类树"
                                    root_assetclass.save()
                                    assetclass_list = list(AssetClass.objects.filter(department=d2).all())
                                    for assetclass in assetclass_list:
                                        assetclass.department = new_d
                                        assetclass.save()
                                    asset_list = list(Asset.objects.filter(department=d2).all())   
                                    for asset in asset_list:
                                        asset.department = new_d
                                        asset.save()          
                                else:
                                    # 否则,直接创建该部门的资产分类树
                                    ac4 = AssetClass.objects.create(department=new_d, name=new_d.name + " 资产分类树", children="", property=0)
                                    ac5 = AssetClass.objects.create(department=new_d, name="条目型资产", parent=ac4, children="", property=3)
                                    ac6 = AssetClass.objects.create(department=new_d, name="数量型资产", parent=ac4, children="", property=4)
                                    ac4.children = "$" + str(ac5.id) + "$" + str(ac6.id)
                                    ac4.save()
                                    d2.children = d2.children + '$' + str(new_d.id)
                                    d2.save()
                                Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                               more_info="系统管理员 " + user.name + " 创建了非根部门 " + new_d.name)
                                return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def get_next_department(req:Request, sessionId:str, DepartmentPath:str,page_id:str,search_name:str,search_auth:str):
    print("调用了get_next_member函数")
    print(sessionId)
    print(DepartmentPath)
    if req.method == 'GET':
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    if DepartmentPath == '000000000':
                        is_leaf = False
                        root_list = list(Department.objects.filter(parent=None,entity=e1).all().order_by('path'))
                        root_num = len(root_list)
                        return_data = {
                            "TotalNum" : 0,
                            "TotalPage" : 0,
                            "is_leaf": is_leaf,
                            # 返回部门路径中经过的所有部门名
                            "route":[
                                {
                                    "Name": e1.name,
                                    "Path": "000000000"
                                }
                            ],
                            "member": [],
                            "Department": [
                                {
                                    "DepartmentName": root_list[i].name,
                                    "DepartmentPath": root_list[i].path,
                                    "DepartmentId": (i + 1)
                                }
                                for i in range(0, root_num)
                            ]
                        }
                        return request_success(return_data)
                    else:
                        d1 = Department.objects.filter(path=DepartmentPath,entity=e1).first()
                        if not d1:
                            return request_failed(1, "部门不存在")
                        else:
                            # 返回部门路径中经过的所有部门名
                            ancestor_list : list[Department] = []
                            ancestor_list.append(d1)
                            tmp_d = d1
                            while tmp_d.parent != None:
                                ancestor_list.append(tmp_d.parent)
                                tmp_d = tmp_d.parent
                            ansector_num = len(ancestor_list)
                            route_list : list[dict] = []
                            route_list.append({"Name": e1.name,"Path": "000000000"})
                            for i in range (0,ansector_num):
                                route_list.append({"Name":ancestor_list[ansector_num - i - 1].name,"Path": ancestor_list[ansector_num - i - 1].path})
                            # 判断是否是叶子部门
                            children_list = parse_children(d1.children)
                            child_num = len(children_list)
                            if child_num == 0:
                                is_leaf = True
                                search_name = search_name[5:]
                                search_auth = search_auth[10:]
                                if search_auth == "":
                                    search_auth = "-1"
                                search_auth = int(search_auth)
                                member_list = list(User.objects.filter(department = d1).all())
                                if search_auth != -1 and search_auth != 2 and search_auth != 3:
                                    return request_failed(1,"要搜索的authority不合法")
                                elif search_auth == 2:
                                    member_list = [member for member in member_list if member.asset_administrator == 1 and 
                                                   search_name in member.name]
                                elif search_auth == 3:
                                    member_list = [member for member in member_list if member.asset_administrator == 0 and 
                                                   search_name in member.name]
                                else:
                                    member_list = [member for member in member_list if search_name in member.name]
                                page = int(page_id)
                                member_num = len(member_list)
                                page_num = math.ceil(member_num / 20)
                                tmp_list : list[User] = []
                                # 访问不存在的页时，返回空
                                if 20 * (page - 1) + 1 > member_num:
                                    tmp_list = []
                                # 能够完整返回20条信息
                                elif 20 * page <= member_num:
                                    tmp_list = member_list[20 * (page - 1): 20 * page]
                                # 返回的信息不足20条
                                else:
                                    tmp_list = member_list[20 * (page - 1):]
                                return_data = {
                                    "TotalNum" : member_num,
                                    "TotalPage" : page_num,
                                    "is_leaf": is_leaf,
                                    "route": route_list,
                                    "member": [return_field(member.serialize(),["Name","Department","Authority","lock"])
                                               for member in tmp_list],
                                    "Department": []
                                }
                                return request_success(return_data)
                            else:
                                is_leaf = False
                                child_list = list(Department.objects.filter(parent=d1,entity=e1).all().order_by('path'))
                                return_data = {
                                    "TotalNum" : 0,
                                    "TotalPage" : 0,
                                    "is_leaf": is_leaf,
                                    "route": route_list,
                                    "member": [],
                                    "Department": [
                                        {
                                            "DepartmentName": child_list[i].name,
                                            "DepartmentPath": child_list[i].path,
                                            "DepartmentId": (i + 1)
                                        }
                                        for i in range(0, child_num)
                                    ]
                                }
                                return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def move_members(req:Request):
    if req.method == "POST":
        session_id = get_session_id(req)
        sessionRecord = SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    DepartmentPathFrom = require(body, "DepartmentPathFrom", "string",
                                             err_msg="Missing or error type of DepartmentPathFrom")
                    d1 = Department.objects.filter(path=DepartmentPathFrom,entity=e1).first()
                    if not d1:
                        return request_failed(4,"From部门不存在")
                    DepartmentPathTo = require(body, "DepartmentPathTo", "string",
                                             err_msg="Missing or error type of DepartmentPathTo")
                    d2 = Department.objects.filter(path=DepartmentPathTo,entity=e1).first()
                    if not d2:
                        return request_failed(1,"To部门不存在")
                    else:
                        child_num = len(parse_children(d2.children))
                        if child_num > 0:
                            return request_failed(1,"To部门不是叶子部门")
                        else :
                            have_asset_admin = False
                            asset_admin = User.objects.filter(department=d2,asset_administrator=1).first()
                            if asset_admin:
                                have_asset_admin = True
                            member_name_list = require(body, "member", "list",
                                             err_msg="Missing or error type of member")
                            member_list : list[User] = []
                            for member_name in member_name_list:
                                if len(member_name) == 0 or len(member_name) >128:
                                    return(4,"用户名长度不合规范")
                                for ch in member_name:
                                    if ch == ' ' or ch == '/' or ch =='\\':
                                        return request_failed(4,"存在非法字符")
                                member = User.objects.filter(name=member_name,department=d1).first()
                                if not member:
                                    return request_failed(4,"用户不存在")
                                elif member.asset_administrator == 1 and have_asset_admin == True:
                                    return request_failed(5,"不能将资产管理员移至一个已有资产管理员的部门")
                                else:
                                    member_list.append(member)
                            for m in member_list:
                                m.department = d2
                                m.save()
                                Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                   more_info="系统管理员 " + user.name + " 将用户 " + m.name + " 从部门 " + 
                                                   d1.name + " 移动至部门 " + d2.name)
                                SessionPool.objects.filter(user=m).all().delete()
                            return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def delete_department(req:Request, sessionId:str, DepartmentPath:str):
    print("调用了delete_department函数")
    if req.method == "DELETE":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    d1 = Department.objects.filter(entity=e1,path=DepartmentPath).first()
                    if not d1:
                        return request_failed(1,"部门不存在")
                    else :
                        child_num = len(parse_children(d1.children))
                        if child_num > 0:
                            return request_failed(4,"该部门还有子部门")
                        else:
                            if len(User.objects.filter(department=d1).all()) > 0:
                                return request_failed(4,"该部门还有员工")
                            else:
                                asset_list = list(Asset.objects.filter(department=d1).all())
                                if len(asset_list) > 0:
                                    return request_failed(4,"该部门还有资产")
                                d2: Department = d1.parent
                                # 根部门，无父节点
                                if not d2:
                                    # 找到所有的同级后续部门
                                    root_list = list(Department.objects.filter(parent=None,entity=e1).all().order_by('path'))
                                    root_num = len(root_list)
                                    index = d1.path[0]
                                    # 用不着d1就删掉，避免路径重复
                                    d1.delete()
                                    node_list1 : list[Department] = []
                                    for i in range(int(index),root_num):
                                        node_list1.append(root_list[i])
                                    # 更改path
                                    while len(node_list1) > 0:
                                        node1 = node_list1[0]
                                        node_list1.pop(0)
                                        tmp_list = list(node1.path)
                                        tmp_list[0] = str(ord(node1.path[0]) - ord('1'))
                                        new_path = ''.join(tmp_list)
                                        node1.path = new_path
                                        node1.save()
                                        child_list1 = parse_children(node1.children)
                                        for child1 in child_list1:
                                            node_list1.append(Department.objects.filter(id=int(child1)).first())
                                # 非根部门，注意还要更改父亲的children
                                else:
                                    # 更改父亲的children_list
                                    child_list = parse_children(d2.children)
                                    child_num = len(child_list)
                                    child_list.remove(str(d1.id))
                                    new_children = ""
                                    for child in child_list:
                                        new_children = new_children + '$' + child
                                    d2.children = new_children
                                    d2.save()
                                    # 找到所有的同级后续部门
                                    path = d1.path
                                    for i in range(0, len(path)):
                                        if path[i] != '0':
                                            continue
                                        else:
                                            index1 = path[i - 1] # 这一位是几
                                            index2 = i - 1 #这是第几位
                                            break
                                    root_list = list(Department.objects.filter(parent=d2).all().order_by('path'))
                                    root_num = len(root_list)
                                    # 用不着d1就删掉，避免路径重复
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                       more_info="系统管理员 " + user.name + " 删除部门 " + d1.name)
                                    d1.delete()
                                    node_list2 : list[Department] = []
                                    for i in range(int(index1),root_num):
                                        node_list2.append(root_list[i])
                                    # 更改path
                                    while len(node_list2) > 0:
                                        node2 = node_list2[0]
                                        node_list2.pop(0)
                                        tmp_list = list(node2.path)
                                        tmp_list[index2] = str(ord(node2.path[index2]) - ord('1'))
                                        new_path = ''.join(tmp_list)
                                        node2.path = new_path
                                        node2.save()
                                        child_list2 = parse_children(node2.children)
                                        for child2 in child_list2:
                                            node_list2.append(Department.objects.filter(id=int(child2)).first())
                                # 最后返回删除成功
                                return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def manage_apps(req:Request,sessionId:str,authority:str):
    print("调用了manage_apps函数")
    if req.method == "POST" or req.method == "PUT" or req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:         
                user = sessionRecord.user
                e1 = user.entity
                if req.method == "GET":
                    print("是GET请求捏！")
                    app_list = list(App.objects.filter(entity=e1,authority=int(authority)).all())
                    return_list = []
                    for app in app_list:
                        return_list.append({"IsInternal":app.Is_Internal,
                                            "IsLock":app.Is_Locked,
                                            "AppName":app.name,
                                            "AppUrl":app.path})
                    return_data = {"AppList": return_list}
                    return request_success(return_data)
                else:
                    if int(authority) < 2 or int(authority) > 3:
                        return request_failed(3,"authority不合法")
                    if user.system_administrator == 0:
                        return request_failed(2, "无权限操作")
                    else:
                        tmp_body = req.body.decode("utf-8")
                        try:
                            body = json.loads(tmp_body)
                        except BaseException as error:
                            print(error, tmp_body)
                        appname = require(body, "AppName", "string",
                                             err_msg="Missing or error type of AppName")
                        appurl = require(body, "AppUrl", "string",
                                             err_msg="Missing or error type of AppUrl")
                        if req.method == "POST":
                            print("现在是POST请求哦！")
                            appimage = require(body, "AppImage", "string",
                                             err_msg="Missing or error type of AppImage")
                            u1 = App.objects.filter(entity=e1,name=appname,authority=int(authority)).first()
                            if u1:
                                return request_failed(1,"应用名称已存在")
                            u2 = App.objects.filter(entity=e1,path=appurl,authority=int(authority)).first()
                            if u2:
                                return request_failed(1,"应用网址已存在")
                            app_num = len(list(App.objects.filter(entity=e1,Is_Internal=False,authority=int(authority)).all()))
                            if app_num >= 9:
                                return request_failed(4,"应用数量已达上限")
                            if appurl[0:8] != "https://" and appurl[0:7] != "http://":
                                appurl = "https://" + appurl
                            App.objects.create(name=appname,path=appurl,entity=e1,Is_Locked=False,image=appimage,
                                               Is_Internal=False,authority=int(authority))
                            if int(authority) == 2:
                                Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                   more_info="系统管理员 " + user.name + " 为资产管理员添加应用 " + appname)
                            else:
                                Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                   more_info="系统管理员 " + user.name + " 为员工添加应用 " + appname)
                            return request_success()
                        else:
                            print("只能是PUT请求了罢！")
                            u1 = App.objects.filter(entity=e1,name=appname,path=appurl).first()
                            if not u1:
                                return request_failed(1,"url不存在")
                            elif u1.Is_Internal == True:
                                return request_failed(4,"内部应用无法锁定")
                            else:
                                if u1.Is_Locked == True:
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                   more_info="系统管理员 " + user.name + " 解锁应用 " + appname)
                                else:
                                    Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                                   more_info="系统管理员 " + user.name + " 锁定应用 " + appname)
                                u1.Is_Locked = not u1.Is_Locked
                                u1.save()
                                return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def get_apps(req:Request,sessionId:str,authority:str):
    print("调用了get_apps函数")
    if req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:         
                user = sessionRecord.user
                e1 = user.entity
                if authority == "":
                    authority = "0"
                app_list = list(App.objects.filter(entity=e1,Is_Internal=False,authority=int(authority)).all())
                return_list = []
                for app in app_list:
                    return_list.append({"IsInternal":app.Is_Internal,
                                        "IsLock":app.Is_Locked,
                                        "AppName":app.name,
                                        "AppUrl":app.path,
                                        "AppImage":app.image})
                return_data = {"AppList": return_list}
                return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def delete_apps(req:Request,sessionId:str,authority:str,appname:str):
    print("调用了delete_apps函数")
    if req.method == "DELETE":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                if int(authority) < 2 or int(authority) > 3:
                    return request_failed(3,"authority不合法")
                user = sessionRecord.user
                if user.system_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    e1 = user.entity
                    u1 = App.objects.filter(entity=e1,authority=int(authority),name=appname).first()
                    if not u1:
                        return request_failed(1,"应用不存在")
                    elif u1.Is_Internal == True:
                        return request_failed(4,"内部应用无法移除")
                    else:
                        if int(authority) == 2:
                            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                               more_info="系统管理员 " + user.name + " 为资产管理员删除应用 " + appname)
                        else:
                            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=e1.name,
                                               more_info="系统管理员 " + user.name + " 为员工删除应用 " + appname)
                        u1.delete()
                        return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def _get_asset_detail(a1:Asset):
    return_data = {}
    asset_detail = {}
    asset_detail["Name"] = a1.name
    asset_detail["ID"] = a1.id
    asset_detail["Status"] = a1.status
    try:
        asset_detail["Owner"] = a1.user.name
    except:
        asset_detail["Owner"] = None
    try:
        asset_detail["Class"] = a1.Class.name
    except:
        asset_detail["Class"] = None
    asset_detail["Description"] = a1.description
    asset_detail["CreateTime"] = a1.create_time
    asset_detail["LabelVisible"] = string_to_bool_label(a1.label_visible)
    asset_detail["ImageUrl"] = AliyunOss().list_dir("photos/{}".format(str(a1.id)))
    asset_detail["PropetyName"],asset_detail["PropetyValue"] = parse_selfprop_to_list(a1.property)
    asset_detail["AssetValue"] = single_asset_value_update(a1)
    if a1.Class.property == 4:
        asset_detail["Type"] = 1
        asset_detail["Volume"] = a1.number
    else:
        asset_detail["Type"] = 0
        asset_detail["Volume"] = 1
    if a1.Class.loss_style == 0:
        asset_detail["LossStyle"] = 0
    else:
        asset_detail["LossStyle"] = 1
    try:
        asset_detail["Time"] = a1.expire.strftime("%Y-%m-%d %H:%M:%S")
    except:
        asset_detail["Time"] = None
    asset_detail["Position"] = a1.position
    try:
        asset_detail["Parent"] = a1.parent.name
    except:
        asset_detail["Parent"] = None
    history_list : list[dict] = []
    history_detail_list = list(PendingRequests.objects.filter(asset=a1,result=APPROVAL).all().order_by('-review_time'))
    for history_detail in history_detail_list:
        history_detail_dict = {}
        history_detail_dict["ID"] = history_detail.id
        history_detail_dict["Review_Time"] = history_detail.review_time
        history_detail_dict["Type"] = history_detail.type
        try:
            history_detail_dict["Initiator"] = history_detail.initiator.name
        except:
            history_detail_dict["Initiator"] = None
        try:
            history_detail_dict["Participant"] = history_detail.participant.name
        except:
            history_detail_dict["Participant"] = None
        try:
            history_detail_dict["Asset_Admin"] = history_detail.asset_admin.name
        except:
            history_detail_dict["Asset_Admin"] = None
        history_list.append(history_detail_dict)
    asset_detail["History"] = history_list
    return_data["Asset_Detail"] = asset_detail
    return return_data


def get_asset_detail(req:Request,sessionId:str,assetId:str):
    print("调用了get_asset_detail函数")
    if req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 1 or user.system_administrator == 1:
                    return request_failed(2, "无权限操作")
                else:
                    d1 = user.department
                    a1 = Asset.objects.filter(id=int(assetId)).first()
                    if not a1:
                        return request_failed(1,"资产不存在")
                    d2 = a1.Class.department
                    if d1 != d2:
                        return request_failed(3,"资产不属于该部门")
                    return_data = _get_asset_detail(a1)
                    return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def QR_get_asset_detail(req:Request,assetId:str):
    if req.method == "GET":
        a1 = Asset.objects.filter(id=int(assetId)).first()
        if not a1:
            return request_failed(1,"资产不存在")
        return_data = _get_asset_detail(a1)
        Li = return_data["Asset_Detail"]["History"]
        L = len(Li)
        if L > 10:
            return_data["Asset_Detail"]["History"] = Li[0:10]
        return request_success(return_data)
    else:
        return BAD_METHOD
    

def get_new_message(req:Request,sessionId:str):
    print("调用了get_new_message函数")
    if req.method == "PUT":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 1 or user.system_administrator == 1:
                    return request_failed(2, "无权限操作")
                else:
                    tmp_body = req.body.decode("utf-8")
                    try:
                        body = json.loads(tmp_body)
                    except BaseException as error:
                        print(error, tmp_body)
                    id = require(body, "ID", "int",
                                 err_msg="Missing or error type of ID")
                    if id == -1:
                        response_list = list(PendingResponse.objects.filter(employee=user,is_read=False).all())
                        for response in response_list:
                            response.is_read = True
                            # response.read_time = get_current_time()
                            response.save()
                    else:
                        response = PendingResponse.objects.filter(id=id,employee=user).first()
                        if not response:
                            return request_failed(1,"消息id不合法")
                        else:
                            if response.is_read == False:
                                response.is_read = True
                                # response.read_time = get_current_time()
                                response.save()
                            else:
                                response.is_read = False
                                # response.read_time = None
                                response.save()
                    return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def get_all_message(req:Request,sessionId:str,page_id:str,search_read:str):
    print("调用了get_all_message函数")
    if req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 1 or user.system_administrator == 1:
                    return request_failed(2, "无权限操作")
                else:
                    return_data = {}
                    return_list :list[dict] = []
                    search_read = search_read[8:]
                    if search_read == "":
                        search_read = "-1"
                    search_read = int(search_read)
                    if search_read < -1 or search_read > 1:
                        return request_failed(1,"阅读情况不合法")
                    if search_read == -1:
                        response_list = list(PendingResponse.objects.filter(employee=user).all().order_by("-response_time"))
                    elif search_read == 0:
                        response_list = list(PendingResponse.objects.filter(employee=user,is_read=False).all().order_by("-response_time"))
                    else:
                        response_list = list(PendingResponse.objects.filter(employee=user,is_read=True).all().order_by("-response_time"))
                    response_num = len(response_list)
                    page_num = math.ceil(response_num / 20)
                    return_data["TotalNum"] = response_num
                    return_data["TotalPage"] = page_num
                    page = int(page_id)
                    tmp_list : list[PendingResponse] = []
                    # 访问不存在的页时，返回空
                    if 20 * (page - 1) + 1 > response_num:
                        tmp_list = []
                    # 能够完整返回20条信息
                    elif 20 * page <= response_num:
                        tmp_list = response_list[20 * (page - 1): 20 * page]
                    # 返回的信息不足20条
                    else:
                        tmp_list = response_list[20 * (page - 1):]
                    for response in tmp_list:
                        tmp_dict = {}
                        tmp_dict["Time"] = response.response_time
                        tmp_dict["Detail"] = response.more_info
                        tmp_dict["Is_Read"] = response.is_read
                        tmp_dict["ID"] = response.id
                        return_list.append(tmp_dict)
                    return_data["Message"] = return_list
                    return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


def get_log_detail(req:Request,sessionId:str,page_type:str,page_id:str,search_succ:str):
    print("调用了get_log_detail函数")
    if req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.system_administrator == 0 and user.super_administrator == 0:
                    return request_failed(2, "无权限操作")
                else:
                    return_data = {}
                    return_list = []
                    log_list : list[Log] = []
                    page = int(page_id)
                    if int(page_type) == 0:
                        if user.super_administrator == 1:
                            log_list.extend(list(Log.objects.all().order_by("-id")))
                        else:
                            log_list.extend(list(Log.objects.filter(entity_name=user.entity.name).all().order_by("-id")))
                    elif 1 <= int(page_type) <= 4:
                        if user.super_administrator == 1:
                            log_list.extend(list(Log.objects.filter(type=int(page_type)).all().order_by("-id")))
                        else:
                            log_list.extend(list(Log.objects.filter(entity_name=user.entity.name,type=int(page_type)).all().order_by("-id")))
                    else:
                        return request_failed(1, "page_type不合法")
                    search_succ = search_succ[8:]
                    if search_succ == "": 
                        search_succ = "-1"
                    search_succ = int(search_succ)
                    if search_succ < -1 or search_succ > 1:
                        return request_failed(1,"成功状态不合法") 
                    elif search_succ == 0:
                        log_list = [log for log in log_list if log.is_succ == 0]
                    elif search_succ == 1:
                        log_list = [log for log in log_list if log.is_succ == 1]
                    log_num = len(log_list)
                    page_num = math.ceil(log_num / 20)
                    return_data["TotalNum"] = log_num
                    return_data["TotalPage"] = page_num
                    tmp_list : list[Log] = []
                    # 访问不存在的页时，返回空
                    if 20 * (page - 1) + 1 > log_num:
                        tmp_list = []
                    # 能够完整返回20条信息
                    elif 20 * page <= log_num:
                        tmp_list = log_list[20 * (page - 1): 20 * page]
                    # 返回的信息不足20条
                    else:
                        tmp_list = log_list[20 * (page - 1):]
                    for log in tmp_list:
                        tmp_dict = {}
                        tmp_dict["ID"] = log.id
                        tmp_dict["Is_Succ"] = log.is_succ
                        tmp_dict["CreateTime"] = log.create_time
                        tmp_dict["Initiator"] = log.user_name
                        tmp_dict["Type"] = log.type 
                        tmp_dict["Detail"] = log.more_info
                        return_list.append(tmp_dict)
                    return_data["LogList"] = return_list
                    return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def change_mobile(req:Request):
    if req.method == "POST":
        tmp_body = req.body.decode("utf-8")
        try:
            body = json.loads(tmp_body)
        except BaseException as error:
            print(error, tmp_body)
        sessionId = require(body, "SessionID", "string",
                        err_msg="Missing or error type of SessionID")
        mobile = require(body, "Mobile", "string",
                        err_msg="Missing or error type of Mobile")
        mobile = "+86" + mobile
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user 
                u1 = User.objects.filter(mobile=mobile).first()
                if u1:
                    return request_failed(1,"该手机号已被绑定")
                user.mobile = mobile
                user.open_id = None
                user.feishu = False
                user.save()
                return request_success()
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD  


def feishu_login(req:Request):
    if req.method == "POST":
        tmp_body = req.body.decode("utf-8")
        try:
            body = json.loads(tmp_body)
        except BaseException as error:
            print(error, tmp_body)
        code = require(body, "code", "string",
                       err_msg="Missing or error type of code")
        url1 = "https://passport.feishu.cn/suite/passport/oauth/token"
        header1 = {"Content-Type" : "application/x-www-form-urlencoded"}
        data1 = {
            "grant_type" : "authorization_code",
            "client_id"  : "cli_a4d587450378500e",
            "client_secret" : "pzse84aHxqBwjZD82YPr1eH2Ftctg8fO",
            "code" : code,
            # todo 之后改成master网址 已完成
            "redirect_uri" : "http://cs-company-frontend-cses.app.secoder.net/main_page"
        }
        resp1 = requests.post(url=url1,data=data1,headers=header1)
        access_token = resp1.json()["access_token"]
        url2 = "https://passport.feishu.cn/suite/passport/oauth/userinfo"
        header2 = {"Authorization" : "Bearer "+ access_token}
        resp2 = requests.get(url=url2,headers=header2)
        open_id = resp2.json()["open_id"]
        mobile = resp2.json()["mobile"]
        u1 = User.objects.filter(mobile=mobile).first()
        if not u1:
            return request_failed(2,"不存在手机号相同的用户，无法绑定")
        if u1.Is_Locked == True:
            Log.objects.create(type=IN_OUT,user_name=u1.name,entity_name=u1.entity.name,is_succ=0,
                               more_info=u1.name + " 尝试通过飞书登录系统，但该用户已被锁定")
            return request_failed(1,"该用户已被锁定")
        sessionID = require(body, "SessionID", "string",
                            err_msg="Missing or error type of SessionID")
        SessionPool.objects.filter(user=u1).all().delete()
        bind_session_id(sessionId=sessionID, user=u1)
        u1.open_id = open_id
        u1.feishu = True
        u1.save()
        if u1.super_administrator == 1:
            Log.objects.create(type=IN_OUT,user_name=u1.name,more_info=u1.name + " 通过飞书登录系统")
        else:
            Log.objects.create(type=IN_OUT,user_name=u1.name,entity_name=u1.entity.name,more_info=u1.name + " 通过飞书登录系统")
        return request_success()
    else:
        return BAD_METHOD
    

def get_tenant_access_token():
    url1 = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    payload1 = json.dumps({
	    "app_id": "cli_a4d587450378500e",
	    "app_secret": "pzse84aHxqBwjZD82YPr1eH2Ftctg8fO"
    })
    header1 = {
        'Content-Type': 'application/json'
    }
    resp1 = requests.request("POST", url1, headers=header1, data=payload1)
    tenant_access_token = resp1.json()["tenant_access_token"]
    return tenant_access_token


def get_open_id(mobile:str):
    tenant_access_token = get_tenant_access_token()
    url1 = "https://open.feishu.cn/open-apis/contact/v3/users/batch_get_id?user_id_type=open_id"
    header1 = {
        'Authorization' : 'Bearer ' + tenant_access_token,
        'Content-Type' : 'application/json'
    }
    payload1 = json.dumps({
	    "mobiles": [mobile]
    })
    resp1 = requests.request("POST",url1,data=payload1,headers=header1)
    open_id = resp1.json()["data"]["user_list"][0]["user_id"]
    return open_id


def send_feishu_message(user:User,msg:str):
    if user.feishu == False:
        return
    if user.open_id == None:
        return
    tenant_access_token = get_tenant_access_token() 
    url1 = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id"
    header1 = {
        'Authorization' : 'Bearer ' + tenant_access_token,
        'Content-Type' : 'application/json'
    }
    payload1 = json.dumps({
        "receive_id" : user.open_id,
        "msg_type" : "text",
        "content" : "{\"text\":\"" + msg + "\"}",
    })
    requests.request("POST",url1,data=payload1,headers=header1)


def disapprove(pending_request:PendingRequests):
    pending_request.result = DISAPPROVAL
    pending_request.save()
    # 告诉员工申请已被拒绝
    op = ""
    if pending_request.type == RECEIVE:
        op = "领用"
    elif pending_request.type == RETURN:
        op = "退库"
    elif pending_request.type == MAINTENANCE:
        op = "维保"
    elif pending_request.type == TRANSFER:
        op = "转移"
    info1 = "您针对资产： " + pending_request.asset.name + " 的" + op + "申请已被驳回"
    PendingResponse.objects.create(employee=pending_request.initiator,
                                   asset_admin=pending_request.asset_admin,
                                   asset=pending_request.asset,type=pending_request.type,
                                   more_info=info1)
    send_feishu_message(pending_request.initiator,info1)
    Log.objects.create(type=ASSET_MANAGE,user_name=pending_request.asset_admin.name,entity_name=pending_request.asset_admin.entity.name,
                           more_info="员工 " + pending_request.initiator.name + " 针对资产： " + pending_request.asset.name  + " 的" + op + "申请已被资产管理员 " + pending_request.asset_admin.name + " 驳回")


def approve(pending_request:PendingRequests):
    if pending_request.type == RECEIVE:
    # 代表需要领用, initiator进行领用
    # 在validate_request已经审核过，可以领用
        asset = pending_request.asset
        # 把Asset的user进行修改
        if pending_request.apply_number != None and pending_request.apply_number >= 0:
            if pending_request.apply_number < asset.number:
                # 将资产分成两半
                new_price = float(asset.price) * float(pending_request.apply_number / asset.number) 
                asset_new = Asset.objects.create(parent=asset.parent, name=asset.name, Class=asset.Class, user=pending_request.initiator, price=new_price, \
                                                 description=asset.description, position=asset.position, number=pending_request.apply_number, property=asset.property, \
                                                 expire=asset.expire, create_time=asset.create_time, status=IN_USE)
                asset.number = asset.number - pending_request.apply_number
                asset.price = float(asset.price) - new_price
                asset.save()
            else:
                asset.user = pending_request.initiator
                asset.status = IN_USE
                asset.save()
        else: 
            asset.user = pending_request.initiator
            asset.status = IN_USE
            asset.save()
        # 告诉员工申请已通过
        info2 = "您已成功领用资产： " + asset.name
        PendingResponse.objects.create(employee=pending_request.initiator,
                                       asset_admin=pending_request.asset_admin,
                                       asset=asset,type=RECEIVE,
                                       more_info=info2)
        send_feishu_message(pending_request.initiator,info2)
        Log.objects.create(type=ASSET_MANAGE,user_name=pending_request.initiator.name,entity_name=pending_request.initiator.entity.name,
                           more_info="员工 " + pending_request.initiator.name + " 已成功领用资产： " + asset.name)
                        
    elif pending_request.type == RETURN:
                        
        asset = pending_request.asset
        department = asset.Class.department
        # 找到这个部门的资产管理员
        asset_admin = User.objects.filter(department=department, asset_administrator=1).first()
        asset.user = asset_admin
        asset.status = IDLE
        asset.save()
        # 告诉员工申请已通过
        info3 = "您的资产： " + asset.name + " 已成功退库"
        PendingResponse.objects.create(employee=pending_request.initiator,
                                       asset_admin=pending_request.asset_admin,
                                       asset=asset,type=RETURN,
                                       more_info=info3)
        send_feishu_message(pending_request.initiator,info3)
        Log.objects.create(type=ASSET_MANAGE,user_name=pending_request.initiator.name,entity_name=pending_request.initiator.entity.name,
                           more_info="员工 " + pending_request.initiator.name + " 的资产： " + asset.name + " 已成功退库")
                        
    elif pending_request.type == MAINTENANCE:
        asset = pending_request.asset
        if pending_request.maintain_time != None:
            asset.expire = time_string_to_datetime({"Time":pending_request.maintain_time})
        asset.status = IN_MAINTAIN
        asset.save()
        # 告诉员工申请已通过
        info4 = "您的资产：" + asset.name + " 已进入维保状态"
        PendingResponse.objects.create(employee=pending_request.initiator,
                                       asset_admin=pending_request.asset_admin,
                                       asset=asset,type=MAINTENANCE,
                                       more_info=info4)
        send_feishu_message(pending_request.initiator,info4)
        Log.objects.create(type=ASSET_MANAGE,user_name=pending_request.initiator.name,entity_name=pending_request.initiator.entity.name,
                           more_info="员工 " + pending_request.initiator.name + " 的资产： " + asset.name + " 已进入维保状态")
                        
    elif pending_request.type == TRANSFER:
        asset = pending_request.asset
        asset.user = pending_request.participant
        asset.status = IN_USE
        asset.Class = pending_request.Class
        asset.department = pending_request.participant.department
        asset.save()
        # 告诉员工申请已通过
        info5 = "您的资产： " + asset.name + " 已转移至 " + pending_request.participant.name + " 手中"
        PendingResponse.objects.create(employee=pending_request.initiator,
                                       asset_admin=pending_request.asset_admin,
                                       asset=asset,type=TRANSFER,
                                       more_info=info5)
        send_feishu_message(pending_request.initiator,info5)
        info6 = "资产： " + asset.name + " 已从 " + pending_request.initiator.name + " 处转移至您手中"
        PendingResponse.objects.create(employee=pending_request.participant,
                                       asset_admin=pending_request.asset_admin,
                                       asset=asset,type=TRANSFER,
                                       more_info=info6)
        send_feishu_message(pending_request.participant,info6)
        Log.objects.create(type=ASSET_MANAGE,user_name=pending_request.initiator.name,entity_name=pending_request.initiator.entity.name,
                           more_info="员工 " + pending_request.initiator.name + " 的资产： " + asset.name + " 已转移至 " + pending_request.participant.name + " 手中")
            # 将这条pending_result的结果置为APPROVAL
    pending_request.result = APPROVAL
    pending_request.review_time = get_current_time()
    pending_request.save() 


def send_feishu_apply(pendingrequest:PendingRequests, op:str):
    # 发送审批卡片
    tenant_access_token = get_tenant_access_token()
    header1 = {
        'Authorization' : 'Bearer ' + tenant_access_token,
        'Content-Type' : 'application/json'
    }
    url1 = "https://www.feishu.cn/approval/openapi/v1/message/send"
    payload1 = json.dumps({
        "template_id" : "1008",
        "open_id" : pendingrequest.asset_admin.open_id,
        "uuid" : str(pendingrequest.id),
        "approval_name" : "@i18n@1",
        "title_user_id" : pendingrequest.initiator.open_id,
        "title_user_id_type" : "open_id",
        "content" : {
            "user_id" : pendingrequest.initiator.open_id,
            "user_id_type" :  "open_id",
            "summaries" : [
                {
                    "summary" : "@i18n@2",
                }
            ]
        },
        "actions" : [
            {
                "action_name":"DETAIL",
                # todo 推master后更改网址 已完成
                "url":" http://cs-company-frontend-cses.app.secoder.net/",
                "android_url":"http://cs-company-frontend-cses.app.secoder.net/",
                "ios_url":"http://cs-company-frontend-cses.app.secoder.net/",
                "pc_url":"http://cs-company-frontend-cses.app.secoder.net/"
            }
        ],
        "action_configs": [
            {
                "action_type": "APPROVE",
                "is_need_reason": True,
                "is_reason_required": False,
                "is_need_attachment": False,
                "next_status": "APPROVED"
            },
            {
                "action_type": "REJECT",
                "is_need_reason": True,
                "is_reason_required": False,
                "is_need_attachment": False,
                "next_status": "REJECTED"
            }
        ],
        "action_callback": {
            # todo 改出一个给跳过sessionid给后端发请求审批的网址 已完成
            "action_callback_url":"https://CS-Company-backend-CSes.app.secoder.net/User/feishu_apply",
        },
        "i18n_resources":[
            {
                "locale":"zh-CN",
                "is_default":True,
                "texts":{
                    "@i18n@1": op + "申请",
                    "@i18n@2": pendingrequest.initiator.name + " 针对资产 " + pendingrequest.asset.name + " 发起了 " + op + " 申请"
                }
            }
        ]
    })
    resp1 = requests.request("POST", url1, headers=header1, data=payload1)             
    message_id = resp1.json()["data"]["message_id"]   
    pendingrequest.message_id = message_id
    pendingrequest.save()


def change_feishu_apply(pendingrequest:PendingRequests,approval:int):
    tenant_access_token = get_tenant_access_token()
    header1 = {
        'Authorization' : 'Bearer ' + tenant_access_token,
        'Content-Type' : 'application/json'
    }
    url1 = "https://www.feishu.cn/approval/openapi/v1/message/update"
    status = ""
    if approval == 1:
        status = "APPROVED"
    elif approval == 0:
        status = "REJECTED"
    payload1 = json.dumps({
        "message_id" : pendingrequest.message_id,
        "status" : status
    })
    resp1 = requests.request("POST", url1, headers=header1, data=payload1)
    print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^",resp1)
    message_id = resp1.json()["data"]["message_id"]
    pendingrequest.message_id = message_id
    pendingrequest.save()


def get_leaf_department(req:Request,entityId:str,sessionId:str):
    print("调用了get_leaf_department函数")
    if req.method == "GET":
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 0: 
                    return request_failed(2, "无权限操作")
                else:
                    e1 = Entity.objects.filter(id=entityId).first()
                    if not e1:
                        return request_failed(1, "业务实体id无效")
                    department_list = Department.objects.filter(entity=e1,children=None).all()
                    return_data = {}
                    return_list = []
                    for d in department_list:
                        tmp_dict = {}
                        tmp_dict["ID"] = d.id,
                        tmp_dict["Name"] = d.name
                        return_list.append(tmp_dict)
                    return_data["Departments"] = return_list
                    return request_success(return_data)
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def change_feishu_department(req:Request):
    print("调用了change_feishu_department函数")
    if req.method == "POST":
        tmp_body = req.body.decode("utf-8")
        try:
            body = json.loads(tmp_body)
        except BaseException as error:
            print(error, tmp_body)
        sessionId = require(body, "SessionID", "string",
                        err_msg="Missing or error type of SessionID")
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 0: 
                    return request_failed(2, "无权限操作")
                else:
                    DepartmentId = require(body, "DepartmentID", "int",
                                           err_msg="Missing or error type of DepartmentID")
                    d1 = Department.objects.filter(id=DepartmentId).first()
                    if not d1:
                        return request_failed(1,"部门id无效")
                    f1 = Feishu.objects.filter(id=1).first()
                    if not f1:
                        Feishu.objects.create(feishu_department=DepartmentId)   
                    else:
                        f1.feishu_department = DepartmentId
                        f1.save()
                    return request_success() 
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD
    

def _sync_feishu_member(data, d1:Department):
    member_list = data["items"] 
    for member in member_list:
        name = member["name"]
        open_id = member["open_id"]
        mobile = member["mobile"]
        u1 = User.objects.filter(mobile=mobile).first()
        # 有相同手机号的用户则将这个用户绑定飞书
        if u1:
            u1.feishu = True
            u1.open_id = open_id
            u1.save()
            Log.objects.create(type=USER_MANAGE,user_name=u1.name,entity_name=u1.entity.name,
                               more_info="员工 " + u1.name + " 通过飞书同步绑定了飞书账号")
        # 否则要在系统中创建新用户
        else:
            # 重名的话随机生成一个十六位字符串，之后用户可以更改用户名
            u2 = User.objects.filter(name=name).first()
            if u2:
                tmp_list = random.sample(string.ascii_letters + string.digits, 16)
                name = "".join(tmp_list)
            user = User.objects.create(name=name,password=sha256(MD5("yiqunchusheng")),
                                       entity=d1.entity,department=d1,
                                       super_administrator=0,system_administrator=0,asset_administrator=0,
                                       function_string="1111100000000000000000",
                                       mobile=mobile,open_id=open_id,feishu=True) 
            Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=user.entity.name,
                               more_info="员工 " + user.name + " 通过飞书同步创建在部门 " + d1.name + " 下" )
            

def sync_feishu_member(req:Request):
    print("调用了sync_feishu_member函数")
    if req.method == "POST":
        tmp_body = req.body.decode("utf-8")
        try:
            body = json.loads(tmp_body)
        except BaseException as error:
            print(error, tmp_body)
        sessionId = require(body, "SessionID", "string",
                        err_msg="Missing or error type of SessionID")
        sessionRecord = SessionPool.objects.filter(sessionId=sessionId).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=sessionId).delete()
                return request_failed(-2, "会话不存在或过期，请重新登录")
            else:
                user = sessionRecord.user
                if user.super_administrator == 0: 
                    return request_failed(2, "无权限操作")
                else:
                    f1 = Feishu.objects.filter(id=1).first()
                    if not f1:
                        return request_failed(1,"当前尚未指定飞书同步部门")
                    d1 = Department.objects.filter(id=f1.feishu_department).first()
                    if not d1:
                        return request_failed(1,"部门id无效")
                    tenant_access_token = get_tenant_access_token() 
                    url1 = "https://open.feishu.cn/open-apis/contact/v3/users/find_by_department?department_id=0&department_id_type=open_department_id&page_size=20&user_id_type=open_id"
                    header1 = {
                        'Authorization': 'Bearer ' + tenant_access_token
                    }       
                    payload1 = ''
                    resp1 = requests.request("GET", url1, headers=header1, data=payload1)
                    _data = resp1.json()["data"]
                    _sync_feishu_member(_data, d1) 
                    if _data["has_more"] == True:
                        while True:
                            page_token = _data["page_token"]
                            url2 = "https://open.feishu.cn/open-apis/contact/v3/users/find_by_department?department_id=0&department_id_type=open_department_id&page_size=20&page_token=" + page_token + "&user_id_type=open_id"
                            resp2 = requests.request("GET", url2, headers=header1, data=payload1)
                            _data = resp2.json()["data"]
                            _sync_feishu_member(_data,d1) 
                            if _data["has_more"] == False:
                                break
                return request_success()                
        else:
            return request_failed(-2, "会话不存在或过期，请重新登录")
    else:
        return BAD_METHOD


class AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        self.key=hashlib.sha256(AESCipher.str_to_bytes(key)).digest()
    @staticmethod
    def str_to_bytes(data):
        u_type = type(b"".decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]
    def decrypt(self, enc):
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return  self._unpad(cipher.decrypt(enc[AES.block_size:]))
    def decrypt_string(self, enc):
        enc = base64.b64decode(enc)
        return  self.decrypt(enc).decode('utf8')
    

def return_feishu_answer(req:HttpRequest):
    tmp_body = req.body.decode("utf-8")
    try:
        body = json.loads(tmp_body)
    except BaseException as error:
        print(error, tmp_body)
    encrypt = require(body, "encrypt", "string",
                        err_msg="Missing or error type of encrypt")
    # todo 在飞书把网址改成master后回来看看这个密钥要不要改
    cipher = AESCipher("g1e11a43at078B1jUqLsnbnv36NRu6Gy")
    data = json.loads(cipher.decrypt_string(encrypt)) 
    try:
        challenge = data["challenge"]
        return JsonResponse({"challenge":challenge})
    except:
        event_object = data["event"]["object"]
        open_id = event_object["open_id"]
        name = event_object["name"]
        mobile = event_object["mobile"]
        f1 = Feishu.objects.filter(id=1).first()
        d1 = Department.objects.filter(id=f1.feishu_department).first()
        u1 = User.objects.filter(name=name).first()
        # 重名的话随机生成一个十六位字符串，之后用户可以更改用户名
        if u1:
            tmp_list = random.sample(string.ascii_letters + string.digits, 16)
            name = "".join(tmp_list)
        user = User.objects.create(name=name,password=sha256(MD5("yiqunchusheng")),
                            entity=d1.entity,department=d1,
                            super_administrator=0,system_administrator=0,asset_administrator=0,
                            function_string="1111100000000000000000",
                            mobile=mobile,open_id=open_id,feishu=True)
        Log.objects.create(type=USER_MANAGE,user_name=user.name,entity_name=user.entity.name,
                           more_info="员工 " + user.name + " 通过飞书同步创建在部门 " + d1.name + " 下" )
        return request_success()
    

def manage_feishu_apply(req:HttpRequest):
    tmp_body = req.body.decode("utf-8")
    try:
        body = json.loads(tmp_body)
    except BaseException as error:
        print(error, tmp_body)
    try:
        encrypt = require(body, "encrypt", "string",
                        err_msg="Missing or error type of encrypt")
        # todo 在飞书把网址改成master后回来看看这个密钥要不要改
        cipher = AESCipher("g1e11a43at078B1jUqLsnbnv36NRu6Gy")
        data = json.loads(cipher.decrypt_string(encrypt)) 
    except:
        data = body
    approval = data["action_type"]
    message_id = data["message_id"]
    pending_request = PendingRequests.objects.filter(message_id=message_id).first()
    if approval == "REJECT":
        disapprove(pending_request)
    elif approval == "APPROVE":
        if validate_request(pending_request.asset, pending_request) >= 0:
            approve(pending_request)
    return request_success()   