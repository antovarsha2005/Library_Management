LIBRARY MANAGEMENT SYSTEM


PROJECT OVERVIEW
----------------

The Library Management System is a web-based application that facilitates the management of library resources in a role‑based environment.  
Users interact with the system according to assigned roles:

- Admin
- Librarian
- User

Built with Flask, backed by SQLite, and packaged with Docker, the project follows a full CI/CD pipeline using GitHub Actions.  
The architecture and workflow satisfy academic DevOps guidelines, demonstrating version control, containerization, automated builds, and deployment.


TECH STACK

Backend
- Python
- Flask

Frontend
- HTML5
- CSS3
- JavaScript

Database
- SQLite

DevOps
- Docker
- DockerHub
- GitHub Actions

VERSION CONTROL
- Git & GitHub


SYSTEM ARCHITECTURE

A single unified Flask application serves all clients.
A shared SQLite database stores data with role-based routing controlling access.
Modules communicate via Flask blueprints; common tables drive functionality.

Shared Tables:
- users
- books
- transactions


DATABASE STRUCTURE

users
  id
  name
  email
  password
  role

books
  id
  title
  author
  totalCopies
  availableCopies

transactions
  id
  user_id
  book_id
  borrow_date
  return_date
  status


USER ROLES & FUNCTIONALITIES (USER MANUAL)

Getting Started
---------------

1. Open application in browser (http://localhost:5000).
2. Sign up and select a role: Admin, Librarian or User.
3. Login with credentials.


Role Capabilities
-----------------

ADMIN
- Add users
- View users
- Update users
- Delete users
- Search users

LIBRARIAN
- Add books
- View books
- Edit books
- Delete books
- Search books

USER
- View available books
- Borrow books
- Return books
- View borrow history
- Check book availability


Borrowing Flow
---------------

Users choose a book, submit a borrow request which updates transactions and decrements availableCopies.
Upon return, the transaction is updated and copies incremented.


HOW TO RUN LOCALLY

Windows

git clone <repo-url>
cd Library_Management
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py

macOS / Linux

git clone <repo-url>
cd Library_Management
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

Access the app at http://localhost:5000.


HOW TO RUN USING DOCKER (RECOMMENDED)

Method 1: Using Docker Desktop GUI

1. Open Docker Desktop
2. Navigate to Images tab
3. Search and pull vishnu10811/library_management:v1
4. Click "Run" on the image
5. Configure Optional Settings:
   - Container name: (Leave blank for random auto-generation)
   - Ports: Enter your preferred Host port (e.g., 80, 3000, 8080 etc.)
   - Container port: 5000 (do not change)
   - Example: Host port 80 → Container port 5000
6. Click "Run" to start the container
7. Access the application at http://localhost:<your-host-port>
   - If host port is 80: http://localhost:80
   - If host port is 3000: http://localhost:3000
   - If host port is 8080: http://localhost:8080

Method 2: Using Command Line

No local Python required.

docker pull vishnu10811/library_management:v1
docker run -p 5000:5000 vishnu10811/library_management:v1

Visit http://localhost:5000.

Or specify a custom host port:

docker run -p 80:5000 vishnu10811/library_management:v1

Visit http://localhost:80.


DOCKER BUILD MANUALLY (OPTIONAL)

docker build -t library_management .
docker run -p 5000:5000 library_management


CI/CD PIPELINE

A GitHub Actions workflow automates:

1. Clone repository on push to main.
2. Build the application.
3. Create Docker image.
4. Push image to DockerHub (vishnu10811/library_management:v1).

Automated builds ensure changes deploy immediately.


PROJECT STRUCTURE

Library_Management/
├── app.py
├── config.py
├── database.py
├── Dockerfile
├── requirements.txt
├── module1/
├── module2/
├── module3/
├── modules/
│   ├── book_module/
│   ├── transaction_module/
│   └── user_module/
├── static/
└── templates/


HOW TO ACCESS SYSTEM AS NEW USER

- Open browser to http://localhost:5000
- Register a new account, choosing a role
- Log in and navigate to the dashboard for role-specific features


TROUBLESHOOTING

- Port already in use: Stop the service on port 5000 or change binding.
- Docker not installed: Install Docker Desktop and restart.
- Python not found: Ensure Python 3.x is in PATH.
- Database file missing: Re-run or initialize database via script
