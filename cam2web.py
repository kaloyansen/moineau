#!/usr/bin/env python
# real-time analysis and streaming video 
# code by Kaloyan Krastev kaloyansen@gmail.com
# music composed, orchestrated and conducted by Kaloyan Krastev kaloyansen@gmail.com 
# title by Milko Ginev nmrp@abv.bg

from gevent import monkey
monkey.patch_all()

from gevent.pool import Pool
from gevent.pywsgi import WSGIServer
from gevent.lock import BoundedSemaphore
import gevent

from flask import Flask, Response
from flask import request, redirect, jsonify
from flask import render_template, send_from_directory, url_for
from flask_ipban import IpBan

import cv2

from markupsafe import escape
import numpy as np
import time
import datetime
import os
import sys
import select
import logging

video_device   =     os.getenv("VIDEO_DEVICE")
log_file       =     os.getenv("LOG_FILE")
work_directory =     os.getenv("FLASK_WORK_DIRECTORY")
page_title     =     os.getenv("PAGE_TITLE")
secret_key     =     os.getenv("FLASK_SECRET_KEY")
fps_limit      = int(os.getenv("FPS_LIMIT"))
jpeg_quality   = int(os.getenv("JPEG_QUALITY"))
gevent_workers = int(os.getenv("GEVENT_WORKERS"))
port           = int(os.getenv("FLASK_PORT"))
ban_count      = int(os.getenv("IP_BAN_LIST_COUNT"))
ban_seconds    = int(os.getenv("IP_BAN_LIST_SECONDS"))

server = Flask(__name__, template_folder = f"{work_directory}/static/template")
server.secret_key = secret_key

os.makedirs(f"{work_directory}/dataset/positives", exist_ok = True)
os.makedirs(f"{work_directory}/dataset/negatives", exist_ok = True)
os.makedirs(f"{work_directory}/ban", exist_ok = True)

cascade1 = cv2.CascadeClassifier(f"{work_directory}/cascade/bird1.xml")
cascade2 = cv2.CascadeClassifier(f"{work_directory}/cascade/bird2.xml")

if log_file == "no":

    logging.basicConfig(level = logging.INFO, encoding = 'utf-8')
else:

    logging.basicConfig(filename = f"{log_file}", level = logging.INFO, encoding = 'utf-8')
ip_ban = IpBan(ban_count = ban_count, ban_seconds = ban_seconds, persist = True, record_dir = f"{work_directory}/ban")
ip_ban.init_app(server)
ip_ban.load_allowed()
ip_ban.load_nuisances()

frame_count = 0
total_frame = 0
wheel_state = 0
wheel_states = ['-', '/', '|', '\\']
x_pub = 320
sleeping = 1e-2

AUDIO_LOC = '/static/audio'
AUDIO_DIR = f"{work_directory}/static/audio"

class SharedData:

    def __init__(self):

        self.raw = None
        self.frame = None
        self.running = True
        self.fps_value = 0

shared_data = SharedData()
bs_lock = BoundedSemaphore()
client_set = set()

def debug_wrapper(func, *args):

    try:

        func(*args)
    except Exception as e:

        server.logger.error(f"error in {func.__name__}: {e}")


def is_not_ascii(mot):

    for c in mot:

        if 0 <= ord(c) <= 127:

            continue
        else:

            return True
    return False


def keyboard_listener():

    while shared_data.running:

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:

            key = sys.stdin.read(1)
            if key == 'q':

                shared_data.running = False
            elif key == 'n':  # Negative frame

                save_frame(shared_data.raw, "negatives")
            elif key == 'p':  # Positive frame

                save_frame(shared_data.raw, "positives")
            elif key == 'c':  # Positive frame

                os.system('clear')
            elif key == 'r':  # Positive frame

                os.system('reset')
        gevent.sleep(0.1)  # Yield control back to gevent


def save_frame(fr, label):

    filename = f"{work_directory}/dataset/{label}/{int(time.time())}.jpg"
    cv2.imwrite(filename, fr)
    print(f"saved: {filename}")
    print("standby")


