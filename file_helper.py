# Helper for reading/writing to files

import dictionaries

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
