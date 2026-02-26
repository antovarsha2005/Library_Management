# Library Management System

## Overview
A modular, web-based library management system built with Flask, HTML5, CSS3, JavaScript, and SQLite. The application is separated into three loosely coupled modules, each maintained on its own Git branch and merged via pull requests, enabling collaborative development and clean separation of concerns.

---

## Technology Stack
- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **Database:** SQLite
- **Version Control:** Git & GitHub
- **CI/CD:** GitHub Actions
- **Containerization:** Docker 

---

## Repository Structure
```
Library_Management/
├─ module1/                 # Book Management
│  ├─ app.py
│  ├─ database.py
│  ├─ requirements.txt
│  ├─ library.db
│  ├─ templates/
│  └─ static/
├─ module2/                 # User Management
│  ├─ app.py
│  ├─ database.py
│  ├─ requirements.txt
│  ├─ library.db
│  ├─ templates/
│  └─ static/
├─ module3/                 # Transaction Management
│  ├─ backend/
│  │  ├─ app.py
│  │  ├─ database.py
│  │  ├─ requirements.txt
│  │  └─ library.db
│  └─ frontend/
│     ├─ index.html
│     ├─ transactions.html
│     ├─ css/
│     └─ js/
└─ README.md                # This file
```

Each module is self-contained and can be run independently for testing or demonstration purposes.

---

## Module Summaries

### Module 1 – Book Management
**Purpose:** Manage catalog entries and inventory.

**Key Features:**
- Librarian signup/login
- Add, edit, delete books
- View all books with pagination (future improvement)
- Search by title or author
- Detailed book view
- Dashboard with statistics

**Books Table Schema:**
| Column          | Type    | Constraints                |
|-----------------|---------|----------------------------|
| id              | INTEGER | Primary Key, Auto Increment |
| title           | TEXT    | NOT NULL                   |
| author          | TEXT    | NOT NULL                   |
| totalCopies     | INTEGER | NOT NULL                   |
| availableCopies | INTEGER | NOT NULL                   |


### Module 2 – User Management
**Purpose:** Handle administrative users and roles.

**Key Features:**
- Admin signup/login
- Create, read, update, delete (CRUD) users
- Role-based access control (admin, librarian, user)
- Search users by name

**Users Table Schema:**
| Column   | Type    | Constraints                 |
|----------|---------|-----------------------------|
| id       | INTEGER | Primary Key, Auto Increment |
| name     | TEXT    | NOT NULL                    |
| email    | TEXT    | UNIQUE, NOT NULL            |
| password | TEXT    | Hashed                      |
| role     | TEXT    | NOT NULL                    |


### Module 3 – Transaction Management
**Purpose:** Track book borrowing and returns.

**Key Features:**
- User signup/login
- Borrow and return books
- View current borrows and history
- Availability checks and duplicate prevention
- Transaction validation (user & book exist)

**Transactions Table Schema:**
| Column      | Type    | Constraints                         |
|-------------|---------|-------------------------------------|
| id          | INTEGER | Primary Key, Auto Increment         |
| user_id     | INTEGER | Foreign Key (users.id)             |
| book_id     | INTEGER | Foreign Key (books.id)             |
| borrow_date | TEXT    |                                     |
| return_date | TEXT    |                                     |
| status      | TEXT    | ["borrowed", "returned", etc.]   |

---

## User Interface
- Modern, responsive design
- Gradient buttons and glassmorphism cards
- Clean typography
- Mobile-friendly layout
- Confirmation dialogs and search functionality

---

## Security
- Passwords hashed using a secure algorithm
- Parameterized SQL queries to prevent SQL injection
- Session-based authentication
- Role-based access control for protected routes
- Server-side form validation and delete confirmations

---

## Installation & Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/library-management.git
   cd library-management
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application:**
   ```bash
   python app.py
   ```
4. **Access the server:**
   Open your browser at `http://127.0.0.1:5000/`

> The SQLite database (`library.db`) is created automatically on first run.

---

## Core Functionality
- Full CRUD operations for books and users
- Transaction handling for borrowing/returning
- Search capabilities for books and users
- Dashboard statistics (module‑specific)
- Responsive and modern UI for all modules

---

## Development Practices
- Feature development in separate branches per module
- Pull requests used for integration into `main`
- Comprehensive commit history and code reviews
- Collaboration encouraged via GitHub contributions

---

## Roadmap & Future Enhancements
- Pagination for book listings
- Live search with AJAX
- Email notifications (registration, due reminders)
- Overdue fine calculations
- Analytical dashboards with charts
- UI role‑based visibility
- Dark mode support

---

## Contributors
- **Module 1:** Book Management team
- **Module 2:** User Management team
- **Module 3:** Transaction Management team

> See individual module READMEs for detailed contributor lists.

---

## License
This project is intended for academic and educational use. No license is currently specified.

---

> _Thank you for exploring the Library Management System!_