import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# הגדרות חיבור לשופיפיי (תשמור במשתני סביבה או תעדכן ישירות)
SHOPIFY_SHOP_URL = os.environ.get(
    "SHOPIFY_SHOP_URL", "your-shop.myshopify.com"
  )
ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN", "your-access-token")
API_VERSION = "2024-01"


def create_shopify_draft_order(line_items, customer_email=None):
  url = f"https://{SHOPIFY_SHOP_URL}/admin/api/{API_VERSION}/draft_orders.json"
  headers = {
      "X-Shopify-Access-Token": ACCESS_TOKEN,
      "Content-Type": "application/json",
  }

  draft_order_data = {"draft_order": {"line_items": line_items}}

  if customer_email:
    draft_order_data["draft_order"]["customer"] = {"email": customer_email}

  response = requests.post(url, json=draft_order_data, headers=headers)

  if response.status_code == 201:
    return response.json()
  else:
    raise Exception(f"Shopify Error [{response.status_code}]: {response.text}")


@app.route("/create-draft", methods=["POST"])
def create_draft():
  data = request.get_json()
  if not data or "line_items" not in data:
    return jsonify({"error": "Missing line_items in request"}), 400

  try:
    result = create_shopify_draft_order(
        data.get("line_items"), data.get("email")
    )
    return jsonify(result), 201
  except Exception as e:
    return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
  app.run(port=5000, debug=True)
