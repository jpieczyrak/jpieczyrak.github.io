import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import exifread
from datetime import datetime

# config
gallery_title = "Jędrzej Pieczyrak - Portfolio"
output_file = "index.html"
image_folder = "photos" # input folder with images
thumbs_folder = Path(image_folder) / "thumbs"
thumb_size = (400, 400)
write_caption_on_image = False

thumbs_folder.mkdir(parents=True, exist_ok=True)

# find images
image_dir = Path(image_folder)
images = sorted([f for f in image_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])

from datetime import datetime
import exifread

def get_exif_caption(img_path):
    try:
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f, stop_tag="UNDEF", details=False)

        #print(f"EXIF for {img_path.name}:")
        if not tags:
            print(f"EXIF for {img_path.name}:")
            print("  brak EXIF")
            return ""

        # for tag in ["Image Model", "EXIF LensModel", "EXIF FocalLength", "EXIF FNumber",
                    # "EXIF ExposureTime", "EXIF ISOSpeedRatings", "EXIF DateTimeOriginal"]:
            # if tag in tags:
                # print(f"  {tag}: {tags[tag]}")

        def g(tag):
            return str(tags.get(tag, '')).strip()

        model = g("Image Model")
        lens = g("EXIF LensModel") or g("EXIF LensSpecification")

        focal = ""
        focal_raw = g("EXIF FocalLength").split()[0]
        if "/" in focal_raw:
            num, denom = map(float, focal_raw.split('/'))
            focal = f"{round(num / denom)}mm"
        elif focal_raw:
            focal = f"{round(float(focal_raw))}mm"


        fnumber = ""
        fnum_raw = g("EXIF FNumber")
        if "/" in fnum_raw:
            num, denom = map(float, fnum_raw.split('/'))
            fnumber = f"f/{round(num / denom, 1)}"
        elif fnum_raw:
            fnumber = f"f/{round(float(fnum_raw), 1)}"


        exposure = g("EXIF ExposureTime")
        iso = g("EXIF ISOSpeedRatings")

        dt = ""
        try:
            date = g("EXIF DateTimeOriginal") or g("Image DateTime")
            if date:
                dt = datetime.strptime(date, "%Y:%m:%d %H:%M:%S").strftime("%Y-%m")
        except Exception:
            pass

        parts = [
            f"[{dt}]" if dt else "",
            model,
            f"+ {lens}" if lens else "",
            f"{fnumber} {exposure}s" if fnumber or exposure else "",
            f"ISO {iso}" if iso else "",
            f"@{focal}" if focal else "",
        ]

        return f"[{dt}] {model} + {lens} | {fnumber} {exposure}s ISO {iso} @{focal}"
        #return " ".join(p for p in parts if p)

    except Exception as e:
        print(f"  Błąd odczytu EXIF: {e}")
        return ""

# HTML head
html_head = f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <title>{gallery_title}</title>
  <link rel="stylesheet" href="https://unpkg.com/photoswipe@5/dist/photoswipe.css">
  <style>
    body {{ font-family: sans-serif; background: #111; color: #eee; padding: 2rem; }}
    .gallery {{ display: flex; flex-wrap: wrap; gap: 10px; }}
    .gallery a img {{ height: 200px; height: auto; border: 2px solid #333; }}
    .pswp__custom-caption {{
      color: #eee;
      font-size: 14px;
      padding: 10px 20px;
      background: rgba(0, 0, 0, 0.6);
      position: absolute;
      bottom: 0;
      width: 100%;
      box-sizing: border-box;
    }}
  .pswp__custom-caption a {{
    color: #fff;
    text-decoration: underline;
  }}
  .hidden-caption-content {{
    display: none;
  }}
  </style>
</head>
<body>
<h1>{gallery_title}</h1>
<div class="gallery" id="gallery">
"""

html_images = ""
counter = 0
total = len(images)
for img_path in images:
    img_name = img_path.name
    thumb_path = thumbs_folder / img_name

    # thumbs creation
    if not thumb_path.exists():
        with Image.open(img_path) as im:
            im = im.convert("RGB")
            target_height = thumb_size[1]
            scale = target_height / im.height
            new_width = int(im.width * scale)
            im = im.resize((new_width, target_height), Image.LANCZOS)
            im.save(thumb_path)


    # read sizes
    with Image.open(img_path) as im:
        width, height = im.size

    # EXIF caption
    caption = get_exif_caption(img_path)
    
    # print caption
    if write_caption_on_image:
        image = Image.open(img_path)
        exif_data = image.info.get('exif', None)
        image = image.convert("RGB")
        draw = ImageDraw.Draw(image)
        font_size = round(image.height * 0.014)  # scaling
        font = ImageFont.truetype("arial.ttf", size=font_size)      
        x, y = 30, 30
        
        # black border
        draw.text((x-1, y), caption, font=font, fill="black")
        draw.text((x+1, y), caption, font=font, fill="black")
        draw.text((x, y-1), caption, font=font, fill="black")
        draw.text((x, y+1), caption, font=font, fill="black")
        
        # white text
        draw.text((x, y), caption, font=font, fill="white")
        if exif_data:
            image.save(img_path, exif=exif_data)
        else:
            image.save(img_path)

    counter += 1
    print(f"[{counter}/{total}] Processing: {img_path.name}", end='\r', flush=True)

    # HTML
    html_images += f'''  <a href="{image_folder}/{img_name}" 
    data-pswp-width="{width}" data-pswp-height="{height}" 
    data-caption="{caption}">
    <img src="{thumb_path.as_posix()}" alt="{caption}">
  </a>\n'''

# HTML footer
html_foot = """
</div>

<!-- PhotoSwipe -->
<script type="module">
  import PhotoSwipeLightbox from 'https://unpkg.com/photoswipe@5/dist/photoswipe-lightbox.esm.js';
  const lightbox = new PhotoSwipeLightbox({
    gallery: '#gallery',
    children: 'a',
    pswpModule: () => import('https://unpkg.com/photoswipe@5/dist/photoswipe.esm.js')
  });

lightbox.on('uiRegister', function() {
  lightbox.pswp.ui.registerElement({
    name: 'custom-caption',
    order: 9,
    isButton: false,
    appendTo: 'root',
    html: 'Caption text',
    onInit: (el, pswp) => {
      lightbox.pswp.on('change', () => {
        const currSlideElement = lightbox.pswp.currSlide.data.element;
        let captionHTML = '';
        if (currSlideElement) {
          const hiddenCaption = currSlideElement.querySelector('.hidden-caption-content');
          if (hiddenCaption) {
            // get caption from element with class hidden-caption-content
            captionHTML = hiddenCaption.innerHTML;
          } else {
            // get caption from alt attribute
            captionHTML = currSlideElement.querySelector('img').getAttribute('alt');
          }
        }
        el.innerHTML = captionHTML || '';
      });
    }
  });
});


  lightbox.init();
</script>

</body>
</html>
"""

# index save
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html_head + html_images + html_foot)

print(f"\nWygenerowano: {output_file}")
