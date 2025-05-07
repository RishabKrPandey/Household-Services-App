# Household Services Web Application

A multi-user web application developed as part of the **Modern Application Development 2** course. This platform allows customers to book household services, while professionals can register, get approved, and manage service requests based on location.

## 🚀 Tech Stack

### 🔧 Backend
- **Flask** – Lightweight web framework
- **SQLAlchemy** – ORM for database operations
- **SQLite** – Lightweight relational database

### 🎨 Frontend
- **Vue.js** – Reactive frontend framework
- **HTML/CSS** – Markup and styling
- **Bootstrap** – Responsive UI components

### ⚙️ Other Tools
- **Redis** – Backend caching and task queuing
- **Celery** – Asynchronous task queue for background jobs
- **MailHog** – SMTP server simulator for email testing

---

## 👥 Features

### ✨ User Roles
- **Customer**:
  - Register/login
  - Browse available services
  - Book services by category
- **Professional/Service Provider**:
  - Register/login
  - Await admin approval
  - View service requests from customers within the same PIN code
  - Accept/Reject assigned service requests
- **Admin**:
  - Approve or reject professional accounts
  - Manage all user activities

### 📍 Smart Matching
Professionals can only view and act upon service requests in their registered PIN code area, ensuring localized service delivery.

---

## 🔧 Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone https://github.com/RishabKrPandey/Household-Services-App.git
   cd Household-Services-App
   ```

2. **Create a Virtual Environment & Install Requirements**
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Redis Server**
   Make sure Redis is installed and running:
   ```bash
   redis-server
   ```

4. **Start Celery Worker**
   ```bash
   celery -A app.celery worker --loglevel=info
   ```

5. **Run MailHog (for email testing)**
   - Download MailHog: https://github.com/mailhog/MailHog
   - Run it:
     ```bash
     ./MailHog
     ```

6. **Start the Flask Application**
   ```bash
   flask run
   ```

---

## 📸 Screenshots

![image](https://github.com/user-attachments/assets/eadd4f41-0df4-4c35-bcee-b4cca999364b)
![image](https://github.com/user-attachments/assets/3fddcf90-21a6-4668-bdad-95c804cb91c2)
![image](https://github.com/user-attachments/assets/f0f62934-19e5-4698-8d1e-198608c6cd4b)
![image](https://github.com/user-attachments/assets/40d346aa-cab8-4d68-9a4b-67ae64035b07)
![image](https://github.com/user-attachments/assets/2110d999-6dec-4b9b-a28e-98f26cc98bf3)

---

## 📬 Contact

Created by [Rishab Kumar](https://github.com/RishabKrPandey) – feel free to reach out for feedback or collaboration!

---

## 📄 License

This project is for academic purposes. All rights reserved.
