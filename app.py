from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_NAME = "carwash.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Bookings table with status stages and add-ons
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            car_model TEXT NOT NULL,
            service TEXT NOT NULL,
            addons TEXT,
            price INTEGER NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')
    # Loyalty tracking table (10th wash free)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS loyalty (
            phone TEXT PRIMARY KEY,
            wash_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

SERVICES = [
    {"name": "Body Wash & Drying", "price": 5000, "desc": "High-pressure exterior wash, wheel shine, and micro-fiber dry."},
    {"name": "Executive Full Wash", "price": 10000, "desc": "Exterior wash, deep interior vacuuming, dashboard shine, and tire dressing."},
    {"name": "Full Detail & Engine Bay", "price": 20000, "desc": "Executive wash + engine bay degreasing and interior upholstery shampoo."}
]

ADDONS = [
    {"name": "Tire Shine & Rim Polish", "price": 1500},
    {"name": "Rain Repellent Coating", "price": 2000},
    {"name": "Interior Fragrance", "price": 1000}
]

@app.route('/')
def index():
    return render_template('index.html', services=SERVICES, addons=ADDONS)

@app.route('/book', methods=['POST'])
def book():
    name = request.form.get('name')
    phone = request.form.get('phone').strip()
    car_model = request.form.get('car_model')
    service_info = request.form.get('service').split('|')
    
    service_name = service_info[0]
    base_price = int(service_info[1])

    # Calculate selected add-ons
    selected_addons = request.form.getlist('addons')
    addon_total = 0
    addon_names = []
    for item in selected_addons:
        parts = item.split('|')
        addon_names.append(parts[0])
        addon_total += int(parts[1])

    total_price = base_price + addon_total
    addons_str = ", ".join(addon_names) if addon_names else "None"

    # Check Loyalty Status
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT wash_count FROM loyalty WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    current_washes = row[0] if row else 0

    is_free_wash = False
    if current_washes + 1 >= 10:
        is_free_wash = True
        total_price = addon_total # Base wash is free!

    cursor.execute('''
        INSERT INTO bookings (client_name, phone, car_model, service, addons, price)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, phone, car_model, service_name, addons_str, total_price))
    conn.commit()
    conn.close()

    # Pre-filled WhatsApp notification
    my_whatsapp = "265XXXXXXXXX" 
    loyalty_msg = "\n🎉 LOYALTY ALERT: This is your 10th Wash! Base wash is FREE!" if is_free_wash else f"\nLoyalty Stamps: {current_washes + 1}/10"
    
    message = f"Hello! New Car Wash Booking:\n\nName: {name}\nPhone: {phone}\nCar: {car_model}\nPackage: {service_name}\nAdd-ons: {addons_str}\nTotal: MK {total_price:,}{loyalty_msg}"
    whatsapp_url = f"https://wa.me/{my_whatsapp}?text={message.replace(' ', '%20').replace('\n', '%0A')}"

    return redirect(whatsapp_url)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == 'POST':
        booking_id = request.form.get('id')
        action = request.form.get('action')
        phone = request.form.get('phone')

        if action in ['Washing', 'Vacuuming', 'Ready']:
            cursor.execute("UPDATE bookings SET status = ? WHERE id = ?", (action, booking_id))
        elif action == 'Completed':
            cursor.execute("UPDATE bookings SET status = 'Completed' WHERE id = ?", (booking_id,))
            
            # Increment Loyalty Count
            cursor.execute("SELECT wash_count FROM loyalty WHERE phone = ?", (phone,))
            row = cursor.fetchone()
            if row:
                new_count = 0 if row[0] >= 9 else row[0] + 1
                cursor.execute("UPDATE loyalty SET wash_count = ? WHERE phone = ?", (new_count, phone))
            else:
                cursor.execute("INSERT INTO loyalty (phone, wash_count) VALUES (?, 1)", (phone,))
                
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
