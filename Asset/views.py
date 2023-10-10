from Asset.models import *
from User.models import *
from utils.utils_request import request_success
from utils.utils_other import list_to_char
from utils.utils_asset import * 
from utils.config import *
from rest_framework.request import Request
from django.http import HttpResponse
from utils.utils_add_data import add_asset_1
from utils.model_date import *
from User.views import *

def modify_department(req: Request, i:int):
    # asset_100 = list(Asset.objects.all())[100 * i: 100 * (i + 1)]
    # for asset in asset_100:
    asset = Asset.objects.filter(id=i).first()
    if asset != None:
        asset.create_time = get_30_days_before()
        asset.save()
    return HttpResponse("i:{}".format(str(i)))


def add_data(req: Request, asset_class_name:str, i:int, j:int, k:int):
    # 增加数据接口
    # add_asset_1()
    # add_user(i,j,k)
    add_asset_final(asset_class_name, i, j, k)
    # ac0 = AssetClass.objects.filter(id = 1).first()
    return HttpResponse("{} i:{},j:{},k:{}".format(asset_class_name, str(i), str(j), str(k)))

def add_asset_class_url(req:Request, i:int, j:int, k:int):

    add_asset_class_final(i, j, k)
    return HttpResponse("i:{},j:{},k:{}".format(str(i), str(j), str(k)))


def _add_asset_class(usr:User, data):

    # 判断是否存在同名的资产分类
    same_name = AssetClass.objects.filter(name = data["AssetClassName"], department = usr.department)
    if(len(same_name) != 0):
        return request_failed(4, "该部门内存在同名资产分类")


    # natural_class = data["NaturalClass"]
    # if natural_class == 0:
    #     property = 1
    # elif natural_class == 1:
    #     property = 4
    # elif natural_class == 2:
    #     property = 3
    # else:
    #     raise KeyError

    parent_asset_class = get_asset_class(data["ParentNodeValue"])

    # if parent_asset_class.property == 0:
    #     return request_failed(5, "该位置不能添加资产分类")
    # else:
    #     grand_parent_asset_class = parent_asset_class.parent
    #     if grand_parent_asset_class.property == 0:
    #         return request_failed(5, "该位置不能添加资产分类")

    if parent_asset_class.property == 3:
        property = 3
    elif parent_asset_class.property == 4:
        property = 4
    else:
        property = 3

    asset_class = AssetClass.objects.create(
        department = usr.department, name = data["AssetClassName"], \
        parent = parent_asset_class, children = "", \
        property = property, loss_style = data["LossStyle"]
    )

    # 修改父亲节点的children
    parent_asset_class.children += ('$' + str(asset_class.id))
    parent_asset_class.save()
    Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                       more_info="资产管理员 " + usr.name + " 创建了资产分类 " + asset_class.name)
    return request_success()

def _modify_asset_class(usr: User, data):

    # 判断是否存在同名的资产分类
    same_name = AssetClass.objects.filter(name = data["AssetClassName"], department = usr.department)

    if (len(same_name) != 0) and (same_name.first().id != int(data["NodeValue"])):
        return request_failed(4, "该部门内存在同名资产分类")
    
    # natural_class = data["NaturalClass"]
    asset_class = AssetClass.objects.filter(id=data["NodeValue"]).first()

    if asset_class.property == 0:
        return request_failed(5, "该节点不能修改")
    
    if asset_class.parent.property == 0:
        return request_failed(5, "该节点不能修改")

    # if (asset_class.property == 0) and data["NaturalClass"] != 0:
    #     return request_failed(5, "不能修改根节点的自然分类")

    # if natural_class == 0:
    #     property = 1
    # elif natural_class == 1:
    #     property = 4
    #     if asset_class.children != "":
    #         return request_failed(6, "不能修改非叶子为品类")

    # elif natural_class == 2:
    #     property = 3
    #     if asset_class.children != "":
    #         return request_failed(6, "不能修改非叶子为品类")

    # else:
    #     raise KeyError

    # 进行更改
    Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                       more_info="资产管理员 " + usr.name + " 将资产分类 " + asset_class.name + " 修改为 " + data["AssetClassName"])
    asset_class.name = data["AssetClassName"]
    asset_class.loss_style = data["LossStyle"]
    # if (asset_class.property != 0):
    #     asset_class.property = property
    asset_class.save()

    return request_success()

def modify_asset_class(req: Request):
    return AssetWarpper(req=req, function=_modify_asset_class, authority_level=ONLY_ASSET_ADMIN, \
        data_require=["AssetClassName", "NodeValue", "LossStyle"])

def _delete_asset_class(user: User, data):
    debug_print("NodeValue", data["NodeValue"])

    # 检查该节点是否存在
    to_delete = AssetClass.objects.filter(id = data["NodeValue"], department = user.department).first()
    if(to_delete == None):
        return request_failed(4, "该节点不存在")
    
    # 检查该节点是否为根节点
    if (to_delete.property == 0):
        return request_failed(5, "该节点位置不能删除")

    if (to_delete.parent.property == 0):
        return request_failed(5, "该节点位置不能删除")

    asset = Asset.objects.filter(Class=to_delete).first()
    if asset != None:
        return request_failed(6, "该节点下面有资产, 不能删除")

    # 之后递归删数据, 因为之后可能还需要检查同名, 所以要把数据真正地删掉
    subtree_list = []
    subtree_list = give_subtree_list_recursive(asset_class_id=data["NodeValue"], department_id=user.department.id, subtree_list=subtree_list)
    debug_print("subtree_list", subtree_list)

    # 修改父节点的children:
    parent_node = AssetClass.objects.filter(id = to_delete.parent.id).first()
    new_children_string = delete_child(parent_node.children, data["NodeValue"])
    parent_node.children = new_children_string
    parent_node.save()


    # 删除 subtree_list 中的资产分类
    Log.objects.create(type=ASSET_MANAGE,user_name=user.name,entity_name=user.entity.name,
                       more_info="资产管理员 " + user.name + " 删除了资产分类 " + to_delete.name + " 极其子分类")
    for sub_node in subtree_list:
        AssetClass.objects.filter(id = sub_node).delete()
    
    return request_success()


def delete_asset_class(req: Request, SessionID:str, NodeValue: int):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["NodeValue"] = NodeValue
    return AssetWarpper(req=req, function=_delete_asset_class, authority_level=ONLY_ASSET_ADMIN, \
        data_pass=data_pass)
    

def add_asset_class(req: Request):

    return AssetWarpper(req=req, function=_add_asset_class, authority_level=ONLY_ASSET_ADMIN, \
        data_require=["AssetClassName", "ParentNodeValue", "LossStyle"])



def _give_tree(usr, data=None):
    # 根据这个usr的department_id来给出这个department的资产分类树
    
    # 找到这个department的根节点
    rootNode = AssetClass.objects.filter(department = usr.department, property = 0).first()

    treeData = {}
    
    add_info = ""
    # if (rootNode.property == 0) or (rootNode.property == 1) or (rootNode.property == 2):
    #     add_info = ""
    # elif rootNode.property == 3:
    #     add_info = " [条目型品类]"
    # elif rootNode.property == 4:
    #     add_info = " [数量型品类]"
    # else:
    #     raise KeyError

    treeData['title'] = str(rootNode.name + add_info)
    treeData['value'] = rootNode.id

    children = []
    # 遍历这个根节点的孩子节点
    children_list = parse_children(rootNode.children)
    for child_id in children_list:
        children.append(give_subtree_recursive(child_id, usr.department.id))
    treeData['children'] = children

    return request_success({"treeData":[treeData]})

def _give_department_tree(usr: User, data):
    user_name = data["UserName"]
    # 根据这个user找到对应的department
    user = User.objects.filter(name=user_name).first()
    
    # 照抄上面那个函数
    # 找到这个department的根节点
    rootNode = AssetClass.objects.filter(department = user.department, property = 0).first()

    treeData = {}
    
    add_info = ""
    # if (rootNode.property == 0) or (rootNode.property == 1) or (rootNode.property == 2):
    #     add_info = ""
    # elif rootNode.property == 3:
    #     add_info = " [条目型品类]"
    # elif rootNode.property == 4:
    #     add_info = " [数量型品类]"
    # else:
    #     raise KeyError

    treeData['title'] = str(rootNode.name + add_info)
    treeData['value'] = rootNode.id

    children = []
    # 遍历这个根节点的孩子节点
    children_list = parse_children(rootNode.children)
    for child_id in children_list:
        children.append(give_subtree_recursive(child_id, user.department.id))
    treeData['children'] = children

    return request_success({"treeData":[treeData]})

def give_department_tree(req: Request):
    data_require = ["UserName"]
    return AssetWarpper(req=req, function=_give_department_tree, authority_level=None, data_require=data_require)

