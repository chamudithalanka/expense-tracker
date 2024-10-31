from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Database configuration - use environment variable
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///expenses.db')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'

db = SQLAlchemy(app)

# Expense model
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    try:
        expenses = Expense.query.all()
        return render_template('index.html', expenses=expenses)
    except Exception as e:
        return str(e), 500

@app.route('/add_expense', methods=['POST'])
def add_expense():
    try:
        description = request.form['description']
        amount = float(request.form['amount'])
        
        expense = Expense(description=description, amount=amount)
        db.session.add(expense)
        db.session.commit()
        
        return redirect(url_for('index'))
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(debug=True)
