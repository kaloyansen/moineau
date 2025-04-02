#!/usr/bin/env python
# real-time analysis and streaming video 
# code by Kaloyan Krastev kaloyansen@gmail.com
# music composed, orchestrated and conducted by Kaloyan Krastev 
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

from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

class SecureContext:
	""" secure context """
	def __init__(self, birdlives):
		""" load context """
		self.video_device   =     self.safe("VIDEO_DEVICE")
		self.log_file       =     self.safe("LOG_FILE")
		self.work_directory =     self.safe("FLASK_WORK_DIRECTORY")
		self.page_title     =     self.safe("PAGE_TITLE")
		self.secret_key     =     self.safe("FLASK_SECRET_KEY")
		self.fps_limit      = int(self.safe("FPS_LIMIT"))
		self.jpeg_quality   = int(self.safe("JPEG_QUALITY"))
		self.gevent_workers = int(self.safe("GEVENT_WORKERS"))
		self.flask_port     = int(self.safe("FLASK_PORT"))
		self.ban_count      = int(self.safe("IP_BAN_LIST_COUNT"))
		self.ban_seconds    = int(self.safe("IP_BAN_LIST_SECONDS"))
	def safe(self, var):
		""" let it be safe """
		good = os.getenv(var, 0)
		if not good:
			""" warn if not good """
			print(f"not good: cannot find {var}")
		return good
	def dump(self):
		""" print all """
		print()
		print('=' * 16, 'secure context', '=' * 16)
		for key, value in self.__dict__.items():
			""" print one """
			print(f"{key}: {value}")
		print('^' * 44)


class InterThreadCommunication:

	def __init__(self, font_name, font_size, frame_size):

		self.font_name = font_name
		self.font_size = font_size
		self.frame_size = frame_size
		self.raw = None
		self.frame = None
		self.running = True
		self.fps_value = 0
		self.count9 = 0
		self.new_message()
	def new_message(self, message = lorem.paragraph(), speed = 6):

		self.speed = speed
		self.x = frame_size_x
		self.text = message
		self.size = cv2.getTextSize(message, self.font_name, self.font_size, 1)[0]
		self.count = 0
	def new_frame(self):

		self.count += 1
		self.count9 += 1
		if self.count9 > 9: self.count9 = 0
		if self.x / self.size[0] + 1 < 0: self.x = self.frame_size - self.size[0] # not too complicated
		self.x -= self.speed
		if self.count > 111: self.new_message()

sc = SecureContext(166)

server = Flask(__name__, template_folder = f"{sc.work_directory}/static/template")
server.secret_key = sc.secret_key

os.makedirs(f"{sc.work_directory}/dataset/positives", exist_ok = True)
os.makedirs(f"{sc.work_directory}/dataset/negatives", exist_ok = True)
os.makedirs(f"{sc.work_directory}/ban", exist_ok = True)

cascade1 = cv2.CascadeClassifier(f"{sc.work_directory}/cascade/bird1.xml")
cascade2 = cv2.CascadeClassifier(f"{sc.work_directory}/cascade/bird2.xml")

if sc.log_file: logging.basicConfig(level = logging.INFO, encoding = 'utf-8', filename = f"{sc.log_file}")
else:           logging.basicConfig(level = logging.INFO, encoding = 'utf-8')

ip_ban = IpBan(ban_count = sc.ban_count, ban_seconds = sc.ban_seconds, persist = True, record_dir = f"{sc.work_directory}/ban")
ip_ban.init_app(server)
ip_ban.load_allowed()
ip_ban.load_nuisances()

wheel_state = 0
wheel_states = ['-', '/', '|', '\\']

frame_size_x = 640
frame_size_y = 480
frame_size_x = 320
frame_size_y = 240
font2 = cv2.FONT_HERSHEY_SIMPLEX

sleeping = 1e-2

AUDIO_LOC = '/static/audio'
AUDIO_DIR = f"{sc.work_directory}/static/audio"
FONT_SIZE = 0.4

itc = InterThreadCommunication(font2, FONT_SIZE, frame_size_x)
bs_lock = BoundedSemaphore()
client_set = set()

def debug_wrapper(func, *args):

	try: func(*args)
	except Exception as e: server.logger.error(f"error in {func.__name__}: {e}")


def is_not_ascii(mot):

	for c in mot:

		if 0 <= ord(c) <= 127:

			continue
		else:

			return True
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
				save_frame(itc.raw, "negatives")
			elif key == 'p':
				# save a positive frame
				save_frame(itc.raw, "positives")
			elif key == 'r':
				# reset command-line interfase
				os.system('reset')
		gevent.sleep(0.1)  # Yield control back to gevent


def save_frame(fr, label):

	filename = f"dataset/{label}/{int(time.time())}"
	filepath = f"{sc.work_directory}/{filename}.jpg"
	cv2.imwrite(filepath, fr)
	print(f"saved: {filepath}")
	itc.new_message(f" {filename}")
	print("standby")


def contrast(fr, text, position, font_scale):

	color = (22, 22, 22)
	outcolor = (222, 222, 222)
	thickness = 1
	outline = 1 #  cv2.LINE_AA
	cv2.putText(fr, text, (position[0] - 1, position[1] - 1), font2, font_scale, outcolor, outline, cv2.LINE_AA)
	cv2.putText(fr, text, (position[0] + 1, position[1] - 1), font2, font_scale, outcolor, outline, cv2.LINE_AA)
	cv2.putText(fr, text, (position[0] - 1, position[1] + 1), font2, font_scale, outcolor, outline, cv2.LINE_AA)
	cv2.putText(fr, text, (position[0] + 1, position[1] + 1), font2, font_scale, outcolor, outline, cv2.LINE_AA)
	cv2.putText(fr, text, position, font2, font_scale, color, thickness, cv2.LINE_AA)


