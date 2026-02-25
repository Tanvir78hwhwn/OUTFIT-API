from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
import os

app = Flask(__name__)
session = requests.Session()

# ========= CONFIG =========
API_KEY = "tanu"
BACKGROUND_FILENAME = "outfit.png"
IMAGE_TIMEOUT = 8
CANVAS_SIZE = (800, 800)

# ========= LOAD BACKGROUND ONCE =========
bg_path = os.path.join(os.path.dirname(__file__), BACKGROUND_FILENAME)
try:
    BACKGROUND_IMAGE = Image.open(bg_path).convert("RGBA")
except:
    BACKGROUND_IMAGE = None


# ========= FETCH PLAYER =========
def fetch_player_info(uid):
    try:
        url = f"https://najmi-info-all-server.vercel.app/player-info?uid={uid}"
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Player API Error:", e)
        return None


# ========= FETCH IMAGE =========
def fetch_image(url, size=(150,150)):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        return img.resize(size, Image.LANCZOS)
    except Exception as e:
        print("Image Error:", e)
        return None


# ========= ROUTE =========
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
        return jsonify({"error": "Failed to fetch player"}), 500

    outfit_ids = player.get("AccountProfileInfo", {}).get("EquippedOutfit", [])

    print("Outfit IDs:", outfit_ids)

    # Create Canvas
    canvas = Image.new("RGBA", CANVAS_SIZE, (0,0,0,255))
    bg_resized = BACKGROUND_IMAGE.resize(CANVAS_SIZE, Image.LANCZOS)
    canvas.paste(bg_resized, (0,0), bg_resized)

    positions = [
        (350,30),
        (575,130),
        (665,350),
        (575,550),
        (350,654),
        (135,570),
        (135,130)
    ]

    # Use first 7 outfit IDs directly
    for i in range(min(7, len(outfit_ids))):
        oid = str(outfit_ids[i])
        image_url = f"https://iconapi.wasmer.app/{oid}"
        img = fetch_image(image_url)

        if img:
            canvas.paste(img, positions[i], img)

    output = BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)

    return send_file(output, mimetype="image/png")


if __name__ == "__main__":
    app.run()