from transformer.exceptions.s_exception import FormatError, TimeZoneError
from datetime import date, time, datetime, timezone, timedelta
from tzlocal import get_localzone
import pytz
import calendar
import re


class TimePoint:
    NOW = 'NOW'

    DATE = 'DATE'
    TIME = 'TIME'
    LOCALTIME = 'LOCALTIME'
    DATETIME = 'DATETIME'
    LOCALDATETIME = 'LOCALDATETIME'

    time_point_type = LOCALDATETIME

    # 根据时间点类型获取当前时间的时间点对象
    def now(self):
        if self.time_point_type == self.DATE:
            return datetime.now().date()
        elif self.time_point_type == self.TIME:
            return datetime.now(timezone.utc).time()
        elif self.time_point_type == self.LOCALTIME:
            return datetime.now(get_localzone()).time()
        elif self.time_point_type == self.DATETIME:
            return datetime.now(timezone.utc)
        elif self.time_point_type == self.LOCALDATETIME:
            return datetime.now(get_localzone())

    def min(self):
        if self.time_point_type == self.DATE:
            return date.min
        elif self.time_point_type in [self.TIME, self.LOCALTIME]:
            return time.min
        elif self.time_point_type in [self.DATETIME, self.LOCALDATETIME]:
            return datetime.min

    # 转换为时间戳
    def timestamp(self):
        if self.time_point_type == self.DATE:
            return datetime.combine(self.date, time(0)).timestamp()
        elif self.time_point_type in [self.TIME, self.LOCALTIME]:
            return datetime.combine(date(1970, 1, 1), self.time).timestamp()
        elif self.time_point_type in [self.DATETIME, self.LOCALDATETIME]:
            return self.datetime.timestamp()

    def __lt__(self, other):
        if self.time_point_type == other.time_point_type:
            if self.time_point_type == self.DATE:
                return self.date < other.date
            elif self.time_point_type in [self.TIME, self.LOCALTIME]:
                return self.time < other.time
            elif self.time_point_type in [self.DATETIME, self.LOCALDATETIME]:
                return self.datetime < other.datetime
        raise TypeError(
            "'<' not supported between instances of '" + self.time_point_type + "' and '" + other.time_point_type + "'.")


class NOW(TimePoint):

    def __init__(self, time_point_type=TimePoint.time_point_type):
        if time_point_type not in [self.DATE, self.TIME, self.LOCALTIME, self.DATETIME, self.LOCALDATETIME]:
            raise ValueError(
                "The time point type must be 'DATE', 'TIME', 'LOCALTIME', 'DATETIME' or 'LOCALDATETIME'.")
        self.time_point_type = time_point_type

    def __getattribute__(self, name):
        if name == 'date' and self.time_point_type == self.DATE:
            return datetime.now().date()
        elif name == 'time':
            if self.time_point_type == self.TIME:
                return datetime.now(timezone.utc).time()
            elif self.time_point_type == self.LOCALTIME:
                return datetime.now(get_localzone()).time()
        elif name == 'datetime':
            if self.time_point_type == self.DATETIME:
                return datetime.now(timezone.utc)
            elif self.time_point_type == self.LOCALDATETIME:
                return datetime.now(get_localzone())
        return TimePoint.__getattribute__(self, name)

    def __str__(self):
        return str(self.now())


