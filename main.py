from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection
connection_string = 'mongodb+srv://shanidkattakal:Shanid%40786@cluster0.8mckznv.mongodb.net/medical_lab'

# Create a MongoClient instance using the connection string
client = MongoClient(connection_string)
db = client['medical_lab']
lab_results_collection = db['lab_results']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lab_results', methods=['GET'])
def get_lab_results():
    report_id = request.args.get('r_id')

    if report_id:
        result = lab_results_collection.find_one({'r_id': report_id})
        if result:
            lab_result = {
                'patient_name': result['patient_name'],
                'test_name': result['test_name'],
                'result': result['result']
            }
            return jsonify({'lab_result': lab_result}), 200
        else:
            return jsonify({'error': 'Report not found'}), 404
    else:
        return jsonify({'error': 'Report ID parameter is required'}), 400

if __name__ == '__main__':
    app.run(debug=True)
