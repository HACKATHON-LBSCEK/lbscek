from flask import Flask, request, jsonify, render_template, send_from_directory
from pymongo import MongoClient
from flask import Flask, request, render_template, redirect, url_for, session
from pymongo import MongoClient
import random
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
import os

import string
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key here

# MongoDB connection
connection_string = 'mongodb+srv://shanidkattakal:Shanid%40786@cluster0.8mckznv.mongodb.net/medical_lab'

# Create a MongoClient instance using the connection string
client = MongoClient(connection_string)
db = client['medical_lab']
lab_results_collection = db['lab_results']

@app.route('/')
def index():
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
            lab_result = {
                'pdf_url': f"/pdf/{result['url']}",
                'patient_name': result['patient_name'],
                'test_name': result['test_name'],
                'status': result['status']
            }
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

@app.route('/pdf/<path:filename>')
def pdf(filename):
    return send_from_directory('pdf', filename)

if __name__ == '__main__':
    app.run(debug=True)