class Date(TimePoint):
    time_point_type = TimePoint.DATE

    date_pattern = "(?P<year>\d{4})(-?((?P<month>\d{2})(-?(?P<day>\d{2})?)|" \
                   "(W(?P<week>\d{2})(-?(?P<day_of_week>\d))?)|" \
                   "(Q(?P<quarter>\d)(-?(?P<day_of_quarter>\d{2}))?)|" \
                   "(?P<ordinal_day>\d{3})))?"

    def __init__(self, date_input=None):
        if isinstance(date_input, str):
            date_input = date_input.strip()
            if re.match(self.date_pattern, date_input):
                date_info = re.search(self.date_pattern, date_input)
                self.date = self.date_parse(date_info)
            else:
                raise FormatError('The format of the date string is incorrect.')
        elif isinstance(date_input, dict):
            for key in ['year', 'month', 'day', 'week', 'day_of_week', 'quarter', 'day_of_quarter', 'ordinal_day']:
                date_input.setdefault(key, None)
            # 至少指定year
            if date_input['year']:
                if int(date_input['month'] is None) + int(date_input['week'] is None) + int(
                        date_input['quarter'] is None) + int(date_input['ordinal_day'] is None) < 3:
                    raise FormatError('The combination of the date components is incorrect.')
                if (date_input['day'] and not date_input['month']) or (
                        date_input['day_of_week'] and not date_input['week']) or (
                        date_input['day_of_quarter'] and not date_input['quarter']):
                    raise FormatError('The combination of the date components is incorrect.')
                self.date = self.date_parse(date_input)
            else:
                raise FormatError('The combination of the date components is incorrect.')
        elif date_input is None:
            self.date = self.now()
        else:
            raise TypeError('The type of the date input is wrong.')

    @staticmethod
    def date_parse(date_info):
        data_string = str(date_info['year']).rjust(4, '0')
        data_pattern = '%Y'
        if date_info['month']:
            if not date_info['day']:
                data_string = data_string + str(date_info['month']).rjust(2, '0') + '01'
            else:
                data_string = data_string + str(date_info['month']).rjust(2, '0') + str(date_info['day']).rjust(2, '0')
            data_pattern = data_pattern + '%m%d'
        elif date_info['week']:
            if not date_info['day_of_week']:
                data_string = data_string + str(int(date_info['week']) - 1).rjust(2, '0') + '1'
            else:
                data_string = data_string + str(int(date_info['week']) - 1).rjust(2, '0') + date_info['day_of_week']
            data_pattern = data_pattern + '%W%u'
        elif date_info['quarter']:
            if not date_info['day_of_quarter']:
                day_of_quarter = 1
            else:
                day_of_quarter = int(date_info['day_of_quarter'])
            # 将一年中的第q个季节的第d天，转换为一年中的m月n日
            year = int(date_info['year'])
            feb_days = calendar.monthrange(year, 2)[1]
            quarter = [1, 4, 7, 10]
            quarter_length = [31, feb_days + 31, feb_days + 62, 30, 61, 91, 31, 62, 92, 31, 61, 92]
            month = quarter[int(date_info['quarter']) - 1]
            if day_of_quarter <= quarter_length[month - 1]:
                day_of_month = day_of_quarter
            elif day_of_quarter <= quarter_length[month]:
                day_of_month = day_of_quarter - quarter_length[month - 1]
                month = month + 1
            elif day_of_quarter <= quarter_length[month + 1]:
                day_of_month = day_of_quarter - quarter_length[month]
                month = month + 2
            else:
                raise ValueError("The day of quarter must be in 1..90(,91,92).")
            data_string = data_string + str(month).rjust(2, '0') + str(day_of_month).rjust(2, '0')
            data_pattern = data_pattern + '%m%d'
        else:
            if not date_info['ordinal_day']:
                data_string = data_string + '001'
            else:
                data_string = data_string + str(date_info['ordinal_day']).rjust(3, '0')
            data_pattern = data_pattern + '%j'
        return datetime.strptime(data_string, data_pattern).date()

    def __str__(self):
        return str(self.date)


