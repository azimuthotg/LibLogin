from django import template

register = template.Library()

THAI_MONTHS_SHORT = ['', 'ม.ค.', 'ก.พ.', 'มี.ค.', 'เม.ย.', 'พ.ค.', 'มิ.ย.',
                     'ก.ค.', 'ส.ค.', 'ก.ย.', 'ต.ค.', 'พ.ย.', 'ธ.ค.']


@register.filter
def thai_date(value):
    """Format datetime as Thai Buddhist Era date: '9 ม.ค. 2569'"""
    if not value:
        return ''
    try:
        return f"{value.day} {THAI_MONTHS_SHORT[value.month]} {value.year + 543}"
    except Exception:
        return str(value)


@register.filter
def thai_datetime(value):
    """Format datetime as Thai Buddhist Era date+time: '9 ม.ค. 2569 14:30'"""
    if not value:
        return ''
    try:
        return f"{value.day} {THAI_MONTHS_SHORT[value.month]} {value.year + 543} {value.hour:02d}:{value.minute:02d}"
    except Exception:
        return str(value)
