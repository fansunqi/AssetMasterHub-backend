# 资产的生命周期
IDLE = 0
IN_USE = 1
IN_MAINTAIN = 2
RETIRED = 3
DELETED = 4

# 权限
ONLY_SUPER_ADMIN = 1
ONLY_ASSET_ADMIN = 2
ONLY_SYSTEM_ADMIN = 3
ONLY_ASSET_ADMIN_AND_USER = 4

# 资产动态变化代号
RECEIVE = 0     # 领用
RETURN = 1      # 退库
MAINTENANCE = 2 # 维保
TRANSFER = 3    # 转移
    # 新增以下三个 -- by邹作休 
CLR = 4         # 清退
END_M = 5       # 退还维保
ALCT = 6        # 调拨
    # 再加以下两个 -- by邹作休
LR = 7          # 录入
BG = 8          # 变更

# 资产request的result
PENDING = 1
APPROVAL = 2
DISAPPROVAL = 3

# validate_request的各种发挥情况
VALID = 1
DOUBLE_RECEIVE = -1
DOUBLE_RETURN = -2
NOT_IDLE = -3
NOT_USER_RECEIVE = -4
NOT_IN_USE = -5
NOT_USER_RETURN = -6
ALREADY_RETURN = -7
NOT_USER_MAINTENANCE = -8
NOT_USER_TRANSFER = -9
ALREADY_TRANSFER = -10
ITEM_RECEIVE_LOTS = -11
RECEIVE_EXCEEDS = -12
NOT_EXIST = -13

# 资产管理员操作 asset_manage
CLEAR = 0         # 清退
END_MAINTAIN = 1  # 退还维保
ALLOCATE = 2      # 调拨 

# 记录日志的type
IN_OUT = 1         #登录登出
USER_MANAGE = 2    #用户管理
ASSET_MANAGE = 3   #资产管理
ENTITY_MANAGE = 4  #业务实体管理

