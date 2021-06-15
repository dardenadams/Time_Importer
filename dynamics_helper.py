# Helper functions to faciliate Dynamics connection

import pyodbc
import teamwork_helper
import dictionaries
import error_handler
import traceback
import file_helper
import time_helper

sql_server = 'sqlsl.esc.com'
sql_db = 'ESCDB'

def sql_connection(database):
    # Establishes a SQL connection using pyodbc
    connection = pyodbc.connect(
        'Driver={SQL Server};'
        f'Server={sql_server};'
        f'Database={database};'
        'Trusted_Connection=yes;'
    )
    return connection

def sql_query(query, database = sql_db):
    # Exports SQL data. Specify query.
    cursor = sql_connection(database).cursor()
    return cursor.execute(query)

def sql_insert(query, database = sql_db):
    # Inserts data to SQL. Specify query.
    connection = sql_connection(database)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()

def sql_update(table, columns, filters, database = sql_db):
    # Updates data in SQL. Specify table, column(s) and filter(s).
    query = f'\
        UPDATE {database}.dbo.{table} \
        SET {columns} \
        WHERE {filters}'
    connection = sql_connection(database)
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()

def sql_bool_test_query(sql_query, database = sql_db):
    # Returns true or false depending on whether query finds data in SQL
    connection = sql_connection(database)
    cursor = connection.cursor()
    cursor.execute(sql_query)
    if cursor.rowcount != 0:
        return True
    else:
        return False

def sql_insert_dataset(dataset, table):
    # Takes as input a mapped SQL dictionary dataset and inserts to the
    # specified table
    header_str = dictionaries.get_header_str(dataset)
    row_str = dictionaries.get_row_str(dataset)
    insert_str = f'INSERT INTO {sql_db}.dbo.{table}({header_str}) \
    VALUES({row_str})'
    # print(insert_str)
    sql_insert(insert_str, sql_db)

def sql_get_hrs(docnbr, proj, task, col, database = sql_db):
    # Returns the current hours value for specified line item from SQL
    ret_val = None
    query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABDET \
        WHERE docnbr=\'{docnbr}\' \
        AND project=\'{proj}\' \
        AND pjt_entity=\'{task}\''
    if sql_bool_test_query(query, database):
        sql_data = sql_query(query, database)
        for item in sql_data:
            ret_val = getattr(item, col)
    return ret_val

def sql_get_notes(docnbr, proj, task, database = sql_db):
    # Returns the current notes value for specified line item from
    ret_val = None
    query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABDET \
        WHERE docnbr=\'{docnbr}\' \
        AND project=\'{proj}\' \
        AND pjt_entity=\'{task}\''
    if sql_bool_test_query(query, database):
        sql_data = sql_query(query, database)
        for item in sql_data:
            ret_val = (item.ld_desc).strip()
    return ret_val

def del_whole_timecard(docnbr, database = sql_db):
    # Removes data from all SQL tables touched by time_importer.py
    connection = sql_connection(database)
    cursor = connection.cursor()

    for sql_table in dictionaries.sql_tables:
        query = '\
        DELETE FROM [' + sql_db + '].[dbo].[' + sql_table + ']\
        WHERE docnbr=\'' + docnbr + '\''
        cursor.execute(query)
    connection.commit()

def del_pjlabdet_entry(docnbr, linenbr, database = sql_db):
    # Removes data from PJLABDET that match input docnbr/linenbr combination.
    # Use to reverse changes to PJLABDET.
    connection = sql_connection(database)
    cursor = connection.cursor()
    query = '\
        DELETE FROM [' + sql_db + '].[dbo].[PJLABDET]\
        WHERE docnbr=\'' + docnbr + '\'\
        AND linenbr=\'' + linenbr + '\''
    cursor.execute(query)
    connection.commit()