def give_tree(req: Request):
    return AssetWarpper(req=req, function=_give_tree, authority_level=ONLY_ASSET_ADMIN)

def _superuser_create(usr, data):
    UserName = data["UserName"]
    EntityName = data["EntityName"]

    # 如果该用户本来就存在
    filtered_user = User.objects.filter(name=UserName).first()
    if(filtered_user != None):
        return request_failed(4, "存在重复用户名")
    
    # 如果存在重复业务实体
    filtered_entity = Entity.objects.filter(name=EntityName).first()
    if(filtered_entity != None):
        return request_failed(5, "存在重复业务实体")

    # 新建一个entity
    e1 = Entity.objects.create(name = EntityName)

    # TODO: 随机设置一个密码, 先使用固定密码yiqunchusheng
    raw_password = "yiqunchusheng"

    # 新建一个系统管理员
    User.objects.create(
        name = UserName ,password = sha256(MD5(raw_password)),
        entity = e1 ,department= None,
        super_administrator = 0,system_administrator = 1, asset_administrator=0,
        function_string = "0000000000000011111100"
    )

    # 新建内部应用

    App.objects.create(name="用户列表",path="/user/system_manager",authority=1,entity=e1)
    App.objects.create(name="角色管理",path="/user/system_manager",authority=1,entity=e1)
    App.objects.create(name="部门管理",path="/user/system_manager/department",authority=1,entity=e1)
    App.objects.create(name="应用管理",path="/user/system_manager/application",authority=1,entity=e1)
    App.objects.create(name="操作日志",path="/user/system_manager/log",authority=1,entity=e1)

    App.objects.create(name="资产审批",path="/user/asset_manager/apply_approval",authority=2,entity=e1)
    App.objects.create(name="资产定义",path="/user/asset_manager/asset_define",authority=2,entity=e1)
    App.objects.create(name="资产录入",path="/user/asset_manager/asset_add",authority=2,entity=e1)
    App.objects.create(name="资产变更",path="/user/asset_manager/asset_change",authority=2,entity=e1)
    App.objects.create(name="资产查询",path="/user/asset_manager/asset_info",authority=2,entity=e1)
    App.objects.create(name="资产清退",path="/user/asset_manager/asset_info",authority=2,entity=e1)
    App.objects.create(name="资产调拨",path="/user/asset_manager/asset_info",authority=2,entity=e1)
    App.objects.create(name="资产统计",path="/user/asset_manager/asset_statistic",authority=2,entity=e1)
    App.objects.create(name="资产告警",path="/user/asset_manager/asset_warn",authority=2,entity=e1)

    App.objects.create(name="资产查看",path="/user/employee",authority=3,entity=e1)
    App.objects.create(name="资产领用",path="/user/employee",authority=3,entity=e1)
    App.objects.create(name="资产退库",path="/user/employee",authority=3,entity=e1)
    App.objects.create(name="资产维保",path="/user/employee",authority=3,entity=e1)
    App.objects.create(name="资产转移",path="/user/employee",authority=3,entity=e1)

    Log.objects.create(type=ENTITY_MANAGE,user_name=usr.name,entity_name=e1.name,
                       more_info="超级管理员 " + usr.name + " 创建了业务实体 " + e1.name + " 并委派 " + UserName + "做为系统管理员")
    return request_success()


def superuser_create(req: Request):
    return AssetWarpper(req=req, function=_superuser_create, authority_level=ONLY_SUPER_ADMIN, \
        data_require=["UserName", "EntityName"])


def _superuser_delete(usr, data):
    entity_name = data["entity_name"]

    # 找到该实体进行删除
    filtered_entity = Entity.objects.filter(name=entity_name).first()
    if(filtered_entity == None):
        return request_failed(4, "实体不存在")
    Log.objects.create(type=ENTITY_MANAGE,user_name=usr.name,entity_name=entity_name,
                       more_info="超级管理员 " + usr.name + " 删除了业务实体 " + entity_name)
    Entity.objects.filter(name=entity_name).delete()
    # 所有与该实体关联的用户应该也都级联删除了
    return request_success()  

def superuser_delete(req: Request, SessionID: str, EntityName: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["entity_name"] = EntityName
    return AssetWarpper(req=req, function=_superuser_delete, authority_level=ONLY_SUPER_ADMIN, data_pass=data_pass)

def _superuser_info(usr, data=None):

    # 把所有的业务实体和对应的系统管理员都返回

    # 筛选出所有系统管理员
    system_user_list = User.objects.filter(system_administrator=1)
    entity_manager = []
    for system_user in system_user_list:
        item = {}
        # item[system_user.entity.name] = system_user.name
        item["Entity"] = system_user.entity.name
        item["Manager"] = system_user.name
        item["ID"] = system_user.entity.id
        entity_manager.append(item)
    return_data = {}
    return_data["entity_manager"] = entity_manager
    # 新增返回飞书制定部门
    feishu_dict = {}
    f1 = Feishu.objects.filter(id=1).first()
    if f1:
        feishu_dict["ID"] = f1.feishu_department
        d1 = Department.objects.filter(id=f1.feishu_department).first()
        if d1:
            feishu_dict["Name"] = d1.name
    return_data["FeishuDepartment"] = feishu_dict
    return request_success(return_data)

def superuser_info(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    return AssetWarpper(req=req, function=_superuser_info, authority_level=ONLY_SUPER_ADMIN, data_pass=data_pass)

def _add_asset(usr:User, data=None):
    # TODO 检查同名资产
    name = data["Name"]

    # 根据type得到AssetClass
    asset_class_id = data["Type"]
    asset_class = AssetClass.objects.filter(id=asset_class_id, department=usr.department).first()
    if asset_class == None:
        return request_failed(4, "该部门不存在此资产分类")

    if asset_class.property == 0:
        return request_failed(5, "该位置不能加资产")
    
    if asset_class.parent.property == 0:
        return request_failed(5, "该位置不能加资产")

    parent_asset_id = data["Parent"]
    if parent_asset_id == None:
        parent = None
    else:
        parent = Asset.objects.filter(id=parent_asset_id).first()
    
    property = data["Property"]
    if property != None:
        if type(property) == dict and bool(property) == True:
            # 如果类型是dict, 且不为空
            self_prop = dict_to_selfprop(property)

            a1 = Asset.objects.create(parent=parent, \
                            name=name, \
                            Class=asset_class, \
                            user=usr, \
                            department=usr.department, \
                            price=data["Value"], \
                            description=data["Describe"], \
                            position=data["Position"], \
                            number=data["Number"], \
                            property=self_prop, \
                            expire=time_string_to_datetime(data))
            PendingRequests.objects.create(asset=a1,result=APPROVAL,review_time=get_datetime(),
                                           type=LR,initiator=usr,asset_admin=usr)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                               more_info="资产管理员 " + usr.name + " 录入资产 " + a1.name)
            
        else:
            a1 = Asset.objects.create(parent=parent, \
                            name=name, \
                            Class=asset_class, \
                            user=usr, \
                            department=usr.department, \
                            price=data["Value"], \
                            description=data["Describe"], \
                            position=data["Position"], \
                            number=data["Number"], \
                            expire=time_string_to_datetime(data))
            PendingRequests.objects.create(asset=a1,result=APPROVAL,review_time=get_datetime(),
                                           type=LR,initiator=usr,asset_admin=usr)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                               more_info="资产管理员 " + usr.name + " 录入资产 " + a1.name)

    else:
        a1 = Asset.objects.create(parent=parent, \
                            name=name, \
                            Class=asset_class, \
                            user=usr, \
                            department=usr.department, \
                            price=data["Value"], \
                            description=data["Describe"], \
                            position=data["Position"], \
                            number=data["Number"], \
                            expire=time_string_to_datetime(data))
        PendingRequests.objects.create(asset=a1,result=APPROVAL,review_time=get_datetime(),
                                           type=LR,initiator=usr,asset_admin=usr)
        Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                       more_info="资产管理员 " + usr.name + " 录入资产 " + a1.name)


    photo_path = "photos/{}".format(str(a1.id))
    return_data = {}
    return_data["PhotoPath"] = photo_path     
    return request_success(return_data)

