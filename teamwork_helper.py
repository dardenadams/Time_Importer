# Helper functions to facilitate Teamwork connection

import requests
import json
import url_helper
import time
import time_helper
import dynamics_helper
import dictionaries
import error_handler

tw_url = 'https://environmentalsystemscorporation.teamwork.com/'
tw_api_key = 'twp_6kws8qMnMI9Epj4ftjdrNUNCwuDL'

def get_key(in_dict, in_val):
	# Returns the first key associated with the input dictionary value
	out_key = None
	for key in in_dict:
		if in_dict[key] == in_val:
			out_key = key
	return out_key

def get_data(url):
    # Get data using input URL and apply json
    raw_data = requests.get(url, auth=(tw_api_key, '')).json()
    return raw_data

def put_data(url, data):
	# Put data using input URL
	response = requests.put(
		url,
		auth=(tw_api_key, ''),
		json=data,
		headers = {"Content-Type": "application/json"}
	)
	return response

def get_all_tags():
	# Prints raw data for all tags in Teamwork
	url = tw_url + '/projects/api/v3/tags.json'
	print(get_data(url))

def put_tag(time_id, tag_str):
	# Adds the input tag to input time record, overwriting any existing tags
	url = tw_url + 'timelogs/' + str(time_id) \
		+ '/tags.json?Content-Type=application/json'
	data = {
		'tags': {
			'content': tag_str
		},
		'replaceExistingTags': 'true'
	}
	response = put_data(url, data)
	return response

def get_time():
	# Returns dictionary of time data filtered by tag.
	# If no data found, returns None.
	time_data = None

	print(error_handler.error_msgs['012'])
	error_handler.log_to_file('012', '')

	# Get raw data
	time_url = url_helper.construct_url('time', 'v3')
	raw_data = get_data(time_url)
    # print(raw_data)

    # Iterate through raw data and extract what we need
	if 'timelogs' in raw_data:
		time_data = {}
		for entry in raw_data['timelogs']:
			cur_id = entry['id']
			cur_pj = entry['project']['id']
			cur_user = entry['userId']
			cur_dt = time_helper.to_central_tz(entry['timeLogged'])
			cur_mins = entry['minutes']
			cur_desc = entry['description']

			# Add to dictionary
			time_data[cur_id] = {}
			time_data[cur_id]['project'] = cur_pj
			time_data[cur_id]['user'] = cur_user
			time_data[cur_id]['date_time'] = cur_dt
			time_data[cur_id]['minutes'] = cur_mins
			time_data[cur_id]['description'] = cur_desc

	return time_data

def print_time_proj():
	# Prints time/project data (for testing). Update tagIds to filter.
	# time_data = None

	# Get raw data
	time_url = url_helper.construct_url('time', 'v3')
	raw_data = get_data(time_url)

    # Iterate through raw data and extract what we need
	count = 0
	if 'timelogs' in raw_data:
		# time_data = {}
		for entry in raw_data['timelogs']:
			print('ID: ' + str(entry['id']) \
				+ ', Proj: ' + str(entry['project']['id']))
			count += 1
		print(count)

def get_project_list(time_dict):
    # Returns a list of Teamwork project IDs from time data
    pj_list = []

    for entry in time_dict:
        cur_pj = time_dict[entry]['project']
        # Add to list if does not already exist
        if not cur_pj in pj_list:
            pj_list.append(cur_pj)
    return pj_list

