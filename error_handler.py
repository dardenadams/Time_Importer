# Functions to record errors

import file_helper
import dynamics_helper
import teamwork_helper
import dictionaries
import smtplib
import time

# Contacts who should be alerted when projects need to be imported to SL
accounting_contacts = [
    'rblackman@escspectrum.com',
    'mdiloreto@escspectrum.com',
    'dadams@escspectrum.com',
    'jshelian@escspectrum.com'
]

# Contacts who should receive log file after each run
import_log_contacts = [
    'dadams@escspectrum.com',
    'jshelian@escspectrum.com'
]

error_dict = {}

error_msgs = {
    '000': '',
    '001': 'Project isn\'t in the SL database yet: ',
    '002': 'Teamwork time entry ID already present in SL database, ' +\
        'skipping import: ',
    '003': 'Unhandled error. Failed to import header line: ',
    '004': 'Unhandled error. Failed to import detail line: ',
    '005': 'Successfully imported header item: ',
    '006': 'Successfully imported line item: ',
    '007': 'Timecard already present in SL, but not posted. Skipping ' +\
        'timecard import and proceeding to line items: ',
    '008': 'Timecard already present in SL and posted. Skipping import for ' +\
        'timecard: ',
    '009': 'Skipping import for timecard line item: ',
    '010': 'Requesting details for project: ',
    '011': 'Adding time entry to dictionary: ',
    '012': 'Getting list of time entries ready to process ...',
    '013': 'Getting detailed project info from Teamwork ...',
    '014': 'Constructing Teamwork data dictionary ...',
    '015': 'Mapping Teamwork data to SQL tables ...',
    '016': 'Mapping time entries for user: ',
    '017': 'Mapping PJLABHDR for: ',
    '018': 'Mapping PJLABDET for: ',
    '019': 'Inserting timecards for user: ',
    '020': 'Inserting timecard for period: ',
    '021': 'Marking time record with new tag: ',
    '022': 'Time record not imported, will not update tag. Teamwork ID: ',
    '023': 'Line item already present in SL. Will perform update not insert: ',
    '024': 'Failed to update line item: ',
    '025': 'Successfully updated line item: ',
    '026': 'Tagging imported items in Teamwork',
    '027': 'No Teamwork time entries to import',
    '028': 'Successfully updated rollup values for existing timecard, ',
    '029': 'Failed to update rollup values for timecard. ',
    '030': 'Total time records marked for import: ',
    '031': 'Reached process rate limit, pausing for 10 seconds ...',
    '032': 'Resuming operation',
    '033': 'Failed to update import status (le_status): ',
    '034': 'Updated import status (le_status): ',
    '035': 'Assigned linenbr info: ',
    '036': 'Running import on SQL database: ',
    '037': 'TW IDs must be marked \'Imported\'. Pausing 60 seconds to ' +\
        'reduce risk of hitting TW process limit ...',
    '038': 'Too many TW IDs to add to PJNOTES. IDs will be truncated.',
    '039': 'Successfully logged imported TW IDs to PJNOTES. Key: ',
    '040': 'Failed to log imported TW IDs to PJNOTES. Key: ',
    '041': 'Successfully updated TW IDs in PJNOTES. Key: ',
    '042': 'Failed to update TW IDs in PJNOTES. Key: ',
    '043': 'No time entries imported or updated for timecard: '
}

def log_to_file(error_id, detail_text):
    # Logs message to file
    file_helper.app_file(\
        dictionaries.files[0], f'{error_msgs[error_id]}{detail_text}\n')

def log_docnbr_insert(docnbr):
    # Logs SL docnbr inserted to PJLABHDR
    file_helper.app_file(dictionaries.files[1], f'{docnbr}\n')

def log_linenbr_insert(docnbr, linenbr):
    # Logs SL docnbr/linenbr combination inserted to PJLABDET
    file_helper.app_file(\
        dictionaries.files[2], f'{docnbr}:{linenbr}\n')

def log_linenbr_update(docnbr, project, task, data_str):
    # Logs SL docnbr/linenbr combination inserted to PJLABDET
    file_helper.app_file(\
        dictionaries.files[3], f'{docnbr}:{project}:{task}:{data_str}\n')

def log_twid_import(twid):
    # Logs Teamwork record ID tagged 'Time Imported'
    file_helper.app_file(dictionaries.files[4], f'{twid}\n')

