# Budgeting App

## Full-Stack Financial Tracking Web Application

---

## Overview

A full-stack web-based budgeting application that allows users to track income, expenses, savings, and withdrawn savings while visualising financial performance through interactive dashboard analytics and monthly comparison charts.

Built with:

- Python (Flask)
- HTML5
- CSS3
- JavaScript
- SQLite

---

## Features

### Authentication
- User registration and login
- Password hashing
- Session-based authentication
- Protected dashboard routes

### Financial Tracking
- Add income
- Add expenses (with merchant and category)
- Track savings
- Record withdrawn savings
- Persistent database storage (SQLite)

### Dashboard Analytics
- Largest expense of the month
- Top merchant by spending
- Savings progress tracker
- Monthly overview

### Data Visualisation
- Monthly comparison charts
- Spending breakdown visuals

### Transaction Filtering
- Filter by merchant
- Filter by category
- Filter by month

---

## Tech Stack

| Layer      | Technology |
|------------|------------|
| Frontend   | HTML5, CSS3, JavaScript |
| Backend    | Python, Flask |
| Database   | SQLite |
| Tools      | Git, GitHub, VS Code |

---

## Project Structure

```text
Budgeting-app/
├── app.py
├── templates/
├── static/
│   ├── style.css
│   └── script.js
├── requirements.txt
└── README.md
```

- Flask routes handle backend logic
- Templates render dynamic views
- Static folder contains frontend assets
- SQLite stores users and transactions

---

## How to Run Locally

```bash
git clone https://github.com/alex-mate/Budgeting-app
cd Budgeting-app
pip install -r requirements.txt
python app.py
```

Open in browser:

```
http://127.0.0.1:5000
```

---

## What This Project Demonstrates

- Full-stack web development
- Secure authentication system
- CRUD operations
- Data persistence
- Dashboard analytics
- Chart integration
- Filtering logic
- Clean separation of frontend and backend

---

## Future Improvements

- Cloud deployment (Render / Railway)
- Export to CSV
- Dark mode
- Enhanced UI animations
- Advanced financial insights

---

## Developer Notes

This project was built as part of my transition into professional web development, focusing on writing clean, structured, and maintainable code while implementing real-world application logic.
