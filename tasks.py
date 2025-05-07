from mail_service import send_message
from celery import shared_task
from models import User, Service_req, db
from jinja2 import Template
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@shared_task(ignore_result=True)
def send_daily_reminders():
    try:
        professionals = User.query.join(User.roles).filter_by(name='serv').all()
        for professional in professionals:
            pending_requests = Service_req.query.filter_by(
                professional_id=professional.id, service_status='requested'
            ).all()
            if pending_requests:
                with open('daily_reminder.html', 'r') as f:
                    template = Template(f.read())
                send_message(
                    professional.email,
                    "Daily Reminder: Pending Service Requests",
                    template.render(name=professional.username)
                )
                logger.info(f"Reminder sent to {professional.email}")
    except Exception as e:
        logger.error(f"Error in send_daily_reminders: {e}")


@shared_task(ignore_result=True)
def send_monthly_reports():
    try:
        customers = User.query.join(User.roles).filter_by(name='cust').all()
        for customer in customers:
            past_month = datetime.utcnow().replace(day=1)  # Get the first day of the current month
            services_requested = Service_req.query.filter(
                Service_req.customer_id == customer.id,
                Service_req.date_of_request >= past_month
            ).all()
            services_closed = Service_req.query.filter(
                Service_req.customer_id == customer.id,
                Service_req.date_of_completion >= past_month,
                Service_req.service_status == "completed"
            ).all()
            
            # Load the monthly report template
            with open('monthly_report.html', 'r') as f:
                template = Template(f.read())
            
            # Render HTML content for the report
            report_content = template.render(
                name=customer.username,
                requested_services=services_requested,
                closed_services=services_closed
            )
            
            # Send the report via email
            send_message(
                customer.email,
                "Monthly Activity Report",
                report_content
            )
            logger.info(f"Monthly report sent to {customer.email}")
    except Exception as e:
        logger.error(f"Error in send_monthly_reports: {e}")