class Time(TimePoint):
    time_point_type = TimePoint.TIME

    # 暂不支持纳秒
    time_pattern = "(?P<hour>\d{2})(:?(?P<minute>\d{2})((:?(?P<second>\d{2}))((.|,)(?P<microsecond>\d{1,6}))?)?)?"
    timezone_pattern = "(?P<Z>Z)|(\[(?P<zone_name1>[\w/]+)\])|(((?P<plus>\+)|(?P<minus>-))(?P<hours>\d{2})(:?(?P<minutes>\d{2}))?(\[(?P<zone_name2>[\w/]+)\])?)"
    global_time_pattern = 'T?(?P<time>(' + time_pattern + '))[ ]*(?P<timezone>(' + timezone_pattern + '))?'

    def __init__(self, time_input=None):
        if isinstance(time_input, str):
            time_input = time_input.strip()
            if re.match(self.global_time_pattern, time_input):
                time_info = re.search(self.global_time_pattern, time_input)
                self.time = self.time_parse(time_info).replace(tzinfo=timezone.utc)
                if time_info["timezone"]:
                    self.time = self.time.replace(tzinfo=self.timezone_parse(time_info))
            else:
                raise FormatError('The format of the time string is incorrect.')
        elif isinstance(time_input, dict):
            key_num = 0
            for key in ['hour', 'minute', 'second', 'millisecond', 'microsecond', 'timezone']:
                time_input.setdefault(key, None)
                if time_input[key]:
                    key_num = key_num + 1
            # 至少指定hour或timezone
            if time_input['hour']:
                if time_input['millisecond']:
                    if time_input['millisecond'] > 999:
                        raise ValueError('Millisecond must be in 0..999')
                    if not time_input['microsecond']:
                        time_input['microsecond'] = 0
                    time_input['microsecond'] = time_input['microsecond'] + time_input['millisecond'] * 1000
                self.time = self.time_parse(time_input)
                if time_input['timezone']:
                    self.time = self.time.replace(tzinfo=self.timezone_parse(time_input['timezone']))
            elif time_input['timezone'] and key_num == 1:
                self.time = datetime.now(self.timezone_parse(time_input['timezone'])).time()
            else:
                raise FormatError('The combination of the time components is incorrect.')
        elif time_input is None:
            self.time = self.now()
        else:
            raise TypeError('The type of the time input is wrong.')

    @staticmethod
    def time_parse(time_info):
        minute = second = microsecond = 0
        if time_info['minute']:
            minute = int(time_info['minute'])
        if time_info['second']:
            second = int(time_info['second'])
        if time_info['microsecond']:
            microsecond = int(str(time_info['microsecond']).ljust(6, '0'))
        return time(hour=int(time_info['hour']), minute=minute, second=second, microsecond=microsecond)

    @staticmethod
    def timezone_parse(timezone_info):
        if timezone_info['Z']:
            return timezone.utc
        elif timezone_info['zone_name1']:
            return pytz.timezone(timezone_info['zone_name1'])
        else:
            hours = int(timezone_info['hours'])
            minutes = 0
            if timezone_info['minutes']:
                minutes = int(timezone_info['minutes'])
            if timezone_info['minus']:
                hours = -hours
                minutes = -minutes
            time_delta1 = timedelta(hours=hours, minutes=minutes)
            if timezone_info['zone_name2']:
                pz = pytz.timezone(timezone_info['zone_name2'])
                time_delta2 = datetime.now(pz).utcoffset()
                if time_delta1 == time_delta2:
                    return timezone(time_delta1, timezone_info['zone_name2'])
                else:
                    raise TimeZoneError("The offset and the zone name are not matched.")
            else:
                return timezone(time_delta1)

    def __str__(self):
        return str(self.time)


class LocalTime(TimePoint):
    time_point_type = TimePoint.LOCALTIME

    def __init__(self, localtime_input=None):
        if isinstance(localtime_input, str):
            localtime_input = localtime_input.strip()
            if re.match(Time.time_pattern, localtime_input):
                localtime_info = re.search(Time.time_pattern, localtime_input)
                self.time = Time.time_parse(localtime_info).replace(tzinfo=get_localzone())
            else:
                raise FormatError('The format of the localtime string is incorrect')
        elif isinstance(localtime_input, dict):
            for key in ['hour', 'minute', 'second', 'millisecond', 'microsecond']:
                localtime_input.setdefault(key, None)
            # 至少指定hour
            if localtime_input['hour']:
                if localtime_input['millisecond']:
                    if not localtime_input['microsecond']:
                        localtime_input['microsecond'] = 0
                    localtime_input['microsecond'] = localtime_input['microsecond'] + localtime_input[
                        'millisecond'] * 1000
                self.time = Time.time_parse(localtime_input).replace(tzinfo=get_localzone())
            else:
                raise FormatError('The combination of the time components is incorrect.')
        elif localtime_input is None:
            self.time = self.now()
        else:
            raise TypeError('The type of the localtime input is wrong.')

    def __str__(self):
        return str(self.time)


