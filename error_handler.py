# Functions to record errors

import file_helper
import dynamics_helper
import teamwork_helper
import dictionaries
import smtplib

error_dict = {}

error_msgs = {
    '000': '',
    '001': 'Project isn\'t in the SL database yet: ',
    '002': 'Teamwork time entry ID(s) already present in SL database, ' +\
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
    '028': 'Successfully updated rollup values for existing timecard. ',
    '029': 'Failed to update rollup values for timecard. '
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
    for id in twids:
        if id != '':
            teamwork_helper.put_tag(id, 'Time Ready for Import')
            print(id)

def err_present():
    # Returns true if any unhandled errors were logged.
    # Errors will be logged if script fails on an update or insert to SQL.
    result = False
    for user in error_dict:
        for timecard in error_dict[user]:
            if 'err' in error_dict[user][timecard]:
                result = True
            for line in error_dict[user][timecard]:
                if 'err' in error_dict[user][timecard][line]:
                    result = True
    return result

def send_script_alert(subject, body):
    # Sends a script alert email. Specify subject and body.
    port = 25  # For SSL
    smtp_server = "smtp.envirosys.com"
    sender_email = "escscript@envirosys.com"  # Enter your address
    receiver_email = "journal@envirosys.com"  # Enter receiver address
    message = 'Subject: {}\n\n{}'.format(subject, body)

    # context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        # server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)

def email_results():
    # Sends and email to admins alerting them of any errors
    body = file_helper.get_file_content(dictionaries.files[0])
    subject = 'Teamwork time import log'
    if err_present():
        subject = f'{subject} - unhandled errors recorded'
    send_script_alert(subject, body)
