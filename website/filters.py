from datetime import datetime

import dateutil.parser

filters = {
    "format_datestring": lambda s: format_datestring(s),
    "format_month_year": lambda s: format_month_year(s),
    "humanize": lambda s: humanize(s),
    "format_year_month": lambda s: format_year_month(s),
}


def format_datestring(date_string):
    """Filter for formatting a date string in a Jinja template."""
    try:
        # check if this is an ISO date string with no time, just a date
        datetime.strptime(date_string, "%Y-%m-%d")
        # if so, then return the date only
        parsed = dateutil.parser.parse(date_string)
        return parsed.strftime("%d %B %Y")
    except ValueError:
        parsed = dateutil.parser.parse(date_string)
        return parsed.strftime("%d %B %Y, %H:%M")


def format_month_year(date_string):
    formatted = format_datestring(date_string)
    parsed = dateutil.parser.parse(formatted)
    return parsed.strftime("%B %Y")


def humanize(text):
    return text.replace("-", " ").capitalize()


def format_year_month(year_month):
    if year_month:
        year, month = year_month
        date = datetime(year=year, month=month, day=1)
        return date.strftime("%B %Y")
    return ""
