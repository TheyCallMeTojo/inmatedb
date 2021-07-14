#!/usr/bin/python3
import sys
import logging
import os


logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, "/var/www/inmatedb/")


from flask_app import app as application
application.secret_key = os.getenv('SECRET_KEY', 'for dev')
