from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)
session = requests.Session()

# ================= CONFIG =================
API_KEY = "tanu"
BACKGROUND_FILENAME = "outfit.png"
IMAGE_TIMEOUT = 8
CANVAS_SIZE = (800, 800)

# ================= LOAD BACKGROUND =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, BACKGROUND_FILENAME)

try:
    BACKGROUND_IMAGE = Image.open(BG_PATH).convert("RGBA")
except Exception as e:
    print("Background load error:", e)
    BACKGROUND_IMAGE = None


# ================= FETCH PLAYER =================
def fetch_player_info(uid):
    try:
        url = f"https://najmi-info-all-server.vercel.app/player-info?uid={uid}"
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Player API error:", e)
        return None


# ================= FETCH IMAGE =================
def fetch_image(url, size=(150, 150)):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize(size, Image.LANCZOS)
    except Exception as e:
        print("Image fetch error:", e)
        return None


# ================= ROUTE =================
@app.route("/outfit-image", methods=["GET"])
def outfit_image():

    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "Invalid API key"}), 401

    if not uid:
        return jsonify({"error": "Missing uid"}), 400

    if BACKGROUND_IMAGE is None:
        return jsonify({"error": "Background image not found"}), 500

    player = fetch_player_info(uid)
    if not player:
        return jsonify({"error": "Failed to fetch player info"}), 500

    # ✅ FIXED JSON PATH
    outfit_ids = player.get("profileInfo", {}).get("clothes", [])

    if not outfit_ids:
        return jsonify({"error": "No outfit data found"}), 404

    # Create canvas
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 255))
    bg_resized = BACKGROUND_IMAGE.resize(CANVAS_SIZE, Image.LANCZOS)
    canvas.paste(bg_resized, (0, 0), bg_resized)

    # Outfit positions
    positions = [
        (350, 30),   # head
        (575, 130),  # face
        (665, 350),  # mask
        (575, 550),  # top
        (350, 654),  # bottom
        (135, 570),  # shoes
        (135, 130)   # extra
    ]

    # Paste first 7 clothes
    for i in range(min(7, len(outfit_ids))):
        oid = str(outfit_ids[i])
        image_url = f"https://iconapi.wasmer.app/{oid}"
        img = fetch_image(image_url)

        if img:
            canvas.paste(img, positions[i], img)

    # Output PNG
    output = BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)

    return send_file(output, mimetype="image/png")


# ================= RUN =================
if __name__ == "__main__":
    app.run()