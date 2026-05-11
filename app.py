import os
import sqlite3
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change_this_secret_key_before_deployment")

DATABASE = os.environ.get("DATABASE_NAME", "library.db")


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_db_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            genre TEXT NOT NULL,
            description TEXT NOT NULL,
            total_copies INTEGER NOT NULL,
            available_copies INTEGER NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS borrowed_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'borrowed',
            borrowed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            returned_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (book_id) REFERENCES books (id)
        )
        """
    )

    conn.commit()

    existing_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]

    if existing_books == 0:
        sample_books = [
            (
                "Introduction to Machine Learning",
                "Ethem Alpaydin",
                "Machine Learning",
                "A beginner-friendly introduction to machine learning concepts, algorithms, and applications.",
                5,
                5,
            ),
            (
                "Python Crash Course",
                "Eric Matthes",
                "Programming",
                "A hands-on introduction to Python programming with practical projects.",
                4,
                4,
            ),
            (
                "Clean Code",
                "Robert C. Martin",
                "Software Engineering",
                "A guide to writing readable, maintainable, and professional software code.",
                3,
                3,
            ),
            (
                "Deep Learning",
                "Ian Goodfellow",
                "Artificial Intelligence",
                "A comprehensive textbook covering deep learning theory and applications.",
                2,
                2,
            ),
            (
                "Database System Concepts",
                "Abraham Silberschatz",
                "Database",
                "A detailed introduction to database systems, SQL, transactions, and database design.",
                4,
                4,
            ),
            (
                "Flask Web Development",
                "Miguel Grinberg",
                "Web Development",
                "A practical guide to building web applications with Flask and Python.",
                3,
                3,
            ),
        ]

        conn.executemany(
            """
            INSERT INTO books
            (title, author, genre, description, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            sample_books,
        )

        conn.commit()

    conn.close()


def login_required(view_function):
    @wraps(view_function)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("login"))
        return view_function(*args, **kwargs)

    return wrapped_view


@app.before_request
def setup_database_once():
    initialize_database()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password),
            )
            conn.commit()
            conn.close()

            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            flash("This email is already registered.", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Login successful.", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have logged out successfully.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()

    total_books = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    available_books = conn.execute("SELECT SUM(available_copies) FROM books").fetchone()[0] or 0
    borrowed_books = conn.execute(
        "SELECT COUNT(*) FROM borrowed_books WHERE status = 'borrowed'"
    ).fetchone()[0]
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_books=total_books,
        available_books=available_books,
        borrowed_books=borrowed_books,
        total_users=total_users,
    )


@app.route("/add-book", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        genre = request.form.get("genre", "").strip()
        description = request.form.get("description", "").strip()
        total_copies = request.form.get("total_copies", "1").strip()

        if not title or not author or not genre or not description or not total_copies:
            flash("All fields are required.", "danger")
            return redirect(url_for("add_book"))

        try:
            total_copies = int(total_copies)
            if total_copies <= 0:
                raise ValueError
        except ValueError:
            flash("Total copies must be a positive number.", "danger")
            return redirect(url_for("add_book"))

        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO books
            (title, author, genre, description, total_copies, available_copies)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, author, genre, description, total_copies, total_copies),
        )
        conn.commit()
        conn.close()

        flash("Book added successfully.", "success")
        return redirect(url_for("books"))

    return render_template("add_book.html")


@app.route("/books")
@login_required
def books():
    search_query = request.args.get("search", "").strip()

    conn = get_db_connection()

    if search_query:
        books_list = conn.execute(
            """
            SELECT * FROM books
            WHERE title LIKE ? OR author LIKE ? OR genre LIKE ?
            ORDER BY title
            """,
            (
                f"%{search_query}%",
                f"%{search_query}%",
                f"%{search_query}%",
            ),
        ).fetchall()
    else:
        books_list = conn.execute("SELECT * FROM books ORDER BY title").fetchall()

    conn.close()

    return render_template("books.html", books=books_list, search_query=search_query)


