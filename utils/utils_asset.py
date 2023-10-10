from Asset.models import *
from User.models import *
from rest_framework.request import Request
from utils.sessions import get_session_id
from utils.utils_other import *
from utils.config import *
from utils.utils_request import *
from utils.model_date import*
import json
import pytz
import datetime as dt
from CS_Company_backend.settings import TIME_ZONE
from MyQR import myqr
import cv2
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import os
import oss2
import math
import re

def get_current_time():
    return dt.datetime.now()

# 鉴权函数
def check_authority(authority_level, usr:User):
    # TODO 
    if authority_level == ONLY_SUPER_ADMIN:
        if usr.super_administrator == 1:
            return None
        else:
            return request_failed(3, "非超级管理员，没有对应权限")
    if authority_level == ONLY_ASSET_ADMIN:
        if usr.asset_administrator == 1:
            return None
        else:
            return request_failed(3, "非资产管理员，没有对应权限")
    if authority_level == ONLY_ASSET_ADMIN_AND_USER:
        if usr.super_administrator == 0 and usr.system_administrator == 0:
            return None
        else:
            return request_failed(3, "超级或系统管理员，没有对应权限")
    
    return None

def parse_data(request, data_require):
    if (request.method == "POST") or (request.method == "PUT"):
        tmp_body = request.body.decode("utf-8")
        
        try:
            body = json.loads(tmp_body) 
        except BaseException as error:
            print("During get_session_id: ", error, tmp_body)

        data = return_field(body, data_require)

        return data

def AssetWarpper(req, function, authority_level=None, data_require=None, validate_data=None, data_pass=None):

    if (req.method == 'POST') or (req.method == 'PUT'):
        # 首先检查 data_pass 中有没有 session_id
        if data_pass != None:
            try:
                session_id = data_pass["session_id"]
            except KeyError:
                session_id = get_session_id(req)
        else:
            session_id = get_session_id(req)
        # print(session_id)
    
        # 下面是 session_id to user的过程
        sessionRecord =SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(2, "session id expire")
            else:
                usr = sessionRecord.user

                # 检查权限
                check_error = check_authority(authority_level, usr)
                if check_error != None:
                    return check_error
                
                # 从req中解析出数据
                if data_require != None:
                    if data_pass != None:
                        data_require_dict = parse_data(req, data_require)
                        data = {**data_require_dict, **data_pass}
                    else:
                        data = parse_data(req, data_require)
                else:
                    data = data_pass

                # 检查数据是否合理有效, 再传一个 validate_data 函数进来
                if(validate_data != None):
                    data_error = validate_data(data)
                    if data_error != None:
                        return data_error

                return function(usr, data)           
        else:
            return request_failed(-2, "session id do not exist")
    
    elif (req.method == 'DELETE') or (req.method == 'GET'):
        session_id = data_pass["session_id"]

        # 下面是 session_id to user的过程
        sessionRecord =SessionPool.objects.filter(sessionId=session_id).first()
        if sessionRecord:
            if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
                SessionPool.objects.filter(sessionId=session_id).delete()
                return request_failed(2, "session id expire")
            else:
                usr = sessionRecord.user

                # 检查权限
                check_error = check_authority(authority_level, usr)
                if check_error != None:
                    return check_error
                
                # 检查数据是否合理有效, 再传一个 validate_data 函数进来
                if(validate_data != None):
                    data_error = validate_data(data_pass)
                    if data_error != None:
                        return data_error

                return function(usr, data_pass)           
        else:
            return request_failed(-2, "session id do not exist")
    
    else:
        return BAD_METHOD


def get_department(department_id):
    department = Department.objects.filter(id=department_id)
    assert department != None, "Department NOT Found!"
    return department

def get_asset_class(asset_class_id):
    asset_class = AssetClass.objects.filter(id=asset_class_id).first()
    assert asset_class != None, "Asset Class NOT Found!"
    return asset_class


