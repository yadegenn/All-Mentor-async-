from datetime import datetime, timedelta, time

current_hour = datetime.combine((datetime.now() + timedelta(days=1)).date(), time())
rule_hour = 20

print(current_hour)
if(current_hour.hour>=rule_hour):
    print("сработало")