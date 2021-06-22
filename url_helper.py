# Functions and dictionaries to build Teamwork URLs

import teamwork_helper
import base64

proj_url_params = {
    'getDeleted': 'false',
    'includeCustomFields': 'true',
    'includeProjectOwner': 'false',
    'orderby': 'name',
    'orderMode': 'asc',
    # 'pageSize': '500',
    'status': 'active'
}

time_url_params = {
    # 'include': 'tags',
    'includeArchivedProjects': 'true',
    'orderby': 'project',
    'orderMode': 'asc',
    #'projectStatus': 'active',
    'showDeleted': 'false',
    'pageSize': '1000',
    'tagIds': '96968' # 96968 = Time Ready for Import, 96888 = Time Imported
}

put_time_url_params = {
    'replaceExistingTags': 'true'
}

def construct_url(url_type, api, id_data = '', includeParams = True):
    # Returns full URL string including all parameters from param dict, unless
    # otherwise specified

    # Get basic URL from teamwork_helper
    ret_url = teamwork_helper.tw_url

    # Build URL based on type
    if url_type == 'projects':
        # Project queries
        ret_url = \
            ret_url + 'projects/api/' + api + '/projects' + id_data + '.json'
        # Append parameters
        if includeParams == True:
            count = 0
            for param in proj_url_params:
                # Append '?' before first param and '&' before subsequent params
                if count == 0:
                    ret_url = ret_url + '?'
                elif count > 0:
                    ret_url = ret_url + '&'
                # Append param name and value
                ret_url = ret_url + param + '=' + proj_url_params[param]
                count += 1
    elif url_type == 'time':
        # Time queries
        ret_url = \
            ret_url + 'projects/api/' + api + '/time.json'
        # Append parameters
        if includeParams == True:
            count = 0
            for param in time_url_params:
                # Append '?' before first param and '&' before subsequent params
                if count == 0:
                    ret_url = ret_url + '?'
                elif count > 0:
                    ret_url = ret_url + '&'
                # Append param name and value
                ret_url = ret_url + param + '=' + time_url_params[param]
                count += 1
    elif url_type == 'people':
        # People queries
        ret_url = \
            ret_url + 'people/' + str(id_data) + '.json'
    #print(ret_url)
    return ret_url
