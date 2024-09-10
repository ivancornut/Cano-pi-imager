from flask import Flask, render_template, redirect, request
from picamera2 import Picamera2, Preview
import datetime
from gpiozero import LED
import time

green_led = LED(27)
red_led = LED(22)

picam2 = Picamera2()

app = Flask(__name__)

# dictionnary that can be used to pass global variables
# since it is mutable python data structure
pic = {'image_link':"static/pictures/example.jpeg",
'picture_string':"Example file"}

status = {'Current_data_id':'Farmer-Bloc-Trat-ID'}

@app.route('/', methods=['GET', 'POST'])
def index():
	# Main page
	timeString = time.strftime("%Y-%m-%d %H:%M") # display currenttime on mainpage
	templateData = {'title' : 'Camera', 'time': timeString,
	'picture':pic['picture_string'], 'ImageLink':pic['image_link'],
	'current_id':status['Current_data_id']}
	
	if request.method == 'POST': 
		# Retrieve the text from the textarea 
		status['Current_data_id'] = request.form.get('textarea') 
		# Print the text in terminal for verification 
		print(status['Current_data_id'])
		return redirect('/')
	
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
		led = red_led
		if action == 'take':
			led.on() # turn on red led
			# setup the camera configurations
			main_cam_config = picam2.create_still_configuration(main={"size":(4056,3040)}) # hires config
			disp_cam_config = picam2.create_still_configuration(main={"size":(640,480)}) # lores config
			# start with main configuration
			picam2.configure(main_cam_config)
			picam2.start()
			dt = time.strftime("%d-%m-%y_%H-%M-%S") # get current RPi time 
			picam2.capture_file("pictures/hemisph_"+status['Current_data_id']+"_"+dt+".jpeg") # capture full resolution file
			picam2.switch_mode(disp_cam_config) # switch to lores for display on webpage
			picam2.capture_file("static/pictures/temp.jpeg") # capture lores file for preview
			picam2.stop()
			
			pic['image_link'] = "static/pictures/temp.jpeg" # link so main page can display image
			pic['picture_string'] = "Acquired picture at: " + dt 
			
			led.off() # turn off red led
	return redirect('/') # go back to main page

if __name__ == '__main__':
	app.run(debug = False, host='0.0.0.0', port = 80) # 80 for direct http access