def give_subtree_recursive(asset_class_id, department_id):
    nodeData = {}

    # 把这个asset_class的title与value填写到nodeData中, value直接写asset_class_id
    asset_class = get_asset_class(asset_class_id)
    assert asset_class.department.id == department_id, "department id is wrong!"

    add_info = ""
    # if (asset_class.property == 0) or (asset_class.property == 1) or (asset_class.property == 2):
    #     add_info = ""
    # elif asset_class.property == 3:
    #     add_info = " [条目型品类]"
    # elif asset_class.property == 4:
    #     add_info = " [数量型品类]"
    # else:
    #     raise KeyError

    # debug_print("xxx", str(asset_class.name + add_info))

    nodeData['title'] = str(asset_class.name + add_info)
    nodeData['value'] = asset_class_id

    # 解析出children_list
    children_list = parse_children(asset_class.children)

    # 如果这个asset_class没有children, 直接返回nodeData
    if len(children_list)==0:
        return nodeData 

    # 如果这个asset_class有children
    children = []
    for child_id in children_list:
        children.append(give_subtree_recursive(child_id, department_id))

    nodeData["children"] = children

    return nodeData

def give_subtree_list_recursive(asset_class_id, department_id, subtree_list:list):

    asset_class = get_asset_class(asset_class_id)
    assert asset_class.department.id == department_id, "department id is wrong!"

    subtree_list.append(asset_class_id)

    # 解析出children_list
    children_list = parse_children(asset_class.children)

    # 如果这个asset_class没有children, 直接返回nodeData
    if len(children_list)==0:
        return subtree_list

    # 如果这个asset_class有children
    for child_id in children_list:
        # debug_print("child_id", type(child_id)) # str
        subtree_list = give_subtree_list_recursive(int(child_id), department_id, subtree_list)

    return subtree_list

def bool_to_string_label(data):
    string_label = ""
    data_require = ["Name", "Class", "Status", "Owner", "Description", "CreateTime"]
    for label_key in data_require:
        if data[label_key] == True:
            string_label += '1'
        else:
            string_label += '0'
    return string_label

def string_to_bool_label(label_string:str):
    data_require = ["Name", "Class", "Status", "Owner", "Description", "CreateTime"]
    count_idx = 0
    label_visible = {}
    for label_char in label_string:
        if label_char == '1':
            label_visible[data_require[count_idx]] = True
        else:
            label_visible[data_require[count_idx]] = False
        count_idx += 1
    debug_print("label_visible", label_visible)
    return label_visible

def draw_qr(weburl:str):
    myqr.run(words=weburl)
            
def draw_label(weburl:str, label_dict):
    debug_print("abspath", os.path.abspath(__file__))

    # # 首先生成白色背景图片
    # H = 700
    # W = 1270

    # bk_img = np.zeros((H, W), np.uint8)
    # bk_img[0:H-1, 0:W-1] = 255
    # cv2.imwrite("img_white_background.png", bk_img)

    bk_img = cv2.imread("img_white_background.png")
    # 设置需要显示的字体
    fontpath1 = "msyh.ttc"
    fontpath2 = "msyhl.ttc"
    font1 = ImageFont.truetype(fontpath1, 32)
    font2 = ImageFont.truetype(fontpath2, 32)
    img_pil = Image.fromarray(bk_img)
    draw = ImageDraw.Draw(img_pil)

    x1 = 30
    x2 = 350
    y_1 = 100
    y_big_interval = 200
    y_2 = y_1 + y_big_interval
    y_3 = y_2 + y_big_interval
    y_interval = 50
    six_key_position = list([(x1,y_1), (x2, y_1), (x1, y_2), (x2, y_2), (x1, y_3), (x2, y_3)])
    six_value_position = list([(x1,y_1+y_interval), (x2, y_1+y_interval), (x1, y_2+y_interval), (x2, y_2+y_interval), (x1, y_3+y_interval), (x2, y_3+y_interval)])

    fill_text = label_dict

    fill_id = 0
    for key,value in fill_text.items():
        draw.text(six_key_position[fill_id],  key,  font = font1, fill = (0, 0, 0))
        draw.text(six_value_position[fill_id],  value,  font = font2, fill = (0, 0, 0))
        fill_id += 1



    myqr.run(words=weburl)
    qr_img = Image.open("qrcode.png")
    img_pil.paste(qr_img,(730, 50))
    bk_img = np.array(img_pil)


    cv2.imwrite("label.jpg", bk_img)


