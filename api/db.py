import mysql.connector
import click
from flask import current_app, g
from flask.cli import with_appcontext
from flask_restful import abort

# tests_runs constants
NULL_TIMESTAMP = '0000-00-00 00:00:00'

# retired flags
HOSTNAME_RETIRED = 1
HOSTNAME_ACTIVE  = 0
# retired flag status name
HOSTNAME_STATUS_ACTIVE = 'active'
HOSTNAME_STATUS_RETIRED = 'retired'

# statuses
STATUS_PASSED = 1
STATUS_FAILED = 2
STATUS_COMPLETED = 3
STATUS_INCOMPLETED = 4
STATUS_RUNNING = 5
STATUS_IN_SHELL = 6
STATUS_SCHEDULED = 7
STATUS_STARTED = 8

def get_db():
  """Getter method to retrieve the current database connection.
    
  Returns:
      A mysql database connection corresponding with host, database, 
      and port as configured below.
  """
  if 'db' not in g:
    g.db = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        passwd = 'Jose88',
        database = 'TestPhoenix',
        port = 3306
    )
  return g.db     

def close_db(error):
  """Closes the database connection."""
  db = g.pop('db', None)

  if db is not None:
    db.close()

def init_app(app):
  """Binds the cloe_db function to be invoked upon app closure."""
  app.teardown_appcontext(close_db)

def execute_sql(command, db_commit=False):
  """Insert into the mysql database.
  
  Args:
      insert_str: string sql command to executed.

  Returns:
      The last row id affected by the sql insert command.
  """
  db = get_db()
  cursor = db.cursor()

  cursor.execute(command)

  if db_commit is True:
    db.commit()
    return cursor.lastrowid

  return cursor.fetchall()

def validate_hostname_status(hostname_status, http_error_code=404):
  """Validates hostname status to be 'active' or 'retired'.
  
  Args:
      hostname_status: binary representation of a hostnmame's status 
      http_error_code: status code returned if error is encountered.

  Raises:
      HTTPException: retiredflag is not valid, raises http_error_code.
  """
  errors = {}
  
  if not is_active(hostname_status) and not is_retired(hostname_status):
    errors.update({'hostname_status' : 'Provided flag \'{}\' is not valid.'.format(statusflag)})

  if errors:
    abort(http_error_code, message=errors)

def validate_retiredflag(retiredflag, http_error_code=404):
  """Validates retiredflag is active '0' or 'retired '1'.
  
  Args:
      retiredflag: binary representation of a hostnmame's status 
      http_error_code: status code returned if error is encountered.

  Raises:
      HTTPException: retiredflag is not valid, raises http_error_code.
  """
  errors = {}

  if not is_active(retiredflag) and not is_retired(retiredflag):
    errors.update({'retiredflag' : 'Provided flag \'{}\' is not valid.'.format(retiredflag)})

  if errors:
    abort(http_error_code, message=errors)

def validate_hostname(hostname, retiredflag, http_error_code=404):
  """Validates hostname's existence in the database
  
  Args:
      hostname: string that represents a unique system.
      retiredflag: string that represents a system status.
      http_error_code: status code returned if error is encountered.

  Raises:
      HTTPException: hostname does not exist in the database as statusflag, raise http_error_code 
  """
  validate_retiredflag(retiredflag)
  hostname_status = to_hostname_status(retiredflag)
  errors = {}

  records = execute_sql("""
      SELECT hostname FROM hostnames 
      WHERE hostname = '{}' AND retired = '{}'
   """.format(hostname, retiredflag))

  if not records:
    # no existing hostname in database
    errors.update({'hostname' : '{} hostname \'{}\' Not Found.'.format(hostname_status, hostname)})
  
  if errors:
    abort(http_error_code, message=errors)

def validate_tests_name(tests_name, http_error_code=404):
  """Validates tests.name existence in the database
  
  Args:
      hostname: string that represents a unique system.
      retiredflag: string that represents a system status.
      http_error_code: status code returned if error is encountered.

  Raises:
      HTTPException: hostname does not exist in the database as statusflag, raise http_error_code 
  """
  errors = {}

  records = execute_sql("""
      SELECT * FROM tests 
      WHERE tests.name = '{}'
  """.format(tests_name))

  if not records:
    # no existing tests.name in the database
    errors.update({'tests_name' : '\'{}\' Not Found.'.format(tests_name)})

  if errors:
    abort(http_error_code, message=errors)

def get_running_tests(hostname=None):
  """GET currently running tests_runs on given hostname.

    Args:
        hostname: system hostname if none query as wildcard.
  """

  # query running tests on given hostname
  sql_command = """
      SELECT hostnames.hostname 
      FROM hostnames, tests_runs
      WHERE hostnames.hostname = '{}'
      AND hostnames.id = tests_runs.hostnames_id
      AND tests_runs.end_timestamp = '{}'
      AND tests_runs.status = '{}'
      AND hostnames.retired = '{}'
  """.format(hostname, NULL_TIMESTAMP, STATUS_RUNNING, HOSTNAME_ACTIVE)

  if hostname is None:
    # query all running_tests
    sql_command = """
      SELECT hostnames.hostname 
      FROM hostnames, tests_runs
      WHERE tests_runs.end_timestamp = '{}'
      AND tests_runs.status = '{}'
      AND hostnames.retired = '{}'
    """.format(NULL_TIMESTAMP, STATUS_RUNNING, HOSTNAME_ACTIVE)

  running_tests = execute_sql(sql_command)

  return running_tests

def get_tests_queue(hostname):
  """GET tests_queue for given hostname"""

  tests_queue = execute_sql("""
      SELECT hostnames.hostname 
      FROM hostnames, tests_runs, tests_runs_queue
      WHERE hostnames.hostname = '{}'
      AND hostnames.id = tests_runs.hostnames_id
      AND tests_runs.id = tests_runs_queue.test_runs_id
      AND hostnames.retired = '{}'
  """.format(hostname, HOSTNAME_ACTIVE))

  return tests_queue

def is_retired(flag):
  return flag == HOSTNAME_RETIRED or flag == HOSTNAME_STATUS_RETIRED

def is_active(flag):
  return flag == HOSTNAME_ACTIVE or flag == HOSTNAME_STATUS_ACTIVE

def to_retiredflag(hostname_status):
  """Convers hostnames_status to an equivalent retiredflag string"""
  if is_retired(hostname_status):
    return HOSTNAME_RETIRED

  return HOSTNAME_ACTIVE

def to_hostname_status(retiredflag):
  """Converts retiredflag to a hostname status strings {'active', 'retired'}"""
  if is_retired(retiredflag):
    return HOSTNAME_STATUS_RETIRED

  return HOSTNAME_STATUS_ACTIVE
