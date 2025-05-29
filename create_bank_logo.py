# Run this script to create a simple bank logo
from PIL import Image, ImageDraw, ImageFont
import os

def create_bank_logo():
    # Create static/images directory if it doesn't exist
    os.makedirs('static/images', exist_ok=True)
    
    # Create a simple bank logo
    width, height = 180, 60
    img = Image.new('RGB', (width, height), color='#1e40af')  # Blue background
    draw = ImageDraw.Draw(img)
    
    # Add text (simple bank name)
    try:
        # Try to use a default font
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    text = "MyBank"
    
    # Get text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Center the text
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the logo
    img.save('static/images/bank-logo.png')
    print("Bank logo created at static/images/bank-logo.png")

if __name__ == "__main__":
    create_bank_logo()