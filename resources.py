from flask import request
from flask_restful import Resource, Api, fields, reqparse, marshal_with, marshal
from flask_security import auth_required, roles_required, current_user
from extensions import db, cache
from models import User, Role, Category, Service, Service_req, Feedback
from datetime import datetime
from sqlalchemy.exc import IntegrityError

api = Api(prefix='/api')

parser = reqparse.RequestParser()

# service handle
parser.add_argument('name', type=str, required=True)
parser.add_argument('description', type=str)
parser.add_argument('price', type=int)
parser.add_argument('category_id', type=int, required=True, help='ID of the category')

service_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String,
    'price': fields.Integer,
    'category_id': fields.Integer,
}

class ServiceResource(Resource):
    @auth_required('token')
    @marshal_with(service_fields)
    def get(self):
        services = Service.query.all()
        return services
    
    @auth_required('token')
    @marshal_with(service_fields)
    def post(self):
        args = parser.parse_args()
        service = Service(
            name=args.name,
            description=args.description,
            price=args.price,
            category_id=args.category_id
        )
        db.session.add(service)
        db.session.commit()
        return {'message': 'Service created'}, 201

    @auth_required('token')
    def put(self, id):
        service = Service.query.get_or_404(id)
        args = parser.parse_args()
        service.name = args.name
        service.description = args.description
        service.price = args.price
        service.category_id = args.category_id
        db.session.commit()
        return {'message': 'Service updated'}, 200

    @auth_required('token')
    def delete(self, id):
        # Find all service requests related to this service
        related_requests = Service_req.query.filter_by(service_id=id).all()

        # Delete each related service request
        for req in related_requests:
            db.session.delete(req)

        # Now delete the service itself
        service = Service.query.get_or_404(id)
        db.session.delete(service)
        
        try:
            db.session.commit()  # Commit the transaction
            return {'message': 'Service and associated service requests deleted'}, 200
        except IntegrityError as e:
            db.session.rollback()  # Rollback the session in case of an error
            return {'message': f'Error deleting service: {str(e)}'}, 400


api.add_resource(ServiceResource, '/services', '/services/<int:id>')

# service request handle


parser.add_argument('professional_id', type=int)
parser.add_argument('service_id', type=int)
parser.add_argument('remarks', type=str)

service_req_fields = {
    'id': fields.Integer,
    'customer_id': fields.Integer,
    'customer_name': fields.String(attribute='customer.username'),  # Customer name
    'customer_email': fields.String(attribute='customer.email'),
    'customer_phone': fields.String(attribute='customer.phone'),
    'customer_address': fields.String(attribute='customer.address'),
    'customer_pin': fields.String(attribute='customer.pin'),
    'professional_id': fields.Integer,
    'professional_name': fields.String(attribute='professional.username'),  # Professional name
    'professional_email': fields.String(attribute='professional.email'),
    'professional_phone': fields.String(attribute='professional.phone'),  # Professional phone
    'professional_pin': fields.String(attribute='professional.pin'),
    'service_id': fields.Integer,
    'service_name': fields.String(attribute='service.name'),  # Service name
    'date_of_request': fields.DateTime,
    'date_of_completion': fields.DateTime,
    'service_status': fields.String,
    'remarks': fields.String
}



class ServiceRequestResource(Resource):
    @auth_required('token')
    @cache.cached(timeout = 5)
    @marshal_with(service_req_fields)
    def get(self):
        user = current_user  

        if any(role.name in ['admin', 'serv'] for role in user.roles):
            service_requests = Service_req.query.all()
        else:
        # Fetch service requests related to this user
            service_requests = Service_req.query.filter_by(customer_id=user.id).all()

        return service_requests

    @auth_required('token')
    def post(self):
        data = request.get_json()

        # Use current_user from Flask-Security for customer authentication
        customer = current_user

        service_id = data.get('service_id')
        if not service_id:
            return {'message': 'Missing service_id'}, 400

        # Check if the service_id is provided
        service = Service.query.get(service_id)
        if not service:
            return {'message': 'Service not found'}, 404

        # Optional: Check if a professional is provided
        professional_id = data.get('professional_id')
        professional = None
        if professional_id:
            professional = User.query.get(professional_id)
            if not professional:
                return {'message': 'Professional not found'}, 404

        # Create a new service request
        service_request = Service_req(
            customer_id=customer.id,  # Automatically get the current customer
            professional_id=professional.id if professional else None,  # professional may be None
            service_id=service.id,
            remarks=data.get('remarks', "No remarks"),
            service_status="requested"  # Initial status
        )

        db.session.add(service_request)
        db.session.commit()

        return {'message': 'Service request successfully', 'service_request_id': service_request.id}, 201

    @auth_required('token')
    @marshal_with(service_req_fields)
    def patch(self, service_request_id):
        data = request.get_json()
        service_request = Service_req.query.get_or_404(service_request_id)

        # Optionally update professional_id if provided
        professional_id = data.get('professional_id')
        if professional_id:  # Only update if professional_id is provided
            professional = User.query.get(professional_id)
            if not professional:
                return {'message': 'Professional not found'}, 404
            service_request.professional_id = professional.id

        # Update service status
        if 'service_status' in data:
            service_request.service_status = data['service_status']
            if data['service_status'] == 'closed':
                service_request.date_of_completion = datetime.utcnow()

        db.session.commit()
        return {'message': 'Service updated successfully', 'service_status': service_request.service_status}, 200