def get_project_details(all_projects):
    # Takes as input a list of all projects and returns a nested dictionary of
    # projects that have Dynamics Project Numbers and Task Codes
	start_time = time.time()
	project_dets = {}

	print(error_handler.error_msgs['013'])
	error_handler.log_to_file('013', '')

	# Iterate through list of projects
	count = 1
	for proj in all_projects:
		# Teamwork limits us to 150 requests/min so must keep track of rate
		# and pause when necessary. Set speed limit to 125/min for buffer.
		elapsed_time = time.time() - start_time
		if elapsed_time == 0:
		    elapsed_time = 1
		proc_rate = count / elapsed_time * 60
		if count > 125 and proc_rate > 125:
		    print('Reached process rate limit, pausing for 10 seconds ...')
		    print('Current rate: ' + str(proc_rate))
		    print('Total time elapsed: ' + str(elapsed_time) + ' seconds')
		    print('Total records processed: ' + str(count))
		    time.sleep(10)
		    print('Resuming operation')

		print(error_handler.error_msgs['010'] + str(proj))
		error_handler.log_to_file('010', str(proj))

		# Query details of each project
		id_data = '/' + str(proj)
		proj_url = url_helper.construct_url('projects', 'v2', id_data)
		raw_data = get_data(proj_url)

		# Iterate through project details to get Dynamics Project Number and
		# Task Code. Ommit projects without both fields populated.
		if 'customFields' in raw_data['project'].keys():
		    if raw_data['project']['customFields'] != None:
		        for field in raw_data['project']['customFields']:
		            # Iterate through customFields list
		            dyn_proj_num = 'No Data'
		            task_code = 'No Data'
		            tw_id = raw_data['project']['id']
		            field_count = 0
		            for field in raw_data['project']['customFields']:
		                # Set current field ID (402 = Project, 219 = Task)
		                field_id = raw_data['project']['customFields']\
		                    [field_count]['customFieldId']
		                # Set field value variable based on field ID
		                if field_id == 402:
		                    dyn_proj_num = raw_data['project']['customFields']\
		                        [field_count]['value']
		                elif field_id == 219:
		                    task_code = raw_data['project']['customFields']\
		                        [field_count]['value']
		                field_count += 1
		            # Populate project details dictionary
		            # if dyn_proj_num != 'No Data' and task_code != 'No Data':
		            project_dets[tw_id] = {}
		            project_dets[tw_id]['Task Code'] = task_code
		            project_dets[tw_id]['SL ID'] = dyn_proj_num
		# print('finished project ' + str(proj) + '!')
		count += 1
	return project_dets

def get_user_email(user_id):
    # Returns a user's email from Teamwork
    people_url = url_helper.construct_url('people', 'v1', user_id)
    raw_data = get_data(people_url)
    email_address = None

    # Retrieve email
    if 'person' in raw_data:
        if 'email-address' in raw_data['person']:
            email_address = raw_data['person']['email-address']
    return email_address

def construct_dict(time_dict, project_details):
	# Returns dictionary of time entries structured by Dynamics User ID
	# Dynamics User ID
	# -- Dynamics User Number
	# -- Period End Date (hdr entry)
	# ---- Dyn Proj Number/Task Code (det entry)
	# ----- Dynamics Project Number
	# ----- Task Code
	# ----- Description
	# ----- Day
	# ------- Minutes
	# ----- Time Entry IDs (csv if more than one)
	master_dict = {}

	print(error_handler.error_msgs['014'])
	error_handler.log_to_file('014', '')

	# Iterate through time entries
	for entry in time_dict:

		print(error_handler.error_msgs['011'] + str(entry))
		error_handler.log_to_file('011', str(entry))

		# Get current entry's data
		tw_proj_id = time_dict[entry]['project']
		tw_user_id = time_dict[entry]['user']
		tw_entry_ids = entry
		dyn_proj_id = project_details[tw_proj_id]['SL ID']
		dyn_user_id = dynamics_helper.get_user_info(tw_user_id, 'id')
		dyn_user_num = dynamics_helper.get_user_info(tw_user_id, 'num')
		task_code = project_details[tw_proj_id]['Task Code']
		date_time = time_dict[entry]['date_time']
		pe_date = time_helper.get_pe_date(date_time) # Calc period end date
		day = 'day' + str(dictionaries.day_map[date_time.weekday()]) + '_hr1'
		proj_task = dyn_proj_id + '-' + task_code
		minutes = time_dict[entry]['minutes']

		# Proceed to add to master dict only if Dynamics Project Number and
		# Task Code are properly populated
		if dyn_proj_id != 'No Data' and task_code != 'No Data':

			# Add user ID dict to master dict if it doesn't already exist
			if not dyn_user_id in master_dict:
			    master_dict[dyn_user_id] = {}

			# Add user num at top level
			if not 'user_num' in master_dict[dyn_user_id]:
				master_dict[dyn_user_id]['user_num'] = dyn_user_num

			# Add PE date dict to master dict if it doesn't already exist
			if not pe_date in master_dict[dyn_user_id]:
				master_dict[dyn_user_id][pe_date] = {}

			# Add Dynamics Project Number/Task combo dict to master dict if it
			# doesn't already exist
			if not proj_task in master_dict[dyn_user_id][pe_date]:
				master_dict[dyn_user_id][pe_date][proj_task] = {}

			# Add days dict to master dict if it doesn't already exist
			if not 'days' in master_dict[dyn_user_id][pe_date][proj_task]:
				master_dict[dyn_user_id][pe_date][proj_task]['days'] = {}

			# Add minutes to minutes already recorded if any exist for current
			# day of the week
			if day in master_dict[dyn_user_id][pe_date][proj_task]['days']:
				minutes = minutes + \
					master_dict[dyn_user_id][pe_date][proj_task]['days'][day]

			# Add Teamwork time entry ID to IDs already recorded, if any
			if 'tw_ids' in master_dict[dyn_user_id][pe_date][proj_task]:
				tw_entry_ids = str(tw_entry_ids) + ',' + \
					str(master_dict[dyn_user_id][pe_date][proj_task]['tw_ids'])

			# Add time entry detail data
			master_dict[dyn_user_id][pe_date][proj_task]['project'] = \
				dyn_proj_id
			master_dict[dyn_user_id][pe_date][proj_task]['task'] = \
				task_code
			master_dict[dyn_user_id][pe_date][proj_task]['tw_ids'] = \
				tw_entry_ids
			master_dict[dyn_user_id][pe_date][proj_task]['days'][day] = \
				minutes
			master_dict[dyn_user_id][pe_date][proj_task]['imported'] = \
				False
			# master_dict[dyn_user_id][pe_date][proj_task]['description'] = \
			#     time_dict[entry]['description']
	return master_dict

