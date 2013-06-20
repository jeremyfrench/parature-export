# Parature Export

This tool will extract all data and linked binaries possible from a given Parature account.  An up to date ZIP of this repository can be obtained from the following URL: https://github.com/Alfresco/parature-export/archive/master.zip

## Usage

* Log onto the server hosting this script, change directory to /opt/parature-export
* Modify 'config' to ensure all of the configuration options (described below) are correct, particularly Parature URL, authentication details and output directory name
* Run the command 'nohup python26 parature-export.py &'
  *'nohup' allows the script to continue even if you exit your session with the server, 'python26' is the version of Python the script needs to run with and the ampersand (&) at end runs the script as a background task straight away.
* Monitor progress by running the tailf command on the log file which will be in the same directory, named as '[date + time script started]-export.log'
  * e.g. "tailf /opt/parature-export/2013-07-15-1015-export.log"

The script will then work until it has completely finished exporting.  The log file will end with the line 'FINISH: Job complete' when it is completed.  All data extracted will be output to the directory name specified in the config file within the same directory the script is run from (e.g. /opt/parature-export/2013-07-15-Production-Export).

There are no flags which can be supplied to script - everything is modified in the config file.  Once the script is started, there is no user interaction until it is finished - it can be left to its own devices and the log file can be monitored to see exactly what it's doing at any given time.  Typically the script running a full export can take up to 30 hours to complete.

## Configuration Options

### PARATURE_URL 
* URL of the Parature environment to perform the extract against, typically either sandbox or production - ensure the right URL is here!
* Example value: https://s5-sandbox.parature.com/api/v1/

### API_TOKEN
* API token for the Parature account you're aiming to use, can be found in your user settings in the Parature interface
* Example value: CZtRKbk8xw1DiMH8mNf8bNz4s2JtQa6JZ/hR1XULdLDz4uP/2F6jE8mufUCOj07fgNWOGurW6GHu0zjgE9yxqA==

### API_ACCOUNT_ID
* Example value: 11111

### API_DEPARTMENT_ID
* Example value: 11111

### LIST_PAGE_SIZE
* Determines the amount of list items to pull back on each object per page, less = faster responses, more = fewer requests
* Example value: 50

### DATE_UPDATED_MIN
* Only get objects modified after this date
* Example value: 2013-01-01

### JOB_ID
* Data and files will be output to a directory with this name
* Example value: 2013-06-19-delta-test

### DOWNLOAD_REFERER
* Used to get binaries from process.alfresco.com - should always be as the example.
* Example value: http://support.alfresco.com

### LOG_FILE
* Text to append to the date + time in the log file name (i.e '2013-06-20-1524-export.log')
* Example value: export.log

### LOG_LEVEL
* Level of information to be kept in the log - 20 (INFO) is recommended as 10 (DEBUG) is incredibly verbose
* Example value: 20

### LOG_FORMAT
* Format for each message in the log
* Example value: %(asctime)s [%(levelname)s] %(message)s

### LOG_DATE_FORMAT
* Example value: %m/%d/%Y %I:%M:%S %p