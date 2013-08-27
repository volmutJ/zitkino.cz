# -*- coding: utf-8 -*-


__version__ = '2.1.dev'


from flask import Flask
from flask.ext.assets import Environment as Assets

from . import log
from .mongo import MongoEngine
import pylibmc


app = Flask(__name__)
app.config.from_object('zitkino.config')

log.init_app(app, **app.config['LOGGING'])


assets = Assets(app)
db = MongoEngine(app)
mc = pylibmc.Client(
	servers=app.config.get('MEMCACHE_SERVERS', None),
    username=app.config.get('MEMCACHE_USERNAME', None),
    password=app.config.get('MEMCACHE_PASSWORD', None),
    binary=True)


from zitkino import views, templating  # NOQA