api.add_resource(ServiceRequestResource, '/service_requests', '/service_requests/<int:service_request_id>')

class Service_Prof_Resources(Resource):
    @auth_required('token')
    def delete(self, user_id):
        service_professional = User.query.filter_by(id = user_id).first()
        if service_professional:
            db.session.delete(service_professional)
            db.session.commit()
            return{'message': f'Service professional with ID {user_id} deleted'}, 200
        else:
            return {'message': f'User with ID {user_id} not found'}, 404

api.add_resource(Service_Prof_Resources, '/service_pro/<int:user_id>')


class CategoryResource(Resource):
    @cache.cached(timeout = 5)
    def get(self, category_id=None):
        # Get a single category by ID
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return {'message': 'Category not found'}, 404
            services = Service.query.filter_by(category_id = category_id).all()
            return [{ 'id': service.id, 'name': service.name, 'description': service.description, 'price': service.price} for service in services], 200
        else: 
        # Get all categories
            categories = Category.query.all()
            return [
                {'id': category.id, 'name': category.name, 'description': category.description}
                for category in categories
            ], 200

    def post(self):
        # Create a new category
        data = request.get_json()
        new_category = Category(
            name=data.get('name'),
            description=data.get('description')
        )
        db.session.add(new_category)
        db.session.commit()
        return {
            'message': 'Category created',
            'category': {
                'id': new_category.id,
                'name': new_category.name,
                'description': new_category.description
            }
        }, 201

    def put(self, category_id):
        # Update an existing category
        category = Category.query.get(category_id)
        if category:
            data = request.get_json()
            category.name = data.get('name', category.name)
            category.description = data.get('description', category.description)
            db.session.commit()
            return {
                'message': 'Category updated',
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                }
            }, 200
        else:
            return {'message': 'Category not found'}, 404

    def delete(self, category_id):
        # Delete a category
        category = Category.query.get(category_id)
        if category:
            db.session.delete(category)
            db.session.commit()
            return {'message': 'Category deleted'}, 200
        else:
            return {'message': 'Category not found'}, 404

api.add_resource(CategoryResource, '/categories/<int:category_id>/services', '/categories')

class Search(Resource):
    @auth_required("token")
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('search', help="Search Key", required=True)
        args = parser.parse_args()
        search_value = args.get('search')
        search = "%{}%".format(search_value)
        
        user = current_user  # Get the current user
        
        # Check user's role and filter data accordingly
        if any(role.name == 'admin' for role in user.roles):
            services = Service.query.filter(Service.name.like(search)).all()
            service_requests = Service_req.query.filter(Service_req.remarks.like(search)).union(
                Service_req.query.filter(Service_req.service_id.in_(
                    Service.query.filter(Service.name.like(search)).with_entities(Service.id)
                ))
            ).all()
        elif any(role.name == 'serv' for role in user.roles):
            services = Service.query.filter(Service.name.like(search)).all()
            service_requests = Service_req.query.filter_by(professional_id=user.id).all()
        elif any(role.name == 'cust' for role in user.roles):
            services = Service.query.filter(Service.name.like(search)).all()
            service_requests = Service_req.query.filter_by(customer_id=user.id).all()
        else:
            return {'message': 'Unauthorized'}, 403

        return {
            "services": marshal(services, service_fields),
            "service_requests": marshal(service_requests, service_req_fields)
        }

api.add_resource(Search, '/search_services')


