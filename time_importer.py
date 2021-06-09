import teamwork_helper
import dynamics_helper
import maps
import time_helper
import datetime
import dictionaries
import error_handler
import file_helper

if __name__ == '__main__':
    # Clear log file
    file_helper.clear_logs()

    # Get Teamwork data dictionary
    teamwork_data = teamwork_helper.get_teamwork_data()

    # Map Teamwork data to SQL table dictionaries
    master_dict = maps.create_master_dict(teamwork_data)

    # Insert data into SQL
    dynamics_helper.insert_data(master_dict)

    # Mark items imported in Teamwork
    teamwork_helper.mark_items_imported(teamwork_data)

    # error_handler.reverse_changes()
