# Cano-Pi-Imager
Leveraging a Raspberry Pi microcomputer and camera, a fisheye lens and a flask webapp to build a simple to use hemispherical photography setup. 

## Hemispherical photography
Leaves are the organs necessary for carbon assimilation and transpiration by plants. Consequently, estimating total leaf surface in forests is useful to understand their functionning. Hemispherical photography is one method that is used in environmental sciences to determine leaf area index (m² of leaves per m² of ground). Simply put, a camera with a fisheye lens is oriented vertically beneath the canopy and a series of pictures are taken. The pictures must ideally be taken when lighting conditions are diffuse (before sunrise or under heavy cloud cover) since the software used will separate leaves and sky in the images. Using mathematical relationships between viewing angles and obstruction of sky at said angles the software is able to calculate Plant area index (leaf area index + branches and trunk surfaces). More information on this method and others can be found [here](https://canopyphotography.wordpress.com/). 

## Implementation
### Hardware
We use a Raspberry Pi computer (3,4 or 5) combined with the RPi High Quality camera and a 180° fisheye lens from Arducam. The total setup approaches 150€ but price depends strongly on the raspberry pi model used.
Needed:
- A phone that will be used to connect to RPi the field and serve to display the webapp
- The RPi (3,3B+, 4, 5)
- A High Quality RPi cam
- A fisheye objective
- The right connector from camera to RPi

### Web app Software
A simple flask web app is used to control the raspberry pi camera from a phone or other device. From the webapp it is possible to set the prefix of the next series of images that will be taken. The app dyanmically displays the last image taken on the page as well as local time.

## Setup the RPi
My advice is to install the [raspbian lite os](https://www.raspberrypi.com/software/operating-systems/) to avoid wasting resources on a desktop when we only need to be able to display stuff on the webapp.
First download this repository in the folder of your choice. Then inside the repository folder create a pictures directory. This will be used to store the hemispherical photographies that you take. 
```shell
git clone https://github.com/ivancornut/Cano-pi-imager
cd Cano-pi-imager
mkdir pictures
```
Then install the python package flask:
```shell
sudo apt install python3-flask
```
### Simple one-time setup to test the app
Simply run the app:
```shell
sudo python3 app.py
```
This command should output camera information followed by: 
```shell
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:80
 * Running on http://192.168.62.150:80
Press CTRL+C to quit
```
Your ip address will be different than the one diplayed here (_192.168.65.150_). Use the ip address that is displayed by your app to connect to the webapp on your phone's browser.

### Setup for use in the field
For this part of the setup you will need a screen and keyboard connected to the RPi. You will also need the phone that you will be using in the field. 
#### Fixed IP address
First we will need to use a fixed ip address. This is necessary to ensure that once the RPi connects to your phone, you are able to know its local ip address without needing a screen. This local ip address is what you will enter in your phone's browser to access the Cano-Pi-imager webapp. The process is decribed [here](https://pimylifeup.com/raspberry-pi-static-ip-address/). First you will need to make sure that the Pi is connected to the hotspot of the phone that you will be using in the field. 
The run the following command:
```shell
ip r | grep default
```
This will output a line like this: 
```shell
default via 192.168.62.4 dev wlan0 proto dhcp src 192.168.62.115 metric 600
```
The first ip address is the address of your router (your phone in this case) and the second ip address is the current ip address of your RPi. 
The open _nmtui_. This command line GUI tool allows you to edit your connections.
1. Click on _Edit a connection_
2. Navigate and enter the phone's hotspot network
3. In the _IPv4 CONFIGURATION_ change _Automatic_ to _manual_
4. Navigate to _Show_
5. Enter the address you want in the _Addresses_. For example in my case, I chose: _192.168.62.140_
6. In _Gateway_ enter the ip address of the router
7. In DNS servers add _8.8.8.8_ (Google's DNS servers)
8. Navigate to _Ok_ at the bottom, then _Back_ and _Quit_

Then for these changes to take effect, run the following command:
```shell
sudo systemctl restart NetworkManager
```
Now your pi should always have the same ip address when you connect it to your field phone.
#### Automatic app startup
First we need to setup the app so it starts automatically on startup of the raspberry pi. For that we are going to stay simple and just use cron. I used inspiration from this good tutorial: [https://www.instructables.com/Raspberry-Pi-Launch-Python-script-on-startup/](https://www.instructables.com/Raspberry-Pi-Launch-Python-script-on-startup/)
First we make the launch script executable by changing rights:
```shell
chmod 775 launcher.sh
```
Then we create a logs directory for crontab logs
```shell
cd /home/pi
mkdir logs
```
Then we open the crontabl config file
```shell
sudo crontab -e
```
And we fill in the following line:
```shell
@reboot sh /home/pi/Documents/Cano-pi-imager/launcher.sh >/home/pi/logs/cronlog 2>&1
```
Then the script should run at each startup.


