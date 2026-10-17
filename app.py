from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
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
    # מחיר דינמי אמיתי שמשתנה לפי אורך הפרומפט והמילים בו
    words_count = len(prompt.split())
    base_price = 20 + (words_count * 4)
    
    if any(k in prompt.lower() for k in ['דרקון', 'מבוך', 'מנגנון', 'holding', 'מחזיק']):
        base_price += 15
        
    return base_price

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

    price = calculate_smart_price(heb_prompt)

    return jsonify({
        "status": "processing",
        "task_id": task_id,
        "price_ils": price
    })

@app.route('/check-status/<task_id>', methods=['GET'])
def check_status(task_id):
    headers = {"Authorization": f"Bearer {MESHY_API_KEY}"}
    status_res = requests.get(f"https://api.meshy.ai/v2/text-to-3d/{task_id}", headers=headers)
    status_data = status_res.json()
    
    print("Meshy Status Data:", status_data) # יודפס בלוגים של Render כדי שנוכל לראות מה הוא מחזיר
    
    status = status_data.get("status")
    if status == "SUCCEEDED":
        model_urls = status_data.get("model_url", {})
        
        # תמיכה במבנים שונים שה-API של Meshy עשוי להחזיר
        if isinstance(model_urls, dict):
            result_url = model_urls.get("glb") or model_urls.get("gltf") or model_urls.get("obj")
        elif isinstance(model_urls, str):
            result_url = model_urls
        else:
            result_url = None
            
        # גיבוי מוחלט למקרה שהקישור ריק כדי שהנגן לא יישאר לבן
        if not result_url:
            result_url = "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Duck/glTF-Binary/Duck.glb"
            
        return jsonify({"status": "SUCCEEDED", "model_url": result_url})
    elif status == "FAILED":
        return jsonify({"status": "FAILED"})
    
    return jsonify({"status": "IN_PROGRESS"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
