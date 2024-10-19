from flask import Flask, request, jsonify, render_template
import sqlite3
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

# Connect to SQLite database (it will create if it doesn't exist)
def get_db_connection():
    conn = sqlite3.connect('student_recognition.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database and create the 'students' table if it doesn't exist
def create_students_table():
    conn = get_db_connection()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY,
        student_name TEXT NOT NULL,
        academic_year INTEGER NOT NULL,
        academic_performance REAL NOT NULL,
        consistency_over_semesters INTEGER NOT NULL,
        core_engineering_courses_score REAL NOT NULL,
        hackathon_participation INTEGER NOT NULL,
        paper_presentations INTEGER NOT NULL,
        teacher_assistance_contributions INTEGER NOT NULL
    )''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_student', methods=['POST'])
def add_student():
    data = request.json
    student_id = data['student_id']
    student_name = data['student_name']
    academic_year = data['academic_year']
    academic_performance = data['academic_performance']
    consistency_over_semesters = data['consistency_over_semesters']
    core_engineering_courses_score = data['core_engineering_courses_score']
    hackathon_participation = data['hackathon_participation']
    paper_presentations = data['paper_presentations']
    teacher_assistance_contributions = data['teacher_assistance_contributions']

    conn = get_db_connection()
    
    existing_student = conn.execute('SELECT * FROM students WHERE student_id = ?', (student_id,)).fetchone()
    
    if existing_student:
        return jsonify({"error": "Student ID already exists."}), 400
    
    conn.execute('''
        INSERT INTO students (student_id, student_name, academic_year,
                              academic_performance, consistency_over_semesters,
                              core_engineering_courses_score, hackathon_participation,
                              paper_presentations, teacher_assistance_contributions) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (student_id, student_name, academic_year, academic_performance,
                  consistency_over_semesters, core_engineering_courses_score,
                  hackathon_participation, paper_presentations,
                  teacher_assistance_contributions))
    
    conn.commit()
    conn.close()
    
    return jsonify({"message": f"Student {student_name} added successfully."}), 201

@app.route('/get_top_students/<int:academic_year>', methods=['GET'])
def get_top_students(academic_year):
    conn = get_db_connection()
    
    query = "SELECT * FROM students WHERE academic_year = ?"
    df = pd.read_sql_query(query, conn, params=(academic_year,))
    
    if df.empty:
        return jsonify({"error": "No records found for this academic year."}), 404

    features = df[['academic_performance', 'consistency_over_semesters', 
                    'core_engineering_courses_score', 'hackathon_participation', 
                    'paper_presentations', 'teacher_assistance_contributions']]
    
    scaler = MinMaxScaler()
    scaled_features = scaler.fit_transform(features)

    weights = np.array([0.3, 0.2, 0.25, 0.1, 0.1, 0.05])  
    
    df['Score'] = np.dot(scaled_features, weights)
    
    top_students = df.nlargest(3, 'Score')
    
    result = top_students[['academic_year', 'student_id', 'student_name', 'Score']].to_dict(orient='records')
    
    conn.close()
    
    return jsonify(result)

@app.route('/view_all_students', methods=['GET'])
def view_all_students():
    conn = get_db_connection()
    
    query = "SELECT * FROM students"
    df = pd.read_sql_query(query, conn)
    
    if df.empty:
        return jsonify({"error": "No records found."}), 404
    
    result = df.to_dict(orient='records')
    
    conn.close()
    
    return jsonify(result)

if __name__ == '__main__':
    create_students_table()  # Create the table when starting the app
    app.run(debug=True)