@app.route("/borrow/<int:book_id>", methods=["POST"])
@login_required
def borrow_book(book_id):
    user_id = session["user_id"]

    conn = get_db_connection()

    book = conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()

    if not book:
        conn.close()
        flash("Book not found.", "danger")
        return redirect(url_for("books"))

    existing_borrow = conn.execute(
        """
        SELECT * FROM borrowed_books
        WHERE user_id = ? AND book_id = ? AND status = 'borrowed'
        """,
        (user_id, book_id),
    ).fetchone()

    if existing_borrow:
        conn.close()
        flash("You already borrowed this book.", "warning")
        return redirect(url_for("books"))

    if book["available_copies"] <= 0:
        conn.close()
        flash("This book is currently not available.", "danger")
        return redirect(url_for("books"))

    conn.execute(
        """
        INSERT INTO borrowed_books (user_id, book_id, status)
        VALUES (?, ?, 'borrowed')
        """,
        (user_id, book_id),
    )

    conn.execute(
        """
        UPDATE books
        SET available_copies = available_copies - 1
        WHERE id = ?
        """,
        (book_id,),
    )

    conn.commit()
    conn.close()

    flash("Book borrowed successfully.", "success")
    return redirect(url_for("borrowed_books"))


@app.route("/borrowed")
@login_required
def borrowed_books():
    user_id = session["user_id"]

    conn = get_db_connection()

    borrowed_list = conn.execute(
        """
        SELECT borrowed_books.id AS borrow_id,
               borrowed_books.borrowed_at,
               books.title,
               books.author,
               books.genre
        FROM borrowed_books
        JOIN books ON borrowed_books.book_id = books.id
        WHERE borrowed_books.user_id = ?
          AND borrowed_books.status = 'borrowed'
        ORDER BY borrowed_books.borrowed_at DESC
        """,
        (user_id,),
    ).fetchall()

    conn.close()

    return render_template("borrowed.html", borrowed_books=borrowed_list)


@app.route("/return/<int:borrow_id>", methods=["POST"])
@login_required
def return_book(borrow_id):
    user_id = session["user_id"]

    conn = get_db_connection()

    borrowed_record = conn.execute(
        """
        SELECT * FROM borrowed_books
        WHERE id = ? AND user_id = ? AND status = 'borrowed'
        """,
        (borrow_id, user_id),
    ).fetchone()

    if not borrowed_record:
        conn.close()
        flash("Borrow record not found.", "danger")
        return redirect(url_for("borrowed_books"))

    book_id = borrowed_record["book_id"]

    conn.execute(
        """
        UPDATE borrowed_books
        SET status = 'returned',
            returned_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (borrow_id,),
    )

    conn.execute(
        """
        UPDATE books
        SET available_copies = available_copies + 1
        WHERE id = ?
        """,
        (book_id,),
    )

    conn.commit()
    conn.close()

    flash("Book returned successfully.", "success")
    return redirect(url_for("borrowed_books"))


@app.route("/delete-book/<int:book_id>", methods=["POST"])
@login_required
def delete_book(book_id):
    conn = get_db_connection()

    active_borrows = conn.execute(
        """
        SELECT COUNT(*) FROM borrowed_books
        WHERE book_id = ? AND status = 'borrowed'
        """,
        (book_id,),
    ).fetchone()[0]

    if active_borrows > 0:
        conn.close()
        flash("Cannot delete a book that is currently borrowed.", "danger")
        return redirect(url_for("books"))

    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
    conn.commit()
    conn.close()

    flash("Book deleted successfully.", "success")
    return redirect(url_for("books"))


@app.route("/recommendations")
@login_required
def recommendations():
    selected_book_id = request.args.get("book_id", type=int)

    conn = get_db_connection()
    all_books = conn.execute("SELECT * FROM books ORDER BY title").fetchall()
    conn.close()

    recommended_books = []

    if selected_book_id and len(all_books) > 1:
        book_texts = []
        book_ids = []

        for book in all_books:
            combined_text = f"{book['title']} {book['author']} {book['genre']} {book['description']}"
            book_texts.append(combined_text)
            book_ids.append(book["id"])

        try:
            vectorizer = TfidfVectorizer(stop_words="english")
            tfidf_matrix = vectorizer.fit_transform(book_texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)

            selected_index = book_ids.index(selected_book_id)
            similarity_scores = list(enumerate(similarity_matrix[selected_index]))

            similarity_scores = sorted(
                similarity_scores,
                key=lambda item: item[1],
                reverse=True,
            )

            recommended_indices = [
                index for index, score in similarity_scores
                if index != selected_index
            ][:3]

            recommended_books = [all_books[index] for index in recommended_indices]

        except ValueError:
            flash("Selected book not found.", "danger")

    return render_template(
        "recommendations.html",
        books=all_books,
        selected_book_id=selected_book_id,
        recommended_books=recommended_books,
    )


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)
