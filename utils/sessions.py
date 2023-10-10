# honorcode: https://github.com/c7w/ReqMan-backend/blob/dev/utils/sessions.py
from User.models import SessionPool, User
import pytz
import datetime as dt
from CS_Company_backend.settings import TIME_ZONE
import random
import string
from django.http import HttpRequest, HttpResponse
from rest_framework.request import Request
import json
from utils.utils_require import MAX_CHAR_LENGTH, CheckRequire, require

def get_session_id(request: Request):
    if (request.method == "POST") or (request.method == "PUT"):
        tmp_body = request.body.decode("utf-8") 
        try:
            body = json.loads(tmp_body) 
        except BaseException as error:
            print("During get_session_id: ", error, tmp_body)
        SessionID = require(body, "SessionID", "string",
                    err_msg="Missing or error type of SessionID")
        return SessionID        
    # elif request.method == "GET":
    #     print(request.GET)
    #     SessionID = require(request.GET, "SessionID", "string",
    #                 err_msg="Missing or error type of SessionID")
    #     return SessionID
    # elif request.method == "DELETE":
    #     print(request.DELETE)
    #     SessionID = require(request.DELETE, "SessionID", "string",
    #                 err_msg="Missing or error type of SessionID")
    #     return SessionID
    

# def set_session_id(response):
#     sessionId = "".join(random.sample(string.ascii_letters + string.digits, 32))
#     response.set_cookie("sessionId", sessionId, expires=60 * 60 * 24 * EXPIRE_DAYS)
#     return response

# def verify_session_id(sessionId):
#     sessionRecord =SessionPool.objects.filter(sessionId=sessionId).first()
#     if sessionRecord:
#         if sessionRecord.expireAt < dt.datetime.now(pytz.timezone(TIME_ZONE)):
#             SessionPool.objects.filter(sessionId=sessionId).delete()
#             return None
#         return sessionRecord.user
#     else:
#         return None

def bind_session_id(sessionId: str, user: User):
    # 将一个sessionId与一个用户进行绑定
    # TODO: 合理地设置expireAt的时间
    SessionPool.objects.create(sessionId=sessionId, user=user)

def disable_session_id(sessionId: str):
    # 用户登出之后,将session删除
    record = SessionPool.objects.filter(sessionId=sessionId).first()
    if record:
        record.delete()
    print("successfully disable session id!")