def reverse_changes():
    # Reads log files and reverses all changes committed by the last import.
    # - Header entries will not be inserted (nor removed here) if they
    #   already existed prior to the last import.
    # - Detail entries will only be removed by themselves (without also
    #   removing associated header entry) if header entry already existed
    #   prior to last import.
    # - Will only re-tag ime IDs in Teamwork that were actually changed
    #   during last import.

    # Get list of whole timecards that were inserted and delete them
    print('Removing docnbrs, if any ...')
    docnbrs = file_helper.get_file_list(dictionaries.files[1])
    for nbr in docnbrs:
        if nbr != '':
            print(f'Removing docnbr: {nbr}')
            dynamics_helper.del_whole_timecard(nbr)

    # Get list of PJLABDET entries that were inserted and delete them
    print('Removing linenbrs, if any ...')
    linenbrs = file_helper.get_file_list(dictionaries.files[2])
    for doc_line in linenbrs:
        if doc_line != '':
            print(f'Removing docnbr/linenbr: {doc_line}')
            doc_line_list = doc_line.split(':')

            # Update values in PJLABDET
            dynamics_helper.del_pjlabdet_entry(\
                doc_line_list[0], # docnbr
                doc_line_list[1]  # linenbr
            )

            # Fix rollup fields in PJLABHDR
            dynamics_helper.update_rollups(doc_line_list[0])

    # Get list of PJLABDET entries that were updated and reverse changes
    print('Reversing linenbr updates, if any ...')
    linenbrs = file_helper.get_file_list(dictionaries.files[3])
    for doc_line in linenbrs:
        if doc_line != '':
            print(\
                f'Removing docnbr/linenbr/proj/task/day|time/notes: {doc_line}')
            doc_line_list = doc_line.split(':')

            # Update values in PJLABDET
            dynamics_helper.undo_pjlabdet_entry(\
                doc_line_list[0], # docnbr
                doc_line_list[1], # project
                doc_line_list[2], # task
                doc_line_list[3], # day/time pairs list
                doc_line_list[4]) # notes string

            # Fix rollup fields in PJLABHDR
            dynamics_helper.update_rollups(doc_line_list[0])

    # Get list of Teamwork time record IDs and replace 'Time Imported' tags
    # with 'Time Ready for Import' tags.
    print('Tagging Teamwork time records \'Ready for Import\' ...')
    twids = file_helper.get_file_list(dictionaries.files[4])
    # twids = twids.splitlines()
    start_time = time.time()
    count = 1
    for id in twids:
        if id != '':
            # Pause processing if necessary to avoid server refusing connection
            elapsed_time = time.time() - start_time
            if elapsed_time == 0:
                elapsed_time = 1
            proc_rate = count / elapsed_time * 60
            if count > 50 and proc_rate > 50:
            	info_msg = \
            		f'\nCurrent rate: {str(proc_rate)}' + \
            		f'\nTotal time elapsed: {str(elapsed_time)} seconds' + \
            		f'\nTotal records processed: {str(count)}'
            	print(error_msgs['031'] + info_msg)
            	time.sleep(10)
            	print(error_msgs['032'])

            teamwork_helper.put_tag(id, 'Time Ready to Import')
            print('id: ' + id)
            count += 1

def err_present():
    # Returns true if any unhandled errors were logged.
    # Errors will be logged if script fails on an update or insert to SQL.
    result = False
    for user in error_dict:
        for timecard in error_dict[user]:
            if 'err' in error_dict[user][timecard]:
                result = True
            for proj_task in error_dict[user][timecard]:
                if proj_task != 'proj_missing':
                    if 'err' in error_dict[user][timecard][proj_task]:
                        result = True
    return result

def msg_to_accounting():
    # Generates email message text to Accounting detailing each project
    # that's missing from SL database.
    msg_str = 'The following projects are missing from Dynamics, ' +\
        'preventing time from being logged: '
    result = False
    for user in error_dict:
        for timecard in error_dict[user]:
            for proj_task in error_dict[user][timecard]:
                if proj_task != 'proj_missing':
                    if error_dict[user][timecard][proj_task]['proj_missing'] \
                    == True:
                        proj = error_dict[user][timecard][proj_task]['proj_num']
                        if not proj in msg_str:
                            msg_str = f'{msg_str}\n{proj}'
                            result = True
    if result == True:
        return msg_str
    else:
        return None

def send_script_alert(\
    subject, \
    body, \
    to_email, \
    from_email = 'escscript@envirosys.com'):
    # Sends a script alert email. Specify subject and body.
    #= 'journal@envirosys.com'

    port = 25  # For SSL, specify 465
    smtp_server = 'smtp.envirosys.com'
    # from_email = 'escscript@envirosys.com'  # Enter your address
    # to_email = 'dadams@escspectrum.com'  # Enter receiver address
    message = 'Subject: {}\n\n{}'.format(subject, body)

    # context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        # server.login(sender_email, password)
        server.sendmail(from_email, to_email, message)

def email_results():
    # Sends and email to admins alerting them of any errors
    body = file_helper.get_file_content(dictionaries.files[0])
    subject = 'Teamwork time import log'
    if err_present():
        subject = f'{subject} - unhandled errors recorded'
    send_script_alert(subject, body, import_log_contacts)

    # Send alert accounting if time failed to import due to project missing
    # from Dynamics database.
    body = msg_to_accounting()
    subject = 'Please add projects to Dynamics'
    if body != None:
        send_script_alert(subject, body, accounting_contacts)

def test_email():
    send_script_alert('Test Email', 'Testing time import alerts.', accounting_contacts)

def mark_imported():
    # Marks time entries from file imported (for cleanup if failed)
    tag = 'Time Imported'
    twids = file_helper.get_file_list(dictionaries.files[4])

    start_time = time.time()
    count = 1

    for id in reversed(twids):
        # Pause processing if necessary to avoid server refusing connection
        elapsed_time = time.time() - start_time
        if elapsed_time == 0:
            elapsed_time = 1
        proc_rate = count / elapsed_time * 60
        print('Process rate: ' + str(proc_rate))
        print('Count: ' + str(count))
        if count > 50 and proc_rate > 50:
        	info_msg = \
        		f'\nCurrent rate: {str(proc_rate)}' + \
        		f'\nTotal time elapsed: {str(elapsed_time)} seconds' + \
        		f'\nTotal records processed: {str(count)}'
        	print(error_msgs['031'] + info_msg)
        	time.sleep(10)
        	print(error_msgs['032'])

        # For each item in CSV, update tag
        info_msg =  f'ID: {id}, Tag: {tag}'
        print(error_msgs['021'] + info_msg)
        teamwork_helper.put_tag(id, tag)

        # Advance counter to avoid Teamwork request limits
        count += 1
