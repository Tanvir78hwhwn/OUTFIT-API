from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image
from io import BytesIO
import os
import math

app = Flask(__name__)
session = requests.Session()

# ================= CONFIG =================
API_KEY = "tanu"
BACKGROUND_FILENAME = "outfit.png"
IMAGE_TIMEOUT = 8
CANVAS_SIZE = (800, 800)
SLOT_SIZE = 150  # width/height of each octagon slot
NUM_SLOTS = 8    # total slots in circular UI

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
def fetch_image(url, max_size=(SLOT_SIZE, SLOT_SIZE)):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")

        # Scale down if too large
        img_w, img_h = img.size
        scale = min(max_size[0]/img_w, max_size[1]/img_h, 1.0)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        return img.resize((new_w, new_h), Image.LANCZOS)
    except Exception as e:
        print("Image fetch error:", e)
        return None

# ================= CALCULATE SLOT POSITIONS =================
def calculate_circular_positions(center_x, center_y, radius, num_slots):
    positions = []
    for i in range(num_slots):
        angle = 2 * math.pi * i / num_slots - math.pi/2  # start from top
        x = int(center_x + radius * math.cos(angle))
        y = int(center_y + radius * math.sin(angle))
        positions.append((x, y))
    return positions

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

    # ===== Get outfit IDs =====
    outfit_ids = player.get("profileInfo", {}).get("clothes", [])

    # ===== Get pet =====
    pet_info = player.get("petInfo", {})
    pet_id = pet_info.get("skinId")  # optional, can use 'id' if you want
    if pet_id:
        outfit_ids.append(pet_id)  # add pet as last slot

    if not outfit_ids:
        return jsonify({"error": "No outfit data found"}), 404

    # ===== Create canvas =====
    canvas_w, canvas_h = CANVAS_SIZE
    canvas = Image.new("RGBA", CANVAS_SIZE, (0,0,0,255))
    bg_resized = BACKGROUND_IMAGE.resize(CANVAS_SIZE, Image.LANCZOS)
    canvas.paste(bg_resized, (0,0), bg_resized)

    # ===== Calculate circular positions =====
    radius = 250  # distance from center to slot center
    center_x, center_y = canvas_w//2, canvas_h//2
    slot_positions = calculate_circular_positions(center_x, center_y, radius, NUM_SLOTS)

    # ===== Paste items =====
    for i in range(min(NUM_SLOTS, len(outfit_ids))):
        oid = str(outfit_ids[i])
        image_url = f"https://iconapi.wasmer.app/{oid}"
        img = fetch_image(image_url, max_size=(SLOT_SIZE, SLOT_SIZE))
        if img:
            slot_x, slot_y = slot_positions[i]
            img_w, img_h = img.size
            paste_x = slot_x - img_w // 2
            paste_y = slot_y - img_h // 2
            canvas.paste(img, (paste_x, paste_y), img)

    # ===== Output PNG =====
    output = BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png")


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)