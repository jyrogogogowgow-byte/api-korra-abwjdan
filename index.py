from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- إعدادات فيسبوك (استبدل هذه القيم ببياناتك) ---
PAGE_ACCESS_TOKEN = "EAATLbkq5LgwBSHZC7n6ZAdn22EQaeXuZCBP97g1xpUW4ZApAYaAhoi2MkB74kWaqbkabRZBb5b4OtszlgMwG6XOYTuIxhkOgkqH2kr9n7g0BnhWMZAtFLfCO0nPa9ftSEZCPZCVvSViUuZC4wTk4MDEifxr5C4qucaoEEz4AoIuTYuQbwqS883cHe2QVVVMxkBWS2NNWxfQZDZD"
VERIFY_TOKEN = "ABCD1234" 

@app.route('/webhook', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        if data.get('object') == 'page':
            for entry in data['entry']:
                for change in entry['changes']:
                    if change['field'] == 'feed' and change['value']['item'] == 'comment' and change['value']['verb'] == 'add':
                        comment_id = change['value']['comment_id']
                        if 'from' in change['value'] and change['value']['from']['id'] != entry['id']:
                            reply_to_comment(comment_id)
                            send_private_message(comment_id)
    except Exception as e:
        print(f"Error: {e}")
        
    return "EVENT_RECEIVED", 200

def reply_to_comment(comment_id):
    url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
    payload = {'message': "أهلاً بك! شكراً لتعليقك وتواصلك معنا. 🌹", 'access_token': PAGE_ACCESS_TOKEN}
    requests.post(url, data=payload)

def send_private_message(comment_id):
    url = f"https://graph.facebook.com/v19.0/{comment_id}/private_replies"
    payload = {'message': "أهلاً بك! شكراً لتعليقك، ممكن متابعة لصفحتنا ليصلك كل جديد؟ 🌸", 'access_token': PAGE_ACCESS_TOKEN}
    requests.post(url, data=payload)

# تذكر: قمنا بإزالة app.run() لأن Vercel هو من يتولى تشغيل التطبيق.
