from django.test import TestCase
from django.test import Client as DefaultClient
from User.models import *
from User.views import *
import json
from utils.utils_other import *
from utils.config import *
from Asset.models import * 
from Asset.views import * 

class Client(DefaultClient):
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)

    def _add_cookie(self, kw):
        if "SessionID" in self.cookies:
            if "data" not in kw:
                kw["data"] = {}
            kw["data"]["SessionID"] = self.cookies["SessionID"].value
        return kw

    def post(self, *args, **kw):
        return super(Client, self).post(*args, **self._add_cookie(kw))

    def get(self, *args, **kw):
        return super(Client, self).get(*args, **self._add_cookie(kw))


class UserTests(TestCase):
    def setUp(self):
        self.raw_password = "yiqunchusheng"
        self.test_password = "YIQUNCHUSHENG"
        self.e1 = Entity.objects.create(name = 'CS_Company1')
        self.d1 = Department.objects.create(name = 'CS_Department1', entity = self.e1, path = '100000000')
        self.d1_1 = Department.objects.create(name = 'CS_Department1_1', entity = self.e1, parent = self.d1, path = '110000000')
        self.d1.children = '$' + str(self.d1_1.id)
        self.d1.save()
        self.d1_2 = Department.objects.create(name = 'CS_Department1_2', entity = self.e1, parent = self.d1, path = '120000000')
        self.d1.children = self.d1.children + '$' + str(self.d1_2.id)
        self.d1.save()
        self.d1_3 = Department.objects.create(name = 'CS_Department1_3', entity = self.e1, parent = self.d1, path = '130000000')
        self.d1.children = self.d1.children + '$' + str(self.d1_3.id)
        self.d1.save()
        self.ac1 = AssetClass.objects.create(department=self.d1_1,name = self.d1_1.name + "资产分类树",property=0)
        self.ac1_1 = AssetClass.objects.create(department=self.d1_1,name = "1_1",parent = self.ac1,property=3)
        self.ac1.children = '$' + str(self.ac1_1.id)
        self.ac1.save()
        self.ac2 = AssetClass.objects.create(department=self.d1_2,name = self.d1_2.name + "资产分类树",property=0)
        self.ac3 = AssetClass.objects.create(department=self.d1_3,name = self.d1_3.name + "资产分类树",property=0)
        self.ac3_1 = AssetClass.objects.create(department=self.d1_3,name = "3_1",parent = self.ac3,property=3)
        self.ac3.children = '$' + str(self.ac3_1.id)
        self.ac3.save()
        self.app1 = App.objects.create(entity=self.e1,name="大出生网站",path="https://www.dachusheng.com",
                                       Is_Locked=False,Is_Internal=True,authority=2)
        self.app2 = App.objects.create(entity=self.e1,name="小出生网站",path="https://www.xiaochusheng.com",
                                       Is_Locked=False,Is_Internal=True,authority=3) 
        self.app3 = App.objects.create(entity=self.e1,name="大出生外网站",path="https://www.dachushengwai.com",
                                       Is_Locked=False,Is_Internal=False,authority=2)   
        self.app4 = App.objects.create(entity=self.e1,name="小出生外网站",path="https://www.xiaochushengwai.com",
                                       Is_Locked=False,Is_Internal=False,authority=3)                          
        self.u1 = User.objects.create(
            name = 'chusheng_1',password = sha256(self.raw_password),
            super_administrator = 1,system_administrator = 0, asset_administrator = 0,
            function_string = "0000000000000000000011"
        )
        self.u2 = User.objects.create(
            name="chusheng_2", password=sha256(self.raw_password),
            entity = self.e1,
            super_administrator = 0,system_administrator = 1, asset_administrator = 0,
            function_string = "0000000000000011111100"
        )
        self.u3 = User.objects.create(
            name="chusheng_3", password=sha256(self.raw_password),
            entity = self.e1,department= self.d1_1,
            super_administrator = 0,system_administrator = 0, asset_administrator = 1,
            function_string = "0000011111111100000000"
        )
        self.u3_5 = User.objects.create(
            name="chusheng_3_5", password=sha256(self.raw_password),
            entity = self.e1,department= self.d1_3,
            super_administrator = 0,system_administrator = 0, asset_administrator = 1,
            function_string = "0000011111111100000000"
        )
        self.u4 = User.objects.create(
            name="chusheng_4", password=sha256(self.raw_password),
            entity = self.e1,department= self.d1_1,
            super_administrator = 0,system_administrator = 0, asset_administrator = 0,
            function_string = "1111100000000000000000"
        )
        self.u5 = User.objects.create(
            name="chusheng_5", password=sha256(self.test_password),
            entity = self.e1,department= self.d1_1,
            super_administrator = 0,system_administrator = 0, asset_administrator = 0,
            function_string = "1111100000000000000000"
        )
        self.a1 = Asset.objects.create(name = "ys",Class = self.ac1_1,user=self.u3,price=23000.0,
                                       description = "game",position = "computer",number = 1,
                                       status = IDLE,department=self.d1_1)
        self.a2 = Asset.objects.create(name = "sr",Class = self.ac3_1,user=self.u3_5,price=7000.0,
                                       description = "game",position = "computer",number = 1,
                                       status = IDLE,department=self.d1_3)
