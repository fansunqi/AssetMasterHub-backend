# honorcode: from https://github.com/c7w/ReqMan-backend/blob/dev/utils/model_date.py
import datetime as dt


def get_timestamp():
    return (dt.datetime.now()).timestamp()

def get_current_time():
    return dt.datetime.now()

def get_datetime():
    return dt.datetime.now() + dt.timedelta(hours=48)

def get_30_days_before():
    return dt.datetime.now() + dt.timedelta(days=-30)



def time_string_to_datetime(data):
    if "Time" in data and data["Time"] != None:
        time_string = data["Time"]
        year = int(time_string[0:4])
        month = int(time_string[5:7])
        day = int(time_string[8:10])
        hour = int(time_string[11:13])
        minute = int(time_string[14:16])
        second = int(time_string[17:19])

        date_time = dt.datetime(year,month,day,hour,minute,second)

        return date_time
    else:
        return None
