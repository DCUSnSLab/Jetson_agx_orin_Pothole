#!/usr/bin/python
#
# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import sys
import time


import argparse
import ctypes


import copy
import numpy as np

import csv
import time
from datetime import date
from datetime import datetime


import shutil
from jetson_utils import videoSource, videoOutput, Log, cudaAllocMapped, cudaConvertColor, cudaDeviceSynchronize, \
    cudaToNumpy, cudaFromNumpy
import jetson_inference

# excel
from ExcelExport import Saver

# gps
import serial
import datetime

from ublox_gps import UbloxGps

import threading

import os
import signal
import sys

output_images =[]
start_time = ""
import cv2
from numpysocket import NumpySocket

def sigterm_handler(signum, frame):
    # global exit_program
    # print("exit_program...")
    # exit_program = True
    # print("success_program...")
    global start_time
    change_time = start_time
    # filename = str(sys.argv[1]) + str(time.strftime("%Y-%m-%d_%H:%M:%s"))
    print("Received SIGTERM signal. Cleaning up...")

    ex_time = time.strftime("%Y-%m-%d_%H-%M:%S")

    # Use the global variable in the directory renaming
    os.rename(f"./Result/full_frame_detect/{change_time}", f"./Result/full_frame_detect/{ex_time}")

    # Save Excel file
    Saver.save_to_excel()
    print("Excel saved successfully.")
    os._exit(os.EX_OK)

# gps
port = serial.Serial('/dev/ttyACM0', baudrate=115200, timeout=1)
gps = UbloxGps(port)

def gps_data_thread():
    global geo
    while not exit_program:  # 스레드를 우아하게 종료하기 위한 플래그 사용
        try:
            geo = gps.geo_coords() # GPS 최신화
        except Exception as e:
            print(f"GPS 데이터 검색 중 오류 발생: {e}")


signal.signal(signal.SIGTERM, sigterm_handler)


# Start GPS data retrieval thread
exit_program = False
gps_thread = threading.Thread(target=gps_data_thread)
gps_thread.start()



# parse the command line
parser = argparse.ArgumentParser(description="Segment a live camera stream using an semantic segmentation DNN.",
                                 formatter_class=argparse.RawTextHelpFormatter, epilog=jetson_inference.segNet.Usage())

parser.add_argument("input", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="fcn-resnet18-cityscapes-1024x512",
                    help="pre-trained model to load, see below for options")
# parser.add_argument("from_path", type=str, help="Path to save data file")
# parser.add_argument("roi_box[0]", type=str, help="ROI box coordinates as 'start_x,start_y,end_x,end_y'")
# parser.add_argument("roi_box[1]", type=str, help="ROI box coordinates as 'start_x,start_y,end_x,end_y'")
parser.add_argument('--x_coord', type=int, help='X coordinate from roi_box')
parser.add_argument('--y_coord', type=int, help='Y coordinate from roi_box')
parser.add_argument('--reversed', type=int, help='img reversed')

parser.add_argument("--filter-mode", type=str, default="point", choices=["point", "linear"],
                    help="filtering mode used during visualization, options are:\n  'point' or 'linear' (default: 'linear')")
parser.add_argument("--ignore-class", type=str, default="void",
                    help="optional name of class to ignore in the visualization results (default: 'void')")
parser.add_argument("--alpha", type=float, default=99.0,
                    help="alpha blending value to use during overlay, between 0.0 and 255.0 (default: 175.0)")
parser.add_argument("--camera", type=str, default="/dev/video0",
                    help="index of the MIPI CSI camera to use (e.g. CSI camera 0)\nor for VL42 cameras, the /dev/video device to use.\nby default, MIPI CSI camera 0 will be used.")
# parser.add_argument("--width", type=int, default=1920, help="desired width of camera stream (default is 1920 pixels)")
# parser.add_argument("--height", type=int, default=1080, help="desired height of camera stream (default is 1080 pixels)")

parser.add_argument("--width", type=int, default=1280, help="desired width of camera stream (default is 1280 pixels)")
parser.add_argument("--height", type=int, default=720, help="desired height of camera stream (default is 720 pixels)")
# parser.add_argument("--width", type=int, default=1024, help="desired width of camera stream (default is 1280 pixels)")
# parser.add_argument("--height", type=int, default=512, help="desired height of camera stream (default is 720 pixels)")


try:
    opt = parser.parse_known_args()[0]
except:
    parser.print_help()
    sys.exit(0)

# load the segmentation network
net = jetson_inference.segNet(opt.network, sys.argv)

# roi_box[0] = list(map(int, opt.roi_box[0].split(','))) if opt.roi_box else []
x_coord = opt.x_coord
y_coord = opt.y_coord
is_reversed = opt.reversed


# set the alpha blending value
net.SetOverlayAlpha(opt.alpha)

# the mask image is half the size
half_width = int(opt.width / 2)
half_height = int(opt.height / 2)

