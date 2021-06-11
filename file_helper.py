# Helper for reading/writing to files

import dictionaries
from datetime import datetime
import os
import shutil

def archive_logs():
    # Archives log files in new folder

    # Create new archive folder
    folder_name = str(datetime.now().strftime("%Y-%m-%d %H%M%S"))
    path = f'{dictionaries.logpath}\\archive\\{folder_name}'
    os.mkdir(path)

    # Copy files
    for f in dictionaries.files:
        shutil.copy(f, path)

def clear_logs():
    # Clears contents of all log files
    for f in dictionaries.files:
        log_file = open(f, "w")
        log_file.write('')
        log_file.close()

def get_file_list(file_path):
    # Returns a list of newline-separated values from the input file
    f = open(file_path, 'r')
    f = f.read()
    f = f.split('\n')
    return f

def app_file(file, some_str):
    # Appends the input string to file
    f = open(file, "a")
    f.write(some_str)
    f.close()

def get_file_content(file):
    # Opens contents of file
    data = None
    with open(file, 'r') as file:
        data = file.read()
    return data
