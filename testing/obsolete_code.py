# sql_update_line:
    # Add Teamwork IDs to update string
    # tw_ids = tc_dict['dets'][proj_task]['ld_desc']
    # cur_notes = sql_get_notes(docnbr, project, task)
    # if cur_notes != '':
    #     cur_notes = f'{cur_notes},'
    # new_notes = f'{cur_notes}{tw_ids}'
    # new_notes = new_notes[:30] # Truncate longer than 30 chars
    # update_str = f'{update_str}, ld_desc=\'{new_notes}\''

# undo_pjlabdet_entry:
    # Add notes
    # sub_chars = len(notes) # Number of characters to subtract
    # cur_notes = sql_get_notes(docnbr, proj, task) # Current notes string
    # cur_len = len(cur_notes) # Number of characters in current notes string
    # if cur_len > sub_chars:
    #     sub_chars += 1 # Remove preceeding comma too if necessary
    # new_notes = cur_notes[:cur_len - sub_chars] # Subtract chars from notes
    # update_str = f'{update_str}, ld_desc=\'{new_notes}\'' # Add to update_str

# insert_timecard:
    # else:
        # error_handler.error_dict[user][timecard][proj_task]['err'] = True

    # Check if timecard entry ID has previously been imported.
    # if id_check(cur_twids):
    #     # Log error, update import status to true since ID already in SL,
    #     # do not insert or update.
    #     print(error_handler.error_msgs['002'] + str(cur_twids))
    #     error_handler.log_to_file('002', str(cur_twids))
    #     mark_imported = True
    #     checks_passed = False

# update_rollups:
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
