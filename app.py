from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'submathtutorialsecret'


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM admins WHERE username = ? AND password = ?", (username, password))
            admin = c.fetchone()

        if admin:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Invalid username or password"

    return render_template("admin_login.html", error=error)



@app.route("/admin-dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")


#admin dashboard 
#add students 1 and 2 

@app.route("/add-student", methods=["GET", "POST"])
def add_student_step1():
    if request.method == "POST":
        name = request.form["name"]
        dob = request.form["dob"]
        contact = request.form["contact"]
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM students WHERE username = ?", (username,))
            existing_user = c.fetchone()

        if existing_user:
            return render_template("add_student_step1.html", error="Username already taken. Please choose another one.")

        session["name"] = name
        session["dob"] = dob
        session["contact"] = contact
        session["email"] = email
        session["username"] = username
        session["password"] = password

        return redirect(url_for("add_student_step2"))

    return render_template("add_student_step1.html")

@app.route("/add-student-step2", methods=["GET", "POST"])
def add_student_step2():
    if request.method == "POST":
        board = request.form["board"]
        student_class = int(request.form["class"])
        stream = request.form.get("stream") if student_class >= 11 else None
        subjects_selected = request.form.getlist("subjects")
        subjects_str = ", ".join(subjects_selected)

        name = session.get("name")
        dob = session.get("dob")
        contact = session.get("contact")
        email = session.get("email")
        username = session.get("username")
        password = session.get("password")

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO students (name, dob, contact, email, username, password) VALUES (?, ?, ?, ?, ?, ?)",
                      (name, dob, contact, email, username, password))
            student_id = c.lastrowid

            c.execute("INSERT INTO subjects (student_id, class, board, stream, subjects) VALUES (?, ?, ?, ?, ?)",
                      (student_id, student_class, board, stream, subjects_str))

            conn.commit()

        session.clear()
        return "<h2>Student added successfully!</h2><a href='/admin-dashboard'>Go back to dashboard</a>"

    return render_template("add_student_step2.html")

#

@app.route("/view-students")
def view_students():
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("""
            SELECT 
                s.id, s.username, s.name, s.dob, s.contact, s.email,
                subj.class, subj.board, subj.stream, subj.subjects
            FROM students s
            JOIN subjects subj ON s.id = subj.student_id
        """)
        students = c.fetchall()
    return render_template("view_students.html", students=students)

  

# -------------------- EDIT STUDENT --------------------

@app.route("/edit-student/<int:student_id>", methods=["GET", "POST"])
def edit_student_step1(student_id):
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()

        if request.method == "POST":
            name = request.form["name"]
            dob = request.form["dob"]
            contact = request.form["contact"]
            email = request.form["email"]
            username = request.form["username"]
            password = request.form["password"]

            c.execute('''UPDATE students 
                         SET name=?, dob=?, contact=?, email=?, username=?, password=?
                         WHERE id=?''',
                      (name, dob, contact, email, username, password, student_id))

            conn.commit()
            session["edit_student_id"] = student_id
            return redirect(url_for("edit_student_step2"))

        c.execute("SELECT * FROM students WHERE id=?", (student_id,))
        student = c.fetchone()

    if student:
        return render_template("edit_student_step1.html", student=student)
    else:
        return "Student not found", 404

@app.route("/edit-student-step2", methods=["GET", "POST"])
def edit_student_step2():
    student_id = session.get("edit_student_id")

    if not student_id:
        return redirect(url_for("view_students"))

    subject_data = None

    with sqlite3.connect("tuition.db", timeout=30) as conn:
        conn.execute("PRAGMA journal_mode=WAL")  # Allow concurrent reads/writes
        c = conn.cursor()

        if request.method == "POST":
            board = request.form["board"]
            student_class = int(request.form["class"])
            stream = request.form.get("stream")
            subjects_selected = request.form.getlist("subjects")
            subjects_str = ", ".join(subjects_selected)

            c.execute('''
                UPDATE subjects 
                SET class = ?, board = ?, stream = ?, subjects = ?
                WHERE student_id = ?
            ''', (student_class, board, stream, subjects_str, student_id))

            conn.commit()
            session.pop("edit_student_id", None)
            return redirect(url_for("view_students"))
        else:
            c.execute("SELECT class, board, stream, subjects FROM subjects WHERE student_id = ?", (student_id,))
            subject_data = c.fetchone()

    return render_template("edit_student_step2.html", subject_data=subject_data)


