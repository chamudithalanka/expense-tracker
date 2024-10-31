from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
import json
from datetime import timedelta
import time
import io
import csv

app = Flask(__name__)
app.secret_key = 'your-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expense_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Add your API key here
API_KEY = '8ba242f13e21b5433ed298da'

# Cache for exchange rates
exchange_rates_cache = {
    'rates': None,
    'last_update': None
}

def get_exchange_rates():
    current_time = time.time()
    
    # Check if we need to update the cache (every 12 hours)
    if (exchange_rates_cache['rates'] is None or 
        exchange_rates_cache['last_update'] is None or 
        current_time - exchange_rates_cache['last_update'] > 43200):
        
        try:
            url = f'https://v6.exchangerate-api.com/v6/{API_KEY}/latest/RON'
            response = requests.get(url)
            data = response.json()
            
            if response.status_code == 200:
                exchange_rates_cache['rates'] = data['conversion_rates']
                exchange_rates_cache['last_update'] = current_time
                return exchange_rates_cache['rates']
            else:
                print(f"API Error: {data.get('error', 'Unknown error')}")
                return get_fallback_rates()
        except Exception as e:
            print(f"Error fetching exchange rates: {e}")
            return get_fallback_rates()
    
    return exchange_rates_cache['rates']

def get_fallback_rates():
    # Fallback rates in case API fails
    return {
        'USD': 0.22,
        'EUR': 0.20,
        'RON': 1.00,
        'LKR': 69.50
    }

# Database models remain the same
class Salary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

def get_user_expenses(user_id, month):
    start_date = datetime.strptime(month, '%Y-%m')
    end_date = start_date + timedelta(days=32)
    end_date = end_date.replace(day=1)
    
    return Expense.query.filter(
        Expense.date >= start_date,
        Expense.date < end_date
    ).all()

@app.route('/')
def index():
    current_currency = session.get('currency', 'RON')
    rates = get_exchange_rates()
    rate = rates.get(current_currency, 1.0)

    salary = Salary.query.order_by(Salary.date.desc()).first()
    expenses = Expense.query.all()
    total_expenses = sum(expense.price for expense in expenses)

    converted_salary = 0
    if salary:
        converted_salary = salary.amount * rate
        
    converted_expenses = total_expenses * rate
    converted_remaining = (salary.amount - total_expenses) * rate if salary else 0

    # Get all available currencies for the dropdown
    available_currencies = sorted(rates.keys())

    return render_template('index.html',
                         salary=converted_salary,
                         expenses=expenses,
                         total_expenses=converted_expenses,
                         remaining_balance=converted_remaining,
                         current_currency=current_currency,
                         conversion_rate=rate,
                         available_currencies=available_currencies)

@app.route('/set_currency/<currency>')
def set_currency(currency):
    if currency in get_exchange_rates():
        session['currency'] = currency
    return redirect(url_for('index'))

@app.route('/add_salary', methods=['POST'])
def add_salary():
    try:
        amount = float(request.form['salary'])
        new_salary = Salary(amount=amount)
        db.session.add(new_salary)
        db.session.commit()
    except Exception as e:
        print(f"Error adding salary: {e}")
    return redirect(url_for('index'))

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        item_name = request.form['item_name']
        price = float(request.form['price'])
        new_expense = Expense(item_name=item_name, price=price)
        db.session.add(new_expense)
        db.session.commit()
    except Exception as e:
        print(f"Error adding expense: {e}")
    return redirect(url_for('index'))

@app.route('/delete_expense/<int:id>')
def delete_expense(id):
    try:
        expense = Expense.query.get_or_404(id)
        db.session.delete(expense)
        db.session.commit()
    except Exception as e:
        print(f"Error deleting expense: {e}")
    return redirect(url_for('index'))

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/download_report')
def download_report():
    try:
        # Get current currency
        current_currency = session.get('currency', 'RON')
        rates = get_exchange_rates()
        rate = rates.get(current_currency, 1.0)

        # Get data
        salary = Salary.query.order_by(Salary.date.desc()).first()
        expenses = Expense.query.all()
        total_expenses = sum(expense.price for expense in expenses)
        remaining = (salary.amount - total_expenses) if salary else 0

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Expense Report'])
        writer.writerow([f'Currency: {current_currency}'])
        writer.writerow([])
        
        # Write salary info
        writer.writerow(['Salary Information'])
        writer.writerow(['Amount', f'{current_currency} {salary.amount * rate:.2f}' if salary else '0'])
        writer.writerow([])
        
        # Write expense details
        writer.writerow(['Expense Details'])
        writer.writerow(['Item', 'Price', 'Date'])
        for expense in expenses:
            writer.writerow([
                expense.item_name,
                f'{current_currency} {expense.price * rate:.2f}',
                expense.date.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Write summary
        writer.writerow([])
        writer.writerow(['Summary'])
        writer.writerow(['Total Expenses', f'{current_currency} {total_expenses * rate:.2f}'])
        writer.writerow(['Remaining Balance', f'{current_currency} {remaining * rate:.2f}'])

        # Prepare the output
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'expense_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )

    except Exception as e:
        print(f"Error generating report: {e}")
        return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)