# Smart Book Library Management System

A Flask-based web application for managing books, users, borrowing records, and book recommendations.

## Project Overview

This project is a full-stack web application that allows users to register, log in, add books, search books, borrow books, return books, and get book recommendations.

The recommendation feature uses TF-IDF vectorization and cosine similarity to recommend books based on title, author, genre, and description.

## Features

- User registration and login
- Secure password hashing
- Add new books
- Search books by title, author, or genre
- Borrow books
- Return books
- Delete books
- Dashboard statistics
- Book recommendation system
- SQLite database
- Bootstrap responsive interface

## Tech Stack

- Python
- Flask
- SQLite
- HTML
- CSS
- Bootstrap
- Scikit-learn
- TF-IDF
- Cosine Similarity

## Project Structure

```text
smart-book-library-management-system/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── base.html
    ├── index.html
    ├── register.html
    ├── login.html
    ├── dashboard.html
    ├── add_book.html
    ├── books.html
    ├── borrowed.html
    └── recommendations.html
```

## How to Run Locally

1. Clone the repository:

```bash
git clone https://github.com/mehnazhossainantora/smart-book-library-management-system.git
cd smart-book-library-management-system
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

For Windows:

```bash
venv\Scripts\activate
```

For macOS/Linux:

```bash
source venv/bin/activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Run the application:

```bash
python app.py
```

6. Open your browser and go to:

```text
http://127.0.0.1:5000
```

## Deployment

This project can be deployed on platforms that support Flask applications, such as Render.

GitHub Pages is not suitable for this project because GitHub Pages is designed for static sites, while this project uses a Python Flask backend and SQLite database.

## Author

Mehnaz Hossain Antora

- GitHub: https://github.com/mehnazhossainantora
- LinkedIn: https://www.linkedin.com/in/mehnaz-antora
- Google Scholar: https://scholar.google.com/citations?user=jZgu--IAAAAJ&hl=en
- Email: mehnazhossainantora@gmail.com
