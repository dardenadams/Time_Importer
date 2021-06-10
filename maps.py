# Functions to map values to dictionaries

import dictionaries
import time_helper
import dynamics_helper
from datetime import datetime
import error_handler

cur_docnbr = 0 # Current docnbr, used by dynamics_helper.get_next_linenbr

def get_total_hrs(tw_dict, user_id, pe_date):
    # Returns total hours for input timecard header entry
    minutes = 0

    for proj_task in tw_dict[user_id][pe_date]:
        for day in tw_dict[user_id][pe_date][proj_task]['days']:
            minutes += tw_dict[user_id][pe_date][proj_task]['days'][day]

    hours = float(minutes / 60)
    return hours

def get_line_count(tw_dict, user_id, pe_date):
    # Returns number of lines this time entry will include (PJLABDET items)
    lines = 0

    for proj_task in tw_dict[user_id][pe_date]:
        lines += 1

    return lines

def get_line_total(type, tw_dict, user_id, pe_date, proj_task, labor_rate = 0):
    # Returns time entry line amount (labor rate * total hours)
    total_hrs = 0

    for day in tw_dict[user_id][pe_date][proj_task]['days']:
        total_hrs += \
            tw_dict[user_id][pe_date][proj_task]['days'][day] / 60

    if type == 'hrs':
        return float(total_hrs)
    elif type == 'amt':
        return round(total_hrs * labor_rate, 2)

def get_gl_acct(proj_num, task_code):
    # Returns the GL Account for this project, determined by project number
    # and task code.
    gl_acct = '5100'

    # If leading int of project number is not zero, this is an internal project
    if int(proj_num[0]) > 0:
        # If task code is 98-00 (QA Tracker development), use 1680 GL Account
        if task_code == '98-00':
            gl_acct = '1680'
        else:
            gl_acct = '6100'
    return gl_acct

def print_master_dict(master_dict):
    # Prints data in master dict for easy reading
    for user_id in master_dict:
        print(user_id)
        for pe_date in master_dict[user_id]:
            print('-- ' + str(pe_date))
            print('---- Header Data' )
            for item in master_dict[user_id][pe_date]['hdr']:
                print('------ ' + str(item) + ': ' + \
                    str(master_dict[user_id][pe_date]['hdr'][item]))
            print('---- Line-item Data')
            for line in master_dict[user_id][pe_date]['dets']:
                print('------ ' + line)
                for l_item in master_dict[user_id][pe_date]['dets'][line]:
                    print('-------- ' + str(l_item) + ': ' + \
                        str(master_dict[user_id][pe_date]['dets']\
                            [line][l_item]))