# 登录测试   
    # 用户名不存在 
    def test_login1(self):
        c = Client()
        resp = c.post(
            "/User/login",
            data={"UserName": self.u1.name +'hahaha', "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], 2)

    # 密码不对
    def test_login2(self):
        c = Client()
        resp = c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password + 'hahaha', "SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], 3)

    # 成功登录 
    def test_login3(self):
        c = Client()
        resp = c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], 0)
    
    # 顶号
    def test_login4(self):
        c = Client()
        resp1 = c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"], 0)
        resp2 = c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"], 0)
        resp = c.post(
            "/User/logout",
            data={"SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], -2)

# 登出测试 
    # 成功登出
    def test_logout1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/logout",
            data={"SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], 0)
    
    # sessionid不存在
    def test_logout2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/logout",
            data={"SessionID": "0"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], -2)

    # 重复登出（同时多次点击） 
    def test_logout3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/logout",
            data={"SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], 0)
        resp = c.post(
            "/User/logout",
            data={"SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], -2)


# 获取用户权限测试
    # 超级管理员
    def test_userinfo1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/info/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(resp.json()["Authority"],0)
        self.assertEqual(resp.json()["Entity"],None)
        self.assertEqual(resp.json()["Department"],None)
        self.assertEqual(resp.json()["UserApp"],"0000000000000000000011")

    # 系统管理员
    def test_userinfo2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/info/2",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(resp.json()["Authority"],1)
        self.assertEqual(resp.json()["Entity"],"CS_Company1")
        self.assertEqual(resp.json()["Department"],None)
        self.assertEqual(resp.json()["UserApp"],"0000000000000011111100")

    # 资产管理员
    def test_userinfo3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/info/3",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(resp.json()["Authority"],2)
        self.assertEqual(resp.json()["Entity"],"CS_Company1")
        self.assertEqual(resp.json()["Department"],"CS_Department1_1")
        self.assertEqual(resp.json()["UserApp"],"0000011111111100000000")

    # 普通用户
    def test_userinfo4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/info/4",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(resp.json()["Authority"],3)
        self.assertEqual(resp.json()["Entity"],"CS_Company1")
        self.assertEqual(resp.json()["Department"],"CS_Department1_1")
        self.assertEqual(resp.json()["UserApp"],"1111100000000000000000")

    # sessionid不存在
    def test_userinfo5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/info/0",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
    
    # sessionid过期    
    def test_userinfo6(self):
        SessionPool.objects.create(sessionId = "04", user = self.u4,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/info/04",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

# 查询业务实体下的所有员工测试（不算系统管理员与超级管理员）
    # 成功查询所有信息
    def test_getallmember1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/member/2/1/Name=/Department=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/member/3/1/Name=/Department=/Authority=0",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/member/4/1/Name=/Department=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)

    # 无权限  
    def test_getallmember2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/member/1/1/Name=/Department=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # sessionid不存在
    def test_getallmember3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/member/20/1/Name=/Department=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期    
    def test_getallmember4(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/member/02/1/Name=/Department=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

# 系统管理员增加用户测试
    # 无权限
    def test_addmember1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/add",
            data={"SessionID": "3", "UserName": "chusheng_6", "Department":"110000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_addmember2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/add",
            data={"SessionID": "20", "UserName": "chusheng_6", "Department":"110000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期
    def test_addmember3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.post(
            "/User/add",
            data={"SessionID": "02", "UserName": "chusheng_6", "Department":"110000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], -2)

    # 用户名已存在
    def test_addmember4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/add",
            data={"SessionID": "2", "UserName": "chusheng_1", "Department":"110000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 部门路径无效
    def test_addmember5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/add",
            data={"SessionID": "2", "UserName": "chusheng_6", "Department":"880000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # 部门不是叶子
    def test_addmember6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/add",
            data={"SessionID": "2", "UserName": "chusheng_6", "Department":"100000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # 成功添加
    def test_addmember7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/add",
            data={"SessionID": "2", "UserName": "chusheng_6", "Department":"110000000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(User.objects.filter(department=self.d1_1).all())),4)

# 系统管理员删除用户测试
# 无权限
    def test_removemember1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/remove/3/chusheng_4",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_removemember2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/remove/20/chusheng_4",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期
    def test_removemember3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.delete(
            "/User/remove/02/chusheng_4",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2 )

    # 用户不存在
    def test_removemember4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/remove/2/chusheng_66",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 尝试删除系统管理员
    def test_removemember5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/remove/2/chusheng_2",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 成功删除
    def test_removemember6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp1 = c.delete(
            "/User/remove/2/chusheng_4",
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        self.assertEqual(len(list(User.objects.filter(department=self.d1_1).all())),2)
        resp = c.post(
            "/Asset/Manage/3",
            data={"operation":2,"AssetList":[str(self.a1.id)],"MoveTo":self.u3_5.name,"Type":self.ac3_1.id},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        resp1 = c.delete(
            "/User/remove/2/chusheng_3",
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        self.assertEqual(len(list(User.objects.filter(department=self.d1_1).all())),1)
        # 被删除的用户的下一个操作应返回'sessionid不存在'
        resp2 = c.post(
            "/User/logout",
            data={"SessionID": "4"},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"], -2)
        
# 系统管理员锁定/解锁用户测试
# 无权限
    def test_lockmember1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/lock",
            data={"SessionID": "3","UserName": "chusheng_4"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_lockmember2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/lock",
            data={"SessionID": "20","UserName": "chusheng_4"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期
    def test_lockmember3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.put(
            "/User/lock",
            data={"SessionID": "02","UserName": "chusheng_4"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 用户不存在
    def test_lockmember4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/lock",
            data={"SessionID": "2","UserName": "chusheng_444"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 尝试锁定系统管理员
    def test_lockmember5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/lock",
            data={"SessionID": "2","UserName": "chusheng_2"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 成功锁定
    def test_lockmember6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        # 成功锁定
        self.assertEqual(User.objects.filter(name="chusheng_4").first().Is_Locked,False)
        resp0 = c.put(
            "/User/lock",
            data={"SessionID": "2","UserName": "chusheng_4"},
            content_type="application/json",
        )
        self.assertEqual(resp0.json()["code"],0)
        self.assertEqual(User.objects.filter(name="chusheng_4").first().Is_Locked,True)
        self.assertEqual(User.objects.filter(name="chusheng_3").first().Is_Locked,False)
        resp0 = c.put(
            "/User/lock",
            data={"SessionID": "2","UserName": "chusheng_3"},
            content_type="application/json",
        )
        self.assertEqual(resp0.json()["code"],0)
        self.assertEqual(User.objects.filter(name="chusheng_3").first().Is_Locked,True)
        # 被锁定后下一个操作应返回sessionid不存在
        resp1 = c.post(
            "/User/logout",
            data={"SessionID": "4"},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"], -2)
        # 锁定状态下无法登录
        resp2 = c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],1)
        # 成功解锁
        resp3 = c.put(
            "/User/lock",
            data={"SessionID": "2","UserName": "chusheng_4"},
            content_type="application/json",
        )
        self.assertEqual(resp3.json()["code"],0)
        self.assertEqual(User.objects.filter(name="chusheng_4").first().Is_Locked,False)

# 系统管理员更改用户权限测试
# 无权限
    def test_changeauthority1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "3","UserName": "chusheng_4","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_changeauthority2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "20","UserName": "chusheng_4","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期
    def test_changeauthority3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "02","UserName": "chusheng_4","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 用户不存在
    def test_changeauthority4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_66666","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 尝试更改系统管理员的权限
    def test_changeauthority5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_2","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 尝试将权限更改为超级/系统管理员
    def test_changeauthority6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_4","Authority": 0},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # 成功更改
    def test_changeauthority7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        # 用户权限不变时，改了但又好像没改
        resp1 = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_4","Authority": 3},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        resp2 = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_3","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],0)
        # 不能同时拥有两个资产管理员
        resp3 = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_4","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp3.json()["code"],4)
        # 但是可以没有资产管理员
        resp0 = c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        self.assertEqual(resp0.json()["code"],0)
        self.assertEqual(User.objects.filter(name="chusheng_3").first().asset_administrator, 1)
        resp = c.post(
            "/Asset/Manage/3",
            data={"operation":2,"AssetList":[str(self.a1.id)],"MoveTo":self.u3_5.name,"Type":self.ac3_1.id},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        resp4 = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_3","Authority": 3},
            content_type="application/json",
        )
        self.assertEqual(resp4.json()["code"],0)
        # 假设被更改的用户处于登录状态，他的sessionid会被删掉
        resp5 = c.post(
            "/User/logout",
            data={"SessionID": "3"},
            content_type="application/json",
        )
        self.assertEqual(resp5.json()["code"], -2)
        # 没有资产管理员的时候还是尽快添加回去为好
        self.assertEqual(User.objects.filter(name="chusheng_4").first().asset_administrator, 0)
        resp6 = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_4","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp6.json()["code"],0)
        self.assertEqual(User.objects.filter(name="chusheng_4").first().function_string, "0000011111111100000000")
        self.assertEqual(User.objects.filter(name="chusheng_4").first().asset_administrator, 1)

# 系统管理员重置用户密码测试
# 无权限
    def test_remakepassword1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/RemakePassword",
            data={"SessionID": "3","UserName": "chusheng_5"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_remakepassword2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/RemakePassword",
            data={"SessionID": "20","UserName": "chusheng_5"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期
    def test_remakepassword3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.post(
            "/User/RemakePassword",
            data={"SessionID": "02","UserName": "chusheng_4"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 用户不存在
    def test_remakepassword4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/RemakePassword",
            data={"SessionID": "2","UserName": "chusheng_567"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 尝试重置系统管理员的密码
    def test_remakepassword5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/RemakePassword",
            data={"SessionID": "2","UserName": "chusheng_2"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 成功重置密码
    def test_remakepassword6(self):
        c = Client()
        # 先登录
        resp1 = c.post(
            "/User/login",
            data={"UserName": self.u5.name, "Password": self.test_password, "SessionID": "5"},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)        
        resp3 = c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        self.assertEqual(resp3.json()["code"],0)
        # 重置密码
        resp4 = c.post(
            "/User/RemakePassword",
            data={"SessionID": "2","UserName": "chusheng_5"},
            content_type="application/json",
        )
        self.assertEqual(resp4.json()["code"],0)
        resp4 = c.post(
            "/User/RemakePassword",
            data={"SessionID": "2","UserName": "chusheng_3"},
            content_type="application/json",
        )
        self.assertEqual(resp4.json()["code"],0)
        # 此时u5的sessionid会被删掉
        resp2 = c.post(
            "/User/logout",
            data={"SessionID": "5"},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],-2)
        # 需要使用重置后的密码重新登录
        resp6 = c.post(
            "/User/login",
            data={"UserName": self.u5.name, "Password": MD5(self.raw_password), "SessionID": "5"},
            content_type="application/json",
        )
        self.assertEqual(resp6.json()["code"],0)
        
# 获取部门树
    # 无权限  
    def test_gettree1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/tree/3",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)
    
    # sessionid不存在
    def test_gettree2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/tree/20",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
    
    # sessionid过期    
    def test_gettree3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/tree/02",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 成功获取
    def test_gettree4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/tree/2",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        print(resp.json()["treeData"])
    
# 系统管理员增加部门测试
    # 无权限  
    def test_adddepartment1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "3", "DepartmentPath":"000000000", "DepartmentName":"CS_Department000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # sessionid不存在
    def test_adddepartment2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "20", "DepartmentPath":"000000000", "DepartmentName":"CS_Department000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期    
    def test_adddepartment3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "02", "DepartmentPath":"000000000", "DepartmentName":"CS_Department000"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # DepartmentName已存在
    def test_adddepartment4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"000000000", "DepartmentName":"CS_Department1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
    
    # DepartmentPath无效
    def test_adddepartment5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"880000000", "DepartmentName":"CS_Department2"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # 子部门数量达到上限
    def test_adddepartment6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        for i in range(4,10):
            resp_i = c.post(
                "/User/department/add",
                data={"SessionID": "2", "DepartmentPath":"100000000", "DepartmentName":"CS_Department1_" + str(i)},
                content_type="application/json",
            )
            self.assertEqual(resp_i.json()["code"],0)
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"100000000", "DepartmentName":"CS_Department1_10"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],3)

    # 创建根部门
    def test_adddepartment7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"000000000", "DepartmentName":"CS_Department2"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(resp.json()["department_path"],"200000000")
        d2 = Department.objects.filter(entity=self.e1,path="200000000").first()
        self.assertEqual(len(AssetClass.objects.filter(department=d2).all()),3)

    # 成功创建非叶子部门的子部门
    def test_adddepartment8(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"100000000", "DepartmentName":"CS_Department1_4"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(resp.json()["department_path"],"140000000")
        d1_3 = Department.objects.filter(entity=self.e1,path="140000000").first()
        self.assertEqual(len(AssetClass.objects.filter(department=d1_3).all()),3)

    # 成功创建叶子部门的子部门并把所有员工和资产分类树转移
    def test_adddepartment9(self):
        c = Client()
        # 先登录
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        # 建部门
        self.assertEqual(len(AssetClass.objects.filter(department=self.d1_1).all()),2)
        resp1 = c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"110000000", "DepartmentName":"CS_Department1_1_1"},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        self.assertEqual(resp1.json()["department_path"],"111000000")
        self.assertEqual(len(User.objects.filter(department=self.d1_1).all()), 0)
        self.assertEqual(len(AssetClass.objects.filter(department=self.d1_1).all()),0)
        d1_1_1 = Department.objects.filter(entity=self.e1,path="111000000").first()
        self.assertEqual(AssetClass.objects.filter(department=d1_1_1,property=0).first().name,d1_1_1.name+"资产分类树")
    
# 查询下一级部门或员工测试
    # 无权限  
    def test_getnextdepartment1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/department/3/100000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_getnextdepartment2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/department/20/100000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期    
    def test_getnextdepartment3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/department/02/100000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
    
    # DepartmentPath无效
    def test_getnextdepartment4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/department/2/888000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 查询非叶子部门，返回下一级的部门信息
    def test_getnextdepartment5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/department/2/100000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["member"]),0)
        self.assertEqual(resp.json()["Department"][0]["DepartmentName"],self.d1_1.name)
        self.assertEqual(resp.json()["Department"][1]["DepartmentName"],self.d1_2.name)
        self.assertEqual(resp.json()["route"][0]["Name"],self.e1.name)
        self.assertEqual(resp.json()["route"][0]["Path"],"000000000")
        self.assertEqual(resp.json()["route"][1]["Name"],self.d1.name)
        self.assertEqual(resp.json()["route"][1]["Path"],"100000000")

    # 查询叶子部门，返回员工信息
    def test_getnextdepartment6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/department/2/110000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["member"]),3)
        self.assertEqual(len(resp.json()["Department"]),0)
        self.assertEqual(resp.json()["route"][0]["Name"],self.e1.name)
        self.assertEqual(resp.json()["route"][0]["Path"],"000000000")
        self.assertEqual(resp.json()["route"][1]["Name"],self.d1.name)
        self.assertEqual(resp.json()["route"][1]["Path"],"100000000")
        self.assertEqual(resp.json()["route"][2]["Name"],self.d1_1.name)
        self.assertEqual(resp.json()["route"][2]["Path"],"110000000")

    # 查询根部门
    def test_getnextdepartment7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/department/2/000000000/1/Name=/Authority=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["member"]),0)
        self.assertEqual(resp.json()["Department"][0]["DepartmentName"],self.d1.name)
        self.assertEqual(resp.json()["route"][0]["Name"],self.e1.name)
        self.assertEqual(resp.json()["route"][0]["Path"],"000000000")

# 移动员工测试
    # 无权限  
    def test_movemember1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "3","DepartmentPathFrom":"110000000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u5.name]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_movemember2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "20","DepartmentPathFrom":"110000000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u5.name]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期    
    def test_movemember3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "02","DepartmentPathFrom":"110000000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u5.name]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # From部门不存在
    def test_movemember4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "2","DepartmentPathFrom":"114514000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u5.name]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # To部门不存在
    def test_movemember5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "2","DepartmentPathFrom":"110000000","DepartmentPathTo":"114514000","member":[self.u4.name,self.u5.name]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # To部门并非叶子
    def test_movemember6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "2","DepartmentPathFrom":"110000000","DepartmentPathTo":"100000000","member":[self.u4.name,self.u5.name]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 某用户不存在
    def test_movemember7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/department/move",
            data={"SessionID": "2","DepartmentPathFrom":"110000000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u5.name,"chusheng_666"]},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)
        self.assertEqual(len(User.objects.filter(department=self.d1_1).all()),3)
 
    # 尝试将资产管理员移至有资产管理员的部门
    def test_movemember8(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp1 = c.post(
            "/User/add",
            data={"SessionID": "2", "UserName": "chusheng_6", "Department":"120000000"},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        resp2 = c.put(
            "/User/ChangeAuthority",
            data={"SessionID": "2","UserName": "chusheng_6","Authority": 2},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],0)
        resp3 = c.post(
            "/User/department/move",
            data={"SessionID": "2","DepartmentPathFrom":"110000000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u5.name,self.u3.name]},
            content_type="application/json",
        )
        self.assertEqual(resp3.json()["code"],5)
        self.assertEqual(len(User.objects.filter(department=self.d1_1).all()),3)

    # 成功移动
    def test_movemember9(self):
        c = Client()
        # 先登录
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp1 = c.post(
            "/User/department/move",
            data={"SessionID": "2","DepartmentPathFrom":"110000000","DepartmentPathTo":"120000000","member":[self.u4.name,self.u3.name]},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        self.assertEqual(len(User.objects.filter(department=self.d1_1).all()),1)
        self.assertEqual(len(User.objects.filter(department=self.d1_2).all()),2)
        # 被挪动的员工需要重新登录
        resp2 = c.post(
            "/User/logout",
            data={"SessionID": "4"},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],-2)

# 删除部门测试：
    # 无权限  
    def test_deletedepartment1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/department/delete/3/120000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_deletedepartment2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/department/delete/20/120000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期    
    def test_deletedepartment3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.delete(
            "/User/department/delete/02/120000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 还有子部门
    def test_deletedepartment4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/department/delete/2/100000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # 还有员工
    def test_deletedepartment5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/department/delete/2/110000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # 还有资产
    def test_deletedepartment6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        a1 = Asset.objects.create(name="资产1",Class=self.ac2,price=10,description="",position="",property="",department=self.d1_2)
        resp = c.delete(
            "/User/department/delete/2/120000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # 成功删除根部门
    def test_deletedepartment7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        for i in range(2,5):
            c.post(
                "/User/department/add",
                data={"SessionID": "2", "DepartmentPath":"000000000", "DepartmentName":"CS_Department" + str(i)},
                content_type="application/json",
            )
        c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"300000000", "DepartmentName":"CS_Department3_1"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/department/delete/2/200000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(Department.objects.filter(entity=self.e1,parent=None).all()),3)
        self.assertEqual(Department.objects.filter(entity=self.e1,path="200000000").first().name,"CS_Department3")
        self.assertEqual(Department.objects.filter(entity=self.e1,path="210000000").first().name,"CS_Department3_1")
        self.assertEqual(Department.objects.filter(entity=self.e1,path="300000000").first().name,"CS_Department4")
        self.assertEqual(Department.objects.filter(entity=self.e1,path="310000000").first(),None)
        self.assertEqual(Department.objects.filter(entity=self.e1,path="400000000").first(),None)

    # 成功删除非根部门
    def test_deletedepartment8(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"100000000", "DepartmentName":"CS_Department1_3"},
            content_type="application/json",
        )
        c.post(
            "/User/department/add",
            data={"SessionID": "2", "DepartmentPath":"130000000", "DepartmentName":"CS_Department1_3_1"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/department/delete/2/120000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(Department.objects.filter(entity=self.e1,parent=self.d1).all()),2)
        self.assertEqual(Department.objects.filter(entity=self.e1,path="120000000").first().name,"CS_Department1_3")
        self.assertEqual(Department.objects.filter(entity=self.e1,path="121000000").first().name,"CS_Department1_3_1")

# 系统管理员管理url测试(删除也放在这里一起测)
    # 无权限
    def test_manageapps1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/App/delete/1/3/小出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/App/3/2",
            data = {"AppName":"大大出生外网站","AppUrl":"www.dadachusheng.com"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionid不存在
    def test_manageapps2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/App/20/3",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
        resp = c.delete(
            "/User/App/delete/20/3/小出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
        resp = c.get(
            "/User/NewApp/20/2",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionid过期
    def test_manageapps3(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/App/02/3",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    def test_manageapps3_1(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.delete(
            "/User/App/delete/02/3/小出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    def test_manageapps3_2(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/NewApp/02/2",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # authority不合法
    def test_manageapps4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/App/2/0",
            data = {"AppName":"大大出生外网站","AppUrl":"www.dadachusheng.com"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],3)
        resp = c.delete(
            "/User/App/delete/2/10/小出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],3)

    # post时已存在/put时不存在/delete时不存在
    def test_manageapps5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"大出生网站","AppUrl":"www.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"出生大网站","AppUrl":"https://www.dachusheng.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        resp = c.put(
            "/User/App/2/2",
            data = {"AppName":"出生大网站","AppUrl":"www.chusheng2.com"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        resp = c.delete(
            "/User/App/delete/2/3/大小出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 尝试delete/put内部应用
    def test_manageapps6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.delete(
            "/User/App/delete/2/3/小出生网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)
        resp = c.delete(
            "/User/App/delete/2/3/小出生网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

    # 增删查改成功
    def test_managaapps7(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"大大出生外网站","AppUrl":"https://www.dadachusheng.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=2).all())),3)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=2,Is_Internal=False).all())),2)
        resp = c.post(
            "/User/App/2/3",
            data = {"AppName":"小小小小出生外网站","AppUrl":"https://www.xiaoxiaoxiaoxiaochusheng.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=3).all())),3)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=3,Is_Internal=False).all())),2)
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"大大大出生外网站","AppUrl":"https://www.dadachusheng.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"大大大出生外网站","AppUrl":"https://www.dadachusheng.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"大大大出生外网站","AppUrl":"https://www.dadachusheng.com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        resp = c.get(
            "/User/App/2/3",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["AppList"]),3)
        resp = c.get(
            "/User/NewApp/2/3",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["AppList"]),2)
        resp = c.put(
            "/User/App/2/2",
            data = {"AppName":"大大出生外网站","AppUrl":"https://www.dadachusheng.com"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=2,Is_Locked=False).all())),2)
        resp = c.put(
            "/User/App/2/2",
            data = {"AppName":"大大出生外网站","AppUrl":"https://www.dadachusheng.com"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=2,Is_Locked=False).all())),3)
        resp = c.delete(
            "/User/App/delete/2/2/大大出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=2).all())),2)
        resp = c.delete(
            "/User/App/delete/2/3/小出生外网站",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(list(App.objects.filter(entity=self.e1,authority=3).all())),2)

    # 达到上限
    def test_managaapps8(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        for i in range(2,10):
            resp = c.post(
                "/User/App/2/2",
                data = {"AppName":"大大出生外网站" + str(i),"AppUrl":"https://www.dadachusheng"+ str(i) +".com","AppImage":""},
                content_type="application/json",
            )
            self.assertEqual(resp.json()["code"],0)
        i = 10
        resp = c.post(
            "/User/App/2/2",
            data = {"AppName":"大大出生外网站" + str(i),"AppUrl":"https://www.dadachusheng"+ str(i) +".com","AppImage":""},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],4)

# 查询资产全视图
    # 无权限 
    def test_getassetdetail1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/Asset_Detail/2/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionId过期
    def test_getassetdetail2(self):
        SessionPool.objects.create(sessionId = "03", user = self.u3,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/Asset_Detail/03/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionId不存在 
    def test_getassetdetail3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "03"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/Asset_Detail/30/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 资产不存在
    def test_getassetdetail4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/Asset_Detail/3/10000000",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

    # 资产不在该部门
    def test_getassetdetail5(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/Asset_Detail/3/2",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],3)

    # 成功查询全视图
    def test_getassetdetail6(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp1 = c.post(
            "/Asset/Apply/4",
            data={"operation":0,"AssetList":[1],"MoveTo":"","Type":self.ac1_1.id},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        resp2 = c.post(
            "/Asset/Approval/3",
            data={"IsApproval":1,"Approval":[1]},
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],0)
        resp3 = c.post(
            "/Asset/Apply/4",
            data={"operation":3,"AssetList":[1],"MoveTo":self.u5.name,"Type":self.ac1_1.id},
            content_type="application/json",
        )
        self.assertEqual(resp3.json()["code"],0)
        c.post(
            "/Asset/Approval/3",
            data={"IsApproval":1,"Approval":[2]},
            content_type="application/json",
        )
        resp5 = c.get(
            "/User/Asset_Detail/3/1",
            content_type="application/json",
        )
        self.assertEqual(resp5.json()["code"],0)
        self.assertEqual(len(resp5.json()["Asset_Detail"]["History"]),2)

    # 干掉sessionid
    def test_QR_getassetdetail(self):
        c = Client()
        resp1 = c.get(
            "/User/QR_Asset_Detail/1",
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)

# 查看消息测试
    # 无权限
    def test_getmessage1(self):
        c = Client()
        # 登录
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        # 更改阅读情况
        resp1 = c.put(
            "/User/Message/New/2",
            date={"ID":1},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],2)
        # 查看全消息
        resp2 = c.get(
            "/User/Message/All/2/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],2)

    # sessionId过期
    def test_getmessage2(self):
        SessionPool.objects.create(sessionId = "03", user = self.u3,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        # 更改阅读情况
        resp1 = c.put(
            "/User/Message/New/03",
            date={"ID":1},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],-2)
    def test_getmessage2_5(self):
        SessionPool.objects.create(sessionId = "04", user = self.u4,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        # 查看全消息
        resp2 = c.get(
            "/User/Message/All/04/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],-2)

    # sessionId不存在
    def test_getnewmessage3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        # 更改阅读情况
        resp1 = c.put(
            "/User/Message/New/40",
            date={"ID":1},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],-2)
        # 查看全消息
        resp2 = c.get(
            "/User/Message/All/40/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],-2)
        
    # 其余情况写在下面一个函数里
    def test_getnewmessage4(self):
        c = Client()
        # 资产管理员登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        # 员工登录
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        # 啥消息没有的时候直接查询
        resp0 = c.get(
            "/User/Message/All/4/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp0.json()["code"],0)
        self.assertEqual(len(resp0.json()["Message"]),0)
        # 申请资产
        resp1 = c.post(
            "/Asset/Apply/4",
            data={"operation":0,"AssetList":[1],"MoveTo":"","Type":self.ac1_1.id},
            content_type="application/json",
        )
        self.assertEqual(resp1.json()["code"],0)
        # 此时员工和资产管理员都有一条新消息
        response = PendingResponse.objects.filter(id=2).first()
        self.assertEqual(response.is_read,False)
        resp2 = c.get(
            "/User/Message/All/4/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp2.json()["code"],0)
        self.assertEqual(len(resp2.json()["Message"]),1)
        resp2_1 = c.get(
            "/User/Message/All/3/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp2_1.json()["code"],0)
        self.assertEqual(len(resp2_1.json()["Message"]),1)
        # 资产管理员审批通过
        resp3 = c.post(
            "/Asset/Approval/3",
            data={"IsApproval":1,"Approval":[1]},
            content_type="application/json",
        )
        self.assertEqual(resp3.json()["code"],0)
        # 资产管理员尝试将消息置为已读
        resp4_1 = c.put(
            '/User/Message/New/3',
            data={"ID": 100},
            content_type="application/json",
        )
        self.assertEqual(resp4_1.json()["code"],1)
        resp4_2 = c.put(
            '/User/Message/New/3',
            data={"ID":2},
            content_type="application/json",
        )
        self.assertEqual(resp4_2.json()["code"],0)
        response = PendingResponse.objects.filter(id=2).first()
        self.assertEqual(response.is_read,True)
        # 此时员工有两条未读，资产管理员一条已读
        resp5 = c.get(
            "/User/Message/All/4/1/Is_Read=-1",
            content_type="application/json",
        )
        self.assertEqual(resp5.json()["code"],0)
        self.assertEqual(len(resp5.json()["Message"]),2)
        resp5_1 = c.get(
            "/User/Message/All/4/1/Is_Read=0",
            content_type="application/json",
        )
        self.assertEqual(resp5_1.json()["code"],0)
        self.assertEqual(len(resp5_1.json()["Message"]),2)
        resp5_2 = c.get(
            "/User/Message/All/4/1/Is_Read=1",
            content_type="application/json",
        )
        self.assertEqual(resp5_2.json()["code"],0)
        self.assertEqual(len(resp5_2.json()["Message"]),0)
        resp5_3 = c.get(
            "/User/Message/All/3/1/Is_Read=1",
            content_type="application/json",
        )
        self.assertEqual(resp5_3.json()["code"],0)
        self.assertEqual(len(resp5_3.json()["Message"]),1)
        # 资产管理员再把已读消息改成未读
        resp6_1 = c.put(
            '/User/Message/New/3',
            data={"ID":2},
            content_type="application/json",
        )
        self.assertEqual(resp6_1.json()["code"],0)
        response = PendingResponse.objects.filter(id=2).first()
        self.assertEqual(response.is_read,False)
        # 此时资产管理员有一条未读
        resp6_2 = c.get(
            "/User/Message/All/3/1/Is_Read=0",
            content_type="application/json",
        )
        self.assertEqual(resp6_2.json()["code"],0)
        self.assertEqual(len(resp6_2.json()["Message"]),1)
        self.assertEqual(resp6_2.json()["Message"][0]["ID"],2)
        # 用户也可以全部设为已读、再挑一个设成未读
        resp6_1 = c.put(
            '/User/Message/New/4',
            data={"ID":-1},
            content_type="application/json",
        )
        self.assertEqual(resp6_1.json()["code"],0)
        response = PendingResponse.objects.filter(id=1).first()
        self.assertEqual(response.is_read,True)
        resp6_2 = c.put(
            '/User/Message/New/4',
            data={"ID":3},
            content_type="application/json",
        )
        self.assertEqual(resp6_1.json()["code"],0)
        response = PendingResponse.objects.filter(id=1).first()
        self.assertEqual(response.is_read,True)
        response = PendingResponse.objects.filter(id=3).first()
        self.assertEqual(response.is_read,False)
        # 此时只有3号消息未读
        resp6_3 = c.get(
            "/User/Message/All/4/1/Is_Read=0",
            content_type="application/json",
        )
        self.assertEqual(resp6_3.json()["code"],0)
        self.assertEqual(len(resp6_3.json()["Message"]),1)
        self.assertEqual(resp6_3.json()["Message"][0]["ID"],3)


# 查看日志测试
    # 无权限
    def test_getlogdetail1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.get(
            "/Log/Detail/3/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionId过期
    def test_getlogdetail2(self):
        SessionPool.objects.create(sessionId = "02", user = self.u2,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/Log/Detail/02/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionId不存在
    def test_getlogdetail3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "02"},
            content_type="application/json",
        )
        resp = c.get(
            "/Log/Detail/20/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 成功查询
    def test_getlogdetail4(self):
        c = Client()
        # 先登录
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )
        # 只有一条登录日志
        resp = c.get(
            "/Log/Detail/2/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),1)
        # 第二页为空
        resp = c.get(
            "/Log/Detail/2/0/2/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        # 新建19条日志
        for i in range (0,9):
            c.post(
                "/User/login",
                data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
                content_type="application/json",
            )
            c.post(
                "/User/logout",
                data={"SessionID": "3"},
                content_type="application/json",
            )
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        # 现在一共20条
        resp = c.get(
            "/Log/Detail/2/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),20)
        # 第二页为空
        resp = c.get(
            "/Log/Detail/2/0/2/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        # 再新建一条日志
        c.post(
            "/User/logout",
            data={"SessionID": "3"},
            content_type="application/json",
        )
        # 查第一页会刷新
        resp = c.get(
            "/Log/Detail/2/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),20)
        # 此时第二页有一条
        resp = c.get(
            "/Log/Detail/2/0/2/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),1)
        # 超级管理员登录，系统管理员查不着
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        # 系统管理员再分类查一查,登录登出日志有20+1
        resp = c.get(
            "/Log/Detail/2/1/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),20)
        resp = c.get(
            "/Log/Detail/2/1/2/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),1)
        # 其他类型都没有
        resp = c.get(
            "/Log/Detail/2/2/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        resp = c.get(
            "/Log/Detail/2/3/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        resp = c.get(
            "/Log/Detail/2/4/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        # type不合法报错
        resp = c.get(
            "/Log/Detail/2/5/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)
        # 超级管理员先总体查再分类查，登录日志应有22条
        resp = c.get(
            "/Log/Detail/1/0/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),20)
        resp = c.get(
            "/Log/Detail/1/0/2/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),2)
        resp = c.get(
            "/Log/Detail/1/1/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),20)
        resp = c.get(
            "/Log/Detail/1/1/2/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),2)
        # 其他类型都没有
        resp = c.get(
            "/Log/Detail/1/2/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        resp = c.get(
            "/Log/Detail/1/3/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        resp = c.get(
            "/Log/Detail/1/4/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        self.assertEqual(len(resp.json()["LogList"]),0)
        # type不合法报错
        resp = c.get(
            "/Log/Detail/1/5/1/Success=-1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

# 更改手机号   
    # sessionId过期
    def test_changemobile1(self):
        SessionPool.objects.create(sessionId = "03", user = self.u3,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.post(
            "/User/change_mobile",
            data={"SessionID": "03", "Mobile" :"13019181205"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
    
    # sessionId不存在
    def test_changemobile2(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/change_mobile",
            data={"SessionID": "40", "Mobile" :"13019181205"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    def test_changemobile3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/change_mobile",
            data={"SessionID": "4", "Mobile" :"13019181205"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "3"},
            content_type="application/json",
        )
        resp = c.post(
            "/User/change_mobile",
            data={"SessionID": "3", "Mobile" :"13019181205"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],1)

# 叶子部门获取与飞书部门指定
    # 无权限
    def test_feishudepartmenrt1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u4.name, "Password": self.raw_password, "SessionID": "4"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/LeafDepartment/4/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)
        resp = c.post(
            "/User/FeishuDepartment",
            data={"DepartmentID": 1, "SessionID": "4"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],2)

    # sessionId过期
    def test_feishudepartmenrt2(self):
        SessionPool.objects.create(sessionId = "01", user = self.u1,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.get(
            "/User/LeafDepartment/01/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    def test_feishudepartmenrt2_1(self):
        SessionPool.objects.create(sessionId = "01", user = self.u1,
                                   expireAt = dt.datetime.now(pytz.timezone(TIME_ZONE)) - dt.timedelta(days=2))
        c = Client()
        resp = c.post(
            "/User/FeishuDepartment",
            data={"DepartmentID": 1, "SessionID": "01"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # sessionId不存在
    def test_feishudepartmenrt3(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/LeafDepartment/01/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)
        resp = c.post(
            "/User/FeishuDepartment",
            data={"DepartmentID": 1, "SessionID": "001"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],-2)

    # 成功查询并指定
    def test_getleafdepartmenrt4(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.get(
            "/User/LeafDepartment/1/1",
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        l1 = resp.json()["Departments"]
        d1 = l1[0]["ID"][0]
        resp = c.post(
            "/User/FeishuDepartment",
            data={"DepartmentID": d1, "SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)
        resp = c.post(
            "/User/feishu_sync",
            data={"SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"],0)

# 飞书相关
    def test_feishu1(self):
        open_id = get_open_id("13019181205")

