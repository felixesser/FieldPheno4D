import glob
from PIL import Image
import os

img_dir = 'data/FieldPheno4D/P146/dem/png/combined/'
images = []
if os.path.exists(img_dir):
    files = sorted(glob.glob(os.path.join(img_dir, '*.png')))
    for f in files:
        img = Image.open(f)
        # resize for reasonable GIF size
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        images.append(img)
    
    if images:
        images[0].save('demo_slider.gif', save_all=True, append_images=images[1:], duration=800, loop=0)
        print("created demo_slider.gif")
    else:
        print("no images in directory")
else:
    print("img_dir not found")
