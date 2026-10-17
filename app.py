from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/generate-3d', methods=['POST'])
def generate_3d():
    data = request.json or {}
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    return jsonify({
        "status": "success",
        "model_url": "https://cdn.shopify.com/s/files/1/0000/0000/files/sample_model.obj",
        "weight_grams": 45.0,
        "price_ils": 45.0
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
