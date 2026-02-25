from PIL import Image, ImageDraw, ImageFont

# ================= NEW CONFIG =================
CANVAS_SIZE = (1000, 1000)
# Define exact XY coordinates for the center of each hexagon slot
SLOT_POSITIONS = {
    "head": (230, 200),
    "mask": (770, 200),
    "top": (130, 400),
    "glass": (870, 400),
    "bottom": (130, 620),
    "shoes": (250, 820),
    "pet": (750, 820),
    "weapon": (800, 620) # The wider rectangular slot
}

def outfit_image():
    # ... [Keep your existing UID/Key validation and player fetch logic] ...

    # 1. Setup Canvas
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 255))
    if BACKGROUND_IMAGE:
        bg = BACKGROUND_IMAGE.resize(CANVAS_SIZE, Image.LANCZOS)
        canvas.paste(bg, (0, 0))
    
    draw = ImageDraw.Draw(canvas)
    
    # 2. Add Player Stats (Top Left)
    try:
        font_main = ImageFont.truetype("arial.ttf", 40)
        font_sub = ImageFont.truetype("arial.ttf", 25)
    except:
        font_main = font_sub = ImageFont.load_default()

    name = player.get("nickname", "DARK TANVIR")
    lvl = player.get("level", "67")
    likes = player.get("likes", "26228")
    
    draw.text((50, 40), name.upper(), fill="white", font=font_main)
    draw.text((50, 90), f"Level {lvl}  |  ❤️ {likes}", fill="white", font=font_sub)

    # 3. Paste Central Character
    # Replace this URL with the actual bundle/avatar image from your API
    char_url = player.get("profileInfo", {}).get("bundleUrl") 
    if char_url:
        char_img = fetch_image(char_url, max_size=(500, 800))
        if char_img:
            # Centering the character
            canvas.paste(char_img, (CANVAS_SIZE[0]//2 - char_img.width//2, 150), char_img)

    # 4. Map Clothes to Specific Slots
    clothes = player.get("profileInfo", {}).get("clothes", [])
    # Mapping logic depends on your API's array order (e.g., 0=head, 1=mask, etc.)
    order = ["head", "top", "bottom", "shoes", "mask", "glass"]
    
    for i, slot_name in enumerate(order):
        if i < len(clothes):
            oid = str(clothes[i])
            img = fetch_image(f"https://iconapi.wasmer.app/{oid}", max_size=(160, 160))
            if img:
                pos = SLOT_POSITIONS[slot_name]
                canvas.paste(img, (pos[0] - img.width//2, pos[1] - img.height//2), img)

    # 5. Paste Pet (Bottom Right)
    pet_id = player.get("petInfo", {}).get("skinId")
    if pet_id:
        p_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}", max_size=(150, 150))
        if p_img:
            pos = SLOT_POSITIONS["pet"]
            canvas.paste(p_img, (pos[0] - p_img.width//2, pos[1] - p_img.height//2), p_img)

    # ... [Save and return file] ...
