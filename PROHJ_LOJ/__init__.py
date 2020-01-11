"""
The flask application package.
"""

from flask import Flask, url_for
from os import listdir, getcwd, environ
from os.path import isfile, join, exists, splitext
from urllib import parse
import mimetypes

app = Flask(__name__)
app.config['IMAGES_FOLDER'] = 'user_images'
app.config['UPLOADED_PHOTOS_DEST'] = join(getcwd(), app.config['IMAGES_FOLDER'])
app.config['USERS_DEST'] = join(getcwd(), 'users')
app.config['USERS_FILE'] = 'users.pkl'
mimetypes.init()

try:
    app.config['DB_URL'] = environ['DATABASE_URL']
except KeyError:
    app.config['DB_URL'] = 'postgres://vqvofoneycrmwf:1127f1ccdd7dd8c816cd7507420232f504732c32681824b02741dd8a852239c8@ec2-54-228-243-238.eu-west-1.compute.amazonaws.com:5432/dcsg44n9sbjolc'
app.config['PHOTO_SCHEMA'] = 'photos'
app.config['USERS_TABLE'] = 'users_photo_gallery'

import cloud_photo_gallery.login as l
import cloud_photo_gallery.views as v
import cloud_photo_gallery.photo_holder as ph
from cloud_photo_gallery.remoteDB import remoteDB as db

db_connected = True
try:
    print("Initializing db:", app.config['DB_URL'])
    db.initialize()
except Exception as e:
    print(e)
    db_connected = False
print("DB", ("SUCCESSFULLY CONNECTED" if db_connected else "CONNECTION FAILED"))

try:
    if db_connected:
        ph.photo_holder.db = db
        l.User.db = db

    users = l.User.load()

    for username in users:
        user = users[username]
        photos = []
        path = join(app.config['UPLOADED_PHOTOS_DEST'], username)
        if exists(path):
            onlyfiles = [f for f in listdir(path) if isfile(join(path, f))]
            for filename in onlyfiles:
                with open(join(path,filename), 'rb') as file:
                    with app.app_context(), app.test_request_context():
                        splitted, ext = splitext(filename)
                        splitted = splitted.split('.')
                        id = splitted[0]
                        name = '.'.join(splitted[1:])
                        url = url_for('photoShow', username = username, id = id)
                        print('Loading from local photo:', str(id)+ '.' + name + ext, 'with url:',url) #debug print
                        photos.append(ph.Photo(id = int(id), name = filename , url = url, filepath = path, content_type = mimetypes.types_map[ext]))
            print('Saving photos for', username, ':', photos) #debug print
            ph.photo_holder.add_photos_for(username, photos)
except FileNotFoundError:
    pass