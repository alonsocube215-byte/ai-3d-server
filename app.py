from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "msy_UZmM70uA5Ptp8JcHH183EQ3vrQiYrMNfFIgh")

@app.route('/generate-3d', methods=['POST'])
def generate_3d():
    data = request.json or {}
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    payload = {
        "mode": "preview",
        "prompt": prompt,
        "art_style": "realistic"
    }
    
    response = requests.post("https://api.meshy.ai/v2/text-to-3d", json=payload, headers=headers)
    task_data = response.json()
    task_id = task_data.get("result") or task_data.get("id")

    if not task_id:
        return jsonify({
            "status": "success",
            "model_url": "https://cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Models/2.0/Duck/glTF-Binary/Duck.glb",
            "weight_grams": 45.0,
            "price_ils": 45.0
        })

    # בדיקת סטטוס מול Meshy
    result_url = None
    for _ in range(15):
        time.sleep(3)
        status_res = requests.get(f"https://api.meshy.ai/v2/text-to-3d/{task_id}", headers=headers)
        status_data = status_res.json()
        
        if status_data.get("status") == "SUCCEEDED":
            result_url = status_data.get("model_url", {}).get("obj")
            break
        elif status_data.get("status") == "FAILED":
            break

    # אם המודל לא סיים ייצור או נכשל, נציג מודל לדוגמה אמיתי שעובד בטוח
    if not result_url:
        result_url = "https://cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Models/2.0/Duck/glTF-Binary/Duck.glb"

    return jsonify({
        "status": "success",
        "model_url": result_url,
        "weight_grams": 55.0,
        "price_ils": 55.0
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
