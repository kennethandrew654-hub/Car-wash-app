import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for

base_dir = os.path.dirname(os.path.abspath(__file__))

subfolders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f))]
template_folder_name = next((f for f in subfolders if f.strip().lower() == 'templates'), 'templates')
template_dir = os.path.join(base_dir, template_folder_name)

app = Flask(__name__, template_folder=template_dir)

SERVICES = {
    'Basic Wash': 5000,
    'Deluxe Wash': 10000,
    'Full Detail': 25000
}

DB_PATH = os.path.join(base_dir, 'carwash.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            vehicle TEXT,
            service TEXT,
            price INTEGER,
            date TEXT,
            time TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    
    # Safely add status column if database existed previously without it
    cursor.execute("PRAGMA table_info(bookings)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'status' not in columns:
        cursor.execute("ALTER TABLE bookings ADD COLUMN status TEXT DEFAULT 'Pending'")

    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html', services=SERVICES)

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name')
    phone = request.form.get('phone')
    vehicle = request.form.get('vehicle')
    service = request.form.get('service')
    date = request.form.get('date')
    time = request.form.get('time')
    price = SERVICES.get(service, 0)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (name, phone, vehicle, service, price, date, time, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    ''', (name, phone, vehicle, service, price, date, time))
    conn.commit()
    conn.close()

    return render_template('success.html', 
                           name=name, 
                           phone=phone, 
                           vehicle=vehicle, 
                           service=service, 
                           price=price, 
                           date=date, 
                           time=time)

@app.route('/admin')
def admin():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM bookings ORDER BY id DESC')
    rows = cursor.fetchall()
    conn.close()

    bookings = [dict(row) for row in rows]
    total_revenue = sum(b['price'] for b in bookings if b.get('status') == 'Completed')
    pending_count = len([b for b in bookings if b.get('status') == 'Pending'])

    return render_template('admin.html', bookings=bookings, revenue=total_revenue, pending=pending_count)

@app.route('/complete/<int:booking_id>', methods=['POST'])
def complete_booking(booking_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE bookings SET status = 'Completed' WHERE id = ?", (booking_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
