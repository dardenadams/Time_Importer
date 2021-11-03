import teamwork_helper
import dynamics_helper
import maps
import datetime
import error_handler
import file_helper
import dictionaries
import time
import utilities

if __name__ == '__main__':
    # Clear log files
    file_helper.clear_logs()

    # Get Teamwork data dictionary
    teamwork_data = teamwork_helper.get_teamwork_data()

    # Proceed to import if any time was found
    if teamwork_data != None:

        # Map Teamwork data to SQL table dictionaries
        master_dict = maps.create_master_dict(teamwork_data)

        # Insert data into SQL
        dynamics_helper.insert_data(master_dict)

        # Mark items imported in Teamwork
        teamwork_helper.mark_items_imported(teamwork_data)

    # Archive log files and send alert email
    file_helper.archive_logs()
    error_handler.email_results()

    # Uncomment to reverse changes logged in last run log files
    # error_handler.reverse_changes()

    # Uncomment to mark Teamwork time logs imported again in case of failure
    # error_handler.mark_imported()