@app.route("/mark-attendance", methods=["GET", "POST"])
def mark_attendance():
    today = date.today().isoformat()
    selected_date = request.form.get("attendance_date") or request.args.get("date")
    tuition_taken = request.form.get("tuition_taken")
    absent_ids = request.form.getlist("absent_ids")
    students = []
    existing_attendance = {}

    if request.method == "POST" and selected_date and tuition_taken:
        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM attendance WHERE date = ?", (selected_date,))

            c.execute("SELECT id FROM students")
            all_students = c.fetchall()

            for (student_id,) in all_students:
                status = "Absent" if str(student_id) in absent_ids else "Present"
                c.execute('''
                    INSERT INTO attendance (student_id, date, status, tuition_taken)
                    VALUES (?, ?, ?, ?)
                ''', (student_id, selected_date, status, tuition_taken))

            conn.commit()
        return redirect(url_for('mark_attendance', date=selected_date))

    if selected_date:
        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute('''
                SELECT a.student_id, a.status, s.name
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date = ?
            ''', (selected_date,))
            rows = c.fetchall()
            if rows:
                tuition_taken = rows[0][2] if len(rows[0]) > 2 else "Yes"
                existing_attendance = {str(row[0]): row[1] for row in rows}
                students = [(row[0], row[2]) for row in rows]
            else:
                c.execute("SELECT id, name FROM students")
                students = c.fetchall()
    else:
        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name FROM students")
            students = c.fetchall()

    return render_template("mark_attendance.html",
                           today=today,
                           students=students,
                           selected_date=selected_date,
                           tuition_taken=tuition_taken,
                           existing_attendance=existing_attendance)

from datetime import date

@app.route("/view-attendance", methods=["GET", "POST"])
def view_attendance():
    selected_date = None
    records = []
    total_students = 0
    absent_count = 0

    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()

        if request.method == "POST":
            selected_date = request.form["attendance_date"]

            c.execute('''
                SELECT s.name, a.status
                FROM attendance a
                JOIN students s ON a.student_id = s.id
                WHERE a.date = ?
                ORDER BY s.name
            ''', (selected_date,))
            records = c.fetchall()
            total_students = len(records)
            absent_count = sum(1 for r in records if r[1] == "Absent")

    return render_template("view_attendance.html",
                           records=records,
                           selected_date=selected_date,
                           total_students=total_students,
                           absent_count=absent_count,
                           today=date.today().isoformat())  # ✅ This fixes the error

@app.route("/add-fee", methods=["GET", "POST"])
def add_fee():
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name FROM students ORDER BY name")
        students = c.fetchall()

    if request.method == "POST":
        student_id = request.form["student_id"]
        amount = request.form["amount"]
        expected_fee = request.form["expected_fee"]
        month = request.form["month"]
        year = request.form["year"]
        payment_date = request.form["payment_date"]
        payment_mode = request.form["payment_mode"]
        notes = request.form.get("notes", "")

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute('''
                INSERT INTO fees (student_id, amount, expected_fee, month, year, payment_date, payment_mode, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (student_id, amount, expected_fee, month, year, payment_date, payment_mode, notes))
            conn.commit()

        return redirect(url_for("add_fee"))

    return render_template("add_fee.html", students=students, now=datetime.now)


@app.route("/view-fees")
def view_fees():
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT f.id, s.name, f.amount, f.expected_fee, f.month, f.year,
                   f.payment_date, f.payment_mode, f.notes
            FROM fees f
            JOIN students s ON f.student_id = s.id
            ORDER BY f.payment_date DESC
        ''')
        fees = c.fetchall()

    # Prepare display-ready list
    processed_fees = []
    for row in fees:
        fee_id = row[0]
        name = row[1]
        amount = row[2]
        expected = row[3]
        month = row[4]
        year = row[5]
        date = row[6]
        mode = row[7]
        notes = row[8]

        # Status logic
        if float(amount) < float(expected):
            status = f"Pending ₹{round(float(expected) - float(amount), 2)}"
        elif float(amount) > float(expected):
            status = f"Advance ₹{round(float(amount) - float(expected), 2)}"
        else:
            status = "Paid"

        processed_fees.append((
            name,         # fee[0]
            amount,       # fee[1]
            expected,     # fee[2]
            month,        # fee[3]
            year,         # fee[4]
            date,         # fee[5]
            mode,         # fee[6]
            notes,        # fee[7]
            status,       # fee[8]
            fee_id        # fee[9] ✅
        ))


    return render_template("view_fees.html", fees=processed_fees)


