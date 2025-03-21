from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask_mail import Mail, Message
import secrets
import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devkey123456789')

# MongoDB Configuration
app.config["MONGO_URI"] = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/user_contacts_app')
mongo = PyMongo(app)

# Email Configuration for Password Reset
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False  # Must be False when using TLS
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', 'your-email-password') # Use an App Password
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'your-email@gmail.com')
mail = Mail(app)

# Authentication middleware
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = mongo.db.users.find_one({'username': username})
        
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('contact'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('Login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        password = request.form.get('password')
        reg_number = request.form.get('reg_number')
        
        # Check if username or email already exists
        existing_user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        if existing_user:
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = {
            'username': username,
            'email': email,
            'mobile': mobile,
            'password': hashed_password,
            'reg_number': reg_number,
            'created_at': datetime.datetime.now()
        }
        
        mongo.db.users.insert_one(new_user)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form.get('email')
        user = mongo.db.users.find_one({'email': email})
        
        if user:
            # Generate password reset token
            token = secrets.token_urlsafe(32)
            expiry = datetime.datetime.now() + datetime.timedelta(hours=24)
            
            # Save token in database
            mongo.db.password_resets.insert_one({
                'email': email,
                'token': token,
                'expires_at': expiry
            })
            
            # Send email with reset link
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', 
            sender=app.config['MAIL_DEFAULT_SENDER'], 
            recipients=[email])
            msg.body = f'''To reset your password, please visit the following link:
{reset_url}

This link will expire in 24 hours.

If you did not make this request, please ignore this email.
'''
            mail.send(msg)
            
            flash('Password reset link has been sent to your email', 'success')
            return redirect(url_for('login'))
        else:
            flash('Email not found', 'error')
    
    return render_template('forgotpassword.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Check if token is valid
    reset_record = mongo.db.password_resets.find_one({
        'token': token,
        'expires_at': {'$gt': datetime.datetime.now()}
    })
    
    if not reset_record:
        flash('The password reset link is invalid or has expired', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Passwords do not match', 'error')
            return redirect(url_for('reset_password', token=token))
        
        # Update user's password
        hashed_password = generate_password_hash(password)
        mongo.db.users.update_one(
            {'email': reset_record['email']},
            {'$set': {'password': hashed_password}}
        )
        
        # Delete the reset token
        mongo.db.password_resets.delete_one({'token': token})
        
        flash('Your password has been updated! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/contact', methods=['GET'])
@login_required
def contact():
    # Show form for entering contact details
    return render_template('form.html')

@app.route('/submit_details', methods=['POST'])
@login_required
def submit_details():
    phone = request.form.get('phone')
    email = request.form.get('email')
    address = request.form.get('address')
    reg_number = request.form.get('reg_number')
    
    # Create or update contact details
    contact_details = {
        'user_id': session['user_id'],
        'phone': phone,
        'email': email,
        'address': address,
        'reg_number': reg_number,
        'updated_at': datetime.datetime.now()
    }
    
    # Check if contact already exists for this registration number
    existing_contact = mongo.db.contacts.find_one({'reg_number': reg_number})
    
    if existing_contact:
        mongo.db.contacts.update_one(
            {'reg_number': reg_number},
            {'$set': contact_details}
        )
        flash('Contact details updated successfully', 'success')
    else:
        mongo.db.contacts.insert_one(contact_details)
        flash('Contact details saved successfully', 'success')
    
    return redirect(url_for('search'))

@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    contacts = None
    
    if request.method == 'POST':
        reg_number = request.form.get('reg_number')
        contacts = mongo.db.contacts.find_one({'reg_number': reg_number})
        
        if not contacts:
            flash('No contacts found for this registration number', 'error')
    
    return render_template('search.html', contacts=contacts)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)