from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

MESHY_API_KEY = os.environ.get("MESHY_API_KEY", "msy_UZmM70uA5Ptp8JcHH183EQ3vrQiYrMNfFIgh")

HEB_TO_ENG = {
    "חתול": "cat",
    "כלב": "dog",
    "מחזיק": "holding",
    "קובייה": "cube",
    "דרקון": "dragon",
    "מחזיק מפתחות": "keychain",
    "תגי שם": "name tag",
    "קופסה": "box",
    "כדור": "ball",
    "מגניב": "cool",
    "רובוט": "robot"
}

def smart_translate(text):
    words = text.split()
    translated_words = []
    for word in words:
        clean_word = word.strip(".,!?")
        if clean_word in HEB_TO_ENG:
            translated_words.append(HEB_TO_ENG[clean_word])
        else:
            translated_words.append(clean_word)
    
    result = " ".join(translated_words)
    return result if result.strip() else "3d model printable object"

def calculate_smart_price(prompt):
    base_weight = 30 + (len(prompt.split()) * 5)
    estimated_weight_grams = min(max(base_weight, 30), 90)
    
    material_cost = estimated_weight_grams * 0.30
    
    complexity_factor = 1.0
    complex_keywords = ['מבוך', 'פרטים', 'דרקון', 'טקסטורה', 'תמיכות', 'שרשרת', 'מובייל', 'חלקים', 'מנגנון', 'holding']
    
    for word in complex_keywords:
        if word in prompt.lower():
            complexity_factor += 0.4
            
    base_fee = 10.0
    total_price = (base_fee + material_cost) * complexity_factor
    return max(round(total_price), 25)

@app.route('/generate-3d', methods=['POST'])
def generate_model():
    data = request.json or {}
    heb_prompt = data.get('prompt', '')
    
    if not heb_prompt:
        return jsonify({"error": "No prompt provided"}), 400

    eng_prompt = smart_translate(heb_prompt)

    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    payload = {
        "mode": "preview",
        "prompt": f"A detailed 3D model of {eng_prompt}, high quality, printable 3d object",
        "art_style": "realistic"
    }
    
    response = requests.post("https://api.meshy.ai/v2/text-to-3d", json=payload, headers=headers)
    task_data = response.json()
    task_id = task_data.get("result") or task_data.get("id")

    if not task_id:
        return jsonify({"error": "לא הצלחנו להתחיל את תהליך היצירה מול Meshy"}), 500

    result_url = None
    # בדיקות מהירות כל 2 שניות (עד 12 ניסיונות = 24 שניות), כדי לא לפגוע במגבלת הזמן של Render
    for _ in range(12):
        time.sleep(2)
        status_res = requests.get(f"https://api.meshy.ai/v2/text-to-3d/{task_id}", headers=headers)
        status_data = status_res.json()
        
        status = status_data.get("status")
        if status == "SUCCEEDED":
            model_urls = status_data.get("model_url", {})
            result_url = model_urls.get("glb") or model_urls.get("gltf") or model_urls.get("obj")
            break
        elif status == "FAILED":
            return jsonify({"error": "היצירה נכשלה בשרת של Meshy"}), 500

    if not result_url:
        return jsonify({"error": "זמן ההמתנה עבר, נסה שוב"}), 500

    price = calculate_smart_price(heb_prompt)

    return jsonify({
        "status": "success",
        "model_url": result_url,
        "price_ils": price
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