class AliyunOss(object):
 
    def __init__(self):
        self.access_key_id = "LTAI5tDPvkkRMCRP24uax2kb"   # 从阿里云查询到的 AccessKey 的ID
        self.access_key_secret = "NtzH0aV3Hpm18SdEUCt7hJcfhoxNZi"  # 从阿里云查询到的 AccessKey 的Secret
        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
        self.bucket_name = "cs-company"  # 阿里云上创建好的Bucket的名称
        self.endpoint = "oss-cn-beijing.aliyuncs.com"  # 阿里云从Bucket中查询到的endpoint
        self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
 
    def put_object_from_file(self, name, file):
        """
        
        :param name: 在阿里云Bucket中要保存的文件名
        :param file: 本地图片的文件名
        :return: 
        """
        self.bucket.put_object_from_file(name, file)
        return name
    
    def list_dir(self, sub_path):
        url_list = []
        for filename in oss2.ObjectIterator(self.bucket, prefix = sub_path):
            # print("文件名称：", filename.key)
            url = "https://cs-company.oss-cn-beijing.aliyuncs.com/" + filename.key
            # print("url", url)
            url_list.append(url)
        return url_list

def exp_dcr(y_0, day_num, now_day_num):
    if now_day_num > day_num:
        return 0
    # 指数折旧
    # y = y_0 * e ^ (-at), y_0是资产原价, 先计算出a
    minusat  = math.log ((0.01 / y_0), math.e)
    a = -1 * (minusat / day_num)
    return y_0 * math.exp((-1) * a * now_day_num)

def single_asset_value_shift(asset: Asset, shift_days:int):
    # 计算单个资产在shift时刻的价值
    # 返回一个float

    # 获取时间并转换为上海时区
    expire_time = asset.expire
    create_time = asset.create_time
    current_time = get_current_time()
    
    # 进行现在时间的平移
    current_time = current_time + dt.timedelta(days=(-1) * shift_days)
    current_time = current_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
    # print("asset_info_current_time4", current_time)
    
    create_time = create_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
    create_time = create_time + dt.timedelta(hours=8)
    # print("asset_info_create_time4", create_time)
    
    if expire_time != None:
        expire_time = expire_time + dt.timedelta(hours=8)
        expire_time = expire_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
    # print("asset_info_expire_time4", expire_time)

    ori_asset_price = float(asset.price)


    # 如果早于创立时间
    if current_time < create_time:
        return 0
    if expire_time == None:
        return float(asset.price)
    else:

        valid_length = expire_time - create_time
        spend_length = current_time - create_time

        # print("asset_name", asset.name)
        # print("expire_time", expire_time)
        # print("create_time", create_time)
        # print("current_time", current_time)
        # print("spend_length", spend_length)
        # print("valid_length", valid_length)
        
        if spend_length > valid_length:
            return 0
        elif asset.Class.loss_style == 0:
            # 指数折旧
            # y = y_0 * e ^ (-at), y_0是资产原价, 先计算出a
            tmp =  exp_dcr(float(asset.price), valid_length.days, spend_length.days)
            return round(tmp, 2)
             
        else:
            # 线性折旧
            tmp = (1 - float(spend_length / valid_length)) * ori_asset_price 
            return round(tmp, 2)

def single_asset_expire(asset: Asset):
    if asset.expire == None:
        return False
    else:
        current_time = get_current_time()
        current_time = current_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
        expire_time = asset.expire + dt.timedelta(hours=8)
        expire_time = expire_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
        if current_time > expire_time:
            return True
        else:
            return False