class AdminSummary(Resource):
    @auth_required('token')
    def get(self):
        user = current_user  # Get the current user
        
        # Check if the user is an admin
        if not any(role.name == 'admin' for role in user.roles):
            return {'message': 'Unauthorized'}, 403
        
        # Fetch total users and service professionals
        total_users = User.query.count()
        total_service_pros = User.query.join(User.roles).filter_by(name='serv').count()

        # Fetch total service requests, completed, and pending requests
        total_requests = Service_req.query.count()
        completed_requests = Service_req.query.filter_by(service_status='closed').count()
        pending_requests = Service_req.query.filter(Service_req.service_status != 'completed').count()

        # Fetch total services and categories
        total_services = Service.query.count()
        total_categories = Category.query.count()

        # Fetch the most popular services (services with the most requests)
        popular_services = db.session.query(Service, db.func.count(Service_req.id).label('request_count')) \
            .join(Service_req, Service.id == Service_req.service_id) \
            .group_by(Service.id) \
            .order_by(db.desc('request_count')) \
            .limit(5) \
            .all()

        # Formatting the popular services data
        popular_services_data = [{'name': service.name, 'request_count': request_count} 
                                 for service, request_count in popular_services]

        # Summary response data
        summary_data = {
            'total_users': total_users,
            'total_service_pros': total_service_pros,
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
            'total_services': total_services,
            'total_categories': total_categories,
            'popular_services': popular_services_data
        }

        return summary_data, 200


# Register the AdminSummary API resource
api.add_resource(AdminSummary, '/admin/summary')


class ServiceProfessionalSummary(Resource):
    @auth_required("token")
    def get(self):
        # Assuming that the current user is a Service Professional
        user = current_user

        # Total requests made by the service professional
        total_requests = Service_req.query.filter_by(professional_id=user.id).count()
        completed_requests = Service_req.query.filter_by(professional_id=user.id, service_status='closed').count()
        pending_requests = Service_req.query.filter_by(professional_id=user.id, service_status='accepted').count()

        return {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
        }

api.add_resource(ServiceProfessionalSummary, '/professional/summary')

class CustomerSummary(Resource):
    @auth_required("token")
    def get(self):
        # Assuming that the current user is a Customer
        user = current_user

        # Total requests made by the customer
        total_requests = Service_req.query.filter_by(customer_id=user.id).count()
        completed_requests = Service_req.query.filter_by(customer_id=user.id, service_status='closed').count()
        pending_requests = Service_req.query.filter_by(customer_id=user.id).filter(Service_req.service_status != 'closed').count()

        return {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
        }


api.add_resource(CustomerSummary, '/customer/summary')

class ServiceTypeResource(Resource):
    def get(self):
        # Fetch all category names from the Category table
        categories = Category.query.with_entities(Category.name).all()

        # Format response to list all category names
        category_list = [category.name for category in categories]
        
        return {'service_types': category_list}, 200

# Register the API resource to expose it on /service_types
api.add_resource(ServiceTypeResource, '/service_types')


# Define the output fields for feedback
feedback_fields = {
    'id': fields.Integer,
    'service_id': fields.Integer,
    'customer_id': fields.Integer,
    'customer_name': fields.String,  # Will map to User.username
    'service_name': fields.String,   # Will map to Service.name
    'rating': fields.Integer,
    'comments': fields.String,
    'date': fields.DateTime(dt_format='iso8601') 
}

# Parser to handle feedback submission
feedback_parser = reqparse.RequestParser()
feedback_parser.add_argument('rating', type=int, required=True, help="Rating (1-5) is required")
feedback_parser.add_argument('comments', type=str, required=False, help="Optional comments for feedback")

class FeedbackResource(Resource):
    @marshal_with(feedback_fields)
    def get(self):
        """
        Fetch the top 5 feedback for each service, ordered by rating
        """
        feedbacks = (
            db.session.query(Feedback)
            .join(User, Feedback.customer_id == User.id)  # Join with User for customer_name
            .join(Service, Feedback.service_id == Service.id)  # Join with Service for service_name
            .with_entities(
                Feedback.id,
                Feedback.service_id,
                Feedback.customer_id,
                Feedback.rating,
                Feedback.comments,
                Feedback.date,
                User.username.label('customer_name'),  # Alias for customer_name
                Service.name.label('service_name')  # Alias for service_name
            )
            .order_by(Feedback.service_id, Feedback.rating.desc())  # Order by service and rating
            .all()
        )

        return feedbacks, 200


    @auth_required('token')
    def post(self, service_id):
        """
        Submit feedback for a specific service
        """
        args = feedback_parser.parse_args()

        # Ensure the service exists
        service = Service.query.get_or_404(service_id)
        
        # Get the current authenticated customer
        customer = current_user
        if not customer:
            return {'message': 'Unauthorized'}, 401

        # Create the feedback entry
        feedback = Feedback(
            service_id=service.id,
            customer_id=customer.id,
            rating=args['rating'],
            comments=args.get('comments', None),
            date=datetime.utcnow()
        )

        db.session.add(feedback)
        db.session.commit()

        return {'message': 'Feedback submitted successfully', 'feedback': marshal(feedback, feedback_fields)}, 201

# Register the FeedbackResource API resource
api.add_resource(FeedbackResource, '/services/<int:service_id>/feedback', '/feedbacks')