def label_frame(fr):

	last_modified = datetime.datetime.now().strftime("%Y-%m-%d")
	maintenant = datetime.datetime.now()
	timestamp = maintenant.strftime("%H:%M:%S")
	timestamp = f"{timestamp}.{itc.count9}"
	video_title = f" {sc.page_title}{itc.fps_value:6.2f} Hz"
	y_bottom = frame_size_y - itc.size[1]
	x_right = frame_size_x - 70

	contrast(                      fr, video_title,      (0,                                  12), FONT_SIZE)
	contrast(                      fr, timestamp,        (x_right,                            12), FONT_SIZE)
	contrast(                      fr, itc.text,         (itc.x,                        y_bottom), FONT_SIZE)
	if itc.x < 0: contrast(        fr, itc.text,         (frame_size_x + itc.x,         y_bottom), FONT_SIZE)
	return fr


def analyze_frame(fr):

	global wheel_state, wheel_states

	gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
	sparrow1 = cascade1.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 5, minSize=(30, 30))
	sparrow2 = cascade2.detectMultiScale(gray, scaleFactor = 1.1, minNeighbors = 5, minSize=(30, 30))
#	if len(sparrow) > 0:

#		save_frame(fr, "positives")
#	else:

#		save_frame(fr, "negatives")
	font = cv2.FONT_HERSHEY_SIMPLEX
	wheel = wheel_states[wheel_state]
	wheel_state = (wheel_state + 1) % len(wheel_states)

	spindex = 0
	for (x, y, w, h) in sparrow1:

		cv2.rectangle(fr, (x, y), (x + w, y + h), (255, 255, 0), 2)
		cv2.putText(fr, f"{spindex} {wheel}", (x, y + 12), font, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
		spindex += 1
	for (x, y, w, h) in sparrow2:

		cv2.rectangle(fr, (x, y), (x + w, y + h), (255, 255, 0), 2)
		cv2.putText(fr, 'bird', (x, y - 2), font, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
		
	return fr


def process_frame(fr):

	analyzed_frame = analyze_frame(fr)
	labeled_frame = label_frame(analyzed_frame)
	return labeled_frame


def read_stream():

	server.logger.info(f"wait while capturing {sc.video_device} ...")
	cap = cv2.VideoCapture(sc.video_device)
	cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
	if not cap.isOpened():

		print(f"... cannot capture {sc.video_device}")
		itc.running = False
	else:

		print(f"... captured {sc.video_device}")
		itc.running = True
	read_count = time.perf_counter()
	while itc.running:

		if time.perf_counter() - read_count < 1. / sc.fps_limit:

			gevent.sleep(sleeping)
			continue

		success, raw_frame = cap.read()
		if not success:

			print(f"cannot read {sc.video_device}")
			read_count = time.perf_counter()
			gevent.sleep(1)
			continue
		raw_frame_resized = cv2.resize(raw_frame, (frame_size_x, frame_size_y))
		raw_frame_resized_copy = raw_frame_resized.copy()
		processed_frame = process_frame(raw_frame_resized_copy)
		with bs_lock:

			itc.raw = raw_frame_resized
			itc.frame = processed_frame # .copy()

		itc.new_frame()
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
			#if last_frame is not None and np.array_equal(itc.frame, last_frame):

				#server.logger.warning("frame repeats")
			#	 gevent.sleep(sleeping)
			#	 continue

			last_frame = itc.frame.copy()

		_, jpeg = cv2.imencode('.jpg', last_frame, [cv2.IMWRITE_JPEG_QUALITY, sc.jpeg_quality])

		itc.fps_value = 1 / (time.perf_counter() - gen_count)
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

#		return "you have been added to the black list", 403
	# elif ip_ban.is_banned(client_ip):

	#	 server.logger.warning(f"{client_ip} is in the list of banned")
	#	 return "you are already in the black list", 403
	else:

		with bs_lock:

			client_set.add(ip)


@server.after_request
def after_request(response): return response

@server.route('/src')
def get_text():

	return jsonify({"text": lorem.paragraph()})


@server.route('/client_counter')
def get_clients():

	with bs_lock:

		return f"{len(client_set)}"


def run_server():

	serve = WSGIServer(("0.0.0.0", sc.flask_port), server)
	serve.serve_forever()


if __name__ == '__main__':

	sc.dump()
	pool = Pool(sc.gevent_workers)

	timestamp = datetime.datetime.now().strftime("%H:%M:%S")
	server.logger.info(f"starting flask server at {timestamp}")

	pool.spawn(debug_wrapper, run_server)
	server.logger.info("starting stream")

	pool.spawn(debug_wrapper, read_stream)
	server.logger.info("starting keyboard listener")

	pool.spawn(debug_wrapper, keyboard_listener)
	# server.logger.info(f"ban_count {ip_ban.ban_count} ban_seconds {ip_ban.ban_seconds}")
	#server.logger.info(f"ip_ban_list ({len(ip_ban._ip_ban_list)})")
	#server.logger.info("\nip_ban_list: ".join(ip_ban._ip_ban_list))
	print("keyboard commands:")
	print("'n' to save a negative image")
	print("'p' to save a positive image")
	print("'q' to quit the application")
	print("standby")

	while itc.running:

		gevent.sleep(0.5)
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	server.logger.warning("stop signal detected\n")
	pool.kill()
	server.logger.info("all tasks stopped\n")
