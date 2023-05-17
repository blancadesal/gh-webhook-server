from fastapi import FastAPI, Depends, HTTPException, Request
from hmac import compare_digest, new
from hashlib import sha1
import os

app = FastAPI()

# This is your secret token, which you'll also set in GitHub when configuring the webhook
SECRET_TOKEN = os.environ.get('GITHUB_WEBHOOK_SECRET')

def verify_signature(request: Request, body: bytes, signature: str | None):
    if signature is None:
        raise HTTPException(status_code=400, detail='Missing X-Hub-Signature header')

    expected_signature = new(SECRET_TOKEN.encode(), body, sha1).hexdigest()
    if not compare_digest(f'sha1={expected_signature}', signature):
        raise HTTPException(status_code=400, detail='Invalid signature')

    return True

@app.post("/webhook/")
async def handle_webhook(request: Request, verified: bool = Depends(verify_signature)):
    payload = await request.json()

    # deployment logic ...

    print(payload)

    return {"message": "success"}