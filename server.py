import requests
import base64
import io
from PIL import Image
from flask import Flask, request, jsonify

API_KEY = "YOUR_2CAPTCHA_API_KEY"   # ← حط مفتاحك هنا

app = Flask(__name__)
session = requests.Session()


# ----------- 1) Download Captcha From Website ----------
def download_captcha(url, headers=None, cookies=None):
    r = session.get(url, headers=headers, cookies=cookies, timeout=10)
    if r.status_code != 200:
        return None
    return r.content


# ----------- 2) Upscale image to avoid errorId 15 ----------
def upscale_image_bytes(img_bytes):
    img = Image.open(io.BytesIO(img_bytes))

    # upscale ×2
    w, h = img.size
    img = img.resize((w * 2, h * 2), Image.LANCZOS)

    # export new PNG
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


# ----------- 3) Convert to Base64 ----------
def to_base64(img_bytes):
    return base64.b64encode(img_bytes).decode()


# ----------- 4) Send to 2Captcha ----------
def solve_captcha(b64):
    payload = {
        "clientKey": API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": b64,
            "math": True
        }
    }

    r = requests.post("https://api.2captcha.com/createTask", json=payload)
    task = r.json()

    if "errorId" in task and task["errorId"] != 0:
        return task

    task_id = task["taskId"]

    # Polling for result
    while True:
        check = requests.post("https://api.2captcha.com/getTaskResult", json={
            "clientKey": API_KEY,
            "taskId": task_id
        }).json()

        if check.get("status") == "ready":
            return check

        import time
        time.sleep(2)


# ----------- API Endpoint ----------
@app.route("/solve", methods=["POST"])
def solve():
    try:
        captcha_url = request.json["url"]

        # Optional headers/cookies
        headers = request.json.get("headers", {})
        cookies = request.json.get("cookies", {})

        # 1) download image
        img_bytes = download_captcha(captcha_url, headers, cookies)
        if img_bytes is None:
            return jsonify({"error": "captcha download failed"}), 400

        # 2) upscale small images (fix error 15)
        img_big = upscale_image_bytes(img_bytes)

        # 3) convert to base64
        img_b64 = to_base64(img_big)

        # 4) solve
        result = solve_captcha(img_b64)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def home():
    return "Math Captcha API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
