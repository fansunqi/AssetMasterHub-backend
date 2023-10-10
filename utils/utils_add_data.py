from Asset.models import *
from User.models import *
from utils.utils_other import *
import datetime as dt


def add_user_class_1():
    pass
    # e1 = Entity.objects.filter(name="demo实体").first()

    # App.objects.create(name="用户列表",path="/user/system_manager",authority=1,entity=e1)
    # App.objects.create(name="角色管理",path="/user/system_manager",authority=1,entity=e1)
    # App.objects.create(name="部门管理",path="/user/system_manager/department",authority=1,entity=e1)
    # App.objects.create(name="应用管理",path="/user/system_manager/application",authority=1,entity=e1)
    # App.objects.create(name="操作日志",path="/user/system_manager/log",authority=1,entity=e1)

    # App.objects.create(name="资产审批",path="/user/asset_manager/apply_approval",authority=2,entity=e1)
    # App.objects.create(name="资产定义",path="/user/asset_manager/asset_define",authority=2,entity=e1)
    # App.objects.create(name="资产录入",path="/user/asset_manager/asset_add",authority=2,entity=e1)
    # App.objects.create(name="资产变更",path="/user/asset_manager/asset_change",authority=2,entity=e1)
    # App.objects.create(name="资产查询",path="/user/asset_manager/asset_info",authority=2,entity=e1)
    # App.objects.create(name="资产清退",path="/user/asset_manager/asset_info",authority=2,entity=e1)
    # App.objects.create(name="资产调拨",path="/user/asset_manager/asset_info",authority=2,entity=e1)
    # App.objects.create(name="资产统计",path="/user/asset_manager/asset_statistic",authority=2,entity=e1)
    # App.objects.create(name="资产告警",path="/user/asset_manager/asset_warn",authority=2,entity=e1)

    # App.objects.create(name="资产查看",path="/user/employee",authority=3,entity=e1)
    # App.objects.create(name="资产领用",path="/user/employee",authority=3,entity=e1)
    # App.objects.create(name="资产退库",path="/user/employee",authority=3,entity=e1)
    # App.objects.create(name="资产维保",path="/user/employee",authority=3,entity=e1)
    # App.objects.create(name="资产转移",path="/user/employee",authority=3,entity=e1)
    

def add_asset_1():
    pass
    # asset_class_1 = AssetClass.objects.filter(name="房地产").first()
    # user_1 = User.objects.filter(name="yuge").first()

    # # asset_1 = Asset.objects.create(name="第一个资产", Class=asset_class_1,\
    # #           user=user_1, price=100.2, description="xxx", position="xxx", property="xxx")
    # asset_2 = Asset.objects.create(name="第二个资产", Class=asset_class_1,\
    #           user=user_1, price=100.1, description="相同的描述", position="xxx", property="xxx")
    # asset_3 = Asset.objects.create(name="第三个资产", Class=asset_class_1,\
    #           user=user_1, price=100.1, description="相同的描述", position="xxx", property="xxx")
    # asset_4 = Asset.objects.create(name="第四个资产", Class=asset_class_1,\
    #           user=user_1, price=99.9, description="xxx", position="xxx", property="xxx")
    # asset_5 = Asset.objects.create(name="第五个资产", Class=asset_class_1,\
    #           user=user_1, price=99.9, description="xxx", position="xxx", property="xxx")
    # asset_6 = Asset.objects.create(name="第六个资产", Class=asset_class_1,\
    #           user=user_1, price=98.9, description="独一无二", position="xxx", property="xxx")

# def add_entity_1():
#     pass   

def is_end(i, j, k, idx):
    pass
    # end_i = 4
    # end_j = 2
    # end_k = 2
    # end_idx = 822
    # if i < end_i:
    #     return True
    # elif i == end_i and j < end_j:
    #     return True
    # elif i == end_i and j == end_j and k < end_k:
    #     return True
    # elif i == end_i and j == end_j and k == end_k and idx <= end_idx:
    #     return True
    # else:
    #     return False

def add_user(i, j, k):
    pass
    # entity = Entity.objects.filter(name="demo实体").first()
    # # 先每个叶子部门创建1000个员工
    # # for i in range(3, 6):
    # #     for j in range(1, 4):
    # #       for k in range(1, 5):
    # if j != 3 and k == 4:
    #     return
    # else:
    #     # 在demo部门i-j-k下面创建员工 
        
    #     department = Department.objects.filter(name="demo部门{}-{}-{}".format(str(i), str(j), str(k))).first()
    #     for idx in range(1000):
    #         if is_end(i, j, k, idx) == True:
    #             continue


    #         if idx == 0:
    #             asset_admin = 1
    #         else:
    #             asset_admin = 0
    #         User.objects.create(name="demo员工-{}-{}-{}-{}".format(str(i), str(j), str(k), str(idx)), \
    #             password=sha256(MD5("yiqunchusheng")), entity=entity, department=department, \
    #             super_administrator=0, system_administrator=0, asset_administrator=asset_admin, \
    #                 function_string="1111100000000000000000")

def time_string_to_datetime(data):
    pass
    # if "Time" in data and data["Time"] != None:
    #     time_string = data["Time"]
    #     year = int(time_string[0:4])
    #     month = int(time_string[5:7])
    #     day = int(time_string[8:10])
    #     hour = int(time_string[11:13])
    #     minute = int(time_string[14:16])
    #     second = int(time_string[17:19])

    #     date_time = dt.datetime(year,month,day,hour,minute,second)

    #     return date_time
    # else:
    #     return None

