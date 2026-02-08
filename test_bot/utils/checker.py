import copy
from datetime import datetime, timedelta

import pytz

from .db import delete_user_week_period, get_all_user_week_period
from ..utils.db import init_db
from .waits_func import scheduled_reminder, weekday_personal, clean_log
from ..middlewares.timeout import user_reminder, user_weekday_period
from ..loader import bot, is_weekday_period, is_scheduled_message
from ..utils.translator import _





rules_checker = [
    {"type": "log_clean",
             "timeout": timedelta(days=2),
             "date": datetime.now(),
             "action": clean_log}
]

if(is_scheduled_message):
    rules_checker.append({"type": "reminder",
                          "timeout": timedelta(seconds=int(_("sheduled_time")) if _("sheduled_time").isdigit() else 0),
                          "action": scheduled_reminder})
if(is_weekday_period):
    rules_checker.append({"type": "periodic_weekday",
         "timeout": timedelta(seconds=int(_("periodic_weekday_time")) if _("periodic_weekday_time").isdigit() else 0),
         "action": weekday_personal} if is_weekday_period else {"type": "none"})
# rules_checker.append({"type": "weekend", "day": 6} if is_weekend_have else {"type": "none"})
# rules_checker.append({"type": "latehour", "hour": 19} if is_latehour_have else {"type": "none"})

async def checker():
    global rules_checker
    for i in rules_checker:
        rules = i
        rule_type = rules["type"]
        if (rule_type == "reminder"):

            rule_timeout = rules["timeout"]
            rule_action = rules["action"]
            for i in copy.deepcopy(user_reminder):
                if (user_reminder[i] == "delete"):
                    del user_reminder[i]
                elif (isinstance(user_reminder[i], datetime)):
                    timeout_date = user_reminder[i] + rule_timeout
                    if (timeout_date <= datetime.now()):
                        await rule_action(i)
                        del user_reminder[i]
        if (rule_type == "periodic_weekday"):

            rule_timeout = rules["timeout"]
            for i in copy.deepcopy(user_weekday_period):
                if (user_weekday_period[i] == "delete"):
                    await delete_user_week_period(i)
                    del user_weekday_period[i]
                elif (isinstance(user_weekday_period[i], datetime)):
                    timeout_date = user_weekday_period[i] + rule_timeout
                    if (timeout_date <= datetime.now().astimezone()):
                        await delete_user_week_period(i)
                        del user_weekday_period[i]
        if (rule_type == "log_clean"):
            rule_timeout = rules["timeout"]
            rule_action = rules["action"]
            timeout_date = rules["date"] + rule_timeout
            if (timeout_date <= datetime.now()):
                await rule_action()
                rules["date"] = datetime.now()
        # elif (rule_type == "group"):
        #     rule_timeout = rules["timeout"]
        #     rule_action = rules["action"]
        #     for i in copy.deepcopy(group_data):
        #         if (group_data[i] == "delete"):
        #             del group_data[i]
        #         elif (isinstance(group_data[i], datetime)):
        #             timeout_date = group_data[i] + rule_timeout
        #             if (timeout_date <= datetime.now()):
        #                 await rule_action(i)
        #                 del group_data[i]
        # elif (rule_type == "weekend"):
        #     rule_day = rules["day"]
        #     moscow_tz = pytz.timezone('Europe/Moscow')
        #     moscow_time = datetime.now(moscow_tz)
        #     day_of_week = moscow_time.weekday()
        #     if (day_of_week == rule_day):
        #         weekend = True
        #     else:
        #         weekend = False
        # elif (rule_type == "latehour"):
        #     rule_hour = int(rules["hour"])
        #     moscow_tz = pytz.timezone('Europe/Moscow')
        #     moscow_time = datetime.now(moscow_tz)
        #     current_hour = moscow_time.hour
        #     if (current_hour >= rule_hour):
        #         latehour = True
        #     else:
        #         latehour = False