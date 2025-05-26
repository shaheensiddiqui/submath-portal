import sqlite3

def init_db():
    with sqlite3.connect("tuition.db") as conn:
        c = conn.cursor()

        # Enable Write-Ahead Logging to prevent locking
        c.execute("PRAGMA journal_mode=WAL")
        # Admins table
        c.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL  -- Note: Store plain for now, later hash!
            )
        ''')

        # Insert default admin only if not exists
        c.execute("SELECT COUNT(*) FROM admins")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", ("admin", "submathtutorial123"))

        # Students table
        c.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                contact TEXT NOT NULL,
                email TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')

        # Subjects table
        c.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                class INTEGER,
                board TEXT,
                stream TEXT,
                subjects TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Attendance table
        c.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT CHECK(status IN ('Present', 'Absent')) NOT NULL,
                tuition_taken TEXT CHECK(tuition_taken IN ('Yes', 'No')) NOT NULL,
                UNIQUE(student_id, date),
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Fees table
        c.execute('''
            CREATE TABLE IF NOT EXISTS fees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                expected_fee REAL NOT NULL,
                month TEXT NOT NULL,
                year TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                payment_mode TEXT,
                notes TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')

        # Homework table
        c.execute('''
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                due_date TEXT NOT NULL,
                assigned_class INTEGER NOT NULL
            )
        ''')

        # Submissions table (for grading)
        c.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                homework_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                grade TEXT,
                FOREIGN KEY (homework_id) REFERENCES homework(id),
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(homework_id, student_id)
            )
        ''')

        # Create student progress comments table
        c.execute('''
            CREATE TABLE IF NOT EXISTS progress_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL, 
                comment TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id)
            )
        ''')


        conn.commit()
        print("✅ Database initialized with all modules.")

if __name__ == "__main__":
    init_db()
