import datetime


schedule_time = datetime.time(hour=10, minute=23)
now = datetime.datetime(hour=10, minute=20, second=5, microsecond=123145, year=2016, month=3, day=16)
# now = datetime.datetime.now()


today_schedule_datetime = datetime.datetime(year=now.year, month=now.month, day=now.day,
                                            hour=schedule_time.hour, minute=schedule_time.minute,
                                            microsecond=schedule_time.microsecond)

if today_schedule_datetime > now:
    schedule_delta = today_schedule_datetime - now
else:
    tomorrow_schedule_datetime = today_schedule_datetime + datetime.timedelta(days=1)
    schedule_delta = tomorrow_schedule_datetime - now

print schedule_delta
print schedule_delta.seconds
