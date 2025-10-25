from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from .routes import register_routes
from .scheduler import register_jobs
from .metrics import init_db

def create_app():
    #app = Flask(__name__)
    app = Flask(__name__, template_folder="../templates")
    init_db()
    register_routes(app)

    sched = BackgroundScheduler()
    register_jobs(sched)
    sched.start()

    return app