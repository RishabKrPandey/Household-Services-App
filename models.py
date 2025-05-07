from extensions import db, security
from flask_security import UserMixin, RoleMixin
from flask_security.models import fsqla_v3 as fsq
from datetime import datetime

fsq.FsModels.set_db_info(db)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable = False, unique = True)
    password = db.Column(db.String, nullable = False)
    city = db.Column(db.String, nullable = True)
    pin = db.Column(db.String(6))
    phone = db.Column(db.String(15))
    address = db.Column(db.String)
    service_type = db.Column(db.String)
    experience = db.Column(db.String(3))
    active = db.Column(db.Boolean)
    fs_uniquifier = db.Column(db.String(), nullable = False)
    roles = db.relationship('Role', secondary = 'user_roles')

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(80), unique = True, nullable = False)
    description = db.Column(db.String)

class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    # Relationship to Service
    services = db.relationship('Service', backref='category', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Integer)
    # Foreign key to Category
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


class Service_req(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    date_of_request = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    date_of_completion = db.Column(db.DateTime, nullable=True)
    
    service_status = db.Column(db.String(20), default="requested", nullable=False)
    
    remarks = db.Column(db.Text, nullable=True)

    # Relationships to services, customers, professionals
    service = db.relationship('Service', backref='service_requests')
    professional = db.relationship('User', foreign_keys = [professional_id])
    customer = db.relationship('User', foreign_keys= [customer_id])

    def __repr__(self):
        return f"<ServiceRequest(id={self.id}, service_status={self.service_status})>"

class DailyVisit(db.Model):
    __tablename__ = 'daily_visits'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    date = db.Column(db.Date)
    user = db.relationship('User', backref='visits')

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # rating can be 1-5 for example
    comments = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    service = db.relationship('Service', backref='feedbacks')
    customer = db.relationship('User', backref='feedbacks')

    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating}, service_id={self.service_id})>"

    