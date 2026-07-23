from flask import Flask, request
import requests
import os

app = Flask(__name__)

# هادو غادي تزيدهم فـ Environment Variables فـ Vercel
PAGE_ACCESS_TOKEN = "EAATLbkq5LgwBSOlWlZBcXEJKzncXB8G0BLnGUTinJdshh6iAL7Vphpu1hHvnZAKQbRdSZCjyaZBT1rAN2Q2SfZAD3yrGVHE21TGPIqu887JqKpDGv0z3uJ4MizZBWa4BE343v2GZC5V0fZAl53uvgUjPEy1fuc1p9pk47u1eAYjntw24C3wUogJZAfSfQN3WGpxPtpveIqwZDZD"
VERIFY_TOKEN = "ABCD1234" 


# مسار باش فيسبوك يدير Verify للـ Webhook
@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Bot is running on Vercel!", 200

# مسار باش نستقبلو الرسائل من عند المستعملين
@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    print("💌 وصلاتني هاد الداتا من فيسبوك: ", data) # هاد السطر غادي يوريك فـ Vercel واش الرسالة وصلات
    
    if data.get('object') == 'page':
        # ... كمل الكود ديالك بحال لي قبل ...
        for entry in data['entry']:
            for messaging_event in entry.get('messaging', []):
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    
                    # قلب واش المستعمل كليكا على شي زر (Quick Reply)
                    quick_reply = messaging_event['message'].get('quick_reply')
                    
                    if quick_reply:
                        payload = quick_reply.get('payload')
                        if payload == 'CORRECT':
                            send_message(sender_id, "جواب صحيح! برافو 👏")
                            # ممكن تزيد كود هنا باش تصيفط السؤال لي موراه
                        elif payload == 'WRONG':
                            send_message(sender_id, "جواب غالط! حاول مرة أخرى ❌")
                    else:
                        # يلا كتب أي حاجة، نصيفطو ليه السؤال
                        send_question(sender_id)
    return "ok", 200

def send_question(recipient_id):
    # إعداد السؤال والأزرار (Quick Replies)
    message_data = {
        "recipient": {"id": recipient_id},
        "message": {
            "text": "شنو هي عاصمة المغرب؟",
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "الدار البيضاء",
                    "payload": "WRONG"
                },
                {
                    "content_type": "text",
                    "title": "الرباط",
                    "payload": "CORRECT" # هادا هو الجواب الصحيح
                },
                {
                    "content_type": "text",
                    "title": "مراكش",
                    "payload": "WRONG"
                }
            ]
        }
    }
    call_send_api(message_data)

def send_message(recipient_id, text):
    message_data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    call_send_api(message_data)

def call_send_api(message_data):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=message_data, headers=headers)
    
    # هاد السطر غادي يبين لينا واش فيسبوك قبل الرسالة ولا رفضها وعلاش
    print("رد فيسبوك:", response.status_code, response.text)
