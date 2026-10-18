from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import os
import requests

app = Flask(__name__)
CORS(app)  # מאפשר חיבור בטוח מכל הדומיינים (CORS)

DB_FILE = 'customer_quotas.json'

def load_quotas():
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_quotas(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/generate-model', methods=['POST'])
def generate_model():
    data = request.json or {}
    customer_id = data.get('customer_id')
    prompt = data.get('prompt')

    if not customer_id:
        return jsonify({'success': False, 'message': 'חובה להתחבר לחשבון כדי ליצור מודל'}), 401

    if not prompt:
        return jsonify({'success': False, 'message': 'נא להזין תיאור למודל'}), 400

    quotas = load_quotas()
    current_month = datetime.now().strftime('%Y-%m')

    user_data = quotas.get(str(customer_id), {
        'count': 0,
        'last_month': current_month
    })

    # איפוס מכסה חודשית בתחילת חודש חדש
    if user_data.get('last_month') != current_month:
        user_data['count'] = 0
        user_data['last_month'] = current_month

    # בדיקת מגבלה (מקסימום 3 בחודש)
    if user_data['count'] >= 3:
        return jsonify({
            'success': False,
            'message': 'הגעת למכסה החודשית של 3 מודלים בחינם! המכסה תתאפס בתחילת החודש הבא.',
            'remaining': 0
        }), 403

    # כאן מתבצעת הפנייה ל-API של יצירת ה-3D
    # stl_url = call_3d_ai_api(prompt)
    stl_url = "https://example.com/generated_model.stl"

    # עדכון המונה ושמירה
    user_data['count'] += 1
    quotas[str(customer_id)] = user_data
    save_quotas(quotas)

    remaining = 3 - user_data['count']

    return jsonify({
        'success': True,
        'stl_url': stl_url,
        'used_this_month': user_data['count'],
        'remaining_this_month': remaining,
        'message': f'המודל נוצר בהצלחה! נותרו לך עוד {remaining} יצירות בחינם החודש.'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
