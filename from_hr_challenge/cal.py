import datetime
import calendar

print(
    calendar.day_name[datetime.datetime.strptime(input(), "%m %d %Y").weekday()].upper()
)
