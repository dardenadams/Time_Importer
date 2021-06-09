# Functions to deal with dates and times

import dictionaries
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import math

def is_dst(dt=None, timezone="US/Central"):
	# Returns true if input time is daylight savings time, else false
    if dt is None:
        dt = datetime.utcnow()
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0

def get_pe_date(input_date):
	# Takes a datetime input and calculates the week end date, known as
	# period end date in SL time enty screen.

	# Strip unnecessary time data
	input_date = input_date.date()

	day_map = dictionaries.day_map

	# Calculate delta
	day_delta = 7 - day_map[input_date.weekday()]

	# Add delta to date to get PE date
	pe_date = input_date + timedelta(days=day_delta)

	return pe_date

def to_central_tz(timestamp):
	# Converts raw timestamp data to DST adjusted central time

	# Cleanup and convert to central time
	utc_time = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
	central_time = utc_time - timedelta(hours=6)

	# Adjust delta if daylight savings time applies
	if is_dst(central_time):
		central_time = central_time + timedelta(hours=1)

	return central_time

def get_fp(pe_date):
    # Returns relevent fiscal period in yyyymm format
    year = pe_date.strftime("%Y")
    month = pe_date.strftime("%m")
    return year + month

def get_week(pe_date):
    # Returns the relevent week number in 0int format. Calculate by dividing
    # period end date by 7 then rounding up.
    week = int(math.ceil(float(pe_date.day) / 7))
    week = '0' + str(week)

    return week