def put_text(fr, text, position, font_scale):

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (22, 22, 22)
    outcolor = (222, 222, 222)
    thickness = 1
    outline = 1 #  cv2.LINE_AA
    cv2.putText(fr, text, (position[0] - 1, position[1] - 1), font, font_scale, outcolor, outline, cv2.LINE_AA)
    cv2.putText(fr, text, (position[0] + 1, position[1] - 1), font, font_scale, outcolor, outline, cv2.LINE_AA)
    cv2.putText(fr, text, (position[0] - 1, position[1] + 1), font, font_scale, outcolor, outline, cv2.LINE_AA)
    cv2.putText(fr, text, (position[0] + 1, position[1] + 1), font, font_scale, outcolor, outline, cv2.LINE_AA)
    cv2.putText(fr, text, position, font, font_scale, color, thickness, cv2.LINE_AA)


def label_frame(fr):

    global total_frame, x_pub
    last_modified = datetime.datetime.now().strftime("%Y-%m-%d")

    maintenant = datetime.datetime.now()
    timestamp = maintenant.strftime("%H:%M:%S")
    timestamp = f"{timestamp}.{frame_count}"
    publicity = ' https://github.com/kaloyansen/moineau'
# 640 x 480
# 320 x 240

    if x_pub > 0:
        x_pub = x_pub - total_frame
    if x_pub < 0:
        x_pub = 0

    fps_value = shared_data.fps_value
    put_text(fr, f" {page_title}", (0, 12), 0.4)
    put_text(fr, timestamp, (260, 12), 0.3)
    put_text(fr, publicity, (x_pub, 230), 0.3)
    put_text(fr, f"{fps_value:6.2f} Hz", (260, 230), 0.3)

    return fr


def analyze_frame(fr):

    global wheel_state, wheel_states

    gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    sparrow1 = cascade1.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 5, minSize=(30, 30))
    sparrow2 = cascade2.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 5, minSize=(30, 30))
#    if len(sparrow) > 0:

#        save_frame(fr, "positives")
#    else:

