from flask import Flask, request, jsonify
import base64
import time
import requests

app = Flask(__name__)

API_KEY = "3fb1bd23d20f532f4f2e8b6e043af1d2"
CREATE_URL = "https://api.2captcha.com/createTask"
GET_URL = "https://api.2captcha.com/getTaskResult"


def solve_math_captcha(img_b64: str):
    payload = {
        "clientKey": API_KEY,
        "task": {
            "type": "ImageToTextTask",
            "body": img_b64,
            "math": True
        }
    }

    r = requests.post(CREATE_URL, json=payload)
    data = r.json()

    if data.get("errorId") != 0:
        return {"error": data}

    task_id = data["taskId"]

    while True:
        res = requests.post(GET_URL, json={"clientKey": API_KEY, "taskId": task_id})
        result = res.json()

        if result.get("status") == "ready":
            return {"solution": result["solution"]["text"]}

        elif result.get("status") == "processing":
            time.sleep(2)
        else:
            return {"error": result}


@app.route("/solve", methods=["POST"])
def solve():
    if request.json and "base64" in request.json:
        img_b64 = request.json["base64"]
    else:
        return jsonify({"error": "Base64 required"}), 400

    result = solve_math_captcha(img_b64)
    return jsonify(result)


@app.route("/")
def home():
    return "Math Captcha Solver API Running"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
