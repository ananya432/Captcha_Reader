from fastapi import FastAPI, UploadFile, File
import requests
import base64
import time
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=".env")

AZCAPTCHA_API_KEY = os.getenv("API_KEY")

if not AZCAPTCHA_API_KEY:
    raise RuntimeError("API_KEY not found in .env")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/solve-captcha")
async def solve_captcha(file: UploadFile = File(...)):
    image_bytes = await file.read()
    base64_image = base64.b64encode(image_bytes).decode()

    r = requests.post(
        "https://azcaptcha.com/in.php",
        data={
            "key": AZCAPTCHA_API_KEY,
            "method": "base64",
            "body": base64_image,
            "json": 1,

            "case_sensitive": 1,
            "min_len": 6,
            "max_len": 6,
            "numeric": 0
        }
    ).json()

    if r.get("status") != 1:
        return {"error": r}

    captcha_id = r["request"]

    # Step 2: poll result
    for _ in range(10):
        time.sleep(5)
        res = requests.get(
            "https://azcaptcha.com/res.php",
            params={
                "key": AZCAPTCHA_API_KEY,
                "action": "get",
                "id": captcha_id,
                "json": 1
            }
        ).json()

        if res.get("status") == 1:
            return {"captcha": res["request"]}

    return {"error": "Timeout waiting for captcha"}
