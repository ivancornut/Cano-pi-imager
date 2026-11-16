from flask import Flask, render_template, redirect, request
from picamera2 import Picamera2
from PIL import Image
from gpiozero import LED
import os
import re
import threading
import time

green_led = LED(27)
red_led = LED(22)

picam2 = Picamera2()

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PICTURES_DIR = os.path.join(BASE_DIR, "pictures") # full resolution hemispherical pictures
PREVIEW_DIR = os.path.join(BASE_DIR, "static", "pictures") # small images shown on the webpage
os.makedirs(PICTURES_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

FULL_SIZE = (4056, 3040) # HQ camera full resolution
PREVIEW_SIZE = (1014, 760) # downscaled whole image for the webpage
FOCUS_CROP = 400 # side (in full resolution pixels) of the centre crop used to check focus

# exposure steps: 3 steps per stop means each click changes brightness by ~26 %,
# which is perceived as an even (linear) change. Set to 1 for full stops (x2 / /2).
STEPS_PER_STOP = 3
MIN_EXPOSURE = 100 # us
MAX_EXPOSURE = 200000000 # us (200 s)

# only one camera operation at a time (double taps / several phones)
camera_lock = threading.Lock()

# dictionnary that can be used to pass global variables
# since it is mutable python data structure
pic = {'image_link': "static/pictures/example.jpeg",
	'focus_link': None,
	'picture_string': "Example file"}

status = {'Current_data_id': 'Farmer-Bloc-Trat-ID'}

# exposure settings: ExposureTime None means auto, otherwise manual.
# BaseExposure is the value found by auto exposure, Steps the offset from it.
exposure = {'ExposureTime': None, 'AnalogueGain': None, 'BaseExposure': None, 'Steps': 0}

def sanitize_id(text):
	"""Make the ID safe to use in a file name (no slashes, newlines, spaces...)."""
	text = (text or "").strip()
	text = re.sub(r'[^A-Za-z0-9._-]+', '-', text).strip('-.')
	return text or "no-ID"

def ev_string():
	"""Human readable exposure offset relative to auto, e.g. '+2/3 EV'."""
	steps = exposure['Steps']
	if steps == 0:
		return "0 EV"
	sign = "+" if steps > 0 else "-"
	whole, rest = divmod(abs(steps), STEPS_PER_STOP)
	parts = []
	if whole:
		parts.append(str(whole))
	if rest:
		parts.append(str(rest) + "/" + str(STEPS_PER_STOP))
	return sign + " ".join(parts) + " EV"

def exposure_controls():
	"""Camera controls matching the current exposure settings."""
	if exposure['ExposureTime'] is None:
		return {"AeEnable": True}
	return {"AeEnable": False,
		"ExposureTime": int(exposure['ExposureTime']),
		"AnalogueGain": exposure['AnalogueGain']}

def capture(save_path=None):
	"""Capture one full resolution frame with the current exposure settings.
	Optionally save it to save_path, then write the downscaled preview and the
	centre focus crop for the webpage. Returns the frame metadata."""
	controls = exposure_controls()
	config = picam2.create_still_configuration(main={"size": FULL_SIZE}, controls=controls)
	picam2.configure(config)
	picam2.start()
	try:
		# auto exposure needs time to converge, manual settings are applied at start
		time.sleep(2 if controls["AeEnable"] else 1)
		req = picam2.capture_request()
		try:
			if save_path is not None:
				req.save("main", save_path) # full resolution file
			metadata = req.get_metadata()
			img = req.make_image("main")
		finally:
			req.release()
	finally:
		picam2.stop()

	# whole image, downscaled
	img.resize(PREVIEW_SIZE, Image.BILINEAR).save(os.path.join(PREVIEW_DIR, "temp.jpeg"), quality=85)
	# centre crop at full resolution (1:1 pixels) to check focus
	w, h = img.size
	left, top = (w - FOCUS_CROP) // 2, (h - FOCUS_CROP) // 2
	img.crop((left, top, left + FOCUS_CROP, top + FOCUS_CROP)).save(
		os.path.join(PREVIEW_DIR, "focus.jpeg"), quality=92)

	# version query string so the browser does not show a cached old image
	v = str(int(time.time() * 1000))
	pic['image_link'] = "static/pictures/temp.jpeg?v=" + v
	pic['focus_link'] = "static/pictures/focus.jpeg?v=" + v
	return metadata

def run_camera(func):
	"""Run func while holding the camera lock. Returns False if the camera was busy."""
	if not camera_lock.acquire(blocking=False):
		pic['picture_string'] = "Camera busy, please wait and retry"
		return False
	try:
		func()
	except Exception as e:
		print("Camera error:", repr(e))
		pic['picture_string'] = "Camera error: " + str(e)
	finally:
		camera_lock.release()
	return True

@app.route('/', methods=['GET', 'POST'])
def index():
	# Main page
	if request.method == 'POST':
		# Retrieve the text from the textarea
		status['Current_data_id'] = sanitize_id(request.form.get('textarea'))
		# Print the text in terminal for verification
		print(status['Current_data_id'])
		return redirect('/')

	timeString = time.strftime("%Y-%m-%d %H:%M") # display currenttime on mainpage
	if exposure['ExposureTime'] is None:
		exp_str = "Auto"
	else:
		exp_str = (ev_string() + " (" + str(int(exposure['ExposureTime'])) + " us, gain "
			+ str(round(exposure['AnalogueGain'], 1)) + ")")
	templateData = {'title': 'Camera', 'time': timeString,
		'picture': pic['picture_string'], 'ImageLink': pic['image_link'],
		'FocusLink': pic['focus_link'],
		'current_id': status['Current_data_id'], 'exposure_info': exp_str}

	return render_template('index.html', **templateData)

@app.route('/<deviceName>/<action>')
def action(deviceName, action):
	if deviceName == 'Green-led':
		led = green_led
		if action == 'on':
			led.on()
		elif action == 'off':
			led.off()
	if deviceName == 'Camera':
		if action == 'take':
			def take():
				red_led.on() # turn on red led
				try:
					dt = time.strftime("%d-%m-%y_%H-%M-%S") # get current RPi time
					path = os.path.join(PICTURES_DIR, "hemisph_" + status['Current_data_id'] + "_" + dt + ".jpeg")
					capture(save_path=path) # full resolution file + previews from the same frame
					pic['picture_string'] = "Acquired picture at: " + dt
				finally:
					red_led.off() # turn off red led
			run_camera(take)
	return redirect('/') # go back to main page

def set_exposure_steps(steps):
	"""Apply an exposure offset (in 1/STEPS_PER_STOP stops) from the auto value."""
	base = exposure['BaseExposure']
	value = base * 2 ** (steps / STEPS_PER_STOP)
	if value > MAX_EXPOSURE or value < MIN_EXPOSURE:
		return # limit reached, keep current setting
	exposure['Steps'] = steps
	exposure['ExposureTime'] = int(round(value))

@app.route('/exposure/auto')
def exposure_auto():
	"""Take a preview with auto exposure and store the resulting settings."""
	def auto():
		exposure['ExposureTime'] = None
		exposure['AnalogueGain'] = None
		exposure['Steps'] = 0
		metadata = capture()
		# extract auto exposure result and store for future manual use
		exposure['ExposureTime'] = metadata['ExposureTime']
		exposure['AnalogueGain'] = metadata['AnalogueGain']
		exposure['BaseExposure'] = metadata['ExposureTime']
		pic['picture_string'] = "Auto exposure: " + str(exposure['ExposureTime']) + " us"
	run_camera(auto)
	return redirect('/')

def change_exposure(delta):
	if exposure['ExposureTime'] is None:
		return exposure_auto()
	def step():
		set_exposure_steps(exposure['Steps'] + delta)
		capture()
		pic['picture_string'] = "Exposure " + ev_string() + ": " + str(exposure['ExposureTime']) + " us"
	run_camera(step)
	return redirect('/')

@app.route('/exposure/increase')
def exposure_increase():
	"""One step brighter (1/STEPS_PER_STOP stop)."""
	return change_exposure(+1)

@app.route('/exposure/decrease')
def exposure_decrease():
	"""One step darker (1/STEPS_PER_STOP stop)."""
	return change_exposure(-1)

@app.route('/exposure/increase_big')
def exposure_increase_big():
	"""One full stop brighter (x2)."""
	return change_exposure(+STEPS_PER_STOP)

@app.route('/exposure/decrease_big')
def exposure_decrease_big():
	"""One full stop darker (/2)."""
	return change_exposure(-STEPS_PER_STOP)

if __name__ == '__main__':
	app.run(debug = False, host='0.0.0.0', port = 80) # 80 for direct http access