def add_asset(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["Name", "Type", "Number", "Position", "Describe", "Value", "Parent", "Property", "Time"]
    return AssetWarpper(req=req, function=_add_asset, authority_level=ONLY_ASSET_ADMIN, \
        data_pass=data_pass, data_require=data_require
        )

def _asset_info(usr: User, data=None):
    
    # 先找到这个user对应的department
    department = usr.department
    # 找出关联到这样部门的所有资产
    # asset_candidates = []

    # asset_all = Asset.objects.filter(status = (IDLE or IN_USE or IN_MAINTAIN))
    # asset_all = Asset.objects.all()
    # asset_all = []
    # asset_idle = list(Asset.objects.filter(status = IDLE))
    # asset_in_use = list(Asset.objects.filter(status = IN_USE))
    # asset_in_maintain = list(Asset.objects.filter(status = IN_MAINTAIN))
    # asset_all.extend(asset_idle)
    # asset_all.extend(asset_in_use)
    # asset_all.extend(asset_in_maintain)

    if usr.asset_administrator == 1:
        # 该人是资产管理员，返回该部门的所有资产
        # for asset in asset_all:
        #     if asset.user.department == department:
        #         asset_candidates.append(asset)
        asset_candidates = Asset.objects.filter(department=department)
    else:
        # 该人是普通员工
        # for asset in asset_all:
        #     if (asset.user.department == department) and ((asset.user.asset_administrator == 1) or (asset.user == usr)):
        #         asset_candidates.append(asset)
        asset_candidates_pre = Asset.objects.filter(department=department)
        asset_candidates = []
        for asset in asset_candidates_pre:
            if (asset.user.asset_administrator == 1) or (asset.user == usr):
                asset_candidates.append(asset)


    return_list = []
    for asset in asset_candidates:

        # 这里可以加自动清退的处理
        if asset.status == RETIRED:
            continue 

        if single_asset_value_update(asset) <= 0:
            # 这个资产应该被自动清退了
            asset_admin = User.objects.filter(asset_administrator=1, department=department).first()
            asset.status = RETIRED
            asset.user = asset_admin
            asset_copy = Asset.objects.filter(id=asset.id).first()
            asset_copy.status = RETIRED
            asset_copy.user = asset_admin
            asset_copy.save()
            PendingResponse.objects.create(employee=asset_copy.user,asset=asset_copy,type=CLR,
                                           more_info="资产 " + asset_copy.name + "被自动清退了")
            Log.objects.create(type=ASSET_MANAGE,user_name=asset_copy.user.name,entity_name=asset_copy.user.entity.name,
                               more_info="资产 " + asset_copy.name + "被自动清退了")
            continue


        return_item = {}
        return_item["Name"] = asset.name
        return_item["ID"] = asset.id
        return_item["Status"] = asset.status
        return_item["Owner"] = asset.user.name
        return_item["Class"] = asset.Class.name
        return_item["Description"] = asset.description
        return_item["CreateTime"] = asset.create_time
        return_item["PropetyName"], return_item["PropetyName"] = parse_selfprop_to_list(asset.property)
        return_item["Number"] = asset.number
        return_item["Time"] = str(asset.expire)
        return_item["Position"] = str(asset.position)
        return_item["Price"] = float(asset.price)
        if asset.Class.property == 4:
            return_item["Type"] = 1
        else:
            return_item["Type"] = 0


        if asset.user.asset_administrator == 1 and asset.status == IDLE:
            return_item["IsReceive"] = 1
        else:
            return_item["IsReceive"] = 0
        
        if asset.user == usr and asset.status == IN_USE:
            return_item["IsReturn"] = 1
            return_item["IsMaintenance"] = 1
            return_item["IsTransfers"] = 1
        else:
            return_item["IsReturn"] = 0
            return_item["IsMaintenance"] = 0
            return_item["IsTransfers"] = 0
        
        return_list.append(return_item)

    return_data = {}
    return_data["Asset"] = return_list

    # 同时还要返回该部门的所有自定义属性
    all_self_prop_list = []
    asset_class_list = AssetClass.objects.filter(department=department)
    for asset_class in asset_class_list:
        all_self_prop_list.extend(parse_children(asset_class.selfprop))
    return_data["DepartmentProp"] = all_self_prop_list

    return request_success(return_data)


def asset_info(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    return AssetWarpper(req=req, function=_asset_info, authority_level=ONLY_ASSET_ADMIN_AND_USER, data_pass=data_pass)

def _asset_apply(usr: User, data=None):

    operation = int(data["operation"])

    move_to = data["MoveTo"]
    participant = User.objects.filter(name=move_to).first()

    if data["Type"] != None and data["Type"] != "":
        new_asset_class = AssetClass.objects.filter(id=int(data["Type"])).first()
    else:
        new_asset_class = None

    # TODO: 这里要不要加用户的限制

    # 筛选出所有资产管理员
    # NOTE:后续可能会去掉这个asset_admin字段
    # asset_admin_list = User.objects.filter(asset_administrator=1)
    # for asset_admin in asset_admin_list:
    #     if asset_admin.department == usr.department:
    #         this_asset_admin = asset_admin
    #         break
    
    this_asset_admin = User.objects.filter(department=usr.department,asset_administrator=1).first()

    for asset_id in data["AssetList"]:
        # 筛选出这个asset
        asset = Asset.objects.filter(id=int(asset_id)).first()
        # 加一个审核资产是否存在的功能
        if(asset == None):
            return request_failed(4, "资产不存在")
        else:
            op = ""
            if operation == RECEIVE:
                op = "领用"
            elif operation == RETURN:
                op = "退库"
            elif operation == MAINTENANCE:
                op = "维保"
            elif operation == TRANSFER:
                op = "转移"
            # 创建PendingRequest
            p1 = PendingRequests.objects.create(initiator=usr, participant=participant, asset=asset, \
                    type=operation, result=PENDING, asset_admin=this_asset_admin, Class=new_asset_class, \
                        apply_number=data["number"], maintain_time=data["Time"], message=data["Message"])         
            # 告诉员工申请已成功提交
            info1 = "您针对资产： " + asset.name + " 的 " + op + " 申请已成功提交至资产管理员 " + this_asset_admin.name + " 处"
            PendingResponse.objects.create(employee=usr,asset=asset,asset_admin=this_asset_admin,type=operation,
                                           more_info=info1)
            send_feishu_message(usr, info1)
            # 告诉资产管理员有新的待办审批
            info2 = usr.name + " 针对资产： " + asset.name + " 提出了 " + op + " 申请"
            PendingResponse.objects.create(employee=this_asset_admin,asset_admin=usr,asset=asset,type=operation,
                                           more_info=info2)
            send_feishu_message(this_asset_admin, info2)
            if usr.open_id and this_asset_admin.open_id:
                send_feishu_apply(p1, op)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                               more_info="员工 " + usr.name + " 针对资产： " + asset.name  + " 向资产管理员 " + this_asset_admin.name + " 提出了 " + op + " 申请")
    
    return request_success()

def asset_apply(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["operation", "AssetList", "MoveTo", "Type", "number", "Time", "Message"]
    return AssetWarpper(req=req, function=_asset_apply, authority_level=None, data_require=data_require, data_pass=data_pass)


def _asset_approval_get(usr: User, data=None):
    # 找出与这个资产管理员相关的请求
    return_list = []
    # all_pending_requests = PendingRequests.objects.all()
    all_pending_requests = PendingRequests.objects.filter(asset_admin=usr, result=PENDING)
    # department = usr.department
    for pending_request in all_pending_requests:
        # pending_request_department = pending_request.initiator.department
        # if pending_request_department == department and pending_request.result == PENDING:
            
        print("get_1")

        asset = pending_request.asset
        
        # TODO: 检查该资产是否存在
        # if asset == None:
        #     return request_failed(4,"该资产不存在")
        assert asset != None, "资产不存在"
        # TODO: 之后要限制有资产申请涉及的资产不能删除

        print("get_2")

        return_item = {}
        return_item["ApplyID"] = pending_request.id
        return_item["Name"] = asset.name
        return_item["AssetID"] = asset.id
        return_item["ApplyTime"] = pending_request.request_time
        return_item["Operation"] = pending_request.type
        return_item["FromPerson"] = asset.user.name
        # if pending_request.participant == None:
        #     return_item["ToPerson"] = None
        # else:
        #     return_item["ToPerson"] = pending_request.participant.name

        print("get_3")
        if pending_request.type == RECEIVE:
            return_item["ToPerson"] = pending_request.initiator.name
        elif pending_request.type == RETURN:
            return_item["ToPerson"] = pending_request.asset_admin.name
        elif pending_request.type == MAINTENANCE:
            return_item["ToPerson"] = pending_request.asset_admin.name
        elif pending_request.type == TRANSFER:
            return_item["ToPerson"] = pending_request.participant.name
        else:
            print("出错了")
            raise KeyError

        print("get_4")

        return_item["Applicant"] = pending_request.initiator.name
        if validate_request(asset, pending_request) > 0:
            return_item["Valid"] = 1
        else:
            return_item["Valid"] = 0
        
        print("get_5")
        if pending_request.message == None:
            return_item["Message"] = None
        else:
            return_item["Message"] = str(pending_request.message)

        return_list.append(return_item)

    return_data = {}
    return_data["ApprovalList"] = return_list
    return_list.reverse()
    return request_success(return_data)

def _asset_approval_post(usr: User, data):
    IsApproval = data["IsApproval"]
    Approval = data["Approval"]
    if IsApproval == 0:
        for pending_request_id in Approval:
            pending_request = PendingRequests.objects.filter(id = int(pending_request_id)).first()
            if(pending_request == None or pending_request.result != PENDING):
                return request_failed(4, "某条资产申请不存在或者已审批")
            else:
                # 将这条pending_result的结果置为0
                disapprove(pending_request)
                # 同步更改飞书卡片
                if pending_request.message_id:
                    change_feishu_apply(pending_request,0)
    elif IsApproval == 1:
        for pending_request_id in Approval:
            pending_request = PendingRequests.objects.filter(id = int(pending_request_id)).first()
            if(pending_request == None or pending_request.result != PENDING):
                return request_failed(4, "某条资产申请不存在或者已审批")
            if validate_request(pending_request.asset, pending_request) < 0:
                error_info = "第" + str(pending_request_id) + "条申请与之前申请冲突"
                return request_failed(5, error_info)
            else:
                approve(pending_request) 
                # 同步更改飞书卡片
                if pending_request.message_id:
                    change_feishu_apply(pending_request,1)  

    return request_success()
    
def asset_approval(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    if req.method == 'GET':
        return AssetWarpper(req=req, function=_asset_approval_get, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)
    if req.method == 'POST':
        data_require = ["IsApproval", "Approval"]
        return AssetWarpper(req=req, function=_asset_approval_post, authority_level=ONLY_ASSET_ADMIN, data_require=data_require, data_pass=data_pass)

def _asset_manage(usr:User, data):
    for asset_id in data["AssetList"]:
        # 根据这个asset_id来筛选出对应的asset
        asset = Asset.objects.filter(id=int(asset_id)).first()

        if data["operation"] == CLEAR:
            # 将这个资产的status设置为RETIRED
            asset.status = RETIRED
            asset.user = usr
            asset.save()
            # 记录资产历史
            PendingRequests.objects.create(initiator=usr,asset=asset,type=CLR,
                                           result=APPROVAL,review_time=get_current_time(),
                                           asset_admin=usr)
            PendingResponse.objects.create(employee=asset.user,asset=asset,type=CLR,
                                           more_info="资产管理员 " + usr.name + " 清退了资产 " + asset.name)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                               more_info="资产管理员 " + usr.name + " 清退了资产 " + asset.name)
        
        elif data["operation"] == END_MAINTAIN:
            # 还给之前那个员工, 这步暂时不需要
            asset.status = IN_USE
            asset.save()
            # 记录资产历史
            PendingRequests.objects.create(initiator=usr,asset=asset,type=END_M,participant=asset.user,
                                           result=APPROVAL,review_time=get_current_time(),
                                           asset_admin=usr)
             # 退还维保后通知员工
            info1 = "您的资产： " + asset.name + " 已完成维保"
            PendingResponse.objects.create(employee=asset.user,asset_admin=usr,asset=asset,type=END_M,
                                           more_info=info1)
            send_feishu_message(asset.user,info1)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                               more_info="资产管理员 " + usr.name + " 完成了资产 " + asset.name + " 的维保")
        
        elif data["operation"] == ALLOCATE:
            # 资产调拨
            # 检查该资产是否闲置
            if asset.status != IDLE or asset.user.asset_administrator != 1:
                return request_failed(4, "调拨资产非闲置")
            
            move_to = User.objects.filter(name=data["MoveTo"]).first()
            asset.user = move_to
             # 检查move_to这个用户是不是资产管理员
            if move_to.asset_administrator != 1:
                return request_failed(5, "调拨给了非资产管理员")
            
            type = AssetClass.objects.filter(id=int(data["Type"])).first()
            asset.Class = type
            
            # 修改调拨之后资产所属的部门
            asset.department = move_to.department

            # TODO: 考虑资产的父子关系

            asset.save()
            # 记录资产历史
            PendingRequests.objects.create(initiator=usr,asset=asset,type=ALCT,participant=move_to,
                                           result=APPROVAL,review_time=get_current_time(),
                                           asset_admin=usr)
             # 通知另一个资产管理员
            info2 = "资产： " + asset.name + " 已从资产管理员 " + usr.name + " 的部门转移至您的部门"
            PendingResponse.objects.create(employee=move_to,asset_admin=usr,asset=asset,type=ALCT,
                                           more_info=info2)
            send_feishu_message(move_to,info2)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                               more_info="资产管理员 " + usr.name + " 将资产 " + asset.name + " 调拨给了资产管理员 " + move_to.name)
            
        else:
            raise KeyError
        
        # 我把这句话放在了前面的if里，改完资产的属性我才好定义pendingrequest -- by 邹作休
        # asset.save()

    return request_success()

