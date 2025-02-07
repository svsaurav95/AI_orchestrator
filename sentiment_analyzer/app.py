# sentiment_analyzer/app.py
from flask import Flask, request, jsonify
from textblob import TextBlob

app = Flask(__name__)

@app.route('/process', methods=['POST'])
def analyze_sentiment():
    text = request.json['data']
    analysis = TextBlob(text)
    return jsonify({
        'result': analysis.sentiment.polarity,
        'message': 'Sentiment analyzed successfully'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
