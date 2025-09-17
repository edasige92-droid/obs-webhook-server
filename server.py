@app.route('/facebook-webhook', methods=['POST'])
def facebook_webhook():
    try:
        data = request.json
        
        # Facebook sends a verification challenge first
        if 'hub.challenge' in request.args:
            return request.args.get('hub.challenge')
        
        if data.get('object') == 'page':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'feed':
                        comment_data = change.get('value')
                        if comment_data.get('item') == 'comment':
                            # Process Facebook comment
                            facebook_comment = {
                                "user": comment_data.get('from', {}).get('name', 'Unknown'),
                                "comment": comment_data.get('message', ''),
                                "platform": "facebook",
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            with comments_lock:
                                comments.append(facebook_comment)
                                if len(comments) > 100:
                                    comments.pop(0)
                            
                            print(f"✅ Facebook comment: {facebook_comment}")
        
        return jsonify({"status": "success"}), 200
        
    except Exception as e:
        print(f"❌ Facebook webhook error: {e}")
        return jsonify({"status": "error"}), 500
