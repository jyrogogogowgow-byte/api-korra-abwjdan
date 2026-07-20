import os
import requests
from fastapi import FastAPI, Request, Response, HTTPException
from mangum import Mangum

app = FastAPI()

# الإعدادات السرية (من الأحسن تحطهم فـ Environment Variables فـ Vercel)

PAGE_ACCESS_TOKEN = "EAATLbkq5LgwBSHZC7n6ZAdn22EQaeXuZCBP97g1xpUW4ZApAYaAhoi2MkB74kWaqbkabRZBb5b4OtszlgMwG6XOYTuIxhkOgkqH2kr9n7g0BnhWMZAtFLfCO0nPa9ftSEZCPZCVvSViUuZC4wTk4MDEifxr5C4qucaoEEz4AoIuTYuQbwqS883cHe2QVVVMxkBWS2NNWxfQZDZD"
VERIFY_TOKEN = "ABCD1234" 

# دالة لجلب الآية من API القرآن
def get_ayah_from_api(surah, ayah):
    url = f"https://api.alquran.cloud/v1/ayah/{surah}:{ayah}/ar.muyassar"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        if data.get("code") == 200:
            text = data["data"]["text"]
            surah_name = data["data"]["surah"]["name"]
            return f"﴿ {text} ﴾\n\nالقدس/السورة: {surah_name}\nالآية: {ayah}"
    except Exception:
        pass
    return "عذراً، لم أجد هذه الآية. تأكد من كتابة رقم السورة والآية بشكل صحيح (مثال: 2:255)."

# دالة لإرسال الرسالة للمستخدم عبر Messenger API
def send_messenger_message(recipient_id, text_message):
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text_message}
    }
    requests.post(url, json=payload, timeout=5)

# 1. الـ Endpoint الخاص بالتحقق (Verification) - كيحتاجو الفيسبوك المرة الأولى فقط
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Invalid verification token", status_code=403)

# 2. الـ Endpoint اللي كيستقبل الرسائل الحقيقية من المستخدمين
@app.post("/webhook")
async def handle_messages(request: Request):
    body = await request.json()
    
    # التأكد من أن الحدث جاي من صفحة فيسبوك
    if body.get("object") == "page":
        for entry in body.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                # إذا كانت الرسالة نصية
                if messaging_event.get("message") and messaging_event["message"].get("text"):
                    sender_id = messaging_event["sender"]["id"]
                    user_text = messaging_event["message"]["text"].strip()
                    
                    # طريقة التفاعل: المستخدم يصيفط مثلا "2:255"
                    if ":" in user_text:
                        try:
                            surah, ayah = user_text.split(":")
                            reply = get_ayah_from_api(surah, ayah)
                        except Exception:
                            reply = "يرجى إرسال رقم السورة والآية بهذا الشكل -> 2:255"
                    else:
                        reply = "مرحباً بك في البوت الإسلامي! 🌙\nللحصول على آية مع تفسيرها، أرسل رقم السورة ورقم الآية مفصولين بنقطتين.\nمثال: 2:255 (سورة البقرة، آية الكرسي)."
                    
                    # إرسال الجواب للمستخدم
                    send_messenger_message(sender_id, reply)
                    
        return {"status": "EVENT_RECEIVED"}
    raise HTTPException(status_code=404)

# ربط FastAPI مع Vercel
handler = Mangum(app)