def print_tw_data(tw_data):
	# Prints out a Teamwork data dictionary for easy reading
	for user in tw_data:
		print(user)
		for pe_date in tw_data[user]:
			if pe_date == 'user_num':
				print('-- ' + pe_date + ': ' + tw_data[user][pe_date])
			else:
				print('-- ' + str(pe_date))
				for projtask in tw_data[user][pe_date]:
					print('---- ' + projtask)
					for detail in tw_data[user][pe_date][projtask]:
						print('------' + str(detail) + ': ' + \
							str(tw_data[user][pe_date][projtask][detail]))

def get_teamwork_data():
	# Returns library of projects with associated time records, task codes,
	# and SL user IDs

	# Get time ready for import
	time_dict = get_time()

	# Get list of projects from ready_time, then get Dynamics Project Number
	# and Task Code for each
	all_projects = get_project_list(time_dict)
	project_details = get_project_details(all_projects)

	# Combine and organize all data
	teamwork_data = construct_dict(time_dict, project_details)

	# print_tw_data(teamwork_data)
	return teamwork_data

def mark_items_imported(tw_dict):
	# Marks items imported in Teamwork if they have the

	# Update Teamwork dict with current import status
	for user in tw_dict:
		for timecard in tw_dict[user]:
			if timecard != 'user_num':
				for proj_task in tw_dict[user][timecard]:
					tw_dict[user][timecard][proj_task]['imported'] = \
					error_handler.error_dict[user][timecard][proj_task]\
					['imported']

					# Entry IDs (may be more than one per line item)
					entry_ids = tw_dict[user][timecard][proj_task]['tw_ids']

					# Update import status
					if tw_dict[user][timecard][proj_task]['imported'] == True:
						entry_ids = str(entry_ids)
						entry_ids = entry_ids.split(',') # IDs are CSV
						for id in entry_ids:
							print(error_handler.error_msgs['021'] + id)
							error_handler.log_to_file('021', id)
							error_handler.log_twid_import(id)
							put_tag(id, 'Time Imported')
					else:
						entry_ids = str(entry_ids)
						entry_ids = entry_ids.split(',')
						for id in entry_ids:
							print(error_handler.error_msgs['022'] + id)
							error_handler.log_to_file('022', id)