def map_table(sql_dict, \
    tw_dict, \
    user_id, \
    pe_date, \
    row, \
    line = 0, \
    proj_task = None\
    ):
    # Populates SQL dictionary instance with Teamworks data
    for sql_key in sql_dict:
        key_val = sql_dict[sql_key]
        labor_rate = dynamics_helper.get_user_rate(tw_dict[user_id]['user_num'])
        user_num = tw_dict[user_id]['user_num']

        if key_val == 'set_cur_time':
            # Get current time
            sql_dict[sql_key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        elif key_val == 'set_user_id':
            # Get first initial/last name user ID
            sql_dict[sql_key] = user_id

        elif key_val == 'set_timecard_num':
            # Get next docnbr (timecard) number from SQL
            cur_docnbr = dynamics_helper.get_next_docnbr(row)
            sql_dict[sql_key] = cur_docnbr

        elif key_val == 'set_user_num':
            # Get user number
            sql_dict[sql_key] = user_num

        elif key_val == 'set_period':
            # Get relevent fiscal period
            sql_dict[sql_key] = time_helper.get_fp(pe_date)

        elif key_val == 'set_total_hours':
            # Sum total hours for this timecard docnbr
            sql_dict[sql_key] = get_total_hrs(tw_dict, user_id, pe_date)

        elif key_val == 'set_line_items':
            # Total lines for this entry awaiting approval
            sql_dict[sql_key] = get_line_count(tw_dict, user_id, pe_date)

        elif key_val == 'set_period_end':
            # Set period end date
            sql_dict[sql_key] = pe_date

        elif key_val == 'set_week':
            # Get week number within fiscal period
            sql_dict[sql_key] = time_helper.get_week(pe_date)

        # Populate items that delve into the proj_task level of tw_dict
        if proj_task in tw_dict[user_id][pe_date]:
            dyn_proj_num = tw_dict[user_id][pe_date][proj_task]['project']
            dyn_task = tw_dict[user_id][pe_date][proj_task]['task']

            if sql_key in tw_dict[user_id][pe_date][proj_task]['days']:
                # Populate hours by day.
                # Key in pjlabdet dict == days key in Teamwork dict
                minutes = tw_dict[user_id][pe_date][proj_task]['days'][sql_key]
                hours = float(minutes / 60)
                sql_dict[sql_key] = hours

            if key_val == 'set_gl_acct':
                # Get the GL account
                sql_dict[sql_key] = get_gl_acct(dyn_proj_num, dyn_task)

            elif key_val == 'set_gl_sub':
                # Get the GL subaccount
                sql_dict[sql_key] = dynamics_helper.get_user_dept(user_num)

            elif key_val == 'set_notes':
                # Get time entry IDs and set in notes column
                sql_dict[sql_key] = \
                    tw_dict[user_id][pe_date][proj_task]['tw_ids']

            elif key_val == 'set_labor_rate':
                # Get the labor rate for this user
                sql_dict[sql_key] = labor_rate

            elif key_val == 'set_line_num':
                # Get the next linenbr
                sql_dict[sql_key] = \
                    dynamics_helper.get_next_linenbr(line, cur_docnbr)

            elif key_val == 'set_task':
                # Get the task code
                sql_dict[sql_key] = dyn_task

            elif key_val == 'set_proj':
                # Get the project number
                sql_dict[sql_key] = dyn_proj_num

            elif key_val == 'set_total_amt':
                # Calculate total line item value
                sql_dict[sql_key] = get_line_total( \
                    'amt', \
                    tw_dict, \
                    user_id, \
                    pe_date, \
                    proj_task, \
                    labor_rate
                )

            elif key_val == 'set_total_hrs':
                # Calculate total line item hours
                sql_dict[sql_key] = get_line_total( \
                    'hrs', \
                    tw_dict, \
                    user_id, \
                    pe_date, \
                    proj_task
                )
    return sql_dict

def create_master_dict(tw_data):
    # Creates a dictionary of populated dictionaries ready for insert
    master_dict = {}

    print(error_handler.error_msgs['015'])
    error_handler.log_to_file('015', '')

    # Iterate through users
    for user_id in tw_data:

        print(error_handler.error_msgs['016'] + user_id)
        error_handler.log_to_file('016', user_id)

        # Create dict to hold all users
        master_dict[user_id] = {}
        row = 0

    # Iterate through week entries (organized by period end dates)
    for pe_date in tw_data[user_id]:
        row += 1 # Keeps track of timecard count for docnbr calc

        # Keep in mind user number is at top level
        if not pe_date == 'user_num':
            # Map tables

            # Create dict to hold time header and line entries
            master_dict[user_id][pe_date] = {}
            master_dict[user_id][pe_date]['dets'] = {}

            # Create header entry for week
            print(error_handler.error_msgs['017'] + str(pe_date))
            error_handler.log_to_file('017', str(pe_date))
            pjlabhdr = dict(dictionaries.pjlabhdr) # Copy of dictionary!
            master_dict[user_id][pe_date]['hdr'] = \
                map_table(pjlabhdr, tw_data, user_id, pe_date, row)

             # Keep track of linenbr. Linenbr + docnbr must be unique, but
             # linenbr may be duplicated so long as docnbr is different.
             # Therefore, restart count for each docnbr (timecard).
            line = 0

            # Iterate through line items (organized by proj/task)
            for proj_task in tw_data[user_id][pe_date]:
                line += 1

                # Create time entry line item
                print(error_handler.error_msgs['018'] + proj_task)
                error_handler.log_to_file('018', proj_task)
                pjlabdet = dict(dictionaries.pjlabdet)
                master_dict[user_id][pe_date]['dets'][proj_task] = \
                    map_table( \
                        pjlabdet, \
                        tw_data,  \
                        user_id,  \
                        pe_date,  \
                        row,      \
                        line,
                        proj_task \
                    )
    # print_master_dict(master_dict)
    return master_dict