def single_asset_value_update(asset: Asset):
    # 计算单个资产在现在时刻的价值
    # 返回一个float

    # 获取时间并转换为上海时区
    expire_time = asset.expire
    create_time = asset.create_time
    current_time = get_current_time()
    
    current_time = current_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
    # print("asset_info_current_time4", current_time)
    
    create_time = create_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
    create_time = create_time + dt.timedelta(hours=8)
    # print("asset_info_create_time4", create_time)
    
    if expire_time != None:
        expire_time = expire_time + dt.timedelta(hours=8)
        expire_time = expire_time.replace(tzinfo=pytz.timezone(TIME_ZONE))
    # print("asset_info_expire_time4", expire_time)

    ori_asset_price = float(asset.price)

    if expire_time != None: 
        valid_length = expire_time - create_time
        spend_length = current_time - create_time

        # print("asset_name", asset.name)
        # print("expire_time", expire_time)
        # print("create_time", create_time)
        # print("current_time", current_time)
        # print("spend_length", spend_length)
        # print("valid_length", valid_length)
        
        if spend_length > valid_length:
            # 已经被完全折旧了
            return 0
        elif asset.Class.loss_style == 0:
            # 指数折旧
            # y = y_0 * e ^ (-at), y_0是资产原价, 先计算出a
            tmp = exp_dcr(float(asset.price), valid_length.days, spend_length.days)   
            return round(tmp, 2)
        else:
            # 线性折旧
            tmp =  (1 - float(spend_length / valid_length)) * ori_asset_price 
            return round(tmp, 2) 
    else:
        # 永远有效
        return round(ori_asset_price, 2)


def single_asset_value(asset: Asset):
    # 计算单个资产在过去30天的资产
    # 返回一个长度为15的list

    price_list = []
    for i in range(15):
        price_list.append(single_asset_value_shift(asset, 28-2*i))
    return price_list
    

def compute_days_list():

    # 返回前三十天的日期（每隔两天）
    now_time = get_current_time()
    now_time = now_time.replace(tzinfo=pytz.timezone(TIME_ZONE))

    former_30_days = []
    for i in range(0, 30, 2):
        end_time = now_time + dt.timedelta(days = -i)
        # 前一天时间只保留 年-月-日
        end_date = end_time.strftime('%m.%d') #格式化输出
        former_30_days.append(end_date)
    former_30_days.reverse()
    return former_30_days

def list_add(list1, list2):
    assert len(list1) == len(list2), "list length equal"
    new_list = []
    for i in range(len(list1)):
        new_value = list1[i] + list2[i]
        new_list.append(new_value)
    return new_list


def warn(asset:Asset):

    if asset.warn_type == 0:
        if (asset.number < asset.warn_content):
            return True
        else:
            return False
    elif asset.warn_type == 1:
        if asset.expire != None:
            
            expire_time = asset.expire
            expire_time = expire_time + dt.timedelta(hours=8)
            expire_time = expire_time.replace(tzinfo=pytz.timezone(TIME_ZONE))

            current_time = get_current_time()
            current_time = current_time.replace(tzinfo=pytz.timezone(TIME_ZONE))

            remain_length = expire_time - current_time
            require_length = dt.timedelta(days=asset.warn_content)
            if remain_length < require_length:
                return True
            else:
                return False
        else:
            return False
    else:
        return False
    

