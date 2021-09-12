import cv2
import json

with open("final_out.json", "r") as f:
    entries = json.load(f)

for i in range(0, len(entries)):
    images = []
    pages = entries[i]["pages"]
    for p in pages:
        im = cv2.imread(f"pdf_images/{p['num']}.jpg")
        y1 = p["top"] - 20
        y2 = p["bottom"]
        x1 = 0
        x2 = im.shape[1]
        if y2 < 0:
            y2 = im.shape[0]

        im = im[y1:y2, x1:x2]
        images.append(im)
        print(im.shape[1])

    w_min = min(im.shape[1] for im in images)
    images_resized = [cv2.resize(im, (w_min, int(im.shape[0] * w_min / im.shape[1])), interpolation=cv2.INTER_CUBIC)
                      for im in images]

    cv2.imwrite(f"entries/images/{i}.jpg", cv2.vconcat(images_resized))
