from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import hash_password
from extensions import db


def create_data(user_datastore : SQLAlchemyUserDatastore):

    print('### creating Data #######')


    # create roles
    user_datastore.find_or_create_role(name= 'admin', description = "Administrator")
    user_datastore.find_or_create_role(name= 'serv', description = "Service provider")
    user_datastore.find_or_create_role(name= 'cust', description = "Customer")

    # create user data

    if not user_datastore.find_user(email = "admin@iitm.ac.in"):
        user_datastore.create_user(username = "admin", email = "admin@iitm.ac.in", password = hash_password('pass'),active = True, roles=['admin'])


    db.session.commit()