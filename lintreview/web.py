import logging
import os

from flask import Flask

app = Flask('lintreview')

app.config.from_object('lintreview.default_settings')

if 'LINTREVIEW_SETTINGS' in os.environ:
    app.config.from_envvar('LINTREVIEW_SETTINGS')


@app.route('/ping')
def ping():
    return 'pong\n'


@app.route('/review/start', methods=['POST'])
def start_review():
    pass
