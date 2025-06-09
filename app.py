from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import csv
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Auto-create inventory.csv if not exists
def create_initial_inventory():
    if not os.path.exists('inventory.csv'):
        with open('inventory.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Medicine', 'Price', 'Stock'])
            writer.writerow(['Paracetamol', 20, 100])
            writer.writerow(['Ibuprofen', 50, 50])
            writer.writerow(['Cetirizine', 10, 200])
            writer.writerow(['Amoxicillin', 100, 75])
            writer.writerow(['Vitamin C', 30, 150])

create_initial_inventory()

# Users with roles
users = {
    'admin': {'password': 'admin123', 'role': 'admin'},
    'staff1': {'password': 'staff123', 'role': 'staff'}
}

# Helper functions for inventory
def read_inventory():
    inventory = {}
    try:
        with open('inventory.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                inventory[row['Medicine']] = {
                    'price': float(row['Price']),
                    'stock': int(row['Stock'])
                }
    except FileNotFoundError:
        pass
    return inventory

def write_inventory(inventory):
    with open('inventory.csv', 'w', newline='') as f:
        fieldnames = ['Medicine', 'Price', 'Stock']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for med, data in inventory.items():
            writer.writerow({
                'Medicine': med,
                'Price': data['price'],
                'Stock': data['stock']
            })

@app.route('/')
def home():
    if 'username' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'staff':
            return redirect(url_for('billing'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.get(username)

        if user and user['password'] == password:
            session['username'] = username
            session['role'] = user['role']
            return redirect(url_for('billing' if user['role'] == 'staff' else 'admin_dashboard'))
        else:
            msg = 'Invalid credentials'
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if session.get('role') not in ['admin', 'staff']:
        return "Access Denied"

    inventory = read_inventory()
    message = ''

    if request.method == 'POST':
        customer = request.form['customer']
        medicines = request.form.getlist('medicine')
        quantities = request.form.getlist('quantity')

        bill_no = str(int(datetime.now().timestamp()))
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total = 0
        bill_data = []

        for med, qty in zip(medicines, quantities):
            qty = int(qty)
            if med in inventory:
                if inventory[med]['stock'] >= qty:
                    cost = inventory[med]['price'] * qty
                    total += cost
                    bill_data.append([bill_no, timestamp, customer, med, qty, cost])
                    inventory[med]['stock'] -= qty
                else:
                    message = f"Not enough stock for {med}"
                    break
            else:
                message = f"{med} not found in inventory"
                break

        if not message:
            # Save bill data
            with open('bills.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                for item in bill_data:
                    writer.writerow(item)
            write_inventory(inventory)
            message = "Bill Generated Successfully!"

    return render_template('billing.html', inventory=inventory, message=message, username=session.get('username'), role=session.get('role'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Access Denied"
    return render_template('admin_dashboard.html', username=session.get('username'))

@app.route('/search_bill', methods=['GET', 'POST'])
def search_bill():
    if session.get('role') != 'admin':
        return "Access Denied"

    found_bills = []

    if request.method == 'POST':
        bill_no = request.form['bill_no']
        try:
            with open('bills.csv', 'r') as f:
                reader = csv.DictReader(f, fieldnames=['Bill No', 'Timestamp', 'Customer', 'Medicine', 'Qty', 'Cost'])
                for row in reader:
                    if row['Bill No'] == bill_no:
                        found_bills.append(row)
        except FileNotFoundError:
            pass

    return render_template('search_bill.html', found_bills=found_bills)

@app.route('/inventory', methods=['GET', 'POST'])
def inventory_editor():
    if session.get('role') != 'admin':
        return "Access Denied"

    inventory = read_inventory()
    message = ''
    if request.method == 'POST':
        med = request.form['medicine']
        try:
            price = float(request.form['price'])
            stock = int(request.form['stock'])
            inventory[med] = {'price': price, 'stock': stock}
            write_inventory(inventory)
            message = f"Inventory updated for {med}."
        except ValueError:
            message = "Invalid input."

    return render_template('inventory.html', inventory=inventory, message=message)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