def undo_pjlabdet_entry(docnbr, proj, task, day_list, notes, database = sql_db):
    # Reverses changes to an existing line from PJLABDET

    # Create column/new value string
    update_str = ''
    # Add day/new hours value pairs
    day_list = day_list.split(',')
    total_hrs = 0
    count = 1
    while count <= 7:
        # Calculate new hours value for day column, if necessary, but iterate
        # through all columns in DB to get a new total_hrs value.

        # Day column to update
        day_col = f'day{str(count)}_hr1'

        # Hours to subtract (zero unless file contains record of update)
        sub_hrs = 0
        for day in day_list:
            day_hrs_pair = day.split('|') # List[day_column, value]
            if day_col == day_hrs_pair[0]:
                sub_hrs = day_hrs_pair[1]

        cur_hrs = sql_get_hrs(docnbr, proj, task, day_col) # Cur hours in DB
        new_hrs = float(cur_hrs) - float(sub_hrs) # New hours value
        total_hrs += new_hrs # Add to running total of hours

        # Add to update string
        if update_str != '':
            update_str = f'{update_str}, '
        update_str = f'{update_str}{day_col}={str(new_hrs)}'

        count += 1

    # Add notes
    sub_chars = len(notes) # Number of characters to subtract
    cur_notes = sql_get_notes(docnbr, proj, task) # Current notes string
    cur_len = len(cur_notes) # Number of characters in current notes string
    if cur_len > sub_chars:
        sub_chars += 1 # Remove preceeding comma too if necessary
    new_notes = cur_notes[:cur_len - sub_chars] # Subtract chars from notes
    update_str = f'{update_str}, ld_desc=\'{new_notes}\'' # Add to update_str

    # Add total hours
    update_str = f'{update_str}, total_hrs={str(total_hrs)}'

    # Add total value (rate * total hours)
    rate = get_line_rate(docnbr, proj, task)
    total_amt = rate * total_hrs
    update_str = f'{update_str}, total_amount={str(total_amt)}'

    # Create filter string
    filters = \
        f'docnbr=\'{docnbr}\' AND project=\'{proj}\' AND pjt_entity=\'{task}\''

    # Update values
    sql_update('PJLABDET', update_str, filters)

def add_header_array(table_name):
    # Specify SQL table name (lower case) to get header information to
    # populate a new array in dictionaries.py.
    f_name = '\'dbo.' + table_name + '\''
    data = \
    sql_query(\
        f'SELECT Name FROM sys.columns WHERE object_id = OBJECT_ID({f_name})')

    headers_file = open("dictionaries.py", "a")
    nl = '\n'
    tab = '\t'
    q = '\''
    counter = 0
    headers_file.write(f'{nl}{table_name.lower()} = [')
    for item in data:
        if counter == 0:
            headers_file.write(f'{nl}{tab}{q}{item.Name}{q}')
        else:
            headers_file.write(f',{nl}{tab}{q}{item.Name}{q}')
        counter += 1
    headers_file.write(f'{nl}]')
    headers_file.close()

def get_user_info(teamwork_user_id, ret_val, database = sql_db):
    # Takes a Teamwork user ID and returns a Dynamics user ID

    # Get email address from Teamwork
    email_address = teamwork_helper.get_user_email(teamwork_user_id)

    # Build SQL query from email address
    username = email_address.split("@", 1)[0].upper()
    q_user = '\'' + username + '\''
    empl_query = \
        f'SELECT employee FROM {database}.dbo.PJEMPLOY WHERE user_id={q_user}'

    # Query SQL and return user ID if any is found
    result = None
    if sql_bool_test_query(empl_query, database):
        sql_data = sql_query(\
            empl_query,
            sql_db
        )
        for item in sql_data:
            result = item.employee
    if ret_val == 'num':
        return result
    elif ret_val == 'id':
        return username

def get_next_docnbr(row_adder, database = sql_db):
    # Returns last docnbr + row adder (timecard counter)
    last_row = 0

    query = \
        f'SELECT TOP 1 * FROM {database}.dbo.PJLABHDR ORDER BY docnbr DESC'

    if sql_bool_test_query(query, database):
        sql_data = sql_query(query)
        for item in sql_data:
            last_row = item.docnbr

    # Add +1 and format as string with leading zeros
    result = int(last_row) + row_adder
    result = str(result)
    result = (10 - len(result)) * '0' + result

    return result

