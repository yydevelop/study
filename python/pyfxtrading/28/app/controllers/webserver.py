from flask import Flask
from flask import render_template

import settings

app = Flask(__name__, template_folder='../views')


@app.teardown_appcontext
def remove_session(ex=None):
    from app.models.base import  Session
    Session.remove()


@app.route('/')
def index():
    app.logger.info('index')
    return render_template('./google.html',
                           word='World')


def start():
    # app.run(host='127.0.0.1', port=settings.web_port, threaded=True)
    app.run(host='0.0.0.0', port=settings.web_port, threaded=True)

