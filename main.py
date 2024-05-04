from flask import Flask, request, jsonify, render_template, send_from_directory
from pymongo import MongoClient
from flask import Flask, request, render_template, redirect, url_for, session
from pymongo import MongoClient
import random
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from random import randint
import string
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key here

# MongoDB connection
connection_string = 'mongodb+srv://shanidkattakal:Shanid%40786@cluster0.8mckznv.mongodb.net/medical_lab'

# Create a MongoClient instance using the connection string
client = MongoClient(connection_string)
db = client['medical_lab']
lab_results_collection = db['lab_results']

@app.route('/report')
def index1():
    return render_template('index.html')
users_collection = db['users']
labs_collection = db['labs']
reports_collection = db['reports']

# Lab login page
@app.route('/lab_login', methods=['GET', 'POST'])
def lab_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        lab = labs_collection.find_one({'username': username, 'password': password})
        if lab:
            session['lab_username'] = username
            return redirect(url_for('lab_dashboard'))
        else:
            return render_template('lab_login.html', message='Invalid username or password')
    return render_template('lab_login.html')
@app.route('/lab_dashboard')
def lab_dashboard():
    if 'lab_username' in session:
        # Fetch reports for this lab
        lab_username = session['lab_username']
        lab_reports = lab_results_collection.find({'lab_username': lab_username})
        return render_template('lab_dashboard.html', lab_reports=lab_reports)
    return redirect(url_for('lab_login'))
@app.route('/lab_results', methods=['GET'])
def get_lab_results():
    report_id = request.args.get('r_id')

    if report_id:
        result = lab_results_collection.find_one({'r_id': report_id})
        if result:
            lab_result = {}

            if 'url' in result:
                lab_result['pdf_url'] = f"/pdf/{result['url']}"

            if 'patient_name' in result:
                lab_result['patient_name'] = result['patient_name']

            if 'test_name' in result:
                lab_result['test_name'] = result['test_name']

            if 'status' in result:
                lab_result['status'] = result['status']



            return jsonify({'lab_result': lab_result}), 200
        else:
            return jsonify({'error': 'Report not found'}), 404
    else:
        return jsonify({'error': 'Report ID parameter is required'}), 400
UPLOAD_FOLDER = 'pdf'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define allowed extensions for file uploads
ALLOWED_EXTENSIONS = {'pdf'}

# Your MongoDB connection and other necessary code here...

# Route to handle PDF upload
@app.route('/upload_result/<report_id>', methods=['POST'])
def upload_result(report_id):
    if 'lab_username' in session:
        # Authenticate lab user
        lab_username = session['lab_username']
        # Check if the POST request has the file part
        if 'result' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['result']
        # If user does not select file, browser also submits an empty part without filename
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file and allowed_file(file.filename):
            # Generate a random filename and save the file to the upload folder
            import os
            import secrets
            from werkzeug.utils import secure_filename

            random_filename = secure_filename(secrets.token_hex(12)) + '.pdf'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], random_filename))
            # Update the database with the PDF URL
            lab_results_collection.update_one({'r_id': report_id}, {'$set': {'url': random_filename}})
            lab_results_collection.update_one({'r_id': report_id}, {'$set': {'status': 'completed'}})
            return redirect(url_for('lab_dashboard'))
        else:
            return jsonify({'error': 'Invalid file type'})
    else:
        return redirect(url_for('lab_login'))

# Function to check if a filename has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/images/<path:image_name>')
def serve_image(image_name):
    return send_from_directory('images', image_name)
from bson import ObjectId  # Import ObjectId for generating unique IDs

import time
import random
import string

# Function to generate a random alphanumeric string
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
@app.route('/search_reports', methods=['GET'])
def search_reports():
    search_mobile = request.args.get('mobile')
    search_name = request.args.get('name')
    search_email = request.args.get('email')

    query = {}
    if search_mobile:
        query['mobile_number'] = search_mobile
    if search_name:
        query['patient_name'] = {'$regex': f'^{search_name}', '$options': 'i'}  # Case-insensitive search
    if search_email:
        query['email'] = {'$regex': f'^{search_email}', '$options': 'i'}  # Case-insensitive search

    results = list(lab_results_collection.find(query, {'_id': 0}))
    return jsonify({'results': results})
@app.route('/add_new_report', methods=['POST'])
def add_new_report():
    if request.method == 'POST':
        data = request.json
        patient_name = data.get('patient_name')
        mobile_number = data.get('mobile_number')
        email=data.get('email')
        # Generate a unique alphanumeric report ID
        timestamp = int(time.time())  # Get current timestamp
        random_string = generate_random_string(10 - len(str(timestamp)))  # Generate random string to make total length 10
        report_id = str(timestamp) + random_string

        # Create a new report in the database with status set to 'pending'
        new_report = {
            'r_id': report_id,  # Include the unique report ID
            'patient_name': patient_name,
            'mobile_number': mobile_number,
            'status': 'pending',
            'lab_username': session.get('lab_username'),
            'email' : email# Ensure 'lab_username' exists in session
        }
        # Insert the new report into your MongoDB collection
        lab_results_collection.insert_one(new_report)

        return jsonify({'message': 'New report added successfully', 'r_id': report_id}), 200
    else:
        return jsonify({'error': 'Method not allowed'}), 405

@app.route('/pdf/<path:filename>')
def pdf(filename):
    return send_from_directory('pdf', filename)



otp_storage = {}

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    phone = request.form['phone']

    # Check if email and phone exist in the reports collection
    user_report = lab_results_collection.find_one({"email": email, "mobile_number": phone})

    if user_report:
        # Generate OTP and store it (replace this with a more secure method)
        otp = randint(100000, 999999)
        otp_storage[email] = otp

        # Send OTP to the user via email (you need to implement this)

        # Redirect to email OTP page
        return redirect(url_for('verify_otp', email=email))
    else:
        # User not found, redirect back to login page
        return jsonify({'results': "eror"})


@app.route('/verify_otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        otp = int(request.form['otp'])

        # Verify OTP
        stored_otp = otp_storage.get(email)
        if stored_otp and otp == stored_otp:
            # Successful OTP verification, redirect to dashboard
            return redirect(url_for('dashboard'))
        else:
            # Invalid OTP, redirect back to email OTP page
            return redirect(url_for('verify_otp', email=email))
    else:
        # Render email OTP verification page
        return render_template('verify_otp.html', email=email)

@app.route('/dashboard')
def dashboard():
    # Render dashboard template or perform any other action for authenticated users
    return "Welcome to the patient dashboard!"

if __name__ == '__main__':
    app.run(debug=True)
