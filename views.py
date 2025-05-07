from flask import jsonify, render_template, render_template_string, request
from flask_security import auth_required, current_user, roles_required, roles_accepted, SQLAlchemyUserDatastore
from flask_security.utils import hash_password, verify_password
from extensions import db
from models import Service
from datetime import datetime


def create_view(app, user_datastore : SQLAlchemyUserDatastore, cache):

    # cache test
    @app.route('/cache-test')
    @cache.cached(timeout = 5)
    def cache_test():
        return jsonify({"time" : datetime.now()})

    # homepage

    @app.route('/')
    def home():
        return render_template('index.html')
    

    @app.route('/user-login', methods=['POST'])
    def user_login():

        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        pin = data.get('pin')

        
        if not email or not password:
            return jsonify({'message' : 'not valid email or password'}), 404
        
        user = user_datastore.find_user(email = email)

        if not user:
            return jsonify({'message' : 'invalid user'}), 404
        
        if verify_password(password, user.password):
            return jsonify({'token' : user.get_auth_token(), 'role' : user.roles[0].name, 'id' : user.id, 'email' : user.email, 'pin' : user.pin }), 200
        else:
            return jsonify({'message' : 'wrong password'})

    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        phone = data.get('phone')
        city = data.get('city')
        pin = data.get('pin')
        address = data.get('address')

        experience = None
        service_type = None

        if role == 'serv':
            experience = data.get('experience')
            service_type = data.get('serviceType')

        if not email or not password or role not in ['cust', 'serv']:
            return jsonify({"message" : "invalid input"})
        
        if user_datastore.find_user(email=email):
            return jsonify({"message" : "user already exists"})
        
        # inst active = False
        if role == 'serv':
            active = False
        elif role == 'cust':
            active = True
        try:    
            user_datastore.create_user( username = username, email = email, password = hash_password(password), roles = [role], active = active, phone = phone, city = city, pin = pin, address = address, experience = experience, service_type = service_type )
            db.session.commit()
        except:
            print('error while creating')
            db.session.rollback()
            return jsonify({'message' : 'error while creating user'}), 408
        
        return jsonify({'message' : 'user created'}), 200
        
    # profile 
    @app.route('/profile')
    @auth_required('token')
    def profile():
        return render_template_string(
            """
                <h1> This is profile page </h1>
                <p> Welcome, {{current_user.email}}
                <a href="/logout">logout</a>
            """
        )
    
    
    @auth_required('token')
    @roles_required('admin')
    @app.route('/activate-serv/<id>' )
    def activate_inst(id):

        user = user_datastore.find_user(id=id)
        if not user:
            return jsonify({'message' : 'user not present'}), 404

        # check if inst already activated
        if (user.active == True):
            return jsonify({'message' : 'user already active'}), 400

        user.active = True
        db.session.commit()
        return jsonify({'message' : 'user is activated'}), 200
    
 

    # endpoint to get inactive serv
    @roles_required('admin')
    @app.route('/inactive_servicepro', methods=['GET'])
    def get_inactive_servicepro():
        # Query for all users
        all_users = user_datastore.user_model().query.all()
        
        # Filter users to get only inactive professionals
        inactive_servicepro = [
            user for user in all_users 
            if not user.active and any(role.name == 'serv' for role in user.roles)
        ]
        
        # Prepare the response data
        results = [
            {
                'id': user.id,
                'name': user.username,
                'service' : user.service_type,
                'experience': user.experience,
            }
            for user in inactive_servicepro
        ]
        
        return jsonify(results), 200

    # Endpoint to get all service professionals (active and inactive)
    @roles_required('admin')
    @app.route('/all_servicepro', methods=['GET'])
    def get_all_servicepro():
        # Query for all users
        all_users = user_datastore.user_model().query.all()
        
        # Filter users to get all service professionals
        all_servicepro = [
            user for user in all_users 
            if any(role.name == 'serv' for role in user.roles)
        ]
        
        # Prepare the response data
        results = [
            {
                'id': user.id,
                'name': user.username,
                'service': user.service_type,
                'experience': user.experience,
                'active': user.active  # Include active status
            }
            for user in all_servicepro
        ]
        
        return jsonify(results), 200
