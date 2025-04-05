#!/usr/bin/env python

import cv2
import os
import pandas as pd

image_folder = os.getenv("IMAGE_FOLDER")
output_csv = os.getenv("OUTPUT_CSV")
scale_factor = int(os.getenv("SCALE_FACTOR"))
window_name = "annotation tool"

if os.path.exists(output_csv):
    annotations = pd.read_csv(output_csv)
else:
    annotations = pd.DataFrame(columns=["filename",
                                        "x",
                                        "y",
                                        "width",
                                        "height",
                                        "bird_id"])
    annotations.to_csv(output_csv, index = False)

def resize_image(img, scale):
    """Resize image while maintaining aspect ratio"""
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    return cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

def load_annotation(img_name):
    """load existing annotations for this image"""
    if not os.path.exists(output_csv): return []
    existing = annotations[annotations['filename'] == img_name]
    birds = []
    for _, row in existing.iterrows():

        birds.append((row['x'], row['y'], row['width'], row['height']))
    return birds

def annotate_image(img_path, img_name):
    """ annotate all birds in a single image """
    img = cv2.imread(img_path)
    if img is None:

        print(f"cannot read {img_path}")
        return -1
    
    display_img = resize_image(img, scale_factor)
    original_height, original_width = img.shape[:2]
    display_height, display_width = display_img.shape[:2]
    
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, display_width, display_height)
    
    # load existing annotations for this image
    birds = load_annotation(img_name)
    bird_count = len(birds)
    
    while True:
        temp_img = display_img.copy()
        
        # draw boxes
        for i, (x, y, w, h) in enumerate(birds):
            """ scale coordinates for display """
            dx = int(x * scale_factor)
            dy = int(y * scale_factor)
            dw = int(w * scale_factor)
            dh = int(h * scale_factor)
            cv2.rectangle(temp_img, (dx, dy), (dx + dw, dy + dh), (0, 255, 0), 2)
            cv2.putText(temp_img, f"bird {i+1}", (dx, dy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imshow(window_name, temp_img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('b'):
            """ a bird detected """
            roi = cv2.selectROI(window_name, display_img, fromCenter=False)
            if roi != (0, 0, 0, 0):
                """ convert ROI back to original image coordinates """
                x = int(roi[0] / scale_factor)
                y = int(roi[1] / scale_factor)
                w = int(roi[2] / scale_factor)
                h = int(roi[3] / scale_factor)
                birds.append((x, y, w, h))
                bird_count += 1
        elif key == ord('d'):
            """ delete last bird """
            if birds:
                birds.pop()
                bird_count -= 1
        elif key == ord('s'):
            """ save and next """
            save_annotation(img_name, birds)
            cv2.destroyAllWindows()
            return 1
        elif key == ord('p'):
            """ previous image """
            cv2.destroyAllWindows()
            return -1
        elif key == ord('n'):
            """ previous image """
            cv2.destroyAllWindows()
            return 1
        elif key == ord('q'):
            """ quit program """
            cv2.destroyAllWindows()
            exit()
    cv2.destroyAllWindows()
    return 0

def save_annotation(img_name, birds):
    """ save csv annotation """
    global annotations
    # remove old annotations for this image
    annotations = annotations[annotations['filename'] != img_name]
    # add new annotations
    new_entries = []
    for i, (x, y, w, h) in enumerate(birds):

        new_entries.append({
            "filename": img_name,
            "x": x,
            "y": y,
            "width": w,
            "height": h,
            "bird_id": i+1
        })
    new_df = pd.DataFrame(new_entries)
    annotations = pd.concat([annotations, new_df], ignore_index=True)
    annotations.to_csv(output_csv, index=False)
    print(f"Saved {len(birds)} birds for {img_name}")


# get sorted list of images
image_file = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])
index_max = len(image_file) - 1
current_index = 0

print("Instructions:")
print("n - go to next image")
print("p - go to previous image")
print("b - Add new bird")
print("d - Delete last bird")
print("s - save and go to next image")
print("q - quit")
while True:
    """ Main annotation loop """
    if current_index < 0: current_index = index_max
    if current_index > index_max: current_index = 0
    img_name = image_file[current_index]
    img_path = os.path.join(image_folder, img_name)
    print(f"\nannotating {img_name} ({current_index}/{index_max})")
    direction = annotate_image(img_path, img_name)
    if not direction is None: current_index += direction
    # if direction is None:  # Error loading image
    #     current_index += 1  # Skip to next
    # else:
    #     current_index += direction

print("\nAnnotation complete!")
print(f"Total birds annotated: {len(annotations)}")
print(f"Saved to: {output_csv}")