class DateTime(TimePoint):
    time_point_type = TimePoint.DATETIME

    datetime_pattern = '(?P<date>' + Date.date_pattern + ')((?P<time>[ ]*(T| )[ ]*(' + Time.time_pattern + '))[ ]*(?P<timezone>(' + Time.timezone_pattern + '))?)?'

    def __init__(self, datetime_input=None):
        if isinstance(datetime_input, str):
            datetime_input = datetime_input.strip()
            if re.match(self.datetime_pattern, datetime_input):
                datetime_info = re.search(self.datetime_pattern, datetime_input)
                date_var = Date.date_parse(datetime_info)
                time_var = time(tzinfo=timezone.utc)
                if datetime_info['time']:
                    time_var = Time.time_parse(datetime_info)
                    if datetime_info['timezone']:
                        time_var = time_var.replace(tzinfo=Time.timezone_parse(datetime_info))
                self.datetime = datetime.combine(date_var, time_var)
            else:
                raise FormatError('The format of the localtime string is incorrect.')
        elif isinstance(datetime_input, dict):
            key_num = 0
            for key in ['year', 'month', 'day', 'week', 'day_of_week', 'quarter', 'day_of_quarter', 'ordinal_day',
                        'hour', 'minute', 'second', 'millisecond', 'microsecond', 'timezone']:
                datetime_input.setdefault(key, None)
                if datetime_input[key]:
                    key_num = key_num + 1
            # 至少指定year或timezone
            if datetime_input['year']:
                if int(datetime_input['month'] is None) + int(datetime_input['week'] is None) + int(
                        datetime_input['quarter'] is None) + int(datetime_input['ordinal_day'] is None) < 3:
                    raise FormatError('The combination of the date components is incorrect.')
                if (datetime_input['day'] and not datetime_input['month']) or (
                        datetime_input['day_of_week'] and not datetime_input['week']) or (
                        datetime_input['day_of_quarter'] and not datetime_input['quarter']):
                    raise FormatError('The combination of the date components is incorrect.')
                date_var = Date.date_parse(datetime_input)
                if datetime_input['millisecond']:
                    if not datetime_input['microsecond']:
                        datetime_input['microsecond'] = 0
                    datetime_input['microsecond'] = datetime_input['microsecond'] + datetime_input['millisecond'] * 1000
                time_var = Time.time_parse(datetime_input).replace(tzinfo=timezone.utc)
                if datetime_input['timezone']:
                    time_var = time_var.replace(tzinfo=Time.timezone_parse(datetime_input['timezone']))
                self.datetime = datetime.combine(date_var, time_var)
            elif datetime_input['timezone'] and key_num == 1:
                self.datetime = datetime.now(Time.timezone_parse(datetime_input['timezone']))
            else:
                raise FormatError('The combination of the datetime components is incorrect.')
        elif datetime_input is None:
            self.datetime = self.now()
        else:
            raise TypeError('The type of the datetime input is wrong.')

    def __str__(self):
        return str(self.datetime)


class LocalDateTime(TimePoint):
    time_point_type = TimePoint.LOCALDATETIME

    localdatetime_pattern = '(?P<date>' + Date.date_pattern + ')(?P<time>[ ]*(T| )[ ]*(' + Time.time_pattern + '))?'

    def __init__(self, localdatetime_input=None):
        if isinstance(localdatetime_input, str):
            localdatetime_input = localdatetime_input.strip()
            if re.match(self.localdatetime_pattern, localdatetime_input):
                localdatetime_info = re.search(self.localdatetime_pattern, localdatetime_input)
                date_var = Date.date_parse(localdatetime_info)
                time_var = time(tzinfo=get_localzone())
                if localdatetime_info['time']:
                    time_var = Time.time_parse(localdatetime_info).replace(tzinfo=get_localzone())
                self.datetime = datetime.combine(date_var, time_var)
            else:
                raise FormatError('The format of the localdatetime string is incorrect.')
        elif isinstance(localdatetime_input, dict):
            for key in ['year', 'month', 'day', 'week', 'day_of_week', 'quarter', 'day_of_quarter', 'ordinal_day',
                        'hour', 'minute', 'second', 'millisecond', 'microsecond']:
                localdatetime_input.setdefault(key, None)
            # 至少指定year
            if localdatetime_input['year']:
                if int(localdatetime_input['month'] is None) + int(localdatetime_input['week'] is None) + int(
                        localdatetime_input['quarter'] is None) + int(localdatetime_input['ordinal_day'] is None) < 3:
                    raise FormatError('The combination of the date components is incorrect.')
                if (localdatetime_input['day'] and not localdatetime_input['month']) or (
                        localdatetime_input['day_of_week'] and not localdatetime_input['week']) or (
                        localdatetime_input['day_of_quarter'] and not localdatetime_input['quarter']):
                    raise FormatError('The combination of the date components is incorrect.')
                date_var = Date.date_parse(localdatetime_input)
                if localdatetime_input['millisecond']:
                    if not localdatetime_input['microsecond']:
                        localdatetime_input['microsecond'] = 0
                    localdatetime_input['microsecond'] = localdatetime_input['microsecond'] + localdatetime_input[
                        'millisecond'] * 1000
                time_var = Time.time_parse(localdatetime_input).replace(tzinfo=get_localzone())
                self.datetime = datetime.combine(date_var, time_var)
            else:
                raise FormatError('The combination of the localdatetime components is incorrect.')
        elif localdatetime_input is None:
            self.datetime = self.now()
        else:
            raise TypeError('The type of the localdatetime input is wrong.')

    def __str__(self):
        return str(self.datetime)


