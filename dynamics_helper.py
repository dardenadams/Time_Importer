# Helper functions to faciliate Dynamics connection

import pyodbc
import teamwork_helper
import dictionaries
import error_handler
import traceback
import file_helper

sql_server = 'sqlsl.esc.com'
sql_db = 'test_ESCDB'

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

def sql_del_whole_timecard(docnbr, database = sql_db):
    # Removes data from all SQL tables touched by time_importer.py
    connection = sql_connection(database)
    cursor = connection.cursor()

    for sql_table in dictionaries.sql_tables:
        query = '\
        DELETE FROM [' + sql_db + '].[dbo].[' + sql_table + ']\
        WHERE docnbr=\'' + docnbr + '\''
        cursor.execute(query)
    connection.commit()

def sql_del_pjlabhdr_entry(docnbr, linenbr, database = sql_db):
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
    query = \
        f'SELECT TOP 1 * FROM {database}.dbo.PJLABHDR \
        WHERE employee=\'{user_num}\' AND pe_date=\'{pe_date}\''
    if sql_bool_test_query(query, database):
        sql_data = sql_query(query)
        for item in sql_data:
            ret_val = item.docnbr
    return ret_val

def replace_docnbr(timecard, new_docnbr):
    # Replaces docnbr with input on timecard entry line items
    for proj_task in timecard['dets']:
        timecard['dets'][proj_task]['docnbr'] = new_docnbr

def insert_timecard(user, timecard, tc_dict):
    # Takes mapped data for a single timecard and inserts it into the SQL DB

    # Check if timecard for this period/user combo exists
    user_num = tc_dict['hdr']['employee']
    pe_date = tc_dict['hdr']['pe_date']
    cur_docnbr = tc_dict['hdr']['docnbr']
    ex_docnbr = pe_user_check(user_num, pe_date)
    timecard_posted = True

    # Insert header data if none already exists
    if ex_docnbr == None:
        try:
            sql_insert_dataset(tc_dict['hdr'], 'PJLABHDR')
        except:
            # Log error and stack trace
            print(error_handler.error_msgs['003'] + pe_date)
            traceback.print_exc()
            error_handler.log_to_file('003', pe_date)
            error_handler.log_to_file('', traceback.format_exc())
        else:
            # Log success
            print(error_handler.error_msgs['005'] + pe_date)
            error_handler.log_to_file('005', pe_date)
            error_handler.log_docnbr_insert(cur_docnbr)
    else:
        # Timecard already exists. Skip inserting header entry and replace
        # docnbr in timecard line-items with existing docnbr.
        replace_docnbr(tc_dict, ex_docnbr)

        # Check if existing docnbr is already marked (P)osted
        if status_posted_check(ex_docnbr):
            # Log error and do not proceed to line item import
            print(error_handler.error_msgs['008'] + pe_date)
            error_handler.log_to_file('008', pe_date)
            timecard_posted = True
        else:
            # Log info message and proceed to import line items
            print(error_handler.error_msgs['007'] + pe_date)
            error_handler.log_to_file('007', pe_date)

    # Insert line-item data
    for proj_task in tc_dict['dets']:
        proceed = True
        cur_proj = tc_dict['dets'][proj_task]['project']
        cur_twids = tc_dict['dets'][proj_task]['ld_desc']
        cur_linenbr = tc_dict['dets'][proj_task]['linenbr']

        # Initialize error dictionary for this line item and set default
        # import status to false.
        error_handler.error_dict[user][timecard][proj_task] = {}
        error_handler.error_dict[user][timecard][proj_task]['imported'] = False

        # Check if project exists in SL
        if not proj_check(cur_proj):
            # Log error, flag do not proceed
            print(error_handler.error_msgs['001'] + cur_proj)
            error_handler.log_to_file('001', cur_proj)
            proceed = False

        # Check if timecard entry ID has previously been imported
        if id_check(cur_twids):
            # Log error, update import status to true since ID already in SL,
            # flag do not proceed.
            print(error_handler.error_msgs['002'] + cur_twids)
            error_handler.log_to_file('002', cur_twids)
            error_handler.error_dict[user][timecard][proj_task]['imported'] \
                = True
            proceed = False

        # Check if timecard is (P)osted, in which case skip importing
        if timecard_posted == True:
            print(error_handler.error_msgs['009'] + cur_twids)
            error_handler.log_to_file('009', cur_twids)

        # If all checks pass, insert line item
        if proceed == True and timecard_posted == False:
            try:
                sql_insert_dataset(tc_dict['dets'][proj_task], 'PJLABDET')
            except:
                # Log failed insert and stack trace
                print(error_handler.error_msgs['004'] + proj_task)
                traceback.print_exc()
                error_handler.log_to_file('004', proj_task)
                error_handler.log_to_file('', traceback.format_exc())
            else:
                # Log successful insert and update import status to true
                print(error_handler.error_msgs['006'] + proj_task)
                error_handler.log_to_file('006', proj_task)
                error_handler.error_dict[user][timecard][proj_task]['imported']\
                    = True
                # If timecard already existed, we also need to log
                # docnbr/linenbr combination in case changes must be reversed.
                if ex_docnbr != None:
                    error_handler.log_linenbr_insert(ex_docnbr, cur_linenbr)

def insert_data(master_dict):
    # Takes a master dict of populated SQL table dicts and attempts to import
    for user in master_dict:
        print(error_handler.error_msgs['019'] + str(user))
        error_handler.log_to_file('019', str(user))

        # Initialize error dictionary for this user
        error_handler.error_dict[user] = {}

        for timecard in master_dict[user]:
            print(error_handler.error_msgs['020'] + str(timecard))
            error_handler.log_to_file('020', str(timecard))

            # Initialize error dictionary for this timecard
            error_handler.error_dict[user][timecard] = {}
            tc_dict = dict(master_dict[user][timecard])
            insert_timecard(user, timecard, tc_dict)
