from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import trimesh
import io
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
    
    response = requests.post("https://api.meshy.ai/v2/text-to-3d", json=payload, headers=headers)
    task_data = response.json()
    result_url = task_data.get("result_url")

    if not result_url:
        return jsonify({"error": "Failed to generate model from Meshy", "details": task_data}), 500

    file_res = requests.get(result_url)
    mesh = trimesh.load(io.BytesIO(file_res.content), file_type='obj')
    
    volume_cm3 = mesh.volume / 1000  
    weight_grams = volume_cm3 * 1.24 * 0.25  
    
    base_price = 25.0
    price_calc = base_price + (weight_grams * 0.6)
    final_price = round(max(price_calc, 39.0), 2)

    return jsonify({
        "status": "success",
        "model_url": result_url,
        "volume_cm3": round(volume_cm3, 2),
        "weight_grams": round(weight_grams, 2),
        "price_ils": final_price
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