def validate_request(asset: Asset, pending_request: PendingRequests):
    # 审核资产申请是否有效
    if pending_request == None or pending_request.result != PENDING:
        return NOT_EXIST
    # 1. 如果想要领用但资产已经被领用了
    if pending_request.type == RECEIVE:
        if asset.user.asset_administrator == 0:
            return DOUBLE_RECEIVE
        if asset.status != IDLE:
            return NOT_IDLE
        if pending_request.initiator.asset_administrator != 0:
            return NOT_USER_RECEIVE
        if pending_request.apply_number != None:
            if pending_request.apply_number > 1 and asset.Class.property == 3:
                # 是条目型资产但是却领用多个
                return ITEM_RECEIVE_LOTS
            if pending_request.apply_number > asset.number:
                # 领用的个数多于剩余的个数
                return RECEIVE_EXCEEDS
    if pending_request.type == RETURN:
        if asset.user.asset_administrator == 1:
            return ALREADY_RETURN
        if asset.status != IN_USE:
            return NOT_IN_USE
        if pending_request.initiator.asset_administrator != 0:
            return NOT_USER_RETURN
    if pending_request.type == MAINTENANCE:
        if asset.user.asset_administrator == 1:
            return ALREADY_RETURN
        if asset.status != IN_USE:
            return NOT_IN_USE
        if pending_request.initiator.asset_administrator != 0:
            return NOT_USER_MAINTENANCE
    if pending_request.type == TRANSFER:
        if asset.user.asset_administrator == 1:
            return ALREADY_RETURN
        if asset.status != IN_USE:
            return NOT_IN_USE
        if pending_request.initiator.asset_administrator != 0:
            return NOT_USER_TRANSFER
        if pending_request.initiator != asset.user:
            return ALREADY_TRANSFER
    return VALID

def parse_year_warn_to_days(year_warn:str):
    my_list = re.split(r'(\d+)', year_warn)
    year_num = int(my_list[1])
    month_num = int(my_list[3])
    day_num = int(my_list[5])
    res = 365 * year_num + 31 * month_num + day_num
    return res

def valid_prop(asset:Asset, prop_name:str, prop_value:str):
    prop_dict = parse_selfprop(asset.property)

    if prop_dict == None:
        # print("valid_prop返回None")
        return 0

    # 没有这个键, 返回0
    if not prop_name in prop_dict:
        return 0

    # 检验是否与prop_value相等
    if prop_dict[prop_name] == prop_value:
        return 1
    else:
        return 0

def valid_prop_key(asset:Asset, prop_name:str):
    prop_dict = parse_selfprop(asset.property)

    if prop_dict == None:
        # print("valid_prop_key返回None")
        return 0

    # 没有这个键, 返回0
    if not prop_name in prop_dict:
        return 0

    return 1

def asset_search(to_search_list:list, data:dict):
    return_list = []
    for asset in to_search_list:
        # 搜ID
        if data["SearchID"] != "ID=-1" and data["SearchID"] != "ID=":
            search_id = int(data["SearchID"][3:])
            if asset.id != search_id:
                continue
        
        # 搜名字,模糊匹配
        if data["SearchName"] != "Name=":
            search_name = data["SearchName"][5:]
            if not search_name in asset.name:
                continue
        
        # 搜类别, 模糊匹配
        # if data["SearchClass"] != "Class=":
        #     search_class = data["SearchClass"][6:]
        #     if not search_class in asset.Class.name:
        #         continue
        
        # 搜状态
        if data["SearchStatus"] != "Status=-1" and data["SearchStatus"] != "Status=":
            search_status = int(data["SearchStatus"][7:])
            if search_status != asset.status:
                continue
        
        # 搜所有者, 模糊搜索
        # if data["SearchOwner"] != "Owner=":
        #     search_owner = data["SearchOwner"][6:]
        #     if not search_owner in asset.user.name:
        #         continue

        # 搜索自定义资产

        # 键和值都有
        if data["SearchProp"] != "Prop=" and data["SearchPropValue"] != "PropValue=":
            search_prop = data["SearchProp"][5:]
            search_prop_value = data["SearchPropValue"][10:]
            if valid_prop(asset, search_prop, search_prop_value) == 0:
                # print("搜索键值return None")
                continue
        
        if data["SearchProp"] != "Prop=" and data["SearchPropValue"] == "PropValue=":
            search_prop = data["SearchProp"][5:]
            if valid_prop_key(asset, search_prop) == 0:
                # print("搜索键return None")
                continue

        return_list.append(asset)

    return return_list
