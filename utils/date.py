import datetime


class Date:
    def __init__(self, year, month, day):
        self.year = year
        self.month = month
        self.day = day
        self.date = datetime.date(year, month, day)

    def get_date(self):
        return self.date

    def plus_days(self, days: int):
        self.date += datetime.timedelta(days=days)

    def __str__(self, date_format: str = "%Y-%m-%d"):
        return self.date.strftime(date_format)