# allocate the output images for the overlay & mask
img_overlay = cudaAllocMapped(opt.width * opt.height * 4 * ctypes.sizeof(ctypes.c_float))
img_mask = cudaAllocMapped(half_width * half_height * 4 * ctypes.sizeof(ctypes.c_float))

# img_overlay = jetson_utils.cudaAllocMapped(width=opt.width, height=opt.height, format='rgb32f')
# img_mask = jetson_utils.cudaAllocMapped(width=half_width, height=half_height, format='rgb32f')

# camera = videoSource(f"{opt.camera}?width={opt.width}&height={opt.height}")

'''
# 현재 카메라 해상도 얻기
c_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
c_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
'''

count = 0
pothole_count = 1
temp = False
# process frames until user exits

# csvfile = open("/mnt/e7edbf37-e345-4c57-9b53-d075f037a001/jetson-inference/build/aarch64/bin/data.csv", "w")
# csvwriter = csv.writer(csvfile)

# delete & make dir
# if (os.path.isdir("./Result") == True):
#     shutil.rmtree("./Result")
if (os.path.isdir("./Result") == False):
    os.mkdir("./Result")

# if (os.path.isdir("./Result/log") == True):
#     shutil.rmtree("./Result/log")
# if (os.path.isdir("./Result/log") == False):
#     os.mkdir("./Result/log")


start_time = time.strftime("%Y-%m-%d_%H-%M:%S")

if (os.path.isdir("./Result/full_frame_detect") == False):
    os.mkdir("./Result/full_frame_detect")

if (os.path.isdir(f"./Result/full_frame_detect/{start_time}") == False):
    os.mkdir(f"./Result/full_frame_detect/{start_time}")


# time

# import cv2

# create the camera and display
# camera = jetson_utils.gstCamera(opt.width, opt.height, opt.camera)
camera = videoSource('/dev/video0')

# display = jetson_utils.glDisplay()
display = videoOutput('display://0', argv=sys.argv)

roi_x = 1024
roi_y = 512

