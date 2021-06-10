import requests
import json
import teamwork
import libraries
import time

tw_url = 'https://environmentalsystemscorporation.teamwork.com/'

def get_single_project(proj_id):
    # Prints raw data from a single project (for testing)
    id_data = '/' + str(proj_id)
    proj_url = libraries.construct_url('projects', 'v2', id_data)
    print(proj_url)
    raw_data = get_data(proj_url)
    print(raw_data)

def get_all_projects():
    # Returns a list of all projects (for testing)
    all_projects = []
    all_projects_url = libraries.construct_url('projects', 'v2')
    raw_data = get_data(all_projects_url)

    # Iterate through top level data to get to projects
    for item in raw_data:
        if item == 'projects':
            # Iterate through projects and add them to list
            count = 0
            for index_item in raw_data[item]:
                all_projects.append(raw_data[item][count]['id'])
                count += 1
    return all_projects

def tw_login():
    # Returns a configured Teamwork intance

    instance = teamwork.Teamwork( \
        'environmentalsystemscorporation.teamwork.com', \
        'twp_6kws8qMnMI9Epj4ftjdrNUNCwuDL' \
    )
    return instance

def get_projects():
    # Returns all active project IDs (archived projects not returned by API)

    instance = tw_login()
    raw_data = instance.get_projects()
    proj_data = clean_data(raw_data, 'project')
    print(raw_data)
    #print_time_data(proj_data)

def print_time_data(time_data):
    # Prints cleaned time data dictionary for easy reading

    for entry in time_data:
        print(entry)
        for column in time_data[entry]:
            print('-- ' + column + ': ' + time_data[entry][column])

def get_time(project_id):
    # Queries Teamwork and returns time entries related to input project ID

    instance = tw_login()
    raw_data = instance.get_project_times(project_id)
    time_data = clean_data(raw_data, 'time')

    #print(time_data)
    print_time_data(time_data)

def clean_data(raw_data, data_type):
    # Extracts columns we want from raw Teamwork data and structure them into
    # a new dictionary with structure:
    #
    # Time Data:
    # time_dict
    # -- Entry ID
    # ---- Data column name: data
    #
    # Project Data:
    # proj_dict
    # -- Dynamics Project Number
    # ---- Data column name: data

    return_dict = {}

    if data_type == 'time':
        time_dict = {}
        for entry in raw_data:
            entry_id = entry['id']
            time_dict[entry_id] = {}
            for column in entry:
                # Filter out unneeded data columns
                if column == 'project-name'\
                or column == 'project-id'\
                or column == 'person-last-name'\
                or column == 'person-first-name'\
                or column == 'description'\
                or column == 'description'\
                or column == 'hoursDecimal'\
                or column == 'project-status'\
                or column == 'person-id'\
                or column == 'date'\
                or column == 'hours':
                    time_dict[entry_id][column] = entry[column]
        return_dict = time_dict

    elif data_type == 'project':
        proj_dict = {}
        for entry in raw_data:
            entry_id = entry['id']
            proj_dict[entry_id] = {}
            for column in entry:
                if column == 'project-name'\
                or column == 'status'\
                or column == 'Dynamics-Project-Number':
                    proj_dict[entry_id][column] = entry[column]
        return_dict = proj_dict

    return return_dict