def get_next_linenbr(line_adder, docnbr, database = sql_db):
    # Returns last linenbr and adds + line adder (line counter) if
    # docnbr/linenbr combo already exists or if line adder > 1.
    linenbr = 0

    # Query for last linenbr in DB
    linenbr_query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABDET ORDER BY linenbr DESC'
    # Get linenbr
    if sql_bool_test_query(linenbr_query, database):
        line_data = sql_query(linenbr_query)
        for line in line_data:
            linenbr = line.linenbr

    # Query to check if docnbr/linenbr combination already exists in DB.
    check_query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABDET \
        WHERE (docnbr=\'{docnbr}\' AND linenbr=\'{linenbr}\')\
        ORDER BY linenbr DESC'

    if line_adder == 1:
        # If first line entry for docnbr (line_adder == 1), then check if
        # docnbr/linenbr combo exists. If it does, apply line_adder.
        if sql_bool_test_query(check_query, database):
            linenbr += line_adder

    else:
        if sql_bool_test_query(check_query, database):
            # If docnbr/linenbr combo exists, apply adder
            linenbr += line_adder
        else:
            # If docnbr/linenbr combo doesn't exist, apply adder but subtract 1.
            # Otherwise, will skip one number since first first line's linenbr
            # will be original top line in DB.
            linenbr += (line_adder - 1)

    linenbr = str(linenbr)
    return linenbr

def get_user_dept(uid, database = sql_db):
    # Returns the input user's department code (GL Subaccount
    gl_sub = None

    query = \
        f'SELECT TOP 1 * FROM {database}.dbo.PJEMPLOY WHERE employee=\'{uid}\''

    if sql_bool_test_query(query, database):
        sql_data = sql_query(query)
        for item in sql_data:
            gl_sub = item.gl_subacct

    return gl_sub

def get_user_rate(uid, database = sql_db):
    # Returns the input user's labor rate
    rate = None

    query = \
        f'SELECT TOP 1 * FROM {database}.dbo.PJEMPPJT WHERE employee=\'{uid}\''

    if sql_bool_test_query(query, database):
        sql_data = sql_query(query)
        for item in sql_data:
            rate = item.labor_rate

    return rate

def get_line_rate(docnbr, proj, task, database = sql_db):
    # Returns the rate from the input line in PJLABDET
    rate = None

    query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABDET \
        WHERE docnbr=\'{docnbr}\' \
        AND project=\'{proj}\' \
        AND pjt_entity=\'{task}\''

    if sql_bool_test_query(query, database):
        sql_data = sql_query(query)
        for item in sql_data:
            rate = item.ld_id06

    return rate

def proj_check(proj, database = sql_db):
    # Returns true if project exists in SL
    query = \
        f'SELECT TOP 1 * FROM {database}.dbo.PJPROJ WHERE project=\'{proj}\''
    return sql_bool_test_query(query, database)

def id_check(entry_ids, database = sql_db):
    # Returns true if Teamworks time entry IDs are found in SL database
    entry_ids = str(entry_ids)
    entry_ids = entry_ids.split(',') # IDs are CSV
    for id in entry_ids:
        query = f'\
            SELECT TOP 1 * FROM {database}.dbo.PJLABDET \
            WHERE ld_desc LIKE \'%{id}%\''

    return sql_bool_test_query(query, database)

def status_posted_check(docnbr, database = sql_db):
    # Returns true if timecard is marked (P)osted
    query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABHDR \
        WHERE docnbr=\'{docnbr}\'\
        AND le_status=\'P\''
    return sql_bool_test_query(query, database)

def pe_user_check(user_num, pe_date, database = sql_db):
    # Returns docnbr of relevent timecard if a timecard already exists for
    # this employee/PE date combo.
    ret_val = None
    query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABHDR \
        WHERE employee=\'{user_num}\' AND pe_date=\'{pe_date}\''
    if sql_bool_test_query(query, database):
        sql_data = sql_query(query)
        for item in sql_data:
            ret_val = item.docnbr
    return ret_val

def line_check(docnbr, proj, task, database = sql_db):
    # Returns true if project/task combination line already exists on timecard
    query = f'\
        SELECT TOP 1 * FROM {database}.dbo.PJLABDET \
        WHERE docnbr=\'{docnbr}\' \
        AND pjt_entity=\'{task}\' \
        AND project=\'{proj}\''
    return sql_bool_test_query(query, database)

def replace_docnbr(timecard, new_docnbr):
    # Replaces docnbr with input on timecard entry line items
    for proj_task in timecard['dets']:
        timecard['dets'][proj_task]['docnbr'] = new_docnbr

def update_rollups(docnbr, user = '', timecard = '', database = sql_db):
    # 1. Updates total hours and total lines values on an existing timecard to
    #   include imported values.
    # 2. Sets status to (C)ompleted if beyond period end date + 5 days.
    #    Otherwise, sets status to (I)n Process.

    # Get hour and line data from SQL
    t_hrs = 0 # Sum of all hours on timecard
    t_lines = 0 # Sum of lines
    query = f'SELECT * FROM {database}.dbo.PJLABDET WHERE docnbr=\'{docnbr}\''
    if sql_bool_test_query(query):
        sql_data = sql_query(query)
        for line in sql_data:
            # Add line total hours to timecard total hours
            t_hrs += float(line.total_hrs)

            # Add line to line count
            t_lines += 1

    # Determine timecard status
    # status = 'I' # Default: (I)n Process
    # pe_date = None
    # query = \
    #     f'SELECT TOP 1 * FROM {database}.dbo.PJLABHDR WHERE docnbr=\'{docnbr}\''
    # if sql_bool_test_query(query):
    #     sql_data = sql_query(query)
    #     for line in sql_data:
    #         pe_date = time_helper.str_to_time(str(line.pe_date))
    #
    # post_date = time_helper.get_post_date(pe_date)
    # cur_date = time_helper.get_cur_time()
    #
    # if cur_date > post_date:
    #     status = 'C'

    # Construct update string
    update_str = f'le_id06={str(t_hrs)}, le_id07={str(t_lines)}'
        # f'le_id06={str(t_hrs)}, le_id07={str(t_lines)}, le_status=\'{status}\''

    # Construct filter string
    filter_str = f'docnbr=\'{docnbr}\''

    # Update values on PJLABHDR
    try:
        sql_update('PJLABHDR', update_str, filter_str)
    except:
        # Log to error dict during normal processing, but do not require
        # parameters so rollup can be called from reverse_changes.
        if user != '' and timecard != '':
            error_handler.error_dict[user][timecard]['err'] = True
        info_str = \
            f'docnbr: {docnbr}, update_str: {update_str}, filters: {filter_str}'
        error_handler.log_to_file('029', info_str)
    else:
        info_str = f'docnbr: {docnbr}'
        error_handler.log_to_file('028', info_str)

def sql_insert_line(tc_dict, user, timecard, proj_task, ex_docnbr, linenbr):
    # Inserts a line of data into PJLABDET
    ret_val = False

    # If timecard already existed, we need to log docnbr/linenbr
    # combination in case changes must be reversed.
    if ex_docnbr != None:
        error_handler.log_linenbr_insert(ex_docnbr, linenbr)

    try:
        # Attempt insert
        sql_insert_dataset(tc_dict['dets'][proj_task], 'PJLABDET')
    except:
        # Log failed insert and stack trace
        # print(error_handler.error_msgs['004'] + proj_task)
        # traceback.print_exc()
        error_handler.error_dict[user][timecard][proj_task]['err'] = True
        error_handler.log_to_file('004', proj_task)
        error_handler.log_to_file('000', traceback.format_exc())
    else:
        # Log successful insert and update import status to true
        # print(error_handler.error_msgs['006'] + proj_task)
        error_handler.log_to_file('006', proj_task)
        ret_val = True

    return ret_val

def sql_update_line(tc_dict, docnbr, linenbr, proj_task, project, task):
    # Updates hours, dollar amount, and notes data for a project/task line item
    ret_val = False

    # Iterate through timecard days and update values
    count = 1
    total_hrs = 0
    update_str = ''
    log_str = ''
    while count <= 7:
        # Get value to be added
        el_id = f'day{str(count)}_hr1'
        new_val = tc_dict['dets'][proj_task][el_id]

        # Record value to be inserted for logging, if nonzero
        if float(new_val) > 0:
            if log_str != '':
                log_str = f'{log_str},' # CSV element:value pairs
            log_str = f'{log_str}{el_id}|{new_val}'

        # Get existing value and sum with value to be added
        ex_val = sql_get_hrs(docnbr, project, task, el_id)
        new_val = float(new_val) + float(ex_val)

        # Add sum to running total of hours for all days
        total_hrs = total_hrs + new_val

        # Add new value to update string
        if count != 1:
            update_str = f'{update_str}, '
        update_str = f'{update_str}{el_id}={str(new_val)}'
        count += 1

    # Add total hours to update string
    update_str = f'{update_str}, total_hrs={str(total_hrs)}'

    # Calculate new total amount dollar value and add to update string
    rate = float(tc_dict['dets'][proj_task]['ld_id06'])
    total_amount = rate * total_hrs
    update_str = f'{update_str}, total_amount={str(total_amount)}'

    # Add Teamwork IDs to update string
    tw_ids = tc_dict['dets'][proj_task]['ld_desc']
    cur_notes = sql_get_notes(docnbr, project, task)
    if cur_notes != '':
        cur_notes = f'{cur_notes},'
    new_notes = f'{cur_notes}{tw_ids}'
    update_str = f'{update_str}, ld_desc=\'{new_notes}\''

    # Log notes changes to be added
    log_str = f'{log_str}:{tw_ids}'

    # Construct query filter
    filter = f'\
        docnbr=\'{docnbr}\' \
        AND project=\'{project}\' \
        AND pjt_entity=\'{task}\''

    # Log attempt to file in case changes must be reversed
    error_handler.log_linenbr_update(docnbr, project, task, log_str)

    # Update line item
    try:
        sql_update('PJLABDET', update_str, filter)
    except:
        err_detail = f'Update string: {update_str}\nFilter: {filter}'
        # print(error_handler.error_msgs['024'] + err_detail)
        # traceback.print_exc()
        error_handler.error_dict[user][timecard][proj_task]['err'] = True
        error_handler.log_to_file('024', err_detail)
        error_handler.log_to_file('000', traceback.format_exc())
    else:
        # print(error_handler.error_msgs['025'] + proj_task)
        error_handler.log_to_file('025', proj_task)
        ret_val = True

    return ret_val

def insert_timecard(user, timecard, tc_dict):
    # Takes mapped data for a single timecard and inserts it into the SQL DB

    # Check if timecard for this period/user combo exists
    user_num = tc_dict['hdr']['employee']
    pe_date = tc_dict['hdr']['pe_date']
    cur_docnbr = tc_dict['hdr']['docnbr']
    ex_docnbr = pe_user_check(user_num, pe_date)
    timecard_posted = False

    # Insert header data if none already exists
    if ex_docnbr == None:
        try:
            sql_insert_dataset(tc_dict['hdr'], 'PJLABHDR')
        except:
            # Log error and stack trace
            # print(error_handler.error_msgs['003'] + str(pe_date))
            # traceback.print_exc()
            error_handler.error_dict[user][timecard]['err'] = True
            error_handler.log_to_file('003', str(pe_date))
            error_handler.log_to_file('000', traceback.format_exc())
        else:
            # Log success
            # print(error_handler.error_msgs['005'] + str(pe_date))
            error_handler.log_to_file('005', str(pe_date))
            error_handler.log_docnbr_insert(cur_docnbr)
    else:
        # Timecard already exists. Skip inserting header entry, replace
        # docnbr in timecard line-items with existing docnbr, and update
        # line total and hour total rollups on existing timecard.
        replace_docnbr(tc_dict, ex_docnbr)

        # Check if existing docnbr is already marked (P)osted
        if status_posted_check(ex_docnbr):
            # Log error and do not proceed to line item import
            # print(error_handler.error_msgs['008'] + str(pe_date))
            error_handler.log_to_file('008', str(pe_date))
            timecard_posted = True
        else:
            # Log info message and proceed to import line items
            # print(error_handler.error_msgs['007'] + str(pe_date))
            error_handler.log_to_file('007', '')

    # Insert line-item data
    for proj_task in tc_dict['dets']:
        operation = 'insert' # Default assume insert, not update operation
        checks_passed = True # Default assume all checks will pass
        mark_imported = False
        cur_proj = tc_dict['dets'][proj_task]['project']
        cur_task = tc_dict['dets'][proj_task]['pjt_entity']
        cur_twids = tc_dict['dets'][proj_task]['ld_desc']
        cur_linenbr = tc_dict['dets'][proj_task]['linenbr']

        # Initialize error dictionary for this line item and set default
        # import status to false.
        error_handler.error_dict[user][timecard][proj_task] = {}
        error_handler.error_dict[user][timecard][proj_task]['imported'] = False

        # Check if timecard is (P)osted. For logging line-item details.
        if timecard_posted == True:
            # Log error, do not insert or update.
            # print(error_handler.error_msgs['009'] + str(cur_twids))
            error_handler.log_to_file('009', str(cur_twids))
            error_handler.error_dict[user][timecard][proj_task]['imported'] = \
                'Posted'
            checks_passed = False

        # Check if project exists in SL. If not, do not insert or update.
        if not proj_check(cur_proj) and checks_passed == True:
            # Log error, do not insert or update
            # print(error_handler.error_msgs['001'] + cur_proj)
            error_handler.log_to_file('001', cur_proj)
            checks_passed = False

        # Check if timecard entry ID has previously been imported.
        if id_check(cur_twids):
            # Log error, update import status to true since ID already in SL,
            # do not insert or update.
            # print(error_handler.error_msgs['002'] + str(cur_twids))
            error_handler.log_to_file('002', str(cur_twids))
            mark_imported = True
            checks_passed = False

        # Determine if update or insert should be performed
        if ex_docnbr != None and checks_passed == True:
            if line_check(ex_docnbr, cur_proj, cur_task):
                # If line already exists, perform update instead of insert.
                # print(error_handler.error_msgs['023'] + str(cur_twids))
                error_handler.log_to_file('023', str(cur_twids))
                operation = 'update'

        # Perform line insert or update as indicated
        if checks_passed == True:
            if operation == 'insert':
                mark_imported = sql_insert_line( \
                    tc_dict, \
                    user, \
                    timecard, \
                    proj_task, \
                    ex_docnbr, \
                    cur_linenbr\
                )
            elif operation == 'update':
                mark_imported = sql_update_line( \
                    tc_dict, \
                    ex_docnbr, \
                    cur_linenbr, \
                    proj_task, \
                    cur_proj, \
                    cur_task \
                )
        # else:
            # error_handler.error_dict[user][timecard][proj_task]['err'] = True

        # Mark line imported if successful
        if mark_imported == True:
            error_handler.error_dict[user][timecard][proj_task]['imported']\
                = True

    # Adjust rollup values in PJLABHDR if detail lines were added to an
    # existing timecard.
    if ex_docnbr != None:
        update_rollups(ex_docnbr, user, timecard)

def insert_data(master_dict):
    # Takes a master dict of populated SQL table dicts and attempts to import
    for user in master_dict:
        # print(error_handler.error_msgs['019'] + str(user))
        error_handler.log_to_file('019', str(user))

        # Initialize error dictionary for this user
        error_handler.error_dict[user] = {}

        for timecard in master_dict[user]:
            # print(error_handler.error_msgs['020'] + str(timecard))
            error_handler.log_to_file('020', str(timecard))

            # Initialize error dictionary for this timecard
            error_handler.error_dict[user][timecard] = {}
            tc_dict = dict(master_dict[user][timecard])
            insert_timecard(user, timecard, tc_dict)
