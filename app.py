from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)
CORS(app)

MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "msy_UZmM70uA5Ptp8JcHH183EQ3vrQiYrMNfFIgh")

@app.route('/generate-3d', methods=['POST'])
def generate_3d():
    data = request.json
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    payload = {
        "mode": "preview",
        "prompt": prompt,
        "art_style": "realistic"
    }
    
    # שלב 1: שליחת הבקשה ליצירת מודל
    response = requests.post("https://api.meshy.ai/v2/text-to-3d", json=payload, headers=headers)
    task_data = response.json()
    task_id = task_data.get("result") or task_data.get("id")

    if not task_id:
        return jsonify({"error": "Failed to start Meshy task", "details": task_data}), 500

    # שלב 2: המתנה לסיום עיבוד המודל ב-Meshy
    result_url = None
    for _ in range(30):  # מנסה במשך דקה וחצי
        time.sleep(3)
        status_res = requests.get(f"https://api.meshy.ai/v2/text-to-3d/{task_id}", headers=headers)
        status_data = status_res.json()
        
        status = status_data.get("status")
        if status == "SUCCEEDED":
            result_url = status_data.get("model_url", {}).get("obj")
            break
        elif status == "FAILED":
            return jsonify({"error": "Meshy generation failed", "details": status_data}), 500

    if not result_url:
        return jsonify({"error": "Timeout waiting for model generation"}), 500

    # חישוב משקל ומחיר פיקטיבי/בסיסי כדי לא לתקוע את השרת
    weight_grams = 45.0  
    final_price = 45.0

    return jsonify({
        "status": "success",
        "model_url": result_url,
        "weight_grams": weight_grams,
        "price_ils": final_price
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
