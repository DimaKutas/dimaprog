"""
This script runs the cloud_photo_gallery application using a development server.
"""

from os import environ
from PROHJ_LOJ import app
import sys

if __name__ == '__main__':
    HOST = '0.0.0.0' #environ.get('HOST', '0.0.0.0')
    try:
        PORT = int(environ.get('PORT', (environ.get('SERVER_PORT', '5000'))))
        print('Attempt to run on', HOST,':', PORT)
    except ValueError:
        PORT = 5000

    print('Running on', HOST,':', PORT)
    app.run(HOST, PORT)
