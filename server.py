from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Store comments in memory (for demo purposes)
comments = []

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        print(f"Received comment: {data}")
        
        # Store the comment
        if data:
            comments.append(data)
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/comments', methods=['GET'])
def get_comments():
    return jsonify(comments)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
