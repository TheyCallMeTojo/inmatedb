#!/var/www/inmatedb/env/bin/python3
import sys
import logging
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/inmatedb/")


from flask_app import app as application
application.secret_key = "A_KEY"