def asset_manage(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["operation", "AssetList", "MoveTo", "Type"]
    return AssetWarpper(req=req, function=_asset_manage, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass, data_require=data_require)

def _asset_change(usr: User, data):

    # 根据ID筛选出对应的资产
    asset = Asset.objects.filter(id=int(data["ID"])).first()

    asset.name = data["Name"]
    asset.number = data["Number"]
    asset.position = data["Position"]
    asset.description = data["Describe"]
    asset.price = data["Value"]

    # 筛选出新的"父资产"
    if data["Parent"] == None:
        asset.parent = None
    else:
        parent_asset = Asset.objects.filter(id=int(data["Parent"])).first()
        asset.parent = parent_asset
    
    asset.save()
    PendingRequests.objects.create(asset=asset,result=APPROVAL,review_time=get_datetime(),
                                   type=BG,initiator=usr,asset_admin=usr)
    Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                       more_info="资产管理员 " + usr.name + " 变更了资产 " + asset.name)
    return request_success()


def asset_change(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["ID", "Name", "Number", "Position", "Describe", "Value", "Parent"]
    return AssetWarpper(req=req, function=_asset_change, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass, data_require=data_require)

def _define_prop(usr:User, data):

    # TODO:ban掉根节点和数量型资产、条目型资产这3个

    asset_class_id = data["AssetClassID"]
    asset_class = AssetClass.objects.filter(id=asset_class_id).first()

    property_list = data["Property"]
    
    # 首先检查property之中有没有美元符号
    for property in property_list:
        if '$' in property:
            return request_failed(4, "自定义属性中不能有特殊字符$")
        
    # 检查property有没有重复
    compress_list = list(set(property_list))
    if len(compress_list) < len(property_list):
        return request_failed(5, "统一资产分类自定义属性不能同名")
    
    if asset_class.selfprop == None:
        asset_class.selfprop = split_by_dollar(property_list)
    else:
        asset_class.selfprop = str(asset_class.selfprop) + split_by_dollar(property_list)
    asset_class.save()
    Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                       more_info="资产管理员 " + usr.name + " 在资产分类 " + asset_class.name + " 中新增了资产自定义属性 " + " ".join(property_list))

    return request_success()

