from PIL import Image, ImageDraw, ImageFont

# ================= UPDATED CONFIG =================
CANVAS_SIZE = (1000, 1000)
# Define fixed positions for the 6 standard hexagons (Left and Right columns)
HEX_POSITIONS = [
    (200, 250), (200, 450), (200, 650), # Left Column
    (800, 250), (800, 450), (800, 800)  # Right Column (Pet at bottom)
]
# Special wider slot for the weapon/glow item
SPECIAL_SLOT = (800, 620) 

def outfit_image():
    # ... (Keep your existing UID/Key validation and player fetch) ...

    # 1. Create Canvas & Paste Background
    canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 255))
    bg_resized = BACKGROUND_IMAGE.resize(CANVAS_SIZE, Image.LANCZOS)
    canvas.paste(bg_resized, (0, 0), bg_resized)
    
    draw = ImageDraw.Draw(canvas)

    # 2. Paste Main Character (Center)
    # Assuming the API provides a 'bundle' or 'fullBody' image URL
    character_url = player.get("profileInfo", {}).get("bundleUrl") 
    if character_url:
        char_img = fetch_image(character_url, max_size=(600, 800))
        if char_img:
            canvas.paste(char_img, (200, 150), char_img)

    # 3. Paste Outfit Items (Hexagons)
    clothes = player.get("profileInfo", {}).get("clothes", [])
    for i in range(min(len(clothes), 5)):  # First 5 items in hexagons
        oid = str(clothes[i])
        img = fetch_image(f"https://iconapi.wasmer.app/{oid}", max_size=(140, 140))
        if img:
            pos_x, pos_y = HEX_POSITIONS[i]
            canvas.paste(img, (pos_x - img.width//2, pos_y - img.height//2), img)
            
            # Label
            draw.text((pos_x - 30, pos_y + 60), "OUTFIT", fill="white")

    # 4. Handle Pet (Bottom Right)
    pet_id = player.get("petInfo", {}).get("skinId")
    if pet_id:
        pet_img = fetch_image(f"https://iconapi.wasmer.app/{pet_id}", max_size=(140, 140))
        if pet_img:
            px, py = HEX_POSITIONS[5] # Last hexagon slot
            canvas.paste(pet_img, (px - pet_img.width//2, py - pet_img.height//2), pet_img)
            draw.text((px - 20, py + 60), "PET", fill="white")

    # 5. Handle Special Item/Weapon (Wide slot)
    # Just an example using the 6th clothing item if it exists
    if len(clothes) > 5:
        special_img = fetch_image(f"https://iconapi.wasmer.app/{clothes[5]}", max_size=(250, 150))
        if special_img:
            sx, sy = SPECIAL_SLOT
            canvas.paste(special_img, (sx - special_img.width//2, sy - special_img.height//2), special_img)

    # ... (Save and return file) ...
