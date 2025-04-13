#!/usr/bin/env python
# real-time analysis and streaming video 
# code by Kaloyan Krastev kaloyansen@gmail.com
# title by Milko Ginev nmrp@abv.bg
# music composed, orchestrated and conducted by Kaloyan Krastev 

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

# from markupsafe import escape
import numpy as np
import time
import datetime
import os
import sys
import select
import logging
import random
import lorem
from itertools import product

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter


class SecureContext:
    """ secure context """
    def __init__(self, birdlives):
        """ load context """
        self.video_device   =       self.safe("VIDEO_DEVICE")
        self.log_file       =       self.safe("LOG_FILE")
        self.work_directory =       self.safe("FLASK_WORK_DIRECTORY")
        self.page_title     =       self.safe("PAGE_TITLE")
        self.secret_key     =       self.safe("FLASK_SECRET_KEY")
        self.audio_dir      =       self.safe("AUDIO_DIRECTORY")
        self.fps_limit      =   int(self.safe("FPS_LIMIT"))
        self.jpeg_quality   =   int(self.safe("JPEG_QUALITY"))
        self.gevent_workers =   int(self.safe("GEVENT_WORKERS"))
        self.flask_port     =   int(self.safe("FLASK_PORT"))
        self.ban_count      =   int(self.safe("IP_BAN_LIST_COUNT"))
        self.ban_seconds    =   int(self.safe("IP_BAN_LIST_SECONDS"))
        self.save_rand_min  =   int(self.safe("SAVE_RANDOM_MINUTES"))
        self.minNeighbors   =   int(self.safe("CASCADE_MIN_NEIGHBORS"))
        self.minSize        =   int(self.safe("CASCADE_MIN_SIZE"))
        self.scaleFactor    = float(self.safe("CASCADE_SCALE_FACTOR"))
        self.classifier     =       self.safe("CASCADE_CLASSIFIER")
    def safe(self, var: str):
        """ let it be safe """
        good = os.getenv(var, 0)
        if not good: print(f"not good: cannot find {var}")
        return good
    def dump(self):
        """ print all """
        print('\n', '=' * 16, 'secure context', '=' * 16)
        for key, value in self.__dict__.items(): print(key, value)
        print('=' * 44, '\n')


class InterThreadCommunication:
    """ shared data """
    def __init__(self, font, font_size, frame_size, save_random):

        self.start = self.get_time()
        self.font = font
        self.font_size = font_size
        self.frame_size = frame_size
        self.save_random = save_random
        self.raw = None
        self.frame = None
        self.running = True
        self.fps_value = 10.0
        self.count = 0
        self.count9 = 0
        self.pos = 0
        self.neg = 0
        self.wheel_index = 0
        self.wheel_state = ['-', '/', '|', '\\']
        self.new_message()
    def new_message(self, message = 0, persist = 216, speed = 6):

        self.speed = speed
        self.persist = persist
        self.x = frame_size[0]
        if message: self.text = message
        else: self.text = lorem.sentence()[:37].rstrip('.').lower()
        self.size = self.get_size(self.text)
    def wheel(self) -> str: return self.wheel_state[self.wheel_index]
    def get_time(self, time_format = "%y%m%d-%H%M%S.%f") -> str: return datetime.datetime.now().strftime(time_format)
    def get_size(self, text: str): return cv2.getTextSize(text, self.font, self.font_size, 1)[0]
    def new_frame(self) -> bool:

        self.count += 1
        self.count9 = (self.count9 + 1) % 9
        if self.x / self.size[0] + 1 < 0: self.x = self.frame_size[0] - self.size[0] # not too complicated
        self.x -= self.speed
        if self.count % self.persist == 0: self.new_message()
        self.wheel_index = (self.wheel_index + 1) % len(self.wheel_state)
        return self.count % self.save_random == 0
    def dump(self):
        """ print all """
        print('\n', '=' * 16, 'shared data', '=' * 16)
        for key, value in self.__dict__.items():

            if key == 'raw' or key == 'frame': continue
            print(key, value)
        print('=' * 44, '\n')


sc = SecureContext(166)

server = Flask(__name__, template_folder = f"{sc.work_directory}/static/template")
server.secret_key = sc.secret_key


positives = f"{sc.work_directory}/dataset/positives"
negatives = f"{sc.work_directory}/dataset/negatives"
os.makedirs(positives, exist_ok = True)
os.makedirs(negatives, exist_ok = True)
os.makedirs(f"{sc.work_directory}/ban", exist_ok = True)

cascade = cv2.CascadeClassifier(sc.classifier)