x1 = x_coord
y1 = y_coord
x2 = x_coord + 1024
y2 = y_coord + 512
with NumpySocket() as s:
    s.connect(("localhost", 9999))
    while True:
        # now = time.localtime()
        now = datetime.datetime.now()

        cimg = camera.Capture()
        if cimg is None:
            print('img error')
            continue
        
        #bgr_img = cudaAllocMapped(width=cimg.width, height=cimg.height, format="rgb8")
        #cudaConvertColor(cimg, bgr_img)
        #coutput = cudaToNumpy(bgr_img)
        #cudaDeviceSynchronize()
        #print('coutput-',coutput.shape)
        #s.sendall(coutput)

        bgr_img = cudaAllocMapped(width=cimg.width, height=cimg.height, format='rgba32f')

        cudaConvertColor(cimg, bgr_img)

        # print('BGR image: ')
        # print(bgr_img)

        # make sure the GPU is done work before we convert to cv2
        cudaDeviceSynchronize()

        # convert to cv2 image (cv2 images are numpy arrays)
        cv_img = cudaToNumpy(bgr_img)

        resize_img = cv2.resize(cv_img, dsize=(1920, 1080), interpolation=cv2.INTER_AREA)

        # if is_reversed == 0:
        #     resize_img = cv2.flip(resize_img, 0)  # 0 means vertical flip
        # o_width = cv_img.shape[1]
        # o_height = cv_img.shape[0]

        o_width = resize_img.shape[1]
        o_height = resize_img.shape[0]

        # ROI crop
        # frame = cv_img[y1:y2, x1:x2]
        frame = resize_img[y1:y2, x1:x2]
        roi = None
        # 왼쪽 위: (x1,y2) 오른쪽 위: (x2, y2) 왼쪽 밑: (x1,y1) 오른쪽 및: (x2,y1)
        while (x1 < 0 or x2 > 1920 or y1 < 0 or y2 > 1080):
            # frame에서 ROI Crop
            # roi = cv_img[y1:y2, x1:x2]
            roi = resize_img[y1:y2, x1:x2]

            if (x2 > 1920):
                x1 = x1 - (x2 - 1920)
                roi = cv_img[y1:y2, x1:1920]
            if (x1 < 0):
                x1 = abs(x1)
                x2 = x2 + x1
                roi = cv_img[y1:y2, 0:x2]
            if (y2 > 1080):
                y1 = y1 - (y2 - 1920)
                roi = cv_img[y1:1920, x1:x2]
            if (y1 < 0):
                y1 = abs(y1)
                y2 = y2 + y1
                roi = cv_img[0:y2, x1:x2]

            frame = roi

            break;

        frame_rgba = frame.astype(np.float32)
        width = frame.shape[1]
        height = frame.shape[0]
        img = cudaFromNumpy(frame_rgba)


        # process the segmentation network
        net.Process(img, width, height, opt.ignore_class)

        # generate the overlay and mask
        net.Overlay(img_overlay, width, height, opt.filter_mode)
        net.Mask(img_mask, int(width / 2), int(height / 2), opt.filter_mode)

        # print(img_overlay)
        img_2 = cudaToNumpy(img_overlay, width, height, 4)
        img_3 = cv2.cvtColor(img_2, cv2.COLOR_RGBA2BGR)
        img_4 = cv2.cvtColor(img_2, cv2.COLOR_RGBA2RGB)

        # print(width, height)
        omask = cudaToNumpy(img_mask, int(width / 2), int(height / 2), 4)
        img_mask2 = cv2.cvtColor(omask, cv2.COLOR_RGBA2BGR)

        # mask copy
        cmask = img_mask2.copy()
        # mask : bgr -> grayscale
        mask_gray = cv2.cvtColor(cmask, cv2.COLOR_BGR2GRAY)
        # binary : less than 100 -> 0
        ret, mask_thres = cv2.threshold(mask_gray, 0, 255, cv2.THRESH_BINARY)
        # cv2.imshow("d", img_3[0:50,0:50])

        mask_thres = mask_thres.astype(np.uint8)

        # find coutour's vertex
        contours, hierarchy = cv2.findContours(mask_thres, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        # draw vertex, green
        cv2.drawContours(mask_thres, contours, -1, (0, 255, 0), 4)
        # draw vertex, circle, blue

        for i in contours:
            for j in i:
                cv2.circle(mask_thres, tuple(j[0]), 1, (255, 0, 0), -1)

        # find center
        # c0 = contours[0]count
        for c in contours:
            M = cv2.moments(c)
            # print(M,type(M))

            if (M['m00'] > 0):
                cx = int(M["m10"] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                # print("found something : (" + str(cx) + ", " + str(cy) + ")")
                cv2.rectangle(mask_thres, (325, 240), (100, 140), (255, 0, 0), 3)
                cv2.circle(mask_thres, (cx, cy), 1, (0, 0, 0), -1)

                # cv2.imwrite("./Result/log/" + str(count) + ".jpg", mask_thres) # log 결과 파일

                # mb, mg, mr = img_mask2[cx, cy]
                mb, mg, mr = img_mask2[cy, cx]
                value = max(mb, mg, mr)
                if value > 0 and value == mr:  # class 별 색상 찾기
                    temp = True
                    # GPS
                    longitude = geo.lon
                    latitude = geo.lat

                    # print("{:2}".format(str(pothole_count)) + " detection " + "(" + str(cx * 2) + ", " + str(cy * 2) + ") frame : " + str(count))
                    # img_name = str(now.year) + str(now.month) + str(now.day) + str(now.hour) + str(now.minute) + str(
                    #     now.second)
                    # 초의 분을 나타내기 위한 코드
                    current_time = time.time()

                    # Extract seconds and milliseconds
                    seconds = int(current_time)
                    milliseconds = int((current_time - seconds) * 1000)

                    # Format the time string including minutes, seconds, and milliseconds with three decimal places
                    formatted_time = time.strftime("%Y-%m-%d_%H:%M:%S.{:03d}", time.localtime(seconds))

                    # Include the milliseconds in the formatted string
                    formatted_time_with_milliseconds = formatted_time.format(milliseconds)

                    img_name = formatted_time_with_milliseconds
                    #print(img_name)

                    # Excel 데이터 추가
                    Saver.add_data(img_name, latitude, longitude)

                    pothole_count += 1
                    break

        # bgr img
        # output = cudaFromNumpy(img_3)
        if (temp == False):
            output_img = cv2.rectangle(resize_img, (x1, y1), (x2, y2), (0, 255, 0), 3)
            output_resize = cv2.resize(output_img, dsize=(1280, 720), interpolation=cv2.INTER_AREA)
            # output = cudaFromNumpy(output_img)
            output = cudaFromNumpy(output_resize)

        else:
            output_img = cv2.rectangle(resize_img, (x1, y1), (x2, y2), (255, 0, 0), 3)
            output_img[y1:y2, x1:x2] = img_2
            output_resize = cv2.resize(output_img, dsize=(1280, 720), interpolation=cv2.INTER_AREA)
            # output = cudaFromNumpy(output_img)
            output = cudaFromNumpy(output_resize)
            # output_img = cv2.cvtColor(output_img, cv2.COLOR_RGBA2BGR)
            output_img = cv2.cvtColor(output_resize, cv2.COLOR_RGBA2BGR)


            Pothole_img = f"{img_name}.jpg"
            cv2.imwrite(f"./Result/full_frame_detect/{start_time}/{Pothole_img}", output_img)
            temp = False

        # display.BeginRender()
        # print(type(img_overlay))
        #display.Render(output)
        #output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
        output_resize = output_resize.astype(np.uint8)
        output_resize = cv2.cvtColor(output_resize, cv2.COLOR_BGR2RGB)
        # if is_reversed == 0:
        #     output_resize = cv2.flip(output_resize, 0)
        s.sendall(output_resize)
        # display.Render(img_mask, width/2, height/2, width)
        # display.EndRender()
        count = count + 1
        if not camera.IsStreaming() or not display.IsStreaming():
            break

exit_program = True
gps_thread.join()  # GPS 스레드가 완료될 때까지 기다림

