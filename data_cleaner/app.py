# data_cleaner/app.py
from flask import Flask, request, jsonify
import pandas as pd
from io import StringIO

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def clean_data():
    data = request.json['data']
    df = pd.read_csv(StringIO(data))
    
    # Simple cleaning operations
    df = df.dropna()
    df = df.drop_duplicates()
    
    return jsonify({
        'result': df.to_csv(index=False),
        'message': 'Data cleaned successfully'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
