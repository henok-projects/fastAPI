from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from typing import Optional
from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

ODOO_API_KEY = os.getenv('ODOO_API_KEY')
ODOO_API_URL = os.getenv('ODOO_API_URL')

app = FastAPI()

# Define the message schema
class Message(BaseModel):
    channel: str  # 'WhatsApp', 'Twitter', 'Telegram'
    company_id: str
    sender: str
    recipient: str
    content: str
    timestamp: str
    delivered: bool = False  
    read: bool = False  
class Message(BaseModel):
    to: str  # The recipient's phone number including the country code
    body: str  # The message body

# Twilio credentials (replace with your actual credentials)
account_sid = 'your_account_sid'
auth_token = 'your_auth_token'
from_whatsapp_number='whatsapp:your_twilio_whatsapp_number'  # Your Twilio WhatsApp number in the format 'whatsapp:+1234567890'
messages = []
client = Client(account_sid, auth_token)

@app.post("/api/write_messages")
async def receive_message_from_extension(message: Message):
    # Simulate saving to a database
    stored_message = message.dict()
    messages.append(stored_message)
    # Forward the message to Odoo if needed
    odoo_response = await send_to_odoo(stored_message)
    return {"status": "success", "message_id": len(messages) - 1, "odoo_response": odoo_response}

@app.get("/api/read_messages")
async def read_messages(company_id: str):
    # Fetch messages that haven't been delivered yet
    new_messages = [msg for msg in messages if msg['company_id'] == company_id and not msg['delivered']]
    for msg in new_messages:
        msg['delivered'] = True  # Update the status as delivered
    return {"new_messages": new_messages}

# Utility function for sending to Odoo
async def send_to_odoo(message: dict):
    headers = {"Authorization": f"Bearer {ODOO_API_KEY}"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(ODOO_API_URL, json=message, headers=headers)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error sending message to Odoo: {str(e)}")
    

@app.post("/send-message/")
async def send_message(message: Message):
    try:
        message = client.messages.create(
            body=message.body,
            from_=from_whatsapp_number,
            to=f'whatsapp:{message.to}'
        )
        return {"message": "Sent", "sid": message.sid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
