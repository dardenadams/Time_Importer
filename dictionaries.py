# SQL tables mapped to dictionaries

# Constants
approver_num = 1144 # Approver user number (Eric Prater=1144)
approver_id = 'EPRATER'  # Approver user ID
logpath = 'C:\\Script\Time-Importer\\Logs' # Root directory for log files

def get_key(in_dict, in_val):
	# Returns the first key associated with the input dictionary value
	out_key = None
	for key in in_dict:
		if in_dict[key] == in_val:
			out_key = key
	return out_key

def get_header_str(dictionary):
	# Returns a concatenated string of header data for a SQL insert
	header = ''
	counter = 0
	for item in dictionary:
		if counter == 0:
		    header += str(item)
		else:
		    header += ', ' + str(item)
		counter += 1
	return header

def get_row_str(dictionary):
	# Returns a concatenated string of row data for a SQL insert
	row = ''
	counter = 0
	for item in dictionary:
		if counter == 0:
		    row += '\'' + str(dictionary[item]) + '\''
		else:
		    row += ', \'' + str(dictionary[item]) + '\''
		counter += 1
	return row

# List converting Python day ints to Dynamics day ints
# Python: 0 = Monday
# Dynamics: 3 = Monday
day_map = [3, 4, 5, 6, 7, 1, 2]

sql_tables = [
	'PJLABHDR',
	'PJLABDET'
]

files = [
	f'{logpath}\\Last_Run_Log.txt',
	f'{logpath}\\Inserted_docnbrs.txt',
	f'{logpath}\\Inserted_linenbrs.txt',
	f'{logpath}\\Updated_linenbrs.txt',
	f'{logpath}\\TWIDs_Tagged_Imported.txt'
]

# PJLABHDR, header data
pjlabhdr = {
	'Approver': approver_num,
	'BaseCuryId': 'USD',
	'CpnyId_home': 'ENV',
	'crtd_datetime': 'set_cur_time',
	'crtd_prog': 'SCRIPT',
	'crtd_user': 'set_user_id', # First initial/last name user ID
	'CuryEffDate': '1900-01-01 00:00:00',
	'CuryId': 'USD',
	'CuryMultDiv': 'M', # (M)ultiply, (D)ivide
	'CuryRate': 1, # M/D by this float
	'CuryRateType': '',
	'docnbr': 'set_timecard_num', # Next number in DB
	'employee': 'set_user_num', # User number
	'fiscalno': 'set_period', # Current fiscal period (yyyymm)
	'le_id01': '',
	'le_id02': '',
	'le_id03': approver_id,
	'le_id04': '',
	'le_id05': '0000', # Site ID
	'le_id06': 'set_total_hours', # Total hours (all proj) for this doc number
	'le_id07': 'set_line_items', # Total line items needing approval (init=all)
	'le_id08': '1900-01-01 00:00:00',
	'le_id09': '1900-01-01 00:00:00',
	'le_id10': 0, # 0 or 1 = 'Transmit status'; Try 0, see what happens?
	'le_key': '', # Used for corrections
	'le_status': 'C', # (C)ompleted status; ready for approval
	'le_type': 'R', # (R)egular (not a (C)orrection)
	'lupd_datetime': 'set_cur_time',
	'lupd_prog': 'SCRIPT',
	'lupd_user': 'SCRIPT',
	'noteid': 0,
	'period_num': 'set_period',
	'pe_date': 'set_period_end', # Period ending date
	'user1': '',
	'user2': '',
	'user3': 0,
	'user4': 0,
	'week_num': 'set_week' # Week number within fiscal period
}

# PJLABDET, detail data
pjlabdet = {
	'CpnyId_chrg': 'ENV',
	'CpnyId_home': 'ENV',
	'crtd_datetime': 'set_cur_time',
	'crtd_prog': 'SCRIPT',
	'crtd_user': 'set_user_id',
	'day1_hr1': 0, # Hours for day 1 in 7 day week. Start day??
	'day1_hr2': 0, # OT hours 1
	'day1_hr3': 0, # OT hours 2
	'day2_hr1': 0,
	'day2_hr2': 0,
	'day2_hr3': 0,
	'day3_hr1': 0,
	'day3_hr2': 0,
	'day3_hr3': 0,
	'day4_hr1': 0,
	'day4_hr2': 0,
	'day4_hr3': 0,
	'day5_hr1': 0,
	'day5_hr2': 0,
	'day5_hr3': 0,
	'day6_hr1': 0,
	'day6_hr2': 0,
	'day6_hr3': 0,
	'day7_hr1': 0,
	'day7_hr2': 0,
	'day7_hr3': 0,
	'docnbr': 'set_timecard_num', # Timecard number we set in HDR entry
	'earn_type_id': '',
	'gl_acct': 'set_gl_acct', # GL Account = task account?
	'gl_subacct': 'set_gl_sub', # GL Subaccount = user's department
	'labor_class_cd': 'EMPL',
	'labor_stdcost': 0,
	'ld_desc': 'set_notes', # Enter TW time entry ID for data consistency
	'ld_id01': 'set_gl_sub',
	'ld_id02': 'Default message for Insert',
	'ld_id03': '',
	'ld_id04': '',
	'ld_id05': 0000, # Site ID
	'ld_id06': 'set_labor_rate', # Labor rate = user's labor rate?
	'ld_id07': 0,
	'ld_id08': '1900-01-01 00:00:00',
	'ld_id09': '1900-01-01 00:00:00',
	'ld_id10': 0,
	'ld_id11': '',
	'ld_id12': '',
	'ld_id13': '',
	'ld_id14': '',
	'ld_id15': '',
	'ld_id16': '',
	'ld_id17': '',
	'ld_id18': 0,
	'ld_id19': 0,
	'ld_id20': '1900-01-01 00:00:00',
	'ld_status': '',
	'linenbr': 'set_line_num',
	'lupd_datetime': 'set_cur_time',
	'lupd_prog': 'SCRIPT',
	'lupd_user': 'SCRIPT',
	'noteid': 0,
	'pjt_entity': 'set_task', # Task code from TW dict
	'project': 'set_proj', # Dynamics Project Number from TW dict
	'rate_source': 'E', # (E)mployee rate
	'shift': '',
	'SubTask_Name': '',
	'SubTask_UID': 0,
	'total_amount': 'set_total_amt', # Hours * rate
	'total_hrs': 'set_total_hrs', # Hours data from TW dict
	'union_cd': '',
	'user1': '',
	'user2': '',
	'user3': 0,
	'user4': 0,
	'work_comp_cd': '',
	'work_type': ''
}