#        save_frame(fr, "negatives")
    font = cv2.FONT_HERSHEY_SIMPLEX
    wheel = wheel_states[wheel_state] # + f" {len(sparrow1)}"
    wheel_state = (wheel_state + 1) % len(wheel_states)

    spindex = 0
    for (x, y, w, h) in sparrow1:

        cv2.rectangle(fr, (x, y), (x + w, y + h), (255, 255, 0), 2)
        cv2.putText(fr, f"{spindex} {wheel}", (x, y + 12), font, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
        spindex += 1
    for (x, y, w, h) in sparrow2:

        cv2.rectangle(fr, (x, y), (x + w, y + h), (255, 255, 0), 2)
        cv2.putText(fr, 'bird', (x, y - 2), font, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
        
    return fr # processed_frame


def process_frame(fr):

    global frame_count
    analyzed_frame = analyze_frame(fr)
    labeled_frame = label_frame(analyzed_frame)

    frame_count += 1
    if frame_count > 9:
        frame_count = 0

    return labeled_frame


def read_stream():

    global total_frame

    server.logger.info(f"gonna capture {video_device}")
    cap = cv2.VideoCapture(video_device)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():

        server.logger.error(f"cannot capture {video_device}")
        shared_data.running = False
    else:

        server.logger.info(f"captured {video_device}")
        shared_data.running = True
    read_count = time.perf_counter()
    while shared_data.running:

        if time.perf_counter() - read_count < 1. / fps_limit:

            gevent.sleep(sleeping)
            continue

        success, raw_frame = cap.read()
        if not success:

            read_count = time.perf_counter()
            gevent.sleep(sleeping)
            continue
         
        raw_frame_resized = cv2.resize(raw_frame, (320, 240))
        raw_frame_resized_copy = raw_frame_resized.copy()
        processed_frame = process_frame(raw_frame_resized_copy)
        with bs_lock:

            shared_data.raw = raw_frame_resized
            shared_data.frame = processed_frame # .copy()

        total_frame += 1
        read_count = time.perf_counter()

    cap.release()


def generation():

    gen_count = time.perf_counter()
    last_frame = None
    while shared_data.running:

        if time.perf_counter() - gen_count < 1. / fps_limit:

            gevent.sleep(sleeping)
            continue

        with bs_lock:

            if shared_data.frame is None:

                server.logger.warning("frame is None")
                gevent.sleep(sleeping)
                continue
            #if last_frame is not None and np.array_equal(shared_data.frame, last_frame):

                #server.logger.warning("frame repeats")
            #     gevent.sleep(sleeping)
            #     continue

            last_frame = shared_data.frame.copy()

        _, jpeg = cv2.imencode('.jpg', last_frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])

        shared_data.fps_value = 1 / (time.perf_counter() - gen_count)
        gen_count = time.perf_counter()

        try:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        except Exception as e:
            server.logger.warning(f"client disconnected: {e}")
            break


@server.context_processor
def serange():

    return dict(title = page_title)


@server.route('/feed')
def feed():

    return Response(generation(), mimetype = 'multipart/x-mixed-replace; boundary=frame')


@server.route('/source_code')
def access_source_code():

    try:

        file_path = os.path.abspath(__file__)
        with open(file_path, "r") as f:

            src = f.read()
        size = len(src.splitlines())
        escaped_code = escape(src)
        return render_template('code.html', code = escaped_code, size = size)
    except Exception as e:
 
        server.logger.error(f"error while reading source code: {e}")
        return f"error: {e}", 500


@server.route('/', methods = ['GET'])
def index():

    audio_files = []
    if os.path.exists(AUDIO_DIR):

        all_files = os.listdir(AUDIO_DIR)
        audio_files =  [f for f in all_files if f.endswith(".mp3")]
    else:

        return "maintenance", 200
    try:

        return render_template('main.html', audio_files=audio_files)
    except Exception as e:

        return f"error: {e}"


@server.route('/static/sound/<filename>', methods = ['GET'])
def serve_audio(filename):

    return send_from_directory(AUDIO_LOC, filename)


@server.route('/sitemap.xml', methods=['GET'])
def sitemap():
    pages = []
    last_modified = datetime.datetime.now().strftime("%Y-%m-%d")

    for rule in server.url_map.iter_rules():

        if "GET" in rule.methods and len(rule.arguments) == 0:  # Ignore dynamic routes

            url = url_for(rule.endpoint, _external=True)
            pages.append(f"""
                <url>
                    <loc>{url}</loc>
                    <lastmod>{last_modified}</lastmod>
                    <changefreq>weekly</changefreq>
                    <priority>0.5</priority>
                </url>""")

    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        {''.join(pages)}
    </urlset>"""

    return Response(sitemap_xml, mimetype = "application/xml")


@server.before_request
def before_request():

    ip = request.remote_addr
    fp = request.full_path
    # server.logger.info(f"{ip} raw method = {request.method}")
    # request.method.encode("ascii", "ignore")
    # server.logger.info(f"{ip} encoded method = {request.method}")
    met = request.method
    if met != 'GET':

        ip_ban.block(ip)
        server.logger.warning(f"method not allowed - save {ip} as banned and return error")
        return "method not allowed {met}", 403
    elif is_not_ascii(met) or is_not_ascii(fp):

        ip_ban.block(ip)
        server.logger.warning(f"non-ascii request - save {ip} as banned and return error")
        return "non-ascii characters in request", 403

#        return "you have been added to the black list", 403
    # elif ip_ban.is_banned(client_ip):

    #     server.logger.warning(f"{client_ip} is in the list of banned")
    #     return "you are already in the black list", 403
    else:

        with bs_lock:

            client_set.add(ip)


@server.after_request
def after_request(response):

    return response


@server.route('/client_counter')
def get_clients():

    with bs_lock:

        return f"{len(client_set)}"


def run_server():

    serve = WSGIServer(("0.0.0.0", port), server)
    serve.serve_forever()


if __name__ == '__main__':

    pool = Pool(gevent_workers)

    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    server.logger.info(f"starting flask server at {timestamp}")

    pool.spawn(debug_wrapper, run_server)
    server.logger.info("starting stream")

    pool.spawn(debug_wrapper, read_stream)
    server.logger.info("starting keyboard listener")

    pool.spawn(debug_wrapper, keyboard_listener)
    server.logger.info(f"ban_count {ip_ban.ban_count} ban_seconds {ip_ban.ban_seconds}")
    #server.logger.info(f"ip_ban_list ({len(ip_ban._ip_ban_list)})")
    #server.logger.info("\nip_ban_list: ".join(ip_ban._ip_ban_list))
    print("'n' to save a negative image")
    print("'p' to save a positive image")
    print("'q' to quit the application")
    print("standby")

    while shared_data.running:

        gevent.sleep(0.5)
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    server.logger.warning("stop signal detected\n")
    pool.kill()
    server.logger.info("all tasks stopped\n")