class Duration:
    # 与Cypher不同（没有年属性、月属性和季节属性）
    duration_pattern = 'P([ ]*(?P<weeks>[\d]{1,64})W)?([ ]*(?P<days>[\d]{1,64})D)?([ ]*(?P<hours>[\d]{1,64})H)?([ ]*(?P<minutes>[\d]{1,64})M)?([ ]*(?P<seconds>[\d]{1,64})((.|,)([\d]{1,6}))?S)?'

    def __init__(self, duration_input=None):
        if isinstance(duration_input, str):
            self.duration = self.duration_parse(duration_input)
        elif isinstance(duration_input, dict):
            for key in ['weeks', 'days', 'hours', 'minutes', 'seconds', 'milliseconds', 'microseconds']:
                duration_input.setdefault(key, None)
            # 至少拥有一个组件
            if not (duration_input['weeks'] or duration_input['days'] or duration_input['hours'] or duration_input[
                'minutes'] or duration_input['seconds'] or duration_input['milliseconds'] or duration_input[
                        'microseconds']):
                raise FormatError('At least one component.')
            self.duration = timedelta()
            if duration_input['weeks']:
                self.duration = self.duration + timedelta(weeks=int(duration_input['weeks']))
            if duration_input['days']:
                self.duration = self.duration + timedelta(days=int(duration_input['days']))
            if duration_input['hours']:
                self.duration = self.duration + timedelta(hours=int(duration_input['hours']))
            if duration_input['minutes']:
                self.duration = self.duration + timedelta(minutes=int(duration_input['minutes']))
            if duration_input['seconds']:
                self.duration = self.duration + timedelta(seconds=float(duration_input['seconds']))
            if duration_input['milliseconds']:
                self.duration = self.duration + timedelta(milliseconds=float(duration_input['milliseconds']))
            if duration_input['microseconds']:
                self.duration = self.duration + timedelta(microseconds=float(duration_input['microseconds']))
        elif duration_input is None:
            self.duration = timedelta()
        else:
            raise TypeError('The type of the duration input is wrong.')

    def duration_parse(self, duration_expression):
        duration_pattern = '^[ ]*' + self.duration_pattern + '[ ]*$'
        duration = timedelta()
        if re.match(duration_pattern, duration_expression):
            duration_info = re.search(duration_pattern, duration_expression)
            if duration_info['weeks']:
                duration = duration + timedelta(weeks=int(duration_info['weeks']))
            if duration_info['days']:
                duration = duration + timedelta(days=int(duration_info['days']))
            if duration_info['hours']:
                duration = duration + timedelta(hours=int(duration_info['hours']))
            if duration_info['minutes']:
                duration = duration + timedelta(minutes=int(duration_info['minutes']))
            if duration_info['seconds']:
                duration = duration + timedelta(seconds=float(duration_info['seconds']))
            return duration
        else:
            raise FormatError('The format of the duration string is incorrect.')

    def __str__(self):
        return str(self.duration)

    def total_seconds(self):
        return self.duration.total_seconds()


class Interval:

    def __init__(self, interval_from: Date | Time | LocalTime | DateTime | LocalDateTime,
                 interval_to: Date | Time | LocalTime | DateTime | LocalDateTime | str):
        if interval_from.__class__ == interval_to.__class__:
            if interval_from > interval_from:
                raise ValueError("The start time cannot be later than the end time.")
            self.interval_from = interval_from
            self.interval_to = interval_to
        elif interval_to == TimePoint.NOW:
            self.interval_from = interval_from
            self.interval_to = NOW(interval_from.time_point_type)
        else:
            raise TypeError("The types of interval.from and interval.to have to be same.")

    def __str__(self):
        return '[' + str(self.interval_from) + ', ' + str(self.interval_to) + ']'