if sc.log_file: logging.basicConfig(level = logging.INFO, encoding = 'utf-8', filename = f"{sc.log_file}")
else: logging.basicConfig(level = logging.INFO, encoding = 'utf-8')

ip_ban = IpBan(ban_count = sc.ban_count, ban_seconds = sc.ban_seconds, persist = True, record_dir = f"{sc.work_directory}/ban")
ip_ban.init_app(server)
ip_ban.load_allowed()
ip_ban.load_nuisances()

#frame_size = (640, 480)
frame_size = (320, 240)

sleeping = 1e-2

itc = InterThreadCommunication(cv2.FONT_HERSHEY_DUPLEX, 0.4, frame_size, sc.fps_limit * sc.save_rand_min * 60)
bs_lock = BoundedSemaphore()
client_set = set()

def debug_wrapper(func, *args):

    try: func(*args)
    except Exception as e: server.logger.error(f"error in {func.__name__}: {e}")


def is_not_ascii(mot: str) -> bool:

    for c in mot:

        if 0 <= ord(c) <= 127: continue
        else: return True
    return False


def keyboard_listener():

    while itc.running:

        if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:

            key = sys.stdin.read(1)
            if key == 'q':
                # quit
                itc.running = False
            elif key == 'n':
                # save a negative frame
                save_frame('-')
            elif key == 'p':
                # save a positive frame
                save_frame('+')
            elif key == 'r':
                # reset command-line interfase
                os.system('reset')
            elif key == 'D':
                # dump shared data
                itc.dump()
            elif key == 'd':
                # dump context
                sc.dump()
        gevent.sleep(0.1)  # Yield control back to gevent


def save_frame(label: str, message = '') -> int:

    if label == '+': save_in = positives
    elif label == '-': save_in = negatives
    else:

        print(f"error in save_frame: unexpected label {label}")
        itc.running = False
        return 1
    filepath = f"{save_in}/{itc.get_time()}{message}.jpg"
    cv2.imwrite(filepath, itc.raw)
    itc.pos = len(os.listdir(positives))
    itc.neg = len(os.listdir(negatives))
    show = f"{label * 3} (+{itc.pos}, -{itc.neg}) {message}"
    print(f"{show} {filepath}")
    itc.new_message(f"{show} {itc.get_time()}")
    print("standby")
    return 0


def outline(fr: np.ndarray, text: str, position: tuple):

    for x, y in product([-1, 1], repeat = 2):

        cv2.putText(fr, text, (position[0] + x, position[1] + y),
                    itc.font, itc.font_size, (0, 50, 100), 1, cv2.LINE_AA)
    cv2.putText(fr, text, position,
                itc.font, itc.font_size, (250, 200, 150), 1, cv2.LINE_AA)


def label_frame(fr: np.ndarray) -> np.ndarray:

    timestamp = f"{itc.get_time('%H:%M:%S')}.{itc.count9} "
    video_title = f" {sc.page_title}{itc.fps_value:6.2f} Hz"
    y_bottom = frame_size[1] - itc.size[1]
    x_right = frame_size[0] - itc.get_size(timestamp)[0]

    outline(                      fr, video_title,      (0,                                  12))
    outline(                      fr, timestamp,        (x_right,                            12))
    outline(                      fr, itc.text,         (itc.x,                        y_bottom))
    if itc.x < 0: outline(        fr, itc.text,         (frame_size[0] + itc.x,         y_bottom))
    return fr


def analyze_frame(fr: np.ndarray) -> np.ndarray:

    gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    sparrow = cascade.detectMultiScale(gray,
                                       scaleFactor = sc.scaleFactor,
                                       minNeighbors = sc.minNeighbors,
                                       minSize = (sc.minSize, sc.minSize))
    len_sparrow = len(sparrow)
    #if len_sparrow > 0:
        #cv2.putText(fr, f"{len_sparrow}/{minNeighbors}", (100, 100), itc.font, 1, (0, 0, 0), 1, 1)

#        save_frame('+')
#    else:

#        save_frame('-')

    spindex = 0
    for (x, y, w, h) in sparrow:

        cv2.rectangle(fr, (x, y), (x + w, y + h), (255, 255, 0), 1)
        cv2.putText(fr, f"{spindex} {itc.wheel()}", (x, y + 12), itc.font, 0.5, (255, 255, 0), 1, cv2.LINE_AA)
        spindex += 1
    return fr


def process_frame(fr: np.ndarray) -> np.ndarray:

    analyzed_frame = analyze_frame(fr)
    labeled_frame = label_frame(analyzed_frame)
    return labeled_frame


