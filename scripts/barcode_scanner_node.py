#!/usr/bin/env python
from io import BytesIO
from time import sleep
from picamera import PiCamera
from PIL import Image
import zbar
import getpass
import requests
from requests_ntlm import HttpNtlmAuth
import untangle
import rospy
from std_msgs.msg import Float32
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import Int32
from sensor_msgs.msg import CompressedImage
from std_srvs.srv import Trigger
from barcode_scanner.srv import *
from recordtype import recordtype
import signal
import sys
import threading
import xml.etree.ElementTree as ET

def scan_barcode(req, camera, imagePub):	
	# Display camera view
#	camera.start_preview()
	
	# create a reader
	scanner = zbar.ImageScanner()

	# configure the reader
	scanner.parse_config('enable')
	
	scanStr = ""
	while True:
		# Capture frame from camera
		stream = BytesIO()
		camera.capture(stream, format='jpeg', use_video_port=True)
		
		# "Rewind" the stream to the beginning so we can read its content
		stream.seek(0)
		
		compImg = CompressedImage();
		compImg.format = 'jpeg';
		compImg.data = stream.read();
		imagePub.publish(compImg);
		
		stream.seek(0)
		# Pass image to zbars
		pil = Image.open(stream)
		
		
		pil = pil.convert('L')
		width, height = pil.size
		raw = pil.tobytes()
		image = zbar.Image(width, height, 'Y800', raw)
		scanner.scan(image)
		
		# Extract results
		for symbol in image:
			scanStr = symbol.data
			break
		if scanStr != "":
			break
		sleep(0.01)
	# Tidy up scannign resources
	del(image)
	del(stream)
	camera.stop_preview()
	return ScanBarcodeResponse(scanStr)

# Main function
def barcode_scanner_node():
	# Initialise some things
	rospy.init_node('barcode_scanner_node', anonymous=True)
	camera = PiCamera(resolution = (480,320), framerate=30)
	imagePub = rospy.Publisher('image/compressed', CompressedImage, queue_size=1)
	s = rospy.Service('scan_barcode', ScanBarcode, lambda req: scan_barcode(req, camera, imagePub));
	rospy.spin()

# ROS main
if __name__ == '__main__':
	try:
		barcode_scanner_node()
	except rospy.ROSInterruptException:
		pass
