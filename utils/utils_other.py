import hashlib

def MD5(password: str):
    hash_object = hashlib.md5()

    # 对数据进行哈希计算
    hash_object.update(password.encode())
    
    # 获取哈希值
    hashed_password = hash_object.hexdigest()
    return hashed_password

def sha256(password: str):
    # 对密码进行SHA256加密
    # 创建 SHA-256 哈希对象
    hash_object = hashlib.sha256()
    
    # 对数据进行哈希计算
    hash_object.update(password.encode())
    
    # 获取哈希值
    hashed_password = hash_object.hexdigest()
    return hashed_password

# 用于调试打印
def debug_print(name, content):
    print("\033[0;31;40m", "----------------------------------------", "\033[0m")
    print(name, content)
    print("\033[0;31;40m", "----------------------------------------", "\033[0m")

def list_to_char(my_list:list):
    my_str = ""
    for item in my_list:
        my_str += '$'
        my_str += str(item)
    return my_str


def parse_children(children_string):
    # 增加children_string==None的一个判断
    if (children_string == None):
        return []
    else:
        children_list = children_string.split('$')
        return children_list[1:]  # 去除最前面的一个空格

def parse_selfprop(self_prop):
    # to dict
    if self_prop == None or self_prop == "":
        # print("parse_selfprop 返回None")
        return None
    answer_dict = {}
    qa_list = self_prop.split('\n')[:-1]
    print(qa_list)
    for qa in qa_list:
        q = qa.split('$')[0]
        a = qa.split('$')[1]
        print(q)
        print(a)
        answer_dict[q] = a
    return answer_dict

def parse_selfprop_to_list(self_prop):
    # to list
    prop_name_list = []
    prop_value_list = []
    if self_prop == None or self_prop == "":
        return prop_name_list, prop_value_list
    qa_list = self_prop.split('\n')[:-1]
    print(qa_list)
    for qa in qa_list:
        q = qa.split('$')[0]
        a = qa.split('$')[1]
        prop_name_list.append(q)
        prop_value_list.append(a)
    return prop_name_list, prop_value_list


def delete_child(children_string, child:int):
    # 从children_string中删除掉一个child
    substr = '$' + str(child)
    pos = children_string.find(substr)

    if pos != -1:
        new_string = children_string[:pos] + children_string[pos+len(substr):]
    else:
        new_string = children_string
        print(f"{substr} not found in string")
    
    return new_string

def split_by_dollar(contents: list):
    result = ""
    for content in contents:
        result += '$'
        result += content
    return result

def dict_to_selfprop(contents: dict):
    res = ""
    for key, value in contents.items():
        res += key
        res += '$'
        res += value
        res += '\n'
    return res