def define_prop(req: Request, SessionID: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["AssetClassID", "Property"]
    return AssetWarpper(req=req, function=_define_prop, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass, data_require=data_require)

def _asset_append_type(usr: User, data):
    asset_class = AssetClass.objects.filter(id=data["asset_class_id"]).first()
    return_data = {}
    return_data["Property"] = parse_children(asset_class.selfprop)

    return request_success(return_data)

def asset_append_type(req: Request, SessionID: str, Type: str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["asset_class_id"] = int(Type)
    return AssetWarpper(req=req, function=_asset_append_type, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def _info_prop(usr:User, data):
    # 先找到这个user对应的department
    department = usr.department
    # 找出关联到这样部门的所有资产
    # asset_candidates = []

    # asset_all = Asset.objects.filter(status = (IDLE or IN_USE or IN_MAINTAIN))
    # asset_all = Asset.objects.all()
    # asset_all = []
    # asset_idle = list(Asset.objects.filter(status = IDLE))
    # asset_in_use = list(Asset.objects.filter(status = IN_USE))
    # asset_in_maintain = list(Asset.objects.filter(status = IN_MAINTAIN))
    # asset_all.extend(asset_idle)
    # asset_all.extend(asset_in_use)
    # asset_all.extend(asset_in_maintain)

    if usr.asset_administrator == 1:
        # 该人是资产管理员，返回该部门的所有资产
        # for asset in asset_all:
        #     if asset.user.department == department:
        #         asset_candidates.append(asset)
        asset_candidates = Asset.objects.filter(department=department)
    else:
        # 该人是普通员工
        # for asset in asset_all:
        #     if (asset.user.department == department) and ((asset.user.asset_administrator == 1) or (asset.user == usr)):
        #         asset_candidates.append(asset)
        asset_candidates_pre = Asset.objects.filter(department=department)
        asset_candidates = []
        for asset in asset_candidates_pre:
            if (asset.user.asset_administrator == 1) or (asset.user == usr):
                asset_candidates.append(asset)

    return_list = []
    for asset in asset_candidates:

        # 除去已经deleted的资产
        if (asset.status == DELETED) or (asset.status == RETIRED):
            continue

        if valid_prop(asset, data["Prop"], data["PropValue"]) == 0:
            continue

        return_item = {}
        return_item["Name"] = asset.name
        return_item["ID"] = asset.id
        return_item["Status"] = asset.status
        return_item["Owner"] = asset.user.name
        return_item["Description"] = asset.description
        return_item["CreateTime"] = asset.create_time
        return_item["PropetyName"], return_item["PropetyName"] = parse_selfprop_to_list(asset.property)

        if asset.user.asset_administrator == 1 and asset.status == IDLE:
            return_item["IsReceive"] = 1
        else:
            return_item["IsReceive"] = 0
        
        if asset.user == usr and asset.status == IN_USE:
            return_item["IsReturn"] = 1
            return_item["IsMaintenance"] = 1
            return_item["IsTransfers"] = 1
        else:
            return_item["IsReturn"] = 0
            return_item["IsMaintenance"] = 0
            return_item["IsTransfers"] = 0
        
        return_list.append(return_item)

    return_data = {}
    return_data["Asset"] = return_list

    # 同时还要返回该部门的所有自定义属性
    all_self_prop_list = []
    asset_class_list = AssetClass.objects.filter(department=department)
    for asset_class in asset_class_list:
        all_self_prop_list.extend(parse_children(asset_class.selfprop))
    return_data["DepartmentProp"] = all_self_prop_list
    
    return request_success(return_data)



def info_prop(req: Request, SessionID: str, Prop:str, PropValue:str):
    # 根据自定义属性来查询资产信息
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["Prop"] = Prop
    data_pass["PropValue"] = PropValue
    return AssetWarpper(req=req, function=_info_prop, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def _modify_label_post(usr:User, data):

    asset_id = data["asset_id"]

    string_label = bool_to_string_label(data)

    # 根据这个asset_id来找对应的资产
    asset = Asset.objects.filter(id=asset_id).first()

    asset.label_visible = string_label
    asset.save()

    debug_print("asset.label_visible", asset.label_visible)

    return request_success()

def _modify_label_get(usr:User, data):

    # 先根据asset_id将这个资产找到对应资产
    asset = Asset.objects.filter(id=data["asset_id"]).first()


    if asset == None:
        return request_failed(4, "当前资产不存在")
    
    label_dict = {}

    if asset.label_visible[0] == '1':
        # Name属性
        label_dict["资产名称"] = asset.name
    if asset.label_visible[1] == '1':
        # ID属性
        label_dict["资产分类"] = str(asset.Class)
    if asset.label_visible[2] == '1':
        # Status属性
        if asset.status == IDLE:
            label_dict["状态"] = "闲置中"
        if asset.status == IN_USE:
            label_dict["状态"] = "使用中"
        if asset.status == IN_MAINTAIN:
            label_dict["状态"] = "维保中"
        if asset.status == RETIRED:
            label_dict["状态"] = "已清退"
        if asset.status == DELETED:
            label_dict["状态"] = "已删除"
    if asset.label_visible[3] == '1':
        # Owner属性
        label_dict["当前所有者"] = asset.user.name
    if asset.label_visible[5] == '1':
        label_dict["创建时间"] = str(asset.create_time)[:19]
    if asset.label_visible[4] == '1':
        # Description属性
        label_dict["资产描述"] = asset.description
    
    
    draw_label("https://cs-company-frontend-cses.app.secoder.net/assets?id={}".format(str(asset.id)), label_dict)
    img_url = AliyunOss().put_object_from_file("asset_label/{}.png".format(str(asset.id)), "label.jpg")
    # 然后把这张图片上传到OSS中

    return_data = {}
    return_data["name"] = img_url

    debug_print("get_label", return_data)
    return request_success(return_data)

def modify_label(req: Request, SessionID:str, AssetID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["asset_id"] = int(AssetID)
    data_require = ["Name", "Class", "Status", "Owner", "Description", "CreateTime"]
    if req.method == 'POST':
        return AssetWarpper(req=req, function=_modify_label_post, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass, data_require=data_require)
    if req.method == 'GET':
        return AssetWarpper(req=req, function=_modify_label_get, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def _asset_multi_append(usr:User, data=None):
    # TODO:检查资产名称

    asset_list = data["chusheng"]  # 待添加的资产列表
    asset_idx = 0

    # 先遍历，检查一遍
    for asset_info in asset_list:

        asset_idx += 1

        name = asset_info["Name"]

        # 根据type得到AssetClass
        asset_class_name = asset_info["Type"]
        asset_class = AssetClass.objects.filter(name=asset_class_name, department=usr.department).first()
        if asset_class == None:
            return request_failed(4, "第{}个资产：该部门不存在{}资产分类".format(str(asset_idx), asset_class_name))
        
        # 再检查property是否合法
        property = asset_info["Property"]
        if property != None:
            # 说明property肯定是一个dict
            for key, value in property.items():
                asset_class_selfprop_list = parse_children(asset_class.selfprop)
                if key in asset_class_selfprop_list:
                    pass
                else:
                    return request_failed(5, "第{}个资产：不存在{}自定义属性".format(str(asset_idx), str(key))) 

    # 再遍历，真正地写入数据库
    for asset_info in asset_list:
        name = asset_info["Name"]
        # 根据type得到AssetClass
        asset_class_name = asset_info["Type"]
        asset_class = AssetClass.objects.filter(name=asset_class_name, department=usr.department).first()

        property = asset_info["Property"]
        if property != None:
            if type(property) == dict and bool(property) == True:
                # 如果类型是dict, 且不为空
                self_prop = dict_to_selfprop(property)

                a1 = Asset.objects.create(parent=None, \
                                name=name, \
                                Class=asset_class, \
                                user=usr, \
                                price=asset_info["Value"], \
                                description=asset_info["Describe"], \
                                position=asset_info["Position"], \
                                number=asset_info["Number"], \
                                property=self_prop, \
                                expire=time_string_to_datetime(asset_info))
                PendingRequests.objects.create(asset=a1,result=APPROVAL,review_time=get_datetime(),
                                            type=LR,initiator=usr,asset_admin=usr)
                Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                                more_info="资产管理员 " + usr.name + " 录入资产 " + a1.name)
                
            else:
                a1 = Asset.objects.create(parent=None, \
                                name=name, \
                                Class=asset_class, \
                                user=usr, \
                                price=asset_info["Value"], \
                                description=asset_info["Describe"], \
                                position=asset_info["Position"], \
                                number=asset_info["Number"])
                PendingRequests.objects.create(asset=a1,result=APPROVAL,review_time=get_datetime(),
                                            type=LR,initiator=usr,asset_admin=usr)
                Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                                more_info="资产管理员 " + usr.name + " 录入资产 " + a1.name)

        else:
            a1 = Asset.objects.create(parent=None, \
                                name=name, \
                                Class=asset_class, \
                                user=usr, \
                                price=asset_info["Value"], \
                                description=asset_info["Describe"], \
                                position=asset_info["Position"], \
                                number=asset_info["Number"])
            PendingRequests.objects.create(asset=a1,result=APPROVAL,review_time=get_datetime(),
                                            type=LR,initiator=usr,asset_admin=usr)
            Log.objects.create(type=ASSET_MANAGE,user_name=usr.name,entity_name=usr.entity.name,
                        more_info="资产管理员 " + usr.name + " 录入资产 " + a1.name)


    return request_success()

def asset_multi_append(req: Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["chusheng"]
    return AssetWarpper(req=req, function=_asset_multi_append, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass, data_require=data_require)



def _asset_statistics(usr:User, data=None):

    # 维护下面这几个变量:
    # 数量型资产
    num_total_num = 0 
    num_kind_num = 0    
    num_in_maintain_num = 0
    num_in_use_num = 0
    num_idle_num = 0
    num_retire_num = 0

    # 条目型资产
    item_total_num = 0
    item_in_maintain_num = 0
    item_in_use_num = 0
    item_idle_num = 0
    item_retire_num = 0

    # 资产价值
    num_value_list = [0.0]*15
    item_value_list = [0.0]*15

    # 先找到这个user对应的department
    department = usr.department
    asset_department = Asset.objects.filter(department=department)

    for asset in asset_department:

        if asset.status == IN_MAINTAIN:

            if asset.Class.property == 3:
                # 条目型资产
                item_in_maintain_num += 1

                asset_value_list = single_asset_value(asset)
                # item_value_list = list(map(lambda x, y: x + y, asset_value_list, item_value_list))
                item_value_list = list_add(asset_value_list, item_value_list)

            elif asset.Class.property == 4:
                # 数量型资产
                num_in_maintain_num += asset.number
                num_kind_num += 1
                asset_value_list = single_asset_value(asset)
                
                # num_value_list = list(map(lambda x, y: x + y, asset_value_list, num_value_list))
                num_value_list = list_add(asset_value_list, num_value_list)
 
        elif asset.status == IN_USE:

            if asset.Class.property == 3:
                # 条目型资产
                item_in_use_num += 1

                asset_value_list = single_asset_value(asset)
                # item_value_list = list(map(lambda x, y: x + y, asset_value_list, item_value_list))
                item_value_list = list_add(asset_value_list, item_value_list)

            elif asset.Class.property == 4:
                # 数量型资产
                num_in_use_num += asset.number
                num_kind_num += 1
                asset_value_list = single_asset_value(asset)
                # num_value_list = list(map(lambda x, y: x + y, asset_value_list, num_value_list))
                num_value_list = list_add(asset_value_list, num_value_list)


        elif asset.status == RETIRED:
            if asset.Class.property == 3:
                # 条目型资产
                item_retire_num += 1
            elif asset.Class.property == 4:
                # 数量型资产
                num_retire_num += asset.number
                num_kind_num += 1
    
        elif asset.status == IDLE:

            if asset.Class.property == 3:
                # 条目型资产
                item_idle_num += 1

                asset_value_list = single_asset_value(asset)
                # item_value_list = list(map(lambda x, y: x + y, asset_value_list, item_value_list))
                item_value_list = list_add(asset_value_list, item_value_list)

            elif asset.Class.property == 4:
                # 数量型资产
                num_idle_num += asset.number
                num_kind_num += 1
                asset_value_list = single_asset_value(asset)
                # num_value_list = list(map(lambda x, y: x + y, asset_value_list, num_value_list))
                num_value_list = list_add(asset_value_list, num_value_list)
    
    num_total_num = num_in_maintain_num + num_in_use_num + num_idle_num + num_retire_num
    item_total_num = item_in_maintain_num + item_in_use_num + item_idle_num + item_retire_num

    return_data = {}
    return_data["NumTotalNum"] = num_total_num
    return_data["ItemTotalNum"] = item_total_num
    return_data["NumKindNum"] = num_kind_num
    
    num_proportion_list = []
    num_proportion_list.append({"name":"维保中", "Value": num_in_maintain_num})
    num_proportion_list.append({"name":"使用中", "Value": num_in_use_num})
    num_proportion_list.append({"name":"闲置中", "Value": num_idle_num})
    num_proportion_list.append({"name":"已清退", "Value": num_retire_num})
    return_data["NumProportion"] = num_proportion_list

    item_proportion_list = []
    item_proportion_list.append({"name":"维保中", "Value": item_in_maintain_num})
    item_proportion_list.append({"name":"使用中", "Value": item_in_use_num})
    item_proportion_list.append({"name":"闲置中", "Value": item_idle_num})
    item_proportion_list.append({"name":"已清退", "Value": item_retire_num})
    return_data["ItemProportion"] = item_proportion_list

    days_list = compute_days_list()


    value_list = []
    for i in range(0, 15):
        value_item = {}
        value_item["Date"] = days_list[i]
        value_item["NumValue"] = round(num_value_list[i], 2)
        value_item["ItemValue"] = round(item_value_list[i], 2)
        value_item["TotalValue"] = value_item["NumValue"] + value_item["ItemValue"]
        value_list.append(value_item)
    
    return_data["Value"] = value_list


    debug_print("资产统计", return_data)

    return request_success(return_data)

def _asset_statistics_fast(usr:User, data=None):
    # 维护下面这几个变量:
    # 数量型资产
    num_kind_num = 0
    num_total_num = 0     
    num_in_maintain_num = 0
    num_in_use_num = 0
    num_idle_num = 0
    num_retire_num = 0

    # 条目型资产
    item_total_num = 0
    item_in_maintain_num = 0
    item_in_use_num = 0
    item_idle_num = 0
    item_retire_num = 0

    # 先找到这个user对应的department
    department = usr.department

    asset_in_maintain = Asset.objects.filter(department=department, status=IN_MAINTAIN)
    asset_in_use = Asset.objects.filter(department=department, status=IN_USE)
    asset_idle = Asset.objects.filter(department=department, status=IDLE)
    asset_retire = Asset.objects.filter(department=department, status=RETIRED)

    for asset in asset_in_maintain:
        if asset.Class.property == 3:
            item_in_maintain_num += 1
        elif asset.Class.property == 4:
            num_in_maintain_num += asset.number
            num_kind_num += 1
    
    for asset in asset_in_use:
        if asset.Class.property == 3:
            item_in_use_num += 1
        elif asset.Class.property == 4:
            num_in_use_num += asset.number
            num_kind_num += 1
    
    for asset in asset_idle:
        if asset.Class.property == 3:
            item_idle_num += 1
        elif asset.Class.property == 4:
            num_idle_num += asset.number
            num_kind_num += 1

    for asset in asset_retire:
        if asset.Class.property == 3:
            item_retire_num += 1
        elif asset.Class.property == 4:
            num_retire_num += asset.number
            num_kind_num += 1

    num_total_num = num_in_maintain_num + num_in_use_num + num_idle_num + num_retire_num
    item_total_num = item_in_maintain_num + item_in_use_num + item_idle_num + item_retire_num
    
    return_data = {}
    return_data["NumTotalNum"] = num_total_num
    return_data["ItemTotalNum"] = item_total_num
    return_data["NumKindNum"] = num_kind_num
    
    num_proportion_list = []
    num_proportion_list.append({"name":"维保中", "Value": num_in_maintain_num})
    num_proportion_list.append({"name":"使用中", "Value": num_in_use_num})
    num_proportion_list.append({"name":"闲置中", "Value": num_idle_num})
    num_proportion_list.append({"name":"已清退", "Value": num_retire_num})
    return_data["NumProportion"] = num_proportion_list


    item_proportion_list = []
    item_proportion_list.append({"name":"维保中", "Value": item_in_maintain_num})
    item_proportion_list.append({"name":"使用中", "Value": item_in_use_num})
    item_proportion_list.append({"name":"闲置中", "Value": item_idle_num})
    item_proportion_list.append({"name":"已清退", "Value": item_retire_num})
    return_data["ItemProportion"] = item_proportion_list

    return request_success(return_data)

def _asset_statistics_slow(usr:User, data=None):
    # 资产价值
    num_value_list = [0.0]*15
    item_value_list = [0.0]*15

    # 先找到这个user对应的department
    department = usr.department
    asset_department = Asset.objects.filter(department=department)

    for asset in asset_department:
        if asset.status == RETIRED:
            continue
        if asset.Class.property == 3:
            asset_value_list = single_asset_value(asset)
            # item_value_list = list(map(lambda x, y: x + y, asset_value_list, item_value_list))
            item_value_list = list_add(asset_value_list, item_value_list)
        elif asset.Class.property == 4:
            asset_value_list = single_asset_value(asset) 
            # num_value_list = list(map(lambda x, y: x + y, asset_value_list, num_value_list))
            num_value_list = list_add(asset_value_list, num_value_list)

    days_list = compute_days_list()

    return_data = {}
    value_list = []
    for i in range(0, 15):
        value_item = {}
        value_item["Date"] = days_list[i]
        value_item["NumValue"] = round(num_value_list[i], 2)
        value_item["ItemValue"] = round(item_value_list[i], 2)
        value_item["TotalValue"] = value_item["NumValue"] + value_item["ItemValue"]
        value_list.append(value_item)
    
    return_data["Value"] = value_list


    debug_print("slow_statistics", return_data)
    return request_success(return_data)

def _asset_statistics_real_fast(usr:User, data=None):
    # 先找到这个user对应的department
    department = usr.department

    asset_in_maintain = Asset.objects.filter(department=department, status=IN_MAINTAIN)
    asset_in_use = Asset.objects.filter(department=department, status=IN_USE)
    asset_idle = Asset.objects.filter(department=department, status=IDLE)
    asset_retire = Asset.objects.filter(department=department, status=RETIRED)

    in_maintain_num = len(asset_in_maintain)
    in_use_num = len(asset_in_use)
    idle_num = len(asset_idle)
    retire_num = len(asset_retire)
    total_num = in_maintain_num + in_use_num + idle_num + retire_num

    return_data = {}
    return_data["TotalNum"] = total_num
    proportion_list = []
    proportion_list.append({"name":"维保中", "Value": in_maintain_num})
    proportion_list.append({"name":"使用中", "Value": in_use_num})
    proportion_list.append({"name":"闲置中", "Value": idle_num})
    proportion_list.append({"name":"已清退", "Value": retire_num})
    return_data["Proportion"] = proportion_list
    
    return request_success(return_data)

def asset_statistics(req: Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    return AssetWarpper(req=req, function=_asset_statistics, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)


def asset_statistics_fast(req:Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    return AssetWarpper(req=req, function=_asset_statistics_fast, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def asset_statistics_slow(req:Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    return AssetWarpper(req=req, function=_asset_statistics_slow, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def asset_statistics_real_fast(req:Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    return AssetWarpper(req=req, function=_asset_statistics_real_fast, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def _user_change_password(usr:User, data=None):
    if sha256(data["OldPassword"]) != usr.password:
        return request_failed(3, "原密码错误")
    if data["NewPassword1"] != data["NewPassword2"]:
        return request_failed(4, "两次输入新密码不一致")
    if len(data["NewPassword1"]) == 0 or len(data["NewPassword1"]) > 32:
        return request_failed(5, "密码长度不符合要求")
    user = User.objects.filter(id=usr.id).first()
    user.password = sha256(data["NewPassword1"])
    user.save()
    return request_success()

def user_change_password(req:Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["OldPassword", "NewPassword1", "NewPassword2"]
    return AssetWarpper(req=req, function=_user_change_password,data_pass=data_pass,data_require=data_require)

def _asset_warn(usr:User, data=None):
    page_type = data["PageType"]
    page_id = data["PageId"]

    # 先找到这个user对应的department
    department = usr.department
    # 组合逻辑: Name,  WarnType
    if data["SearchName"] == '' and (data["WarnType"] == '' or data['WarnType'] == '-1'):
        # 00
        asset_candidates = Asset.objects.filter(department=department)
    elif data["SearchName"] == '' and (data["WarnType"] == '0' or data['WarnType'] == '1' or data['WarnType'] == '2'):
        # 01
        asset_candidates = Asset.objects.filter(department=department, warn_type=int(data['WarnType']))
    elif data["SearchName"] != '' and (data["WarnType"] == '' or data['WarnType'] == '-1'):
        # 10
        asset_candidates = Asset.objects.filter(department=department, name=data["SearchName"])
    elif data["SearchName"] != '' and (data["WarnType"] == '0' or data['WarnType'] == '1' or data['WarnType'] == '2'):
        asset_candidates = Asset.objects.filter(department=department, name=data["SearchName"], warn_type=int(data['WarnType']))
    else:
        asset_candidates = []

    to_search_list = []
    if page_type == 0:

        for asset in asset_candidates:

            if warn(asset) == True:
                to_search_list.append(asset)
    elif page_type == 1:
        for asset in asset_candidates:

            if warn(asset) == False:
                to_search_list.append(asset)
    else:
        to_search_list = asset_candidates

    
    # 遍历to_search_list，进行AssetType的搜索
    return_list = []
    if data["AssetType"] != '' and data["AssetType"] != '-1':
        for asset in to_search_list:
            if asset.Class.property == (int(data["AssetType"]) + 3):
                return_list.append(asset)
    else:
        return_list = to_search_list

    final_return_list = []
    for asset in return_list[20 * (page_id - 1): 20 * (page_id)]:

        return_item = {}
        return_item["Name"] = asset.name
        return_item["ID"] = asset.id
        if asset.Class.property == 3:
            return_item["AssetType"] = 0
        else:
            return_item["AssetType"] = 1
        return_item["WarnType"] = asset.warn_type
        if asset.warn_type == 0:
            return_item["WarnStrategy"] = "剩余数量小于等于{}告警".format(str(asset.warn_content))
            return_item["Description"] = "剩余数量为{}".format(str(asset.number))
        elif asset.warn_type == 1:
            year_num = int(asset.warn_content / 365)
            month_num = int((asset.warn_content - 365 * year_num) / 30)
            days_num = asset.warn_content - 365 * year_num - 30 * month_num 
            if year_num == 0:
                if month_num == 0:
                    return_item["WarnStrategy"] = "剩余时间小于等于{}天告警".format(str(days_num))
                else:
                    return_item["WarnStrategy"] = "剩余时间小于等于{}月{}天告警".format(str(month_num), str(days_num))
            else:
                return_item["WarnStrategy"] = "剩余时间小于等于{}年{}月{}天告警".format(str(year_num), str(month_num), str(days_num))


            expire_time = asset.expire
            if expire_time == None:
                return_item["Description"] = "无过期时间"
            else:
                expire_time = expire_time + dt.timedelta(hours=8)
                expire_time = expire_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
                current_time = get_current_time()
                current_time = current_time.replace(tzinfo=pytz.timezone(TIME_ZONE))

                remain_length = expire_time - current_time

                remain_length_days = remain_length.days
                year_num = int(remain_length_days / 365)
                month_num = int((remain_length_days - 365 * year_num) / 30)
                days_num = remain_length_days - 365 * year_num - 30 * month_num 
                if year_num == 0:
                    if month_num == 0:
                        return_item["Description"] = "剩余时间为{}天".format(str(days_num))
                    else:
                        return_item["Description"] = "剩余时间为{}月{}天".format(str(month_num), str(days_num))
                else:
                    return_item["Description"] = "剩余时间为{}年{}月{}天".format(str(year_num), str(month_num), str(days_num))

                # debug_print("test", "检验这一支")
        else:
            return_item["WarnStrategy"] = "无告警策略"
            return_item["Description"] = "无告警信息"
        
        if page_type == 0:
            return_item["IsWarning"] = 0
        else:
            if warn(asset):
                return_item["IsWarning"] = 0
            else:
                return_item["IsWarning"] = 1

        final_return_list.append(return_item)
    
    # 下面对return_list进行分页
    return_data = {}
    return_data["TotalNum"] = len(return_list)
    return_data["AssetList"] = final_return_list

    return request_success(return_data)

def asset_warn(req:Request, SessionID:str, PageType:int, PageId:int, SearchName:str, AssetType:str, WarnType:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["PageType"] = PageType
    data_pass["PageId"] = PageId
    data_pass["SearchName"] = SearchName[5:]
    data_pass["AssetType"] = AssetType[10:] # 有可能为空
    data_pass["WarnType"] = WarnType[9:]

    # debug_print("search_name", data_pass["SearchName"])
    # debug_print("asset_type", data_pass["AssetType"])
    # debug_print("warn_type", data_pass["WarnType"])

    return AssetWarpper(req=req, function=_asset_warn, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass)

def _user_asset_warn(usr:User, data=None):
    page_type = data["PageType"]
    page_id = data["PageId"]

    # 组合逻辑: Name,  WarnType
    if data["SearchName"] == '' and (data["WarnType"] == '' or data['WarnType'] == '-1'):
        # 00
        asset_candidates = Asset.objects.filter(user=usr)
    elif data["SearchName"] == '' and (data["WarnType"] == '0' or data['WarnType'] == '1' or data['WarnType'] == '2'):
        # 01
        asset_candidates = Asset.objects.filter(user=usr, warn_type=int(data['WarnType']))
    elif data["SearchName"] != '' and (data["WarnType"] == '' or data['WarnType'] == '-1'):
        # 10
        asset_candidates = Asset.objects.filter(user=usr, name=data["SearchName"])
    elif data["SearchName"] != '' and (data["WarnType"] == '0' or data['WarnType'] == '1' or data['WarnType'] == '2'):
        asset_candidates = Asset.objects.filter(user=usr, name=data["SearchName"], warn_type=int(data['WarnType']))
    else:
        asset_candidates = []

    to_search_list = []
    if page_type == 0:

        for asset in asset_candidates:

            if warn(asset) == True:
                to_search_list.append(asset)
    elif page_type == 1:
        for asset in asset_candidates:

            if warn(asset) == False:
                to_search_list.append(asset)
    else:
        to_search_list = asset_candidates

    
    # 遍历to_search_list，进行AssetType的搜索
    return_list = []
    if data["AssetType"] != '' and data["AssetType"] != '-1':
        for asset in to_search_list:
            if asset.Class.property == (int(data["AssetType"]) + 3):
                return_list.append(asset)
    else:
        return_list = to_search_list

    final_return_list = []
    for asset in return_list[20 * (page_id - 1): 20 * (page_id)]:

        return_item = {}
        return_item["Name"] = asset.name
        return_item["ID"] = asset.id
        if asset.Class.property == 3:
            return_item["AssetType"] = 0
        else:
            return_item["AssetType"] = 1
        return_item["WarnType"] = asset.warn_type
        if asset.warn_type == 0:
            return_item["WarnStrategy"] = "剩余数量小于等于{}告警".format(str(asset.warn_content))
            return_item["Description"] = "剩余数量为{}".format(str(asset.number))
        elif asset.warn_type == 1:
            year_num = int(asset.warn_content / 365)
            month_num = int((asset.warn_content - 365 * year_num) / 30)
            days_num = asset.warn_content - 365 * year_num - 30 * month_num 
            if year_num == 0:
                if month_num == 0:
                    return_item["WarnStrategy"] = "剩余时间小于等于{}天告警".format(str(days_num))
                else:
                    return_item["WarnStrategy"] = "剩余时间小于等于{}月{}天告警".format(str(month_num), str(days_num))
            else:
                return_item["WarnStrategy"] = "剩余时间小于等于{}年{}月{}天告警".format(str(year_num), str(month_num), str(days_num))


            expire_time = asset.expire
            if expire_time == None:
                return_item["Description"] = "无过期时间"
            else:
                expire_time = expire_time + dt.timedelta(hours=8)
                expire_time = expire_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
                current_time = get_current_time()
                current_time = current_time.replace(tzinfo=pytz.timezone(TIME_ZONE))

                remain_length = expire_time - current_time

                remain_length_days = remain_length.days
                year_num = int(remain_length_days / 365)
                month_num = int((remain_length_days - 365 * year_num) / 30)
                days_num = remain_length_days - 365 * year_num - 30 * month_num 
                if year_num == 0:
                    if month_num == 0:
                        return_item["Description"] = "剩余时间为{}天".format(str(days_num))
                    else:
                        return_item["Description"] = "剩余时间为{}月{}天".format(str(month_num), str(days_num))
                else:
                    return_item["Description"] = "剩余时间为{}年{}月{}天".format(str(year_num), str(month_num), str(days_num))

                # debug_print("test", "检验这一支")
        else:
            return_item["WarnStrategy"] = "无告警策略"
            return_item["Description"] = "无告警信息"
        
        if page_type == 0:
            return_item["IsWarning"] = 0
        else:
            if warn(asset):
                return_item["IsWarning"] = 0
            else:
                return_item["IsWarning"] = 1

        final_return_list.append(return_item)
    
    # 下面对return_list进行分页
    return_data = {}
    return_data["TotalNum"] = len(return_list)
    return_data["AssetList"] = final_return_list

    return request_success(return_data)

def user_asset_warn(req:Request, SessionID:str, PageType:int, PageId:int, SearchName:str, AssetType:str, WarnType:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["PageType"] = PageType
    data_pass["PageId"] = PageId
    data_pass["SearchName"] = SearchName[5:]
    data_pass["AssetType"] = AssetType[10:] # 有可能为空
    data_pass["WarnType"] = WarnType[9:]

    # debug_print("search_name", data_pass["SearchName"])
    # debug_print("asset_type", data_pass["AssetType"])
    # debug_print("warn_type", data_pass["WarnType"])

    return AssetWarpper(req=req, function=_asset_warn, data_pass=data_pass)

def _asset_warn_set(usr:User, data=None):
    asset = Asset.objects.filter(id=data["AssetID"]).first()
    asset.warn_type = data["WarnType"]
    if asset.warn_type == 0:
        asset.warn_content = data["WarnStrategy"]
    elif asset.warn_type == 1:
        # asset.warn_content = int(365 * float(data["WarnStrategy"]))
        asset.warn_content = parse_year_warn_to_days(data["WarnStrategy"])
    asset.save()
    return request_success()

def asset_warn_set(req:Request, SessionID:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_require = ["AssetID", "WarnType", "WarnStrategy"]
    return AssetWarpper(req=req, function=_asset_warn_set, authority_level=ONLY_ASSET_ADMIN, data_pass=data_pass, data_require=data_require)

def _info_search(usr:User, data=None):

    department = usr.department

    if data["SearchClass"] == "Class=" and data["SearchOwner"] == "Owner=":
        # 类别和所有者都没有
        asset_candidates = Asset.objects.filter(department=department)
    elif data["SearchClass"] != "Class=" and data["SearchOwner"] == "Owner=":
        # 搜类别
        search_class_name = data["SearchClass"][6:]
        search_class = AssetClass.objects.filter(name=search_class_name, department=department).first()
        asset_candidates = Asset.objects.filter(department=department, Class=search_class)
    elif data["SearchClass"] == "Class=" and data["SearchOwner"] != "Owner=":
        # 搜所有者
        search_owner_name = data["SearchOwner"][6:]
        search_owner = User.objects.filter(name=search_owner_name).first()
        asset_candidates = Asset.objects.filter(department=department, user=search_owner)
    else:
        # 类别和所有者都搜
        search_class_name = data["SearchClass"][6:]
        search_class = AssetClass.objects.filter(name=search_class_name, department=department).first()
        search_owner_name = data["SearchOwner"][6:]
        search_owner = User.objects.filter(name=search_owner_name).first()
        asset_candidates = Asset.objects.filter(department=department, user=search_owner, Class=search_class)
    
    # 检验资产编号:
    if data["SearchID"] != "ID=-1" and data["SearchID"] != "ID=":
        try:
            search_id = int(data["SearchID"][3:])
        except:
            return request_failed(4, "输入id不符合规范")


    searched_list = asset_search(asset_candidates, data)
    return_list = []

    print("3", get_current_time())
    page_id = int(data["PageID"])
    for asset in searched_list[20 * (page_id - 1): 20 * (page_id)]:

        if single_asset_expire(asset) == True:
            # 这个资产应该被自动清退了
            asset_admin = User.objects.filter(asset_administrator=1, department=department).first()
            asset.status = RETIRED
            asset.user = asset_admin
            asset_copy = Asset.objects.filter(id=asset.id).first()
            asset_copy.status = RETIRED
            asset_copy.user = asset_admin
            asset_copy.save()
            PendingResponse.objects.create(employee=asset_copy.user,asset=asset_copy,type=CLR,
                                           more_info="资产 " + asset_copy.name + "被自动清退了")
            Log.objects.create(type=ASSET_MANAGE,user_name=asset_copy.user.name,entity_name=asset_copy.user.entity.name,
                               more_info="资产 " + asset_copy.name + "被自动清退了")
            continue


        return_item = {}
        return_item["Name"] = asset.name
        return_item["ID"] = asset.id
        return_item["Status"] = asset.status
        return_item["Owner"] = asset.user.name
        return_item["Class"] = asset.Class.name
        return_item["Description"] = asset.description
        return_item["CreateTime"] = asset.create_time
        return_item["PropetyName"], return_item["PropetyName"] = parse_selfprop_to_list(asset.property)
        return_item["Number"] = asset.number
        return_item["Time"] = str(asset.expire)
        return_item["Position"] = str(asset.position)
        return_item["AssetValue"] = single_asset_value_update(asset)
        if asset.Class.property == 4:
            return_item["Type"] = 1
        else:
            return_item["Type"] = 0


        if asset.user.asset_administrator == 1 and asset.status == IDLE:
            return_item["IsReceive"] = 1
        else:
            return_item["IsReceive"] = 0
        
        if asset.user == usr and asset.status == IN_USE:
            return_item["IsReturn"] = 1
            return_item["IsMaintenance"] = 1
            return_item["IsTransfers"] = 1
        else:
            return_item["IsReturn"] = 0
            return_item["IsMaintenance"] = 0
            return_item["IsTransfers"] = 0
        
        return_list.append(return_item)

    # 下面在to_search_list里面进行搜索
    print("4", get_current_time())
    return_data = {}
    return_data["TotalNum"] = len(searched_list)
    return_data["Asset"] = return_list
    
    print("5", get_current_time())
    # 同时还要返回该部门的所有自定义属性
    all_self_prop_list = []
    asset_class_list = AssetClass.objects.filter(department=department)
    for asset_class in asset_class_list:
        all_self_prop_list.extend(parse_children(asset_class.selfprop))
    return_data["DepartmentProp"] = all_self_prop_list
    print("6", get_current_time())
    return request_success(return_data)

def info_search(req:Request, SessionID:str, PageID:int, SearchID:str, SearchName:str, \
    SearchClass:str, SearchStatus:str, SearchOwner:str, SearchProp:str, SearchPropValue:str):
    data_pass = {}
    data_pass["session_id"] = SessionID
    data_pass["PageID"] = PageID
    data_pass["SearchID"] = SearchID
    data_pass["SearchName"] = SearchName
    data_pass["SearchClass"] = SearchClass
    data_pass["SearchStatus"] = SearchStatus
    data_pass["SearchOwner"] = SearchOwner
    data_pass["SearchProp"] = SearchProp
    data_pass["SearchPropValue"] = SearchPropValue
    return AssetWarpper(req=req, function=_info_search, data_pass=data_pass)


