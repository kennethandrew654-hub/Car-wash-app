from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'carwash_secret_key_malawi'

DB_NAME = "carwash.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            car_model TEXT NOT NULL,
            service TEXT NOT NULL,
            price INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

SERVICES = [
    {"name": "Body Wash & Drying", "price": 5000, "desc": "High-pressure exterior wash, wheel shine, and micro-fiber dry."},
    {"name": "Executive Full Wash", "price": 10000, "desc": "Exterior wash, deep interior vacuuming, dashboard shine, and tire dressing."},
    {"name": "Full Detail & Engine Bay", "price": 20000, "desc": "Full executive wash + engine bay degreasing and interior upholstery shampoo."}
]

@app.route('/')
def index():
    return render_template('index.html', services=SERVICES)

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name')
    phone = request.form.get('phone')
    car_model = request.form.get('car_model')
    service_info = request.form.get('service').split('|')
    
    service_name = service_info[0]
    price = int(service_info[1])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO bookings (client_name, phone, car_model, service, price)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, phone, car_model, service_name, price))
    conn.commit()
    conn.close()

    # Pre-filled WhatsApp message redirect
    my_whatsapp = "265991554333" # Put your WhatsApp phone number here
    message = f"Hello! New Car Wash Booking Request:\n\nName: {name}\nPhone: {phone}\nCar: {car_model}\nService: {service_name}\nPrice: MK {price:,}"
    whatsapp_url = f"https://wa.me/{my_whatsapp}?text={message.replace(' ', '%20').replace('\n', '%0A')}"

    return redirect(whatsapp_url)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == 'POST':
        booking_id = request.form.get('id')
        action = request.form.get('action')
        if action == 'complete':
            cursor.execute("UPDATE bookings SET status = 'Completed' WHERE id = ?", (booking_id,))
        elif action == 'delete':
            cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
        conn.commit()

    cursor.execute("SELECT * FROM bookings ORDER BY id DESC")
    bookings = cursor.fetchall()

    cursor.execute("SELECT SUM(price) FROM bookings WHERE status = 'Completed'")
    total_revenue = cursor.fetchone()[0] or 0

    conn.close()
    return render_template('admin.html', bookings=bookings, total_revenue=total_revenue)

if __name__ == '__main__':
    app.run(debug=True)