def read_stream():

    server.logger.info(f"wait while capturing {sc.video_device} ...")
    cap = cv2.VideoCapture(sc.video_device)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():

        server.logger.error(f"... cannot capture {sc.video_device}")
        itc.running = False
        return
    server.logger.info(f"... captured {sc.video_device}")
    itc.running = True
    server.logger.info("keyboard commands:")
    server.logger.info("[d] dump context")
    server.logger.info("[D] dump data")
    server.logger.info("[n] save a negative image")
    server.logger.info("[p] save a positive image")
    server.logger.info("[q] quit the application")
    read_count = time.perf_counter()
    while itc.running:

        if time.perf_counter() - read_count < 1. / sc.fps_limit:

            gevent.sleep(sleeping)
            continue

        success, raw_frame = cap.read()
        if not success:

            server.logger.error(f"cannot read {sc.video_device}")
            read_count = time.perf_counter()
            gevent.sleep(1)
            continue
        raw_frame_resized = cv2.resize(raw_frame, frame_size)
        raw_frame_resized_copy = raw_frame_resized.copy()
        processed_frame = process_frame(raw_frame_resized_copy)
        with bs_lock:

            itc.raw = raw_frame_resized
            itc.frame = processed_frame # .copy()
        if itc.new_frame(): save_frame('-', '.random')
        itc.fps_value = 1 / (time.perf_counter() - read_count)
        itc.save_random = int(itc.fps_value * sc.save_rand_min * 60)
        read_count = time.perf_counter()
    cap.release()


def generation():

    gen_count = time.perf_counter()
    last_frame = None
    while itc.running:

        if time.perf_counter() - gen_count < 1. / sc.fps_limit:

            gevent.sleep(sleeping)
            continue

        with bs_lock:

            if itc.frame is None:

                server.logger.warning("frame is None")
                gevent.sleep(sleeping)
                continue
            last_frame = itc.frame.copy()

        _, jpeg = cv2.imencode('.jpg', last_frame, [cv2.IMWRITE_JPEG_QUALITY, sc.jpeg_quality])

        #itc.fps_value = 1 / (time.perf_counter() - gen_count)
        #itc.save_random = int(itc.fps_value * sc.save_rand_min * 60)
        gen_count = time.perf_counter()

        try:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
        except Exception as e:
            server.logger.warning(f"client disconnected: {e}")
            break


@server.context_processor
def serange():

    return dict(title = sc.page_title)


@server.route('/feed')
def feed():

    return Response(generation(), mimetype = 'multipart/x-mixed-replace; boundary=frame')


@server.route('/source_code')
def access_source_code():
    """ route this file hilited """
    formatter = HtmlFormatter(style = 'native', full = True, cssclass = "codehilite")
    try:

        file_path = os.path.abspath(__file__)
        with open(file_path, "r") as f:

            src = f.read()
        size = len(src.splitlines())
        # escaped_code = escape(src)
        hi_code = highlight(src, PythonLexer(), formatter)
        return render_template('code.html', code = hi_code, size = size)
    except Exception as e:
 
        server.logger.error(f"error while reading source code: {e}")
        return f"error: {e}", 500


@server.route('/', methods = ['GET'])
def index():

    audio_files = []
    if os.path.exists(sc.audio_dir):

        list_dir = os.listdir(sc.audio_dir)
        audio_files =  [f for f in list_dir if f.endswith(".mp3")]
    else:

        return "maintenance", 200
    try:

        return render_template('main.html', audio_files=audio_files)
    except Exception as e:

        return f"error: {e}"


@server.route('/static/sound/<filename>', methods = ['GET'])
def serve_audio(filename):

    itc.new_message(filename) # does not work
    return send_from_directory('/static/audio', filename)


@server.route('/sitemap.xml', methods=['GET'])
def sitemap():
    pages = []
    last_modified = itc.get_time("%Y-%m-%d")

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
    else:

        with bs_lock: client_set.add(ip)


@server.after_request
def after_request(response): return response


@server.route('/src')
def get_text():

    return jsonify({"text": lorem.paragraph()})


@server.route('/client_counter')
def get_clients():

    with bs_lock: return f"{len(client_set)}"


def run_server():

    serve = WSGIServer(("0.0.0.0", sc.flask_port), server)
    serve.serve_forever()


if __name__ == '__main__':

    pool = Pool(sc.gevent_workers)
    
    server.logger.info(f"starting flask server at {itc.get_time()}")
    pool.spawn(debug_wrapper, run_server)
    server.logger.info("starting stream")
    pool.spawn(debug_wrapper, read_stream)
    server.logger.info("starting keyboard listener")
    pool.spawn(debug_wrapper, keyboard_listener)
    while itc.running: gevent.sleep(0.5)
    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    server.logger.warning("stop signal detected\n")
    pool.kill()
    server.logger.info("all tasks stopped\n")