@app.route("/edit-fee/<int:fee_id>", methods=["GET", "POST"])
def edit_fee(fee_id):
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()

        # Fetch students for dropdown
        c.execute("SELECT id, name FROM students ORDER BY name")
        students = c.fetchall()

        # Fetch current fee record
        c.execute("SELECT * FROM fees WHERE id = ?", (fee_id,))
        fee = c.fetchone()

    if not fee:
        return "Fee record not found", 404

    if request.method == "POST":
        student_id = request.form["student_id"]
        amount = request.form["amount"]
        expected_fee = request.form["expected_fee"]
        month = request.form["month"]
        year = request.form["year"]
        payment_date = request.form["payment_date"]
        payment_mode = request.form["payment_mode"]
        notes = request.form.get("notes", "")

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute('''
                UPDATE fees SET
                    student_id = ?, amount = ?, expected_fee = ?, month = ?, year = ?,
                    payment_date = ?, payment_mode = ?, notes = ?
                WHERE id = ?
            ''', (student_id, amount, expected_fee, month, year, payment_date, payment_mode, notes, fee_id))
            conn.commit()

        return redirect(url_for("view_fees"))

    return render_template("edit_fee.html", students=students, fee=fee)

@app.route("/delete-fee/<int:fee_id>", methods=["POST"])
def delete_fee(fee_id):
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM fees WHERE id = ?", (fee_id,))
        conn.commit()
    return redirect(url_for("view_fees"))

@app.route("/add-homework", methods=["GET", "POST"])
def add_homework():
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        due_date = request.form["due_date"]
        assigned_class = int(request.form["assigned_class"])

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("INSERT INTO homework (title, description, due_date, assigned_class) VALUES (?, ?, ?, ?)",
                      (title, description, due_date, assigned_class))
            conn.commit()

        return redirect(url_for("view_homework"))

    return render_template("add_homework.html")

@app.route("/view-homework")
def view_homework():
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT id, title, due_date, assigned_class FROM homework ORDER BY due_date DESC")
        homeworks = c.fetchall()

    return render_template("view_homework.html", homeworks=homeworks)

@app.route("/view-homework/<int:homework_id>", methods=["GET", "POST"])
def view_homework_detail(homework_id):
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()

        # Fetch homework details
        c.execute("SELECT id, title, description, due_date, assigned_class FROM homework WHERE id = ?", (homework_id,))
        hw = c.fetchone()

        if not hw:
            return "Homework not found", 404

        assigned_class = hw[4]

        # Fetch students of this class
        c.execute('''
            SELECT s.id, s.name 
            FROM students s 
            JOIN subjects subj ON s.id = subj.student_id
            WHERE subj.class = ?
        ''', (assigned_class,))
        students = c.fetchall()

        # If grades are submitted
        if request.method == "POST":
            for student_id, _ in students:
                grade_input = request.form.get(f"grade_{student_id}")
                if grade_input:
                    # Check if submission exists
                    c.execute("SELECT id FROM submissions WHERE student_id=? AND homework_id=?", (student_id, homework_id))
                    if c.fetchone():
                        c.execute("UPDATE submissions SET grade=? WHERE student_id=? AND homework_id=?",
                                  (grade_input, student_id, homework_id))
                    else:
                        c.execute("INSERT INTO submissions (homework_id, student_id, grade) VALUES (?, ?, ?)",
                                  (homework_id, student_id, grade_input))
            conn.commit()

        # Fetch current grades
        c.execute("SELECT student_id, grade FROM submissions WHERE homework_id = ?", (homework_id,))
        submitted = {row[0]: row[1] for row in c.fetchall()}

    return render_template("homework_detail.html", hw=hw, students=students, submitted=submitted)



@app.route("/delete-homework/<int:homework_id>", methods=["POST"])
def delete_homework(homework_id):
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM submissions WHERE homework_id = ?", (homework_id,))
        c.execute("DELETE FROM homework WHERE id = ?", (homework_id,))
        conn.commit()
    return redirect(url_for("view_homework"))

