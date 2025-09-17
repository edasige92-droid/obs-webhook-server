from flask import Flask, request, jsonify, render_template_string
from datetime import datetime
import threading

app = Flask(__name__)

# Store comments in memory (with timestamps)
comments = []
comments_lock = threading.Lock()

# HTML template for the root page
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>OBS Webhook Server</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { background: #007bff; color: white; padding: 20px; border-radius: 5px; }
        .endpoints { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .comment { border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { color: #28a745; }
        .error { color: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎥 OBS Webhook Server</h1>
        <p>Server is running and ready to receive comments!</p>
    </div>
    
    <div class="endpoints">
        <h2>📋 Available Endpoints:</h2>
        <p><strong>POST</strong> <code>/webhook</code> - Receive OBS comments (JSON)</p>
        <p><strong>GET</strong> <code>/comments</code> - View all received comments</p>
        <p><strong>GET</strong> <code>/health</code> - Check server status</p>
        <p><strong>POST</strong> <code>/clear</code> - Clear all comments</p>
    </div>

    <div>
        <h2>🚀 Quick Test:</h2>
        <form action="/test-webhook" method="POST">
            <input type="text" name="test_comment" placeholder="Enter test comment" required>
            <input type="text" name="test_user" placeholder="Your name" value="TestUser">
            <button type="submit">Send Test Comment</button>
        </form>
    </div>

    <div>
        <h2>📊 Stats:</h2>
        <p>Total comments received: <strong>{{ total_comments }}</strong></p>
        <p>Server status: <span class="success">🟢 Running</span></p>
        <p>Server time: {{ current_time }}</p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Root endpoint with server information"""
    return render_template_string(HTML_TEMPLATE, 
                                total_comments=len(comments),
                                current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/webhook', methods=['POST'])
def webhook():
    """Main webhook endpoint for OBS comments"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400
        
        # Add timestamp and ensure required fields
        comment_data = {
            "user": data.get("user", "Anonymous"),
            "comment": data.get("comment", ""),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": data.get("type", "comment")
        }
        
        # Thread-safe comment storage
        with comments_lock:
            comments.append(comment_data)
            # Keep only last 100 comments to prevent memory issues
            if len(comments) > 100:
                comments.pop(0)
        
        print(f"✅ Received comment: {comment_data}")
        return jsonify({
            "status": "success", 
            "message": "Comment received",
            "comment": comment_data
        }), 200
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/comments', methods=['GET'])
def get_comments():
    """Get all stored comments"""
    with comments_lock:
        return jsonify({
            "total_comments": len(comments),
            "comments": comments
        })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "comments_count": len(comments)
    })

@app.route('/clear', methods=['POST'])
def clear_comments():
    """Clear all comments"""
    with comments_lock:
        comments.clear()
    return jsonify({"status": "success", "message": "All comments cleared"})

@app.route('/test-webhook', methods=['POST'])
def test_webhook():
    """Test endpoint to simulate OBS webhook"""
    test_data = {
        "user": request.form.get("test_user", "TestUser"),
        "comment": request.form.get("test_comment", "Test comment"),
        "type": "test"
    }
    
    with comments_lock:
        test_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        comments.append(test_data)
        if len(comments) > 100:
            comments.pop(0)
    
    print(f"✅ Test comment received: {test_data}")
    return f"""
    <div style="background: #d4edda; padding: 20px; border-radius: 5px;">
        <h3 style="color: #155724;">✅ Test Successful!</h3>
        <p><strong>User:</strong> {test_data['user']}</p>
        <p><strong>Comment:</strong> {test_data['comment']}</p>
        <p><strong>Time:</strong> {test_data['timestamp']}</p>
        <p><a href="/comments">View all comments</a> | <a href="/">Back to home</a></p>
    </div>
    """

if __name__ == '__main__':
    print("🚀 Starting OBS Webhook Server...")
    print("📍 Endpoints:")
    print("   - GET  /          - Server info")
    print("   - POST /webhook   - Receive OBS comments")
    print("   - GET  /comments  - View all comments")
    print("   - GET  /health    - Health check")
    print("   - POST /clear     - Clear comments")
    print("   - POST /test-webhook - Test endpoint")
    print("")
    print("📝 Ready to receive webhooks from OBS Studio!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
