from flask import Flask, render_template, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['medical_lab']
lab_results_collection = db['lab_results']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lab_results')
def get_lab_results():
    results = lab_results_collection.find()
    lab_results = []
    for result in results:
        lab_results.append({
            'patient_name': result['patient_name'],
            'test_name': result['test_name'],
            'result': result['result']
        })
    return jsonify({'lab_results': lab_results})

if __name__ == '__main__':
    app.run(debug=True)
