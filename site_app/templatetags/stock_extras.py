import datetime
import pandas as pd
import math

from django import template

register = template.Library()

@register.filter(name="as_percentage")
def as_percentage(decimal):
    return '{0:.2%}'.format(decimal)

@register.filter(name="format_date_table")
def format_date_table(pandas_date):
    # dt = pandas.DatetimeIndex(periods=10, start='2014-02-01', freq='10T')
    # date.format(formatter=lambda x: x.strftime('%b'))
    if (pd.notnull(pandas_date)):
        dt = pandas_date.to_datetime()
        return dt.strftime('%b. %-d, %Y, %-I:%M%P')
    else:
        return ('')

@register.filter(name="format_large_nums")
def format_large_nums(entry):
    if (pd.notnull(entry)):
        if entry<1000000000:
            return('$'+str(math.floor(entry/1000000))+'M')
        else:
            return('$'+str(round(entry/1000000000,2))+'B')
    else:
        return ('n.a.')

@register.filter(name="format_dollar_value")
def format_dollar_value(entry):
    if (pd.notnull(entry)):
        return('$'+format(math.floor(entry),','))
    else:
        return ('n.a.')


# @register.filter(name="convert_timestamp")
# def convert_timestamp(data):
#     new_list = []

#     for item in data:
#         for key in item.keys():
#             if isinstance(item[key], pd.tslib.Timestamp):
#                 date = item[key]
#                 dt = date.to_datetime()
#                 item[key] = dt.strftime('%Y-%m-%d')

#     return data
