import flask
from flask import request, jsonify
import json
import os

app = flask.Flask(__name__)

# File path for JSON data
data_file = 'data.json'

# Load initial data if file exists
try:
    with open(data_file, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

@app.route('/data', methods=['GET'])
def get_data():
    return jsonify(data)

@app.route('/data', methods=['POST'])
def update_data():
    new_data = request.get_json()
    data.update(new_data)
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=4)
    return jsonify({'message': 'Data updated successfully'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
