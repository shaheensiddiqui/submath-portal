import sqlite3

conn = sqlite3.connect("tuition.db")
c = conn.cursor()

# Insert sample student
c.execute('''
    INSERT INTO students (name, dob, contact, email, username, password)
    VALUES (?, ?, ?, ?, ?, ?)
''', ("Rohan Desai", "2006-04-25", "9876543212", "rohan@example.com", "rohan123", "hello123"))

# Get student ID
student_id = c.lastrowid

# Insert matching subject info (class 11, Commerce)
c.execute('''
    INSERT INTO subjects (student_id, class, board, stream, subjects)
    VALUES (?, ?, ?, ?, ?)
''', (student_id, 11, "CBSE", "Commerce", "Math"))

conn.commit()
conn.close()

print("✅ Test student added with username rohan123 and password hello123")