@app.route("/progress-list")
def progress_list():
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()
        c.execute("SELECT id, name FROM students ORDER BY name")
        students = c.fetchall()
    return render_template("progress_list.html", students=students)


@app.route("/view-progress/<int:student_id>", methods=["GET", "POST"])
def view_progress(student_id):
    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()

        # Get student basic info
        c.execute("SELECT name FROM students WHERE id = ?", (student_id,))
        student = c.fetchone()

        # Total lectures held (distinct dates where tuition_taken = 'Yes')
        c.execute("SELECT COUNT(DISTINCT date) FROM attendance WHERE tuition_taken = 'Yes'")
        total_lectures = c.fetchone()[0]

        # Absent count for this student
        c.execute("SELECT COUNT(*) FROM attendance WHERE student_id = ? AND status = 'Absent'", (student_id,))
        absent_lectures = c.fetchone()[0]

        # Total assignments given to student's class
        c.execute("SELECT subj.class FROM subjects subj WHERE subj.student_id = ?", (student_id,))
        student_class = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM homework WHERE assigned_class = ?", (student_class,))
        total_homework = c.fetchone()[0]

        # Submissions made by student
        c.execute("SELECT COUNT(*) FROM submissions WHERE student_id = ?", (student_id,))
        completed_homework = c.fetchone()[0]

        # Fetch current progress comment
        c.execute("SELECT comment FROM progress_comments WHERE student_id = ?", (student_id,))
        comment_row = c.fetchone()
        comment = comment_row[0] if comment_row else ""

        # Update comment if submitted
        if request.method == "POST":
            new_comment = request.form["comment"]
            if comment_row:
                c.execute("UPDATE progress_comments SET comment = ? WHERE student_id = ?", (new_comment, student_id))
            else:
                c.execute("INSERT INTO progress_comments (student_id, comment) VALUES (?, ?)", (student_id, new_comment))
            conn.commit()
            return redirect(url_for("view_progress", student_id=student_id))

    return render_template("student_progress.html", student=student, total_lectures=total_lectures,
                           absent_lectures=absent_lectures, total_homework=total_homework,
                           completed_homework=completed_homework, comment=comment)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# STUDENT SIDE STUFF

@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        with sqlite3.connect("tuition.db", timeout=10) as conn:
            c = conn.cursor()
            c.execute("SELECT id, name FROM students WHERE username = ? AND password = ?", (username, password))
            student = c.fetchone()

        if student:
            session["student_id"] = student[0]
            session["student_name"] = student[1]
            return redirect(url_for("student_dashboard"))
        else:
            error = "Invalid credentials. Please try again."

    return render_template("student_login.html", error=error)

@app.route("/student-dashboard")
def student_dashboard():
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("student_login"))

    with sqlite3.connect("tuition.db", timeout=10) as conn:
        c = conn.cursor()

        # Total lectures held
        c.execute("SELECT COUNT(DISTINCT date) FROM attendance WHERE tuition_taken = 'Yes'")
        total_lectures = c.fetchone()[0]

        # Attended lectures
        c.execute("SELECT COUNT(*) FROM attendance WHERE student_id = ? AND status = 'Present'", (student_id,))
        attended_lectures = c.fetchone()[0]

        # Homework assigned to their class
        c.execute("SELECT class FROM subjects WHERE student_id = ?", (student_id,))
        student_class = c.fetchone()[0]

        c.execute("SELECT id, title, due_date FROM homework WHERE assigned_class = ?", (student_class,))
        all_homework = c.fetchall()

        # Submissions by this student
        c.execute("SELECT homework_id, grade FROM submissions WHERE student_id = ?", (student_id,))
        submitted = {row[0]: row[1] for row in c.fetchall()}

        # Admin progress comment
        c.execute("SELECT comment FROM progress_comments WHERE student_id = ?", (student_id,))
        comment_row = c.fetchone()
        progress_note = comment_row[0] if comment_row else ""

    return render_template("student_dashboard.html",
                           name=session["student_name"],
                           total_lectures=total_lectures,
                           attended_lectures=attended_lectures,
                           all_homework=all_homework,
                           submitted=submitted,
                           progress_note=progress_note)



if __name__ == "__main__":
    app.run(debug=True)
