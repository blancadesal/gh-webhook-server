import hashlib
import hmac
import json
import logging
import os
import subprocess

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    filename="webhook_server.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

app = FastAPI()

with open("app_config.json") as config_file:
    APP_CONFIG = json.load(config_file)


async def get_payload_body(request: Request) -> bytes:
    return await request.body()


def get_signature_header(request: Request) -> str | None:
    return request.headers.get("x-hub-signature-256")


def verify_signature(
    app_name: str,
    payload_body: bytes = Depends(get_payload_body),
    signature_header: str | None = Depends(get_signature_header),
) -> bool:
    if not signature_header:
        raise HTTPException(
            status_code=403, detail="x-hub-signature-256 header is missing"
        )

    if app_name not in APP_CONFIG:
        raise HTTPException(status_code=404, detail=f"App {app_name} not configured")

    secret_env_var = f"GITHUB_WEBHOOK_SECRET_{app_name.upper()}"
    secret_token = os.environ.get(secret_env_var)

    if not secret_token:
        raise HTTPException(
            status_code=500, detail=f"Secret for {app_name} not configured"
        )

    hash_object = hmac.new(
        secret_token.encode("utf-8"), msg=payload_body, digestmod=hashlib.sha256
    )
    expected_signature = "sha256=" + hash_object.hexdigest()

    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match")

    return True


@app.get("/healthz")
async def healthz():
    return JSONResponse(content={"status": "ok"})


@app.post("/github/webhook/{app_name}")
async def handle_webhook(
    app_name: str, request: Request, verified: bool = Depends(verify_signature)
):
    if app_name not in APP_CONFIG:
        return JSONResponse(
            status_code=404,
            content={"status": "error", "detail": f"App {app_name} not configured"},
        )

    payload = await request.json()
    ref = payload.get("ref", "")
    logging.info(f"Received webhook for {app_name} with ref {ref}")

    if ref == "refs/heads/main":
        deploy_script = APP_CONFIG[app_name]
        if not os.path.exists(deploy_script):
            error_msg = f"Deploy script for {app_name} not found"
            logging.error(error_msg)
            return JSONResponse(
                status_code=500, content={"status": "error", "detail": error_msg}
            )

        process = subprocess.Popen(
            ["bash", deploy_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_msg = f"Deployment failed for {app_name}: {stderr.decode('utf-8')}"
            logging.error(error_msg)
            return JSONResponse(
                status_code=500, content={"status": "error", "detail": error_msg}
            )

        success_msg = f"{app_name} deployed successfully"
        logging.info(success_msg)
        return JSONResponse(content={"status": "success", "message": success_msg})
    else:
        logging.info(f"Push was to {ref}, not deploying {app_name}")

    return JSONResponse(
        content={"status": "info", "message": "Webhook received, but no action taken"}
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code, content={"status": "error", "detail": exc.detail}
    )
