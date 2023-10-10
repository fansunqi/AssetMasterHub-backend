from django.db import models
from User.models import User, Entity, Department
import utils.model_date as getTime 
from utils.config import *

# 本表用于记录资产类别 ( 自己添加 )
class AssetClass(models.Model):
    id = models.BigAutoField(primary_key = True)  # 资产类别的 id 
    department = models.ForeignKey(to = Department, on_delete = models.CASCADE)
    name = models.CharField(max_length = 128)     # 资产类别, 如"房地产"
    parent = models.ForeignKey(to = "AssetClass", on_delete = models.CASCADE, null = True)
    children = models.CharField(max_length=256, null = True)   # 存储方式, $1$2....
    property = models.IntegerField()  # 资产类别属性
    
    # 0: 根节点
    #(废弃) 1: 非根节点, 非品类
    #(废弃) 2: 尚未被定义为条目型资产还是数量型资产的品类
    # 3: 条目型资产品类
    # 4: 数量型资产品类

    selfprop =  models.TextField(null=True)

    loss_style = models.IntegerField(default=1, null=True)  # 0 代表指数折旧, 1代表线性折旧
    
    def __str__(self):
        return self.name

# 本表用于记录资产有关的信息
class Asset(models.Model):
    id = models.BigAutoField(primary_key = True)
    parent = models.ForeignKey(to = "Asset", on_delete = models.CASCADE, null = True) # 上一级 Asset
    name = models.CharField(max_length = 128)
    Class = models.ForeignKey(to = AssetClass, on_delete = models.CASCADE)  # 注意, Class 字段为了区别关键字 class, 首字母大写
    user = models.ForeignKey(to = User, on_delete = models.CASCADE, null= True)

    department = models.ForeignKey(to = Department, on_delete=models.CASCADE, null=True)

    price = models.DecimalField(max_digits = 8, decimal_places = 2)
    description = models.CharField(max_length = 128)
    position = models.CharField(max_length = 128)
    number = models.IntegerField(default=1)

    property = models.TextField(null=True)
    # expire = models.DateTimeField(default=getTime.get_datetime)
    expire = models.DateTimeField(null=True)
    create_time = models.DateTimeField(default=getTime.get_current_time)
    status = models.IntegerField(default=IDLE)     # 资产的生命周期

    label_visible = models.CharField(max_length = 128, default="111111")   # 定义详见工作文档6.3.9.1, 1代表True, 0代表False

    # 告警类型
    warn_type = models.IntegerField(default=2)
    # 0代表数量告警，1代表年限告警，2代表当前无告警
    warn_content = models.IntegerField(null=True)
    # 存储的是数量或者天数

    class Meta:
        indexes = [models.Index(fields=["department"])]

    def __str__(self):
        return self.name

class PendingRequests(models.Model):
    id = models.BigAutoField(primary_key = True)
    initiator = models.ForeignKey(to = User, on_delete = models.CASCADE, related_name = 'PendingRequests_initiator')
    participant = models.ForeignKey(to = User, on_delete = models.CASCADE, null = True, related_name = 'PendingRequests_participant')
    asset = models.ForeignKey(to = Asset, on_delete = models.CASCADE)
    # asset_list = models.CharField(max_length = 256) # 类似于parse_children, 支持批量操作
    type = models.IntegerField()
    result = models.IntegerField()
    request_time = models.DateTimeField(default=getTime.get_current_time)
    review_time = models.DateTimeField(null=True)

    # 在资产转移的时候，需要重新指定资产分类
    Class = models.ForeignKey(to = AssetClass, on_delete = models.CASCADE, null = True) 

    # 暂时不使用这个asset_admin
    asset_admin = models.ForeignKey(to = User, on_delete = models.CASCADE, related_name = 'PendingRequests_asset_admin')

    # 用于飞书发送审批卡片
    message_id = models.CharField(max_length=64, null=True) 

    # 后续资产申请修改
    apply_number = models.IntegerField(null=True)                  # 数量型资产领用数量
    maintain_time = models.CharField(max_length=32, null=True)     # 截止日期更改
    message = models.TextField(null=True)



    class Meta:
        indexes = [models.Index(fields=["result"]),
                   models.Index(fields=["message_id"])]

    def __str__(self):
        return self.id
    
class PendingResponse(models.Model):
    id = models.BigAutoField(primary_key = True)
    # 记录与之相关的 消息接收者（可以是员工和资产管理员）、涉及到的人（一般是资产管理员，可以没有）、资产

    # 接收者，名字不改了
    employee = models.ForeignKey(to = User, on_delete = models.CASCADE, related_name = 'PendingResponse_employee') 
    # 涉及到的人，名字不改了
    asset_admin = models.ForeignKey(to = User, on_delete = models.CASCADE, null = True, related_name = 'PendingResponse_asset_admin')
    # 资产
    asset = models.ForeignKey(to = Asset, on_delete = models.CASCADE)
    # 操作类型 （领用、退库、维保、转移、退还维保、清退）
    type = models.IntegerField()
    # 消息内容
    more_info = models.CharField(null=True,max_length=128)
    # 该消息是否已读
    is_read = models.BooleanField(default=False)
    # 消息发送时间
    response_time = models.DateTimeField(default=getTime.get_current_time)
    # 消息阅读时间
    read_time = models.DateTimeField(null=True)

    def __str__(self):
        return self.id
