# Import necessary modules
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, send_from_directory
from pymongo import MongoClient
import random
import string
from werkzeug.utils import secure_filename
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Initialize Flask app and set secret key
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MongoDB connection
connection_string = 'mongodb+srv://shanidkattakal:Shanid%40786@cluster0.8mckznv.mongodb.net/medical_lab'
client = MongoClient(connection_string)
db = client['medical_lab']
lab_results_collection = db['lab_results']
labs_collection = db['labs']
consultations_collection = db['consultations']

# Define upload folder and allowed file extensions
UPLOAD_FOLDER = 'pdf'
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to send OTP email
def send_otp_email(email, otp):
    sender_email = 'shanidsulthan@gmail.com'
    sender_password = 'pvhtbatctnnuktke'
    subject = 'Your OTP for Patient Login'
    message = f'Your OTP is: {otp}'

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, email, msg.as_string())

# Function to generate a random alphanumeric string
def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Route for lab login
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

# Route for lab dashboard
@app.route('/lab_dashboard')
def lab_dashboard():
    if 'lab_username' in session:
        lab_username = session['lab_username']
        lab_reports = lab_results_collection.find({'lab_username': lab_username})
        return render_template('lab_dashboard.html', lab_reports=lab_reports)
    return redirect(url_for('lab_login'))

# Route for uploading result
@app.route('/upload_result/<report_id>', methods=['POST'])
def upload_result(report_id):
    if 'lab_username' in session:
        lab_username = session['lab_username']
        if 'result' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['result']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
            random_filename = secure_filename(os.path.splitext(file.filename)[0]) + '-' + generate_random_string(6) + '.pdf'
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], random_filename))
            lab_results_collection.update_one({'r_id': report_id}, {'$set': {'url': random_filename}})
            lab_results_collection.update_one({'r_id': report_id}, {'$set': {'status': 'completed'}})
            return redirect(url_for('lab_dashboard'))
        else:
            return jsonify({'error': 'Invalid file type'})
    else:
        return redirect(url_for('lab_login'))

# Route for searching reports
@app.route('/search_reports', methods=['GET'])
def search_reports():
    search_mobile = request.args.get('mobile')
    search_name = request.args.get('name')
    search_email = request.args.get('email')

    query = {}
    if search_mobile:
        query['mobile_number'] = search_mobile
    if search_name:
        query['patient_name'] = {'$regex': f'^{search_name}', '$options': 'i'}
    if search_email:
        query['email'] = {'$regex': f'^{search_email}', '$options': 'i'}

    results = list(lab_results_collection.find(query, {'_id': 0}))
    return jsonify({'results': results})

# Route for adding a new report
@app.route('/add_new_report', methods=['POST'])
def add_new_report():
    if request.method == 'POST':
        data = request.json
        patient_name = data.get('patient_name')
        mobile_number = data.get('mobile_number')
        email = data.get('email')
        timestamp = int(time.time())
        random_string = generate_random_string(10 - len(str(timestamp)))
        report_id = str(timestamp) + random_string

        new_report = {
            'r_id': report_id,
            'patient_name': patient_name,
            'mobile_number': mobile_number,
            'status': 'pending',
            'lab_username': session.get('lab_username'),
            'email': email
        }
        lab_results_collection.insert_one(new_report)
        return jsonify({'message': 'New report added successfully', 'r_id': report_id}), 200
    else:
        return jsonify({'error': 'Method not allowed'}), 405

# Route for patient login
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    phone = request.form['phone']
    user_report = lab_results_collection.find_one({"email": email, "mobile_number": phone})

    if user_report:
        otp = randint(100000, 999999)
        otp_storage[email] = otp
        session['email'] = email
        session['phone'] = phone
        session['otp'] = otp
        send_otp_email(email, otp)
        return redirect(url_for('verify_otp', email=email))
    else:
        return jsonify({'results': "error"})

# Route for verifying OTP
@app.route('/verify_otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        otp = int(request.form['otp'])
        stored_otp = otp_storage.get(email)
        if stored_otp and otp == stored_otp:
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('verify_otp', email=email))
    else:
        return render_template('verify_otp.html', email=email)

# Route for patient dashboard
@app.route('/dashboard')
def dashboard():
    if 'email' in session and 'phone' in session:
        email = session['email']
        phone = session['phone']
        user_reports = lab_results_collection.find({"email": email, "mobile_number": phone})
        return render_template('dashboard.html', reports=user_reports)
    else:
        return redirect('/login')

# Route for sending consultation
@app.route('/send_consultation', methods=['POST'])
def send_consultation():
    report_id = request.form['report_id']
    selected_doctor = request.form['doctor']
    consultation = {
        'report_id': report_id,
        'doctor': selected_doctor,
        'status': 'pending',
        'timestamp': datetime.now()
    }
    consultations_collection.insert_one(consultation)

    return redirect(url_for('dashboard'))
@app.route('/doctor_login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Assuming you have a 'doctors' collection
        doctor = db.doctors.find_one({'username': username, 'password': password})
        if doctor:
            session['doctor_username'] = username
            return redirect(url_for('doctor_dashboard'))
        else:
            return render_template('doctor_login.html', message='Invalid username or password')
    return render_template('doctor_login.html')

# Route for doctor dashboard
@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'doctor_username' in session:
        username = session['doctor_username']
        # Fetch consultations for this doctor
        consultations = consultations_collection.find({'doctor': username})
        return render_template('doctor_dashboard.html', consultations=consultations)
    return redirect(url_for('doctor_login'))

# Route for uploading PDF and adding remarks
@app.route('/add_remarks/<consultation_id>', methods=['POST'])
def add_remarks(consultation_id):
    if 'doctor_username' in session:
        username = session['doctor_username']
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Update consultation record with PDF URL and remarks
                consultations_collection.update_one(
                    {'r_id': consultation_id},
                    {'$set': {'pdf_url': filename, 'remarks': request.form['remarks']}}
                )
                return redirect(url_for('doctor_dashboard'))
    return redirect(url_for('doctor_login'))

# Function to check if a filename has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Main function to run the app
if __name__ == '__main__':
    app.run(debug=True)
