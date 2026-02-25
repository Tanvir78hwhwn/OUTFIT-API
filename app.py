from flask import Flask, request, jsonify, send_file
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import os

app = Flask(__name__)
session = requests.Session()

# ================= CONFIG =================
API_KEY = "tanu"
CANVAS_SIZE = (1000, 1000)

# Exact positions based on your red hexagon reference image
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

# ================= HELPERS =================
def fetch_image(url, max_size=(160, 160)):
    try:
        r = session.get(url, timeout=8)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img.thumbnail(max_size, Image.LANCZOS)
        return img
    except:
        return None

def get_font(size):
    # Vercel doesn't always have Arial. This fallback prevents the 500 crash.
    try:
        return ImageFont.truetype("arial.ttf", size)
    except:
        return ImageFont.load_default()

# ================= ROUTE =================
@app.route("/outfit-image", methods=["GET"])
def outfit_image():
    uid = request.args.get("uid")
    key = request.args.get("key")

    if key != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    # Fetch Player Data
    try:
        player_url = f"https://najmi-info-all-server.vercel.app/player-info?uid={uid}"
        player = session.get(player_url, timeout=8).json()
    except:
        return jsonify({"error": "Player not found"}), 404

    # Create Background (Red Gradient Style)
    canvas = Image.new("RGBA", CANVAS_SIZE, (40, 0, 0, 255)) 
    draw = ImageDraw.Draw(canvas)

    # 1. Draw Player Info (Top Left)
    name = player.get("nickname", "UNKNOWN")
    lvl = player.get("level", "0")
    likes = player.get("likes", "0")
    
    draw.text((50, 40), name.upper(), fill="white", font=get_font(40))
    draw.text((50, 90), f"Level {lvl}  |  ❤️ {likes}", fill="white", font=get_font(24))

    # 2. Add Center Character
    # Note: Ensure your API provides a 'bundle' image link
    char_url = player.get("profileInfo", {}).get("bundleUrl")
    if char_url:
        char_img = fetch_image(char_url, max_size=(500, 800))
        if char_img:
            canvas.paste(char_img, (250, 180), char_img)

    # 3. Add Items to Slots
    clothes = player.get("profileInfo", {}).get("clothes", [])
    # Mapping indices to slots
    slot_mapping = ["head", "top", "bottom", "shoes", "mask", "glass"]
    
    for i, slot_name in enumerate(slot_mapping):
        if i < len(clothes):
            img = fetch_image(f"https://iconapi.wasmer.app/{clothes[i]}")
            if img:
                pos = SLOT_POSITIONS[slot_name]
                # Center the item in the slot
                canvas.paste(img, (pos[0]-img.width//2, pos[1]-img.height//2), img)
                # Label
                draw.text((pos[0]-30, pos[1]+80), slot_name.upper(), fill="white", font=get_font(14))

    # 4. Add Pet
    pet_id = player.get("petInfo", {}).get("skinId")
    if pet_id:
        p_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}")
        if p_img:
            pos = SLOT_POSITIONS["pet"]
            canvas.paste(p_img, (pos[0]-p_img.width//2, pos[1]-p_img.height//2), p_img)
            draw.text((pos[0]-15, pos[1]+80), "PET", fill="white", font=get_font(14))

    # Output
    img_io = BytesIO()
    canvas.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True)
