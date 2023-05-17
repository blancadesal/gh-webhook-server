import hashlib
import hmac
import os

from fastapi import Depends, FastAPI, HTTPException, Request


app = FastAPI()

async def get_payload_body(request: Request) -> bytes:
    return await request.body()

def get_signature_header(request: Request) -> str | None:
    return request.headers.get("x-hub-signature-256")

def verify_signature(payload_body: bytes = Depends(get_payload_body),
                     signature_header: str | None = Depends(get_signature_header)) -> bool:
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing!")

    secret_token = os.environ.get('GITHUB_WEBHOOK_SECRET')

    hash_object = hmac.new(secret_token.encode('utf-8'), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

    return True

@app.post("/webhook")
async def handle_webhook(request: Request, verified: bool = Depends(verify_signature)):
    payload = await request.json()

    # Print the entire payload
    print(payload['ref'])

    return {"message": "success"}
