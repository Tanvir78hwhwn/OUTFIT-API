from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = Flask(__name__)
session = requests.Session()

# ================= CONFIG (Keep your names) =================
API_KEY = "tanu"
BACKGROUND_FILENAME = "outfit.png"
IMAGE_TIMEOUT = 8
CANVAS_SIZE = (1000, 1000)

# Exact positions for your Red Hexagon layout
SLOT_POSITIONS = {
    "head": (230, 210),
    "mask": (770, 210),
    "top": (130, 410),
    "glass": (870, 410),
    "bottom": (130, 630),
    "shoes": (260, 830),
    "pet": (740, 830),
    "weapon": (810, 630)
}

# ================= LOAD BACKGROUND (Your Logic) =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BG_PATH = os.path.join(BASE_DIR, BACKGROUND_FILENAME)

def get_bg():
    try:
        return Image.open(BG_PATH).convert("RGBA")
    except:
        # Fallback to black if file is missing to prevent 500 Error
        return Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 255))

# ================= HELPERS =================
def fetch_image(url, max_size=(160, 160)):
    try:
        r = session.get(url, timeout=IMAGE_TIMEOUT)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img.thumbnail(max_size, Image.LANCZOS)
        return img
    except:
        return None

# ================= ROUTE =================
@app.route("/outfit-image", methods=["GET"])
def outfit_image():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    # Fetch Player Info
    try:
        url = f"https://najmi-info-all-server.vercel.app/player-info?uid={uid}"
        player = session.get(url, timeout=IMAGE_TIMEOUT).json()
    except:
        return jsonify({"error": "Failed to fetch player"}), 500

    # 1. Prepare Canvas with your background
    bg_img = get_bg().resize(CANVAS_SIZE, Image.LANCZOS)
    canvas = Image.new("RGBA", CANVAS_SIZE)
    canvas.paste(bg_img, (0,0))
    draw = ImageDraw.Draw(canvas)

    # Use default font to avoid "font not found" crashes
    font = ImageFont.load_default()

    # 2. Character Body (Center)
    char_url = player.get("profileInfo", {}).get("bundleUrl")
    if char_url:
        char_img = fetch_image(char_url, max_size=(500, 800))
        if char_img:
            canvas.paste(char_img, (250, 180), char_img)

    # 3. Items (1 item per slot)
    clothes = player.get("profileInfo", {}).get("clothes", [])
    # Mapping order: Head, Top, Bottom, Shoes, Mask, Glass
    slots = ["head", "top", "bottom", "shoes", "mask", "glass"]
    
    for i, slot_name in enumerate(slots):
        if i < len(clothes):
            item_img = fetch_image(f"https://iconapi.wasmer.app/{clothes[i]}")
            if item_img:
                pos = SLOT_POSITIONS[slot_name]
                canvas.paste(item_img, (pos[0]-item_img.width//2, pos[1]-item_img.height//2), item_img)
                draw.text((pos[0]-20, pos[1]+80), slot_name.upper(), fill="white", font=font)

    # 4. Pet Slot
    pet_id = player.get("petInfo", {}).get("skinId")
    if pet_id:
        pet_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}")
        if pet_img:
            pos = SLOT_POSITIONS["pet"]
            canvas.paste(pet_img, (pos[0]-pet_img.width//2, pos[1]-pet_img.height//2), pet_img)
            draw.text((pos[0]-10, pos[1]+80), "PET", fill="white", font=font)

    # Export
    output = BytesIO()
    canvas.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
