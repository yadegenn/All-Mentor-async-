import copy
from datetime import datetime

import pytz

from middlewares.timeout import user_data, group_data
async def checker():
    global weekend, latehour,rules_checker
    for i in rules_checker:
        rules = i
        rule_type = rules["type"]
        if (rule_type == "private"):

            rule_timeout = rules["timeout"]
            rule_action = rules["action"]
            for i in copy.deepcopy(user_data):
                if (user_data[i] == "delete"):
                    del user_data[i]
                elif (isinstance(user_data[i], datetime)):
                    timeout_date = user_data[i] + rule_timeout
                    if (timeout_date <= datetime.now()):
                        await rule_action(i)
                        del user_data[i]
        elif (rule_type == "group"):
            rule_timeout = rules["timeout"]
            rule_action = rules["action"]
            for i in copy.deepcopy(group_data):
                if (group_data[i] == "delete"):
                    del group_data[i]
                elif (isinstance(group_data[i], datetime)):
                    timeout_date = group_data[i] + rule_timeout
                    if (timeout_date <= datetime.now()):
                        await rule_action(i)
                        del group_data[i]
        elif (rule_type == "weekend"):
            rule_day = rules["day"]
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = datetime.now(moscow_tz)
            day_of_week = moscow_time.weekday()
            if (day_of_week == rule_day):
                weekend = True
            else:
                weekend = False
        elif (rule_type == "latehour"):
            rule_hour = int(rules["hour"])
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = datetime.now(moscow_tz)
            current_hour = moscow_time.hour
            if (current_hour >= rule_hour):
                latehour = True
            else:
                latehour = False