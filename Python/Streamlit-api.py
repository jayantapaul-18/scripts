from flask import Flask, request, jsonify
import streamlit as st

app = Flask(__name__)

def streamlit_app():
    # Your Streamlit app logic here
    st.title("My Streamlit App")
    # ...

@app.route('/')
def index():
    # Serve Streamlit app
    return streamlit.cli.main(['run', 'your_streamlit_app.py'])

@app.route('/api/data', methods=['GET'])
def get_data():
    # Your API logic here
    return jsonify({'data': 'some data'})

if __name__ == '__main__':
    app.run(port=8501)
