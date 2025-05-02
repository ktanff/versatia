en2fa_translation = str.maketrans("1234567890", "۱۲۳۴۵۶۷۸۹۰")
en2ar_translation = str.maketrans("1234567890", "١٢٣٤٥٦٧٨٩٠")

_enWeekdays = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday","Saturday", "Sunday"]
_enMonthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
_faWeekdays=["دوشنبه","سه‌شنبه","چهارشنبه","پنج‌شنبه","آدینه","شنبه","یک‌شنبه"]
_faMonthNames=["فروردین","اردی‌بهشت","خرداد","تیر","مرداد","شهریور","مهر","آبان","آذر","دی","بهمن","اسپند"]
_arWeekdays = [ "اثنین", "ثلاثه", "اربعه", "خمس", "جمعه", "سبت","احد"]
_arMonthNames = [
    "محرم", "صفر", "ربیع الاول", "ربیع الثانی",
    "جمادی الاولی", "جمادی الثانی", "رجب", "شعبان",
    "رمضان", "شوال", "ذی القعده", "ذی الحجه"
]

def today_date_line():
    from datetime import datetime
    g_today = datetime.today()
    j_today = gregorian2jalali(g_today)
    q_today = gregorian2lunar(g_today)
    return jalali_format(*j_today)+" برابر است با "+gregorian_format(g_today)+" و "+lunar_format(*q_today)

def gregorian_format(date, weekday=False):
    g_year = date.year
    g_month = date.month
    g_day = date.day
    g_weekday_en = _enWeekdays[date.weekday()]+' ' if weekday else ''
    g_month_en = _enMonthNames[g_month-1]
    return f"{g_weekday_en}{g_day} {g_month_en} {g_year}"

def jalali_format(j_year, j_month, j_day, weekday=None):
    j_weekday_fa = _faWeekdays[weekday]+' ' if weekday else ''
    j_month_fa = _faMonthNames[j_month-1]
    j_day_fa = str(j_day).translate(en2fa_translation)
    j_year_fa = str(j_year).translate(en2fa_translation)
    return f"{j_weekday_fa}{j_day_fa} {j_month_fa} {j_year_fa}"

def lunar_format(qy, qm, qd, wd=None):
    if wd:
        str_lunar_hijri_today = f'{_arWeekdays[wd]}, '
    else:
        str_lunar_hijri_today = ''
    str_lunar_hijri_today += f'{qd} {_arMonthNames[int(qm) - 1]} {qy} هـ.ق'
    str_lunar_hijri_today = str_lunar_hijri_today.translate(en2ar_translation)
    return str_lunar_hijri_today

def gregorian2jalali(date):
    g_year = date.year
    g_month = date.month
    g_day = date.day
    weekday=date.weekday()
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if (g_month > 2):
        gy2 = g_year + 1
    else:
        gy2 = g_year
    days = 355666 + (365 * g_year) + ((gy2 + 3) // 4) - (
        (gy2 + 99) // 100) + ((gy2 + 399) // 400) + g_day + g_d_m[g_month - 1]
    j_year = -1595 + (33 * (days // 12053))
    days %= 12053
    j_year += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        j_year += (days - 1) // 365
        days = (days - 1) % 365
    if (days < 186):
        j_month = 1 + (days // 31)
        j_day = 1 + (days % 31)
    else:
        j_month = 7 + ((days - 186) // 30)
        j_day = 1 + ((days - 186) % 30)
    return j_year, j_month, j_day, weekday

def jalali2gregorian(j_year, j_month, j_day):
    j_year += 1595
    days = -355668 + (365 * j_year) + ((j_year // 33) * 8) + (((j_year % 33) + 3) // 4) + j_day
    if (j_month < 7):
        days += (j_month - 1) * 31
    else:
        days += ((j_month - 7) * 30) + 186
    g_year = 400 * (days // 146097)
    days %= 146097
    if (days > 36524):
        days -= 1
        g_year += 100 * (days // 36524)
        days %= 36524
        if (days >= 365):
            days += 1
    g_year += 4 * (days // 1461)
    days %= 1461
    if (days > 365):
        g_year += ((days - 1) // 365)
        days = (days - 1) % 365
    g_day = days + 1
    if ((g_year % 4 == 0 and g_year % 100 != 0) or (g_year % 400 == 0)):
        kab = 29
    else:
        kab = 28
    sal_a = [0, 31, kab, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    g_month = 0
    while (g_month < 13 and g_day > sal_a[g_month]):
        g_day -= sal_a[g_month]
        g_month += 1
    from datetime import date
    return date(g_year, g_month, g_day)

def gregorian2lunar(date, adjustment=0):
    day = date.day
    month = date.month
    year = date.year
    wd = date.weekday()
    ## الگوریتم کویتی برای تبدیل تاریخ میلادی به هجری قمری
    # convert_gregorian_date_to_str_lunar_hijri
    from math import floor
    day -= adjustment
    if month < 3:
        year -= 1
        month += 12
    a = floor(year / 100.0)
    b = 2 - a + floor(a / 4.0)
    jd = floor(365.25 * (year + 4716)) + floor(30.6001 * (month + 1)) + day + b - 1525
    if jd > 2299160:
        a = floor((jd - 1867216.25) / 36524.25)
        b = 1 + a - floor(a / 4.0)
    bb = jd + b + 1524
    cc = floor((bb - 122.1) / 365.25)
    dd = floor(365.25 * cc)
    ee = floor((bb - dd) / 30.6001)
    day = (bb - dd) - floor(30.6001 * ee)
    month = ee - 1
    if ee > 13:
        cc += 1
        month = ee - 13
    year = cc - 4716
    iyear = 10631.0 / 30.0
    epochastro = 1948084
    shift1 = 8.01 / 60.0
    z = jd - epochastro
    cyc = floor(z / 10631.0)
    z = z - 10631 * cyc
    j = floor((z - shift1) / iyear)
    qy = 30 * cyc + j
    z = z - floor(j * iyear + shift1)
    qm = floor((z + 28.5001) / 29.5)
    if qm == 13:
        qm = 12
    qd = floor(z + 30 - 29.5001 * qm)
    return qy,qm,qd,wd
