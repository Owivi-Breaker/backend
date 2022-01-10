# 日期处理类
import datetime

from utils import logger


class Date:
    def __init__(self, *args):
        if len(args) >= 3:
            self.year, self.month, self.day = args
        elif len(args) == 1 and isinstance(args[0], str):
            self.year, self.month, self.day = [int(x) for x in args[0].split('-')]
        self.date = datetime.date(self.year, self.month, self.day)

    def get_date(self):
        return self.date

    def plus_days(self, days: int = 1):
        """
        当前日期加days天
        """
        self.date += datetime.timedelta(days=days)

    def __str__(self, date_format: str = "%Y-%m-%d"):
        return self.date.strftime(date_format)
