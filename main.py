from flask import Flask, jsonify
import views
from extensions import db, security, cache
from create_initial_data import create_data
import resources
from worker import celery_init_app
from tasks import send_daily_reminders, send_monthly_reports
from celery.schedules import crontab


celery_app = None

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "should-not-be-exposed"
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data.db"
    app.config['SECURITY_PASSWORD_SALT'] = 'salty-password'

    # configure token
    app.config['SECURITY_TOKEN_AUTHENTICATION_HEADER'] = 'Authentication-Token'
    # app.config['SECURITY_TOKEN_MAX_AGE'] = 3600 #1hr
    app.config['SECURITY_LOGIN_WITHOUT_CONFIRMATION'] = True

    # cache config
    app.config["DEBUG"]= True         # some Flask specific configs
    app.config["CACHE_TYPE"]= "RedisCache"  # Flask-Caching related configs
    app.config['CACHE_REDIS_HOST'] = 'localhost'
    app.config['CACHE_REDIS_PORT'] = 6379
    app.config['CACHE_REDIS_DB'] = 0
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
    app.config["CACHE_DEFAULT_TIMEOUT"]= 300

    cache.init_app(app)
    db.init_app(app)

    

    with app.app_context():

        from models import User, Role
        from flask_security import SQLAlchemyUserDatastore

        user_datastore = SQLAlchemyUserDatastore(db, User, Role) 

        security.init_app(app, user_datastore)

        db.create_all()
        
        create_data(user_datastore)

    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['SECURITY_CSRF_PROTECT_MECHANISHMS'] = []
    app.config['SECURITY_CSRF_IGNORE_UNAUTH_ENDPOINTS'] = True


    views.create_view(app, user_datastore, cache)

    # connect flask to flask_restful
    resources.api.init_app(app)

    return app


app = create_app()
celery_app = celery_init_app(app)


@celery_app.on_after_configure.connect
def automated_tasks(sender, **kwargs):
    # daily at 6:30 AM
    sender.add_periodic_task(
        20,
        # crontab(hour=6,minute=30),
        send_daily_reminders.s(),
    )


    # Monthly report task on the 1st of every month at 8:00 AM
    sender.add_periodic_task(
        30,
        # crontab(day_of_month=1, hour=8, minute=0),
        send_monthly_reports.s()
    )


@app.route('/test-reminder', methods=['POST'])
def test_reminder():
    send_daily_reminders.delay()  # Call the task asynchronously
    return jsonify({"status": "Reminder task triggered"}), 200


if __name__ == "__main__":
    app.run(debug=True)