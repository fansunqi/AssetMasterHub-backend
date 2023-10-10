from django.db import models
import utils.model_date as getTime

# 本表用于记录业务实体的信息
class Entity(models.Model):
    id = models.BigAutoField(primary_key = True)
    name = models.CharField(max_length = 128)

    def __str__(self):
        return self.name

# 本表用于记录组织有关的信息
class Department(models.Model):
    id = models.BigAutoField(primary_key = True)
    parent = models.ForeignKey(to = "Department", on_delete = models.CASCADE, null = True) # 上一级 Department
    children = models.CharField(max_length=256, null = True)   # 存储方式, $1$2....
    entity = models.ForeignKey(to = Entity, on_delete = models.CASCADE)
    name = models.CharField(max_length = 128)
    path = models.CharField(max_length = 128,null=True) # 九位的数字串

    def __str__(self):
        return self.name

# 本表用于记录用户的信息
class User(models.Model):
    id = models.BigAutoField(primary_key = True)
    name = models.CharField(max_length = 128, unique = True)
    password = models.CharField(max_length=100)
    entity = models.ForeignKey(to = Entity, on_delete = models.CASCADE, null= True) # 超级管理员没有业务实体
    department = models.ForeignKey(to = Department, on_delete = models.CASCADE, null=True) # 系统管理员没有部门
    super_administrator = models.IntegerField()   # 用户是否为超级管理员
    system_administrator = models.IntegerField()  # 用户是否为系统管理员
    asset_administrator = models.IntegerField()   # 用户是否为资产管理员
    function_string = models.CharField(max_length=50)          # 代表该用户的权能01字符串
    Is_Locked = models.BooleanField(default=False) # 用户是否被锁定
    mobile = models.CharField(max_length=32,null=True,unique=True)      # 手机号，用户绑定飞书用户
    open_id = models.CharField(max_length=128,null=True)                # 飞书用户的open_id
    feishu = models.BooleanField(default=False)                         # 用户是否绑定飞书，默认为否

    class Meta:
        indexes = [models.Index(fields=["mobile"])]

    def serialize(self):
        authority: int
        if self.super_administrator == 1:
            authority = 0
        elif self.system_administrator == 1:
            authority = 1
        elif self.asset_administrator == 1:
            authority = 2
        else:
            authority = 3
        return {
            "Name": self.name,
            "Department": self.department.name, 
            "Authority": authority,
            "lock": self.Is_Locked
        }   
    
    def __str__(self):
        return self.name

# 记录应用与第三方URL
class App(models.Model):
    id = models.BigAutoField(primary_key = True)
    name = models.CharField(max_length = 128)    # 名称
    path = models.CharField(max_length = 128)    # 网址
    entity = models.ForeignKey(to = Entity, on_delete = models.CASCADE, null= True) # 对应的业务实体
    Is_Locked = models.BooleanField(default=False) # 该应用是否被锁定
    Is_Internal = models.BooleanField(default=True) # 该应用是否为内部应用
    authority = models.IntegerField() #是哪一种用户的应用，2表示资产管理员，3表示员工，其余值无效
    image = models.CharField(null=True,max_length=256) #应用图片

    def __str__(self):
        return self.name

        
        
# honorcode: from https://github.com/c7w/ReqMan-backend/blob/dev/ums/models.py
class SessionPool(models.Model):
    sessionId = models.CharField(max_length=48) # 实际长度: 32
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expireAt = models.DateTimeField(default=getTime.get_datetime) # TODO:搞清楚这里的get_datetime

    class Meta:
        indexes = [models.Index(fields=["sessionId"])]


class Log(models.Model):
    id = models.BigAutoField(primary_key = True)
    # 创建时间
    create_time = models.DateTimeField(default=getTime.get_current_time)
    # 操作类型,可取1~4，分别表示登录登出、用户管理、资产管理、业务实体管理
    type = models.IntegerField()
    # 用户主体的名字，不用foreign key防止级联删除
    user_name = models.CharField(max_length = 128)
    # 日志的详细信息
    more_info = models.CharField(null=True,max_length=128)
    # 业务实体名，用于筛选
    entity_name = models.CharField(null=True,max_length = 128)
    # 是否成功，默认为是
    is_succ = models.IntegerField(default=1)
    class Meta:
        indexes = [models.Index(fields=["type"]),
                   models.Index(fields=["entity_name"]),
                   models.Index(fields=["type","entity_name"])]
        

class Feishu(models.Model):
    id = models.BigAutoField(primary_key = True)
    feishu_department = models.IntegerField(null=True)