def add_asset_final(asset_class_name, i, j, k):
    pass
    # # asset_class_name="房屋和建筑物"
    # user_name = "demo员工-{}-{}-{}-0".format(str(i), str(j), str(k))

    # user = User.objects.filter(name=user_name).first()
    # asset_class = AssetClass.objects.filter(name=asset_class_name, department=user.department).first()

    # for i in range(600, 700):
    #     Asset.objects.create(name=user_name + '-' + asset_class_name + '-' + str(i), Class=asset_class, user=user, \
    #         price=100, description="描述", position="位置", department=user.department, \
    #         create_time=getTime.get_30_days_before(), expire=time_string_to_datetime({"Time":"2023-06-30 20:05:45"}))


def add_asset_class_final(i,j,k):
    pass
    # depart_name = "demo部门{}-{}-{}".format(str(i), str(j), str(k))

    # department = Department.objects.filter(name=depart_name).first()
    # ac_num = AssetClass.objects.filter(department=department,name="数量型资产").first()
    # ac_item = AssetClass.objects.filter(department=department,name="条目型资产").first()

    # # 不要忘记修改ac_num和ac_item的children
    
    # ac1 = AssetClass.objects.create(department=department, name="房屋和建筑物", parent=ac_item, property=3, loss_style=1)
    # ac1_1 = AssetClass.objects.create(department=department, name="办公楼", parent=ac1, property=3, loss_style=1)
    # ac1_2 = AssetClass.objects.create(department=department, name="车库", parent=ac1, property=3, loss_style=0)
    # ac1_3 = AssetClass.objects.create(department=department, name="烟囱", parent=ac1, property=3, loss_style=0)
    # ac1_4 = AssetClass.objects.create(department=department, name="宿舍", parent=ac1, property=3, loss_style=1)
    # ac1_5 = AssetClass.objects.create(department=department, name="食堂", parent=ac1, property=3, loss_style=0)
    # ac1_6 = AssetClass.objects.create(department=department, name="活动室", parent=ac1, property=3, loss_style=0)
    # ac1.children = '$' + str(ac1_1.id) + '$' + str(ac1_2.id) + '$' + str(ac1_3.id) + '$' + str(ac1_4.id) + '$' + str(ac1_5.id) + '$' + str(ac1_6.id)
    # ac1.save()

    # ac2 = AssetClass.objects.create(department=department, name="运输设备", parent=ac_num, property=4, loss_style=0)
    # ac2_1 = AssetClass.objects.create(department=department, name="轿车", parent=ac2, property=4, loss_style=0)
    # ac2_2 = AssetClass.objects.create(department=department, name="面包车", parent=ac2, property=4, loss_style=0)
    # ac2_3 = AssetClass.objects.create(department=department, name="火车", parent=ac2, property=4, loss_style=0)
    # ac2_4 = AssetClass.objects.create(department=department, name="轮船", parent=ac2, property=4, loss_style=0)
    # ac2_5 = AssetClass.objects.create(department=department, name="三轮车", parent=ac2, property=4, loss_style=1)
    # ac2.children = '$' + str(ac2_1.id) + '$' + str(ac2_2.id) + '$' + str(ac2_3.id) + '$' + str(ac2_4.id) + '$' + str(ac2_5.id)
    # ac2.save()

    # ac3 = AssetClass.objects.create(department=department, name="机械设备", parent=ac_num, property=4, loss_style=1)
    # ac3_1 = AssetClass.objects.create(department=department, name="机床", parent=ac3, property=4, loss_style=1)
    # ac3_2 = AssetClass.objects.create(department=department, name="发电机", parent=ac3, property=4, loss_style=1)
    # ac3.children = '$' + str(ac3_1.id) + '$' + str(ac3_2.id)
    # ac3.save()

    # ac4 = AssetClass.objects.create(department=department, name="医疗设备", parent=ac_num, property=4, loss_style=1)
    # ac4_1 = AssetClass.objects.create(department=department, name="X光机", parent=ac4, property=4, loss_style=1)
    # ac4.children = '$' + str(ac4_1.id)
    # ac4.save()

    # ac5 = AssetClass.objects.create(department=department, name="文物和陈列物品", parent=ac_num, property=4, loss_style=1)
    # ac5_1 = AssetClass.objects.create(department=department, name="书籍", parent=ac5, property=4, loss_style=1)
    # ac5_2 = AssetClass.objects.create(department=department, name="字画", parent=ac5, property=4, loss_style=1)
    # ac5_3 = AssetClass.objects.create(department=department, name="纪念物品", parent=ac5, property=4, loss_style=1)
    # ac5.children = '$' + str(ac5_1.id) + '$' + str(ac5_2.id) + '$' + str(ac5_3.id)
    # ac5.save()

    # ac6 = AssetClass.objects.create(department=department, name="办公设备", parent=ac_num, property=4, loss_style=1)
    # ac6_1 = AssetClass.objects.create(department=department, name="桌子", parent=ac6, property=4, loss_style=1)
    # ac6_2 = AssetClass.objects.create(department=department, name="椅子", parent=ac6, property=4, loss_style=1)
    # ac6_3 = AssetClass.objects.create(department=department, name="沙发", parent=ac6, property=4, loss_style=1)
    # ac6.children = '$' + str(ac6_1.id) + '$' + str(ac6_2.id) + '$' + str(ac6_3.id)
    # ac6.save()
    
    # ac_num.children = '$' + str(ac2.id) + '$' + str(ac3.id) + '$' + str(ac4.id) + '$' + str(ac5.id) + '$' + str(ac6.id)
    # ac_item.children = '$' + str(ac1.id)
    # ac_num.save()
    # ac_item.save()




# 之后加资产的时候可以注意一下创建时间和过期时间，做出资产折旧的样子
