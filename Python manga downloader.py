import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO

# === CONFIGURATION ===
start_url = "https://flamecomics.xyz/series/44/503e0f7071083096"
output_folder = "flamecomics_panels"
min_height = 800         # Only process images this tall or more
min_aspect_ratio = 0.5   # Filters out horizontal / weirdly wide images
slice_height = 800       # Height of each sub-panel when slicing tall images

# === SETUP ===
os.makedirs(output_folder, exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")  # Headless browser
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--log-level=3")

driver = webdriver.Chrome(service=ChromeService(), options=chrome_options)
print(f"🌐 Loading: {start_url}")
driver.get(start_url)

# Wait for JS images to load
time.sleep(5)
soup = BeautifulSoup(driver.page_source, "html.parser")
driver.quit()

# === FETCH IMAGES ===
images = soup.select("img")
print(f"🔍 Found {len(images)} image(s) on page.")

count = 0
for img in images:
    src = img.get("data-src") or img.get("src")
    if not src:
        continue

    img_url = urljoin(start_url, src)
    try:
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")

        width, height = image.size
        aspect_ratio = width / height

        if height < min_height or aspect_ratio > min_aspect_ratio:
            print(f"⚠️ Skipping: Too small or too wide ({width}x{height})")
            continue

        # === SLICE LOGIC ===
        if height > slice_height:
            num_slices = (height + slice_height - 1) // slice_height
            for i in range(num_slices):
                upper = i * slice_height
                lower = min((i + 1) * slice_height, height)
                cropped = image.crop((0, upper, width, lower))

                slice_filename = f"page_{count:03}_part{i + 1}.jpg"
                slice_path = os.path.join(output_folder, slice_filename)
                cropped.save(slice_path)
                print(f"🪓 Sliced: {slice_path}")
        else:
            filename = f"page_{count:03}.jpg"
            save_path = os.path.join(output_folder, filename)
            image.save(save_path)
            print(f"✅ Saved: {save_path}")

        count += 1

    except Exception as e:
        print(f"❌ Failed to download: {img_url} - {e}")

print(f"\n🎉 Done! {count} image(s) processed & saved into '{output_folder}' ✅")
