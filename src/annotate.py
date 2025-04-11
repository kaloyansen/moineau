#!/usr/bin/env python

import cv2
import os
#from pathlib import Path
import shutil

folder = os.getenv('POSITIVES')
annofile = os.getenv('ANNOTATE_TXT')
annobkp = os.getenv('ANNOTATE_BKP')
scale_factor = int(os.getenv('SCALE_FACTOR'))
annodict = {}


def quit(message: str, code: int):

    print(message)
    exit(code)


def load_data():

    with open(annofile) as f:

        for line in f:

            mot = line.strip().split()
            filename = mot[0]
            num = int(mot[1])
            boxes = [(int(mot[i]), int(mot[i + 1]), int(mot[i + 2]), int(mot[i + 3])) for i in range(2, 2 + num * 4, 4)]
            annodict[filename] = boxes
    print("annotations loaded from", annofile)


def save_data():

    with open(annofile, 'w') as f:

        for filename, boxes in annodict.items():

            #absolute = Path(absolute)
            #base = Path("/home/yocto/moineau/dataset")
            #filename = absolute.relative_to(base)
            line = f"{filename} {len(boxes)}"
            for (x, y, w, h) in boxes: line += f" {x} {y} {w} {h}"
            f.write(line + "\n")
    print("annotations saved to", annofile)            


def resize_image(img, scale):
    """ resize image while maintaining aspect ratio """
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)
    return cv2.resize(img, (width, height), interpolation = cv2.INTER_AREA)


def annotate_image(img_name: str) -> int:
    """ annotate image """
    global title
    key = f"positives/{img_name}"
    filepath = os.path.join(folder, img_name)
    img = cv2.imread(filepath)
    if img is None:

        print(f"cannot read {filepath}")
        return 2
    display_img = resize_image(img, scale_factor)
    original_height, original_width = img.shape[:2]
    display_height, display_width = display_img.shape[:2]
    
    cv2.namedWindow(title, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(title, display_width, display_height)

    if key in annodict.keys():

        boxes = annodict[key]
        count = len(boxes)
        print(count, 'annotations found')
    else:
        boxes = []
        annodict[key] = boxes
        print('new image')

    while True:
        """ control loop """
        temp_img = display_img.copy()
        for i, (x, y, w, h) in enumerate(boxes):
            """ scale coordinates for display """
            dx = int(x * scale_factor)
            dy = int(y * scale_factor)
            dw = int(w * scale_factor)
            dh = int(h * scale_factor)
            cv2.rectangle(temp_img, (dx, dy), (dx + dw, dy + dh), (255, 0, 255), 2)
            cv2.putText(temp_img, f"{i}", (dx, dy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        cv2.imshow(title, temp_img)
        button = cv2.waitKey(1) & 0xFF
        if button == ord('b'):
            """ new object """
            roi = cv2.selectROI(title, display_img, fromCenter = False)
            if roi != (0, 0, 0, 0):
                """ convert ROI back to original image coordinates """
                x = int(roi[0] / scale_factor)
                y = int(roi[1] / scale_factor)
                w = int(roi[2] / scale_factor)
                h = int(roi[3] / scale_factor)
                boxes.append((x, y, w, h))
                count += 1
        elif button == ord('d'):
            """ delete last bird """
            if boxes:
                boxes.pop()
                count -= 1
        elif button == ord('s'):
            """ save and open next image """
            save_data()
            cv2.destroyAllWindows()
            return 1
        elif button == 8:
            """ backspace to open previous image """
            cv2.destroyAllWindows()
            return -1
        elif button == ord(' '):
            """ next image """
            cv2.destroyAllWindows()
            return 1
        elif button == ord('r'):
            """ remove image """
            if key in annodict.keys():

                annodict.pop(key, None)
                save_data()
            cv2.destroyAllWindows()
            os.remove(filepath)
            return 1e6
        elif button == ord('q'):
            """ quit program """
            cv2.destroyAllWindows()
            return -1e6
if not os.path.exists(annofile): quit(f"cannot find {annofile}", 1)
if not os.path.exists(folder): quit(f"cannot find {folder}", 1)
shutil.copy(annofile, annobkp)
load_data()
ilist = sorted([f for f in os.listdir(folder) if f.endswith(('.jpg', '.jpeg'))])

print("control:\n[space] show annotations or go to next image\n[backspace] go to previous image")
print("[b] add new bird\n[d] delete last bird\n[r] remove image\n[s] save\n[q] quit")
current_index = 0
while True:
    """ main loop """
    if current_index < 0: current_index = len(ilist) - 1
    if current_index > len(ilist) - 1: current_index = 0
    img_name = ilist[current_index]
    title = f"\n{folder}/{img_name} ({current_index}/{len(ilist) - 1})"
    print(title)
    direction = annotate_image(img_name)
    if not direction is None:

        if direction == -1e6:

            break
        elif direction == 1e6:

            print('removed', ilist.pop(current_index))
        else:

            current_index += direction
    else:

        print('no direction')
total = 0
for k in annodict: total += len(annodict[k])
quit(f"\nannotation complete with {total} annotations from {len(ilist)} frames", 0)
