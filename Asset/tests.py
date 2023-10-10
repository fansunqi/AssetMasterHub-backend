from django.test import TestCase
from User.models import Entity,Department, User, SessionPool
from Asset.models import AssetClass, Asset, PendingRequests
from django.test import Client as DefaultClient
from utils.utils_other import *
from utils.utils_asset import *
from Asset.views import *
from User.views import *

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



class AssetTests(TestCase):
    def setUp(self):
        self.raw_password = "yiqunchusheng"
        self.e1 = Entity.objects.create(name = 'CS_Company')
        self.d1 = Department.objects.create(name = 'depart1',entity = self.e1)
        self.u1 = User.objects.create(
            name = 'chusheng_1',password = sha256(self.raw_password),
            entity = self.e1,department= self.d1,
            super_administrator = 1,system_administrator = 0, asset_administrator=0
        )
        self.u2 = User.objects.create(
            name="chusheng_2", password=sha256(self.raw_password),
            entity = self.e1,department= self.d1,
            super_administrator = 0,system_administrator = 1, asset_administrator=0
        )
        self.u3 = User.objects.create(
            name="chusheng_3", password=sha256(self.raw_password),
            entity = self.e1,department= self.d1,
            super_administrator = 0,system_administrator = 0, asset_administrator=1
        )
        self.u4 = User.objects.create(
            name="chusheng_4", password=sha256(self.raw_password),
            entity = self.e1,department= self.d1,
            super_administrator = 0,system_administrator = 0, asset_administrator=0
        )
        # 下面这句话应该没有作用吧
        # SessionPool.objects.create(user = self.u1)
        
        # 创建资产分类asset class简称ac
        self.ac0 = AssetClass.objects.create(
            department = self.d1, name = "department1 资产分类树", children = "$2$3",  property = 0
        )
        self.ac1 = AssetClass.objects.create(
            department = self.d1, name = "房屋与构筑物", parent = self.ac0, children = "$4$5", property = 1
        )
        self.ac2 = AssetClass.objects.create(
            department = self.d1, name = "设备", parent = self.ac0, children = "$6$7", property = 1
        )
        self.ac3 = AssetClass.objects.create(
            department = self.d1, name = "房屋", parent = self.ac1, children = "", property = 3
        )
        self.ac4 = AssetClass.objects.create(
            department = self.d1, name = "土地", parent = self.ac1, children = "", property = 3
        )
        self.ac5 = AssetClass.objects.create(
            department = self.d1, name = "信息化设备", parent = self.ac2, children = "", property = 2
        )
        self.ac6 = AssetClass.objects.create(
            department = self.d1, name = "车辆", parent = self.ac2, children = "", property = 2
        )
        
    def test_tree_1(self):
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )
        resp = c.post(
            "/Asset/tree",
            data={"SessionID": "1"},
            content_type="application/json",
        )
        self.assertEqual(resp.json()["code"], 0)

    def test_superuser_create_1(self):
        # 检查正常返回
        c = Client()
        
        # 先进行登录
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 然后进行创建
        resp = c.put(
            "/SuperUser/Create",
            data={"SessionID": "1", "UserName": "张三", "EntityName":"大象金融"},
            content_type="application/json",
        )

        # 用创建的这个系统管理员登录一下
        resp2 = c.post(
            "/User/login",
            data={"UserName": "张三", "Password": MD5("yiqunchusheng"), "SessionID": "3"},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0 )

    def test_superuser_create_2(self):
        # 检查非超级管理员登录
        # 返回:request_failed(3, "非超级管理员，没有对应权限")
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u2.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )

        # 然后再根据登录的sessionID进行功能实现
        resp = c.put(
            "/SuperUser/Create",
            data={"SessionID": "2", "UserName": "张三", "EntityName":"大象金融"},
            content_type="application/json",
        )
        

        self.assertEqual(resp.json()["code"], 3)
    
    def test_superuser_create_3(self):
        # 检查创建同名
        # 返回:request_failed(4, "存在重复用户名")
        c = Client()
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "2"},
            content_type="application/json",
        )

        # 然后再根据登录的sessionID进行
        resp = c.put(
            "/SuperUser/Create",
            data={"SessionID": "2", "UserName": "chusheng_1", "EntityName":"大象金融"},
            content_type="application/json",
        )
        

        self.assertEqual(resp.json()["code"], 4)
    
    def test_superuser_delete_1(self):
        c = Client()

        # 超级管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 然后进行创建
        resp1 = c.put(
            "/SuperUser/Create",
            data={"SessionID": "1", "UserName": "张三", "EntityName":"大象金融"},
            content_type="application/json",
        )

        # 超级管理员发送delete请求
        resp2 = c.delete(
            "/SuperUser/Delete/1/大象金融", 
            content_type="application/json",
        )

        self.assertEqual(resp2.json()["code"], 0)
    
    def test_superuser_delete_2(self):
        c = Client()

        # 超级管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 然后进行创建
        resp1 = c.put(
            "/SuperUser/Create",
            data={"SessionID": "1", "UserName": "张三", "EntityName":"大象金融"},
            content_type="application/json",
        )

        # 超级管理员发送delete请求
        resp2 = c.delete(
            "/SuperUser/Delete/1/大象金融", 
            content_type="application/json",
        )

        # 然后试图登录张三这个账号
        # 用创建的这个系统管理员登录一下
        resp3 = c.post(
            "/User/login",
            data={"UserName": "张三", "Password": MD5("yiqunchusheng"), "SessionID": "3"},
            content_type="application/json",
        )

        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 2)
    
    def test_superuser_info_1(self):

        c = Client()

        # 超级管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

         # 然后进行创建
        resp1 = c.put(
            "/SuperUser/Create",
            data={"SessionID": "1", "UserName": "张三", "EntityName":"大象金融"},
            content_type="application/json",
        )

        # 然后获取信息
        resp = c.get(
            "/SuperUser/info/1",
            content_type="application/json",
        )

        debug_print("返回体", resp.json())

        self.assertEqual(resp.json()["code"], 0)
    
    def test_add_asset_class_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # parent_asset_class = get_asset_class(1)
        # debug_print("former children", parent_asset_class.children)

        # 资产管理员调用add_asset_class函数
        resp = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

        # parent_asset_class = get_asset_class(1)
        # debug_print("later children", parent_asset_class.children)

        self.assertEqual(resp.json()["code"], 0)
    
    def test_add_asset_class_2(self):
        # 测试能否创建同名资产分类
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )


        # 资产管理员调用add_asset_class函数
        resp = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

        # 再调用一次
        resp2 = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 0, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )


        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 4)
    
    def test_modify_asset_class_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset_class函数
        resp = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

        asset_class = get_asset_class(1)
        debug_print(asset_class.property, asset_class.name)

        # 资产管理员调用modify_asset_class函数
        resp2 = c.post(
            "/Asset/ModifyAssetClass",
            data={"SessionID": "1", "NodeValue": 1, "AssetClassName": "改成这一个资产类别", "LossStyle": 0},
            content_type="application/json",
        )

        self.assertEqual(resp2.json()["code"], 5)

    def test_modify_asset_class_2(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset_class函数
        resp = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

        asset_class = get_asset_class(1)
        debug_print(asset_class.property, asset_class.name)

        # 资产管理员调用modify_asset_class函数
        resp2 = c.post(
            "/Asset/ModifyAssetClass",
            data={"SessionID": "1", "NodeValue": 1, "AssetClassName": "改成这一个资产类别", "LossStyle": 1},
            content_type="application/json",
        )

        asset_class = get_asset_class(1)
        debug_print(asset_class.property, asset_class.name)

        self.assertEqual(resp2.json()["code"], 5)
    
    def test_delete_asset_class(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset_class函数
        resp = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

        root_node = AssetClass.objects.filter(id=1).first()
        debug_print("root_node", root_node.children)
        all_node = AssetClass.objects.all()
        debug_print("all", len(all_node))


        # 资产管理员调用delete_asset_class函数
        resp2 = c.delete(
            "/Asset/DeleteAssetClass/1/8",
            content_type="application/json",
        )

        resp3 = c.delete(
            "/Asset/DeleteAssetClass/1/2",
            content_type="application/json",
        )

        root_node = AssetClass.objects.filter(id=1).first()
        # debug_print("root_node", root_node.children)
        all_node = AssetClass.objects.all()
        # debug_print("all", len(all_node))


        self.assertEqual(resp2.json()["code"], 5)
        self.assertEqual(resp3.json()["code"], 5)
    
    def test_add_asset_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, \
                  "Time": "2023-05-24 20:05:45"},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
    
    def test_asset_info_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset_class函数
        resp = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

         # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, \
                  "Time":"2023-05-24 20:05:45"},
            content_type="application/json",
        )

        # 资产管理员调用asset_info函数
        resp2 = c.post(
            "/Asset/Info/1",
            content_type="application/json",
        )

        self.assertEqual(resp2.json()["code"], 0)
    
    def test_asset_info_2(self):
        c = Client()

        # 超级管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 超级管理员调用asset_info函数(没有权限)
        resp = c.post(
            "/Asset/Info/1",
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 3)
    
    def test_asset_apply_and_approval(self):

        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )
        
        debug_print("resp", resp.json()["code"])
        asset_list = Asset.objects.all()
        for asset in asset_list:
            debug_print(asset.id, asset.name)

        # 资产管理员调用asset_apply函数
        # NOTE:严格来说，这里需要用户来调用asset_apply函数
        resp = c.post(
            "/Asset/Apply/1",
            data={"operation": 0 ,\
                  "AssetList": [1, 2], \
                  "MoveTo": "", \
                  "Type": ""}, \
            content_type="application/json",\
        )

        resp = c.post(
            "/Asset/Apply/1",
            data={"operation": "1" ,\
                  "AssetList": ["1"], \
                  "MoveTo": "chusheng_4"}, \
            content_type="application/json",\
        )

        resp = c.post(
            "/Asset/Apply/1",
            data={"operation": "2" ,\
                  "AssetList": ["1"], \
                  "MoveTo": "chusheng_4"}, \
            content_type="application/json",\
        )


        # 资产管理员调用asset_approval函数的GET方法
        resp2 = c.get(
            "/Asset/Approval/1",\
            content_type="application/json",\
        )

        # 资产管理员调用asset_approval函数的POST方法
        resp3 = c.post(
            "/Asset/Approval/1", 
            data = {"IsApproval": 0,   
                    "Approval" : [2]}, 
            content_type="application/json",
        )

        debug_print("resp2", resp2.json())

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)
    
    def test_asset_apply_and_approval_2(self):

        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )
        
        debug_print("resp", resp.json()["code"])
        asset_list = Asset.objects.all()
        for asset in asset_list:
            debug_print(asset.id, asset.name)

        # 资产管理员调用asset_apply函数
        # NOTE:严格来说，这里需要用户来调用asset_apply函数
        resp = c.post(
            "/Asset/Apply/1",
            data={"operation": 0 ,\
                  "AssetList": [1, 2], \
                  "MoveTo": "", \
                  "Type": "", \
                  "number": 50, \
                  "Message": "XXXXX"}, \
            content_type="application/json",\
        )

        resp = c.post(
            "/Asset/Apply/1",
            data={"operation": "1" ,\
                  "AssetList": ["1"], \
                  "MoveTo": "chusheng_4", \
                  "Message":"XXXX"}, \
            content_type="application/json",\
        )

        resp = c.post(
            "/Asset/Apply/1",
            data={"operation": "2" ,\
                  "AssetList": ["1"], \
                   "MoveTo": "chusheng_4", \
                   "Time": "2023-05-24 20:05:45", \
                   "Message":"XXXX"}, \
            content_type="application/json",\
        )


        # 资产管理员调用asset_approval函数的GET方法
        resp2 = c.get(
            "/Asset/Approval/1",\
            content_type="application/json",\
        )

        # 资产管理员调用asset_approval函数的POST方法
        resp3 = c.post(
            "/Asset/Approval/1", 
            data = {"IsApproval": 0,   
                    "Approval" : [2]}, 
            content_type="application/json",
        )

        debug_print("resp2", resp2.json())

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)

    def test_asset_manage_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用asset_manage函数
        resp2 = c.post(
            "/Asset/Manage/1",
            data={"operation": CLEAR, \
                  "AssetList": [1], \
                  "MoveTo":None, \
                  "Type":None},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)

    def test_asset_change_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用asset_change函数
        resp2 = c.post(
            "/Asset/Change/1",
            data={"ID": 1, \
                  "Name": "资产的名称-修改版", \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
    
    def test_define_prop_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        selfproperty = ["显卡型号", "CPU型号", "屏幕大小"]
        # 资产管理员自定义属性
        resp = c.post(
            "/Asset/DefineProp/1",
            data={"AssetClassID": 1, "Property": selfproperty},
            content_type="application/json",
        )

        asset_class = AssetClass.objects.filter(id=1).first()
        debug_print("asset_class_prop", asset_class.selfprop)

        self.assertEqual(resp.json()["code"], 0)
    
    def test_append_type_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        selfproperty = ["显卡型号", "CPU型号", "屏幕大小"]
        # 资产管理员自定义属性
        resp = c.post(
            "/Asset/DefineProp/1",
            data={"AssetClassID": 1, "Property": selfproperty},
            content_type="application/json",
        )

        asset_class = AssetClass.objects.filter(id=1).first()
        debug_print("asset_class_prop", asset_class.selfprop)

        # 资产管理员调用asset_append_type
        resp2 = c.get(
            "/Asset/AppendType/1/1",
            content_type="application/json",
        )

        debug_print("自定义属性", resp2.json()["Property"])

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
    
    def test_modify_label_1(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员修改标签中的显示内容
        resp2 = c.post(
            "/Asset/Label/1/1",
            data={"Name":False, \
                  "ID":False, \
                  "Status":True, \
                  "Owner":False, \
                  "Description":True, \
                  "CreateTime":False}, 
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
    
    def test_modify_label_2(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员修改标签中的显示内容
        resp2 = c.get(
            "/Asset/Label/1/1",
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
    
    def test_asset_multi_append(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用asset_multi_append函数
        resp = c.post(
            "/Asset/MutiAppend/1",
            data={"chusheng" : [{"Name": "资产的名称", \
                  "Type": "分类的名称", \
                  "Number": 100, \
                  "Position": "位置1", \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, \
                  "Property": {"CPU型号": "nvidia", \
                               "GPU型号": "Intel" }}, \
                  {"Name": "资产的名称2", \
                  "Type": "分类的名称", \
                  "Number": 100, \
                  "Position": "位置2", \
                  "Describe": "这是一段对资产的描述2", \
                  "Value": 10.1, \
                  "Property": {"CPU型号": "nvidia", \
                               "GPU型号": "Intel" }}
            ]},
            content_type="application/json",
        )

        # 资产管理员调用add_asset_class函数
        resp1 = c.post(
            "/Asset/AddAssetClass",
            data={"SessionID": "1", "ParentNodeValue": 1, "AssetClassName": "这是一个待添加的资产类别", "NaturalClass": 0},
            content_type="application/json",
        )

        # 资产管理员调用asset_multi_append函数
        resp2 = c.post(
            "/Asset/MutiAppend/1",
            data={"chusheng" : [{"Name": "资产的名称", \
                  "Type": "这是一个待添加的资产类别", \
                  "Number": 100, \
                  "Position": "位置1", \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, \
                  "Property": {"CPU型号": "nvidia", \
                               "GPU型号": "Intel" }}, \
                  {"Name": "资产的名称2", \
                  "Type": "这是一个待添加的资产类别", \
                  "Number": 100, \
                  "Position": "位置2", \
                  "Describe": "这是一段对资产的描述2", \
                  "Value": 10.1, \
                  "Property": {"CPU型号": "nvidia", \
                               "GPU型号": "Intel" }}
            ]},
            content_type="application/json",
        )

        asset_class = AssetClass.objects.filter(name="这是一个待添加的资产类别").first()

        # 资产管理员自定义属性
        selfproperty = ["显卡型号", "CPU型号", "屏幕大小"] 
        resp3 = c.post(
            "/Asset/DefineProp/1",
            data={"AssetClassID": asset_class.id, "Property": selfproperty},
            content_type="application/json",
        )

        # 资产管理员调用asset_multi_append函数
        resp4 = c.post(
            "/Asset/MutiAppend/1",
            data={"chusheng" : [{"Name": "资产的名称", \
                  "Type": "这是一个待添加的资产类别", \
                  "Number": 100, \
                  "Position": "位置1", \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, \
                  "Property": {"CPU型号": "nvidia", \
                               "显卡型号": "Intel" }, \
                   "Time": "2023-05-24 20:05:45"}, \
                  {"Name": "资产的名称2", \
                  "Type": "这是一个待添加的资产类别", \
                  "Number": 100, \
                  "Position": "位置2", \
                  "Describe": "这是一段对资产的描述2", \
                  "Value": 10.1, \
                  "Property": {"CPU型号": "nvidia", \
                               "显卡型号": "Intel" }, \
                   "Time": "2023-05-24 20:05:45"} \
            ]},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 4)
        self.assertEqual(resp2.json()["code"], 5)
        self.assertEqual(resp4.json()["code"], 0)
    
    def test_asset_statistics(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp2 = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称2", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, 
                  "Time":"2023-05-24 20:05:45"},
            content_type="application/json",
        )

        # 资产管理员调用asset_statistics函数
        resp3 = c.get(
            "/Asset/Statistics/1",
            content_type="application/json",
        )

        # 资产管理员调用asset_statistics_fast函数
        resp4 = c.get(
            "/Asset/StatisticsFast/1",
            content_type="application/json",
        )

        # 资产管理员调用asset_statistics_slow函数
        resp5 = c.get(
            "/Asset/StatisticsSlow/1",
            content_type="application/json",
        )

        # 资产管理员调用asset_statistics_real_fast函数
        resp6 = c.get(
            "/Asset/StatisticsRealFast/1",
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)
        self.assertEqual(resp4.json()["code"], 0)
        self.assertEqual(resp5.json()["code"], 0)
        self.assertEqual(resp6.json()["code"], 0)

    def test_user_change_password_1(self):
        c = Client()

        # 用户先登录
        resp = c.post(
            "/User/login",
            data={"UserName": self.u1.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 用户更改密码, 两次输入密码不一致
        resp2 = c.post(
            "/Asset/ChangePassword/1",
            data={ "OldPassword":self.raw_password,"NewPassword1":"yyyyy", "NewPassword2":"zzzzz"},
            content_type="application/json",
        )

        # 用户更改密码, 原密码错误
        resp3 = c.post(
            "/Asset/ChangePassword/1",
            data={ "OldPassword":self.raw_password + '1',"NewPassword1":"yyyyy", "NewPassword2":"yyyyy"},
            content_type="application/json",
        )

        # 用户更改密码, 两次输入密码不一致
        resp4 = c.post(
            "/Asset/ChangePassword/1",
            data={ "OldPassword":self.raw_password,"NewPassword1":"yyyyy", "NewPassword2":"yyyyy"},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 4)
        self.assertEqual(resp3.json()["code"], 3)
        self.assertEqual(resp4.json()["code"], 0)

    
    def test_asset_warn(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp2 = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称2", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, 
                  "Time":"2023-05-24 20:05:45"},
            content_type="application/json",
        )

        resp5 = c.post(
            "/Asset/Warn/1",
            data={"AssetID": 2, \
                  "WarnType" : 1, \
                  "WarnStrategy" : "0年0月1天"},
            content_type="application/json",
        )

        

        # 资产管理员调用asset_warn函数
        resp3 = c.get(
            "/Asset/Warn/1/1/1/Name=/AssetType=/WarnType=",
            content_type="application/json",
        )

        # TODO:增加更多测例
        resp4 = c.get(
            "/Asset/Warn/1/1/1/Name=资产的名称/AssetType=-1/WarnType=-1",
            content_type="application/json",
        )

        # 资产管理员调用asset_warn函数
        resp5 = c.get(
            "/Asset/UserWarn/1/1/1/Name=/AssetType=/WarnType=",
            content_type="application/json",
        )

        # TODO:增加更多测例
        resp6 = c.get(
            "/Asset/UserWarn/1/1/1/Name=资产的名称/AssetType=-1/WarnType=-1",
            content_type="application/json",
        )

        # debug_print("warn_print", resp4.json()["TotalNum"])
        # debug_print("warn_print", resp4.json()["AssetList"])

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)
        self.assertEqual(resp4.json()["code"], 0)
        self.assertEqual(resp5.json()["code"], 0)
        self.assertEqual(resp6.json()["code"], 0)


    def test_asset_warn_set(self):
        c = Client()

        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp2 = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称2", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, 
                  "Time":"2023-05-24 20:05:45"},
            content_type="application/json",
        )

        # 资产管理员调用asset_warn函数
        resp3 = c.post(
            "/Asset/Warn/1",
            data={"AssetID": 1, \
                  "WarnType" : 0, \
                  "WarnStrategy" : 200},
            content_type="application/json",
        )

        resp4 = c.post(
            "/Asset/Warn/1",
            data={"AssetID": 1, \
                  "WarnType" : 1, \
                  "WarnStrategy" : "0年0月1天"},
            content_type="application/json",
        )

        resp5 = c.post(
            "/Asset/Warn/1",
            data={"AssetID": 1, \
                  "WarnType" : 2},
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)
        self.assertEqual(resp4.json()["code"], 0)
        self.assertEqual(resp5.json()["code"], 0)

    def test_info_prop(self):
        c = Client()
        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp2 = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称2", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, 
                  "Time":"2023-05-24 20:05:45"},
            content_type="application/json",
        )

        # 资产管理员调用info_prop函数
        resp3 = c.get(
            "/Asset/InfoProp/1/xxxx/yyyy", 
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)
    
    def test_info_search(self):
        c = Client()
        # 资产管理员先登录
        c.post(
            "/User/login",
            data={"UserName": self.u3.name, "Password": self.raw_password, "SessionID": "1"},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10},
            content_type="application/json",
        )

        # 资产管理员调用add_asset函数
        resp2 = c.post(
            "/Asset/Append/1",
            data={"Name": "资产的名称2", \
                  "Type": 4, \
                  "Parent":None, \
                  "Number": 100, \
                  "Position": 1, \
                  "Describe": "这是一段对资产的描述", \
                  "Value": 10, 
                  "Time":"2023-05-24 20:05:45"},
            content_type="application/json",
        )

        # 资产管理员调用info_search函数
        resp3 = c.get(
            "/Asset/Info/1/1/ID=-1/Name=[资产名称]/Class=[资产类别]/Status=-1/Owner=[资产所有者]/Prop=[自定义属性名]/PropValue=[自定义属性值]",
            content_type="application/json",
        )

        self.assertEqual(resp.json()["code"], 0)
        self.assertEqual(resp2.json()["code"], 0)
        self.assertEqual(resp3.json()["code"], 0)
