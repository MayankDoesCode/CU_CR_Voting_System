from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.secret_key = "cu_secret_key"

# ---------------- DATABASE ----------------

conn = sqlite3.connect("voting.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS candidates(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    voter_name TEXT UNIQUE,
    candidate_name TEXT
)
""")

conn.commit()
conn.close()

# ---------------- HOME PAGE ----------------

@app.route("/", methods=["GET", "POST"])
def home():

    conn = sqlite3.connect("voting.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    if request.method == "POST":

        voter = request.form["voter"]
        candidate = request.form["candidate"]

        # Check duplicate vote
        cursor.execute(
            "SELECT * FROM votes WHERE voter_name=?",
            (voter,)
        )

        existing_vote = cursor.fetchone()

        if existing_vote:
            conn.close()
            return "You Have Already Voted!"

        # Store vote
        cursor.execute("""
        INSERT INTO votes(voter_name, candidate_name)
        VALUES(?, ?)
        """, (voter, candidate))

        conn.commit()
        conn.close()

        return "Vote Submitted Successfully!"

    conn.close()

    return render_template(
        "index.html",
        candidates=candidates
    )

# ---------------- ADMIN LOGIN ----------------

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect("/admin")
        else:
            error = "Invalid Administrative Credentials"

    return render_template("admin_login.html", error=error)


# ---------------- ADMIN PANEL ----------------

@app.route("/admin", methods=["GET", "POST"])
def admin():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voting.db")
    cursor = conn.cursor()

    if request.method == "POST":

        candidate = request.form["candidate"]

        cursor.execute("""
        INSERT INTO candidates(name)
        VALUES(?)
        """, (candidate,))

        conn.commit()

    cursor.execute("SELECT * FROM candidates")
    candidates = cursor.fetchall()

    conn.close()

    return render_template(
        "admin.html",
        candidates=candidates
    )

# ---------------- DELETE CANDIDATE ----------------

@app.route("/delete_candidate/<int:id>")
def delete_candidate(id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = sqlite3.connect("voting.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM candidates WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

# ---------------- RESULTS ----------------

@app.route("/results")
def results():

    conn = sqlite3.connect("voting.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT candidates.name,
    COUNT(votes.candidate_name) as total_votes
    FROM candidates
    LEFT JOIN votes
    ON candidates.name = votes.candidate_name
    GROUP BY candidates.name
    ORDER BY total_votes DESC
    """)

    results = cursor.fetchall()

    winner = None

    if results:
        winner = results[0][0]

    conn.close()

    return render_template(
        "results.html",
        results=results,
        winner=winner
    )

# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.pop("admin", None)

    return redirect("/")

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(debug=True)