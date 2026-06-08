from flask import Flask, render_template, request, redirect, url_for, flash, session
import cv2, os, csv, numpy as np
from datetime import datetime, date, timedelta

app = Flask(__name__)
# Secure key for session encryption
app.secret_key = "vibrant_secure_attendance_2026_key"

# --- CONFIGURATION ---
USER_DB = 'users.csv'
CSV_FILE = 'attendance_v2.csv'
HOLIDAY_FILE = 'holidays.txt'
TRAINER_PATH = 'trainer/trainer.yml'
names = ['None', 'Joshna', 'Akshaya', 'Sritha']

# Initialize AI Tools
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
recognizer = cv2.face.LBPHFaceRecognizer_create()

# Timetable Mapping
TIMETABLE = {
    0: {"P1": "JAVA_LAB", "P2": "JAVA_LAB", "P3": "JAVA", "P4": "DM", "P5": "ATCD"},
    1: {"P1": "DBMS_LAB", "P2": "DBMS_LAB", "P3": "GS", "P4": "DM"},
    2: {"P1": "DBMS", "P2": "IAI", "P3": "DM", "P4": "PROLOG_LAB", "P5": "PROLOG_LAB"},
    3: {"P1": "JAVA", "P2": "GS", "P3": "RTRP", "P4": "RTRP_LAB", "P5": "RTRP_LAB", "P6": "RTRP_LAB"},
    4: {"P1": "DBMS", "P2": "ATCD", "P3": "JAVA", "P4": "ATCD", "P5": "IAI"},
    5: {"P4": "ATCD", "P5": "IAI", "P6": "DBMS"}
}

# --- DATABASE & AUTH FUNCTIONS ---

def save_user(username, password, role):
    file_exists = os.path.isfile(USER_DB)
    with open(USER_DB, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists: writer.writerow(['Username', 'Password', 'Role'])
        writer.writerow([username, password, role])

def verify_user(username, password):
    if not os.path.exists(USER_DB): return None
    with open(USER_DB, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Username'] == username and row['Password'] == password:
                return row['Role']
    return None

# --- ATTENDANCE ANALYTICS LOGIC ---

def is_holiday(check_date_str):
    d = datetime.strptime(check_date_str, '%Y-%m-%d').date()
    if d.weekday() == 6: return True 
    if d.weekday() == 5 and (8 <= d.day <= 14 or 22 <= d.day <= 28): return True
    if os.path.exists(HOLIDAY_FILE):
        with open(HOLIDAY_FILE, 'r') as f:
            if check_date_str in f.read(): return True
    return False

def get_day_weight(date_obj):
    if is_holiday(date_obj.strftime('%Y-%m-%d')): return 0
    day_periods = TIMETABLE.get(date_obj.weekday(), {})
    return sum(2 if "LAB" in v.upper() else 1 for k, v in day_periods.items() if v.upper() not in ["GS", "LIBRARY", "CLUBS"])

def get_full_stats():
    today_obj = date.today()
    today_str = today_obj.strftime('%Y-%m-%d')
    stats = {name: {'day_att': 0, 'day_total': get_day_weight(today_obj), 'mon_att': 0, 'mon_total': 0, 'periods': []} for name in names[1:]}
    
    # Calculate Monthly Possible Weight (1st to Today)
    curr = today_obj.replace(day=1)
    mon_total_weight = 0
    while curr <= today_obj:
        mon_total_weight += get_day_weight(curr)
        curr += timedelta(days=1)
    
    for n in names[1:]: stats[n]['mon_total'] = mon_total_weight

    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            for r in csv.DictReader(f):
                if r['Name'] in stats:
                    w = 2 if "LAB" in r['Subject'].upper() else 1
                    stats[r['Name']]['mon_att'] += w
                    if r['Date'] == today_str:
                        stats[r['Name']]['day_att'] += w
                        if r['Period'] not in stats[r['Name']]['periods']:
                            stats[r['Name']]['periods'].append(r['Period'])
    
    for n in names[1:]:
        d_t, m_t = stats[n]['day_total'], stats[n]['mon_total']
        stats[n]['day_percent'] = round(stats[n]['day_att']/d_t*100, 1) if d_t > 0 else 0
        stats[n]['mon_percent'] = round(stats[n]['mon_att']/m_t*100, 1) if m_t > 0 else 0
    return stats, today_str

# --- ROUTES ---

@app.route('/')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/signup_process', methods=['POST'])
def signup_process():
    save_user(request.form['username'], request.form['password'], request.form['role'])
    flash("Registration Successful! Please login.")
    return redirect(url_for('login_page'))

@app.route('/login_process', methods=['POST'])
def login_process():
    username, password = request.form['username'], request.form['password']
    role = verify_user(username, password)
    if role:
        session['user'] = username
        session['role'] = role
        return redirect(url_for('faculty' if role == 'Faculty' else 'index'))
    flash("Invalid Username or Password!")
    return redirect(url_for('login_page'))

@app.route('/dashboard')
def index():
    if 'user' not in session: return redirect(url_for('login_page'))
    stats, today_str = get_full_stats()
    daily = {n: {'status': 'Present' if i['day_att']>0 else 'Absent', 'periods': i['periods'], 'percent': i['day_percent']} for n, i in stats.items()}
    return render_template('index.html', students=stats, daily=daily, today=today_str)

@app.route('/faculty', methods=['GET', 'POST'])
def faculty():
    # RESTRICT ACCESS: Only Faculty can enter
    if session.get('role') != 'Faculty':
        flash("Unauthorized! Faculty access only.")
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        selected_date = request.form.get('date')
        if 'mark_holiday' in request.form:
            with open(HOLIDAY_FILE, 'a') as f: f.write(selected_date + "\n")
            return redirect(url_for('faculty'))

        period = request.form.get('period')
        day_idx = datetime.strptime(selected_date, '%Y-%m-%d').weekday()
        subject = TIMETABLE.get(day_idx, {}).get(period, "Extra Class")
        
        target_names = []
        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            if os.path.exists(TRAINER_PATH):
                recognizer.read(TRAINER_PATH)
                faces = face_detector.detectMultiScale(gray, 1.2, 8)
                for (x, y, w, h) in faces:
                    id_num, conf = recognizer.predict(gray[y:y+h, x:x+w])
                    if conf < 65: target_names.append(names[id_num])
        elif 'manual_name' in request.form:
            target_names.append(request.form['manual_name'])

        for name in set(target_names):
            log_attendance(name, selected_date, period, subject)
        return redirect(url_for('index'))
        
    return render_template('faculty.html', names=names[1:], today=date.today().strftime('%Y-%m-%d'))

def log_attendance(name, date, period, subject):
    file_exists = os.path.isfile(CSV_FILE)
    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists or os.stat(CSV_FILE).st_size == 0:
            writer.writerow(['Name', 'Date', 'Period', 'Subject', 'Status'])
        writer.writerow([name, date, period, subject, 'Present'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/refresh')
def refresh():
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)