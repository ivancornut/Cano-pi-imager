# Cano-Pi-Imager
Leveraging a Raspberry Pi microcomputer and camera, a fisheye lens and a flask webapp to build a simple to use hemispherical photography setup. 

## Hemispherical photography
Leaves are the organs necessary for carbon assimilation and transpiration by plants. Consequently, estimating total leaf surface in forests is useful to understand their functionning. Hemispherical photography is one method that is used in environmental sciences to determine leaf area index (m² of leaves per m² of ground). Simply put, a camera with a fisheye lens is oriented vertically beneath the canopy and a series of pictures are taken. The pictures must ideally be taken when lighting conditions are diffuse (before sunrise or under heavy cloud cover) since the software used will separate leaves and sky in the images. Using mathematical relationships between viewing angles and obstruction of sky at said angles the software is able to calculate Plant area index (leaf area index + branches and trunk surfaces). More information on this method and others can be found [here](https://canopyphotography.wordpress.com/). 

## Implementation
### Hardware
We use a Raspberry Pi computer (3,4 or 5) combined with the RPi High Quality camera and a 180° fisheye lens from Arducam. The total setup approaches 150€ but price depends strongly on the raspberry pi model used.

### Web app Software
A simple flask web app is used to control the raspberry pi camera from a phone or other device. From the webapp it is possible to set the prefix of the next series of images that will be taken. The app dyanmically displays the last image taken on the page as well as local time.

### Setup the RPi
#### Simple one-time setup to test the app
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
Finally simply run the app:
```shell
python3 app.py
```
#### Setup for use in the field
First we need to setup the app so it starts automatically on startup of the raspberry pi. For that we are going to stay simple and just use cron.
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
