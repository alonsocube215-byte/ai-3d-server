from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "msy_UZmM70uA5Ptp8JcHH183EQ3vrQiYrMNfFIgh")

def calculate_smart_price(prompt, estimated_weight_grams=45):
    material_cost = estimated_weight_grams * 0.30
    
    complexity_factor = 1.0
    complex_keywords = ['מבוך', 'פרטים', 'דרקון', 'טקסטורה', 'תמיכות', 'שרשרת', 'מובייל', 'חלקים', 'מנגנון']
    
    for word in complex_keywords:
        if word in prompt.lower():
            complexity_factor += 0.3
            
    base_fee = 12.0
    total_price = (base_fee + material_cost) * complexity_factor
    return max(round(total_price), 25)

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
        price = calculate_smart_price(prompt, 40)
        return jsonify({
            "status": "success",
            "model_url": "https://cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Models/2.0/Duck/glTF-Binary/Duck.glb",
            "price_ils": price
        })

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

    if not result_url:
        result_url = "https://cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Models/2.0/Duck/glTF-Binary/Duck.glb"

    price = calculate_smart_price(prompt, 50)

    return jsonify({
        "status": "success",
        "model_url": result_url,
        "price_ils": price
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
