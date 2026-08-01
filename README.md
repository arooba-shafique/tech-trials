# Institution Management System

A Django-based school management system with role-based dashboards for admins, teachers, students, and parents. Includes HR/payroll management, activity audit logging, and timetable scheduling.

## Live Demo

- [tech-trials.vercel.app](https://tech-trials.vercel.app)
- [arooba.pythonanywhere.com](https://arooba.pythonanywhere.com/)

## Features

### Role-Based Dashboards
- **Admin Dashboard** - Full school overview: students, teachers, parents, classes, subjects, attendance stats, HR data
- **Admin Manager Dashboard** - Manage admin managers with limited admin access
- **Teacher Dashboard** - View assigned classes/subjects, mark attendance, manage homework, create exams, upload results, view timetable
- **Student Dashboard** - View attendance, results, homework, timetable
- **Parent Dashboard** - Track children's attendance (with percentage), results, homework, timetable

### Academic Management
- Classes, subjects, and teacher-subject-class assignments
- Student attendance marking (per subject per day)
- Exam creation and result upload with pass/fail calculation
- Homework management with file attachments
- Weekly timetable management (save/load/clear via JSON API)

### HR and Payroll
- Employee CRUD with search/filter by type, designation, gender
- Salary configuration (tax, allowances, PF, bonus, late deduction rules)
- Bulk monthly salary generation with auto-calculations
- Salary slip generation (HTML view and downloadable)
- CSV export for bank transfers
- Monthly attendance summary tracking

### Activity Logging
- Tracks LOGIN, LOGOUT, LOGIN_FAILED, PASSWORD_CHANGED, PAGE_VISIT, CREATE, UPDATE, DELETE
- Stores IP address, user agent, path, method, old/new values
- Active session viewer (browser, OS, device, login time)
- Force-logout capability

### Other Features
- Separate login portals for each role
- Password reset via email
- School-level trial expiry system with middleware enforcement
- Multi-school support

## Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Python / Django | 6.0.2 |
| Frontend | HTML, CSS, JavaScript | - |
| Database (dev) | SQLite | - |
| Database (prod) | PostgreSQL | via psycopg2-binary 2.9.10 |
| WSGI Server | Gunicorn | 25.1.0 |
| Static Files | WhiteNoise | 6.12.0 |
| Images | Pillow | 12.1.1 |
| Deployment | Vercel, PythonAnywhere | - |

## Project Structure

```
tech-trials/
├── academics/              # Core academic records app (classes, students, exams, attendance, timetable)
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
├── accounts/               # User authentication and management (custom User model, roles)
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
├── hr/                     # Human resources and payroll management
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── forms.py
├── activity/               # Activity audit logging and session management
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   └── middleware.py
├── dps_ravi/               # Main Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   ├── middleware.py
│   ├── wsgi.py
│   ├── static/
│   └── media/
├── api/                    # Vercel serverless entry point
│   └── index.py
├── templates/              # HTML templates (dashboards, login pages, HR, activity)
├── fixtures/               # Database fixtures (initial_admin.json)
├── manage.py
├── requirements.txt
├── vercel.json
├── Procfile
├── build.py                # Vercel build script (migrations + loaddata)
└── create_dummy_data.py    # Test data generator (teachers, salary configs)
```

## Django Apps

| App | Purpose |
|-----|---------|
| `accounts` | Custom User model with roles (admin, admin_manager, principal, teacher, student, parent), School model, AdminManager profile, authentication |
| `academics` | Class, Subject, StudentProfile, TeacherProfile, ParentProfile, Attendance, Exam, Result, HomeTask, TimetableSlot, TeacherSubjectAssignment |
| `hr` | SalaryConfig, EmployeeSalary, MonthlySalary, EmployeeAttendance |
| `activity` | ActivityLog model, ActivityTrackingMiddleware for automatic page visit logging |

## Getting Started

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/arooba-shafique/tech-trials.git
   cd tech-trials
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate       # Windows
   source venv/bin/activate    # Linux/Mac
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. (Optional) Load initial admin fixture:
   ```bash
   python manage.py loaddata initial_admin
   ```

6. (Optional) Seed dummy data (8 teachers, salary configs):
   ```bash
   python create_dummy_data.py
   ```

7. Run the development server:
   ```bash
   python manage.py runserver
   ```

## Deployment

### Vercel
- Entry point: `api/index.py` (WSGI adapter)
- Build script (`build.py`) runs migrations and loads fixtures on cold start
- Static files served via WhiteNoise

### PythonAnywhere / Heroku
```
web: gunicorn dps_ravi.wsgi --log-file -
```

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `SECRET_KEY` | Django secret key | Insecure dev key |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | `*` |
| `DATABASE_URL` | PostgreSQL connection string | Falls back to SQLite |
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` |
| `EMAIL_USE_TLS` | TLS for email | `True` |
| `EMAIL_HOST_USER` | Email address | - |
| `EMAIL_HOST_PASSWORD` | Email app password | - |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/subjects-by-class/<class_id>/` | Get subjects for a class |
| POST | `/timetable/save/` | Save full timetable (JSON body) |
| GET | `/timetable/load/?class_id=` | Load timetable for a class |
| POST | `/timetable/clear/` | Clear timetable slots |
| POST | `/activity/force-logout/<session_key>/` | Force-logout a session |
