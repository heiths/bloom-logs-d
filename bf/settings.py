""" This file looks at `etc/triage.conf`, `/etc/triage.conf`
It can be edited to end user's local settings, Few are default
and few are as per local environment settings.
"""
import configparser

LOG_CONTAINER = "access_raw"

# Worker settings can also be passed as an argument to the celery command.
# http://docs.celeryproject.org/en/latest/userguide/workers.html#commands.
SEARCH_QUEUE_RATE_LIMIT = 100000
PROCESS_LOG_RATE_LIMIT = 100000

# This is the username & password as described in the README.  It can be changed.
CELERY_BROKER_URL = 'amqp://admin:_4JQvSJQvS@192.168.6.1:5672//'
CELERY_BACKEND = 'redis://192.168.6.1:6379/0'

# If nginx is not configured, you will need to add the port 5000 to localhost.
BASE_URL = "http://localhost"
SEARCH_URL = "{}/search".format(BASE_URL)
PROCESS_URL = "{}/search".format(BASE_URL)
UPDATE_DB_URL = "{}/update".format(BASE_URL)
TASKS_URL = "{}/tasks".format(BASE_URL)


conf = configparser.ConfigParser()
config_search_order = ['etc/triage.conf', '/etc/triage.conf']

if not len(conf.read(config_search_order)):
    print("Please provide correct conf file, etc/triage.conf or /etc/triage.conf")
    raise configparser.NoSectionError
else:
    conf.read(config_search_order[0])
    TESTING = conf['DEFAULT'].getboolean('TESTING')
    LOG_CONTAINER = conf['DEFAULT']['LOG_CONTAINER']

    SEARCH_QUEUE_RATE_LIMIT = conf['LIMITS'].getint('SEARCH_QUEUE_RATE_LIMIT')
    PROCESS_LOG_RATE_LIMIT = conf['LIMITS'].getint('PROCESS_LOG_RATE_LIMIT')

    CELERY_BROKER_URL = conf['CELERY_SERVER']['CELERY_BROKER_URL']
    CELERY_BACKEND = conf['CELERY_SERVER']['CELERY_BACKEND']

    MONGO_HOST = conf['MONGO_SETTINGS'].get('MONGO_HOST', "192.168.6.1")
    MONGO_PORT = conf['MONGO_SETTINGS'].getint('MONGO_PORT', 27017)

    swiftly_config = {
        "auth_url": conf['SWIFTLY']["auth_url"],
        "auth_user": conf['SWIFTLY']["auth_user"],
        "auth_key": conf['SWIFTLY']["auth_key"],
        "region": conf['SWIFTLY']["region"],
        "insecure": conf['SWIFTLY'].getboolean("insecure"),
        "auth_tenant": conf['SWIFTLY']["auth_tenant"]
    }