import os
import sys
import numpy as np
from matplotlib import pyplot as plt
import cv2
import time

from BasicDemo import *
from CamOperation_class import *

from root import *
os.chdir(root + "\\Imports")
sys.path.append(root + "\\Imports")
from MvCameraControl_class import *
from PyQt5.QtWidgets import *



# Ideal params for MV-CE200-10UC
# FR = 19 E = 2.8e4 - 1 G = 0

# Ideal params for MV-CA060-10GC
# FR = E = G = 



def ToHexStr(num):
    chaDic = {10: 'a', 11: 'b', 12: 'c', 13: 'd', 14: 'e', 15: 'f'}
    hexStr = ""
    if num < 0:
        num = num + 2 ** 32
    while num >= 16:
        digit = num % 16
        hexStr = chaDic.get(digit, str(digit)) + hexStr
        num //= 16
    hexStr = chaDic.get(num, str(num)) + hexStr
    return hexStr



def CHW2HWC(img): # convert a single image array from (C, H, W) channel-first formatting to (H, W, C) channel-last, input = img (ndarray)
    return np.transpose(img, (1,2,0))



def HWC2CHW(img): # convert a single image array from (H, W, C) channel-last formatting to (C, H, W) channel-first, input = img (ndarray)
    return np.transpose(img, (2,0,1))



def readImage(path):
    img = plt.imread(path)
    return img



def printImage(img, CHW = True): # prints a single image and assumes (C, H, W) channel-first input, input = CHW (boolean)
    if(CHW):
        plt.imshow(CHW2HWC(img), interpolation = 'nearest')
    else:
        plt.imshow(img, interpolation = 'nearest')
    plt.show()



def clearDirectory():
    for image in os.listdir(root + "\\TrainingImages"):
        os.remove(root + "\\TrainingImages\\" + image)



isOpen = [False, False, False, False]
isRecording = [False, False, False, False]



class Cameras:

    def __init__(self):

        print('\nCamera List:\n')

        (ret, self.devList, self.serialList) = enum_devices()

        if ret != 0:
            strError = "Device Enumeration failed. Error code is: " + ToHexStr(ret)
            QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)

        self.numDevices = len(self.devList)
        self.MvCamObjects = []
        self.obj_cam_operation = []
        self.bufferList = {self.serialList[x]: '' for x in range(self.numDevices)}



    def print_camera_list(self):

        print("\nCamera List: ")
        for i in range(self.numDevices):
            print('[{}] {}'.format(i, self.serialList[i]))



    def open_cameras(self, all = True, deviceNum = -1):

        if(all):
            print()

            for i in range(self.numDevices):
                if isOpen[i]:
                    strError = self.serialList[i] + " is already open!"
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    isOpen[i] = True

                    self.MvCamObjects.append(MvCamera())
                    (ret, obj_cam_operation) = open_device(self.MvCamObjects[i], i)

                    if 0 != ret:
                        strError = self.serialList[i] + " failed to open. Error code is: " + To_hex_str(ret)
                        QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                    else:
                        print("{} opened successfully!\n".format(self.serialList[i]))
                        self.obj_cam_operation.append(obj_cam_operation)
        else:
            if(len(self.MvCamObjects) == 0):
                print()
            
            if isOpen[deviceNum]:
                strError = self.serialList[deviceNum] + " is already open!"
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            elif deviceNum >= self.numDevices:
                strError = "Cam" + str(deviceNum) + " could be detected."
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            else:
                isOpen[deviceNum] = True

                self.MvCamObjects.append(MvCamera())
                (ret, obj_cam_operation) = open_device(self.MvCamObjects[deviceNum], deviceNum)

                if 0 != ret:
                    strError = self.serialList[deviceNum] + " failed to open. Error code is: " + To_hex_str(ret)
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    print("{} opened successfully!\n".format(self.serialList[deviceNum]))
                    self.obj_cam_operation.append(obj_cam_operation)



    def set_parameters(self, all = True, deviceNum = -1, FrameRate = 19.00, Exposure = 27999.00, Gain = 0.00):

        if(all):
            self.FrameRate = FrameRate
            self.Exposure = Exposure
            self.Gain = Gain

            for i in range(len(self.obj_cam_operation)):
                ret = set_initial_param(self.obj_cam_operation[i], self.FrameRate, self.Exposure, self.Gain)

                if 0 != ret:
                    strError = self.serialList[i] + " failed to set parameters. Error code is: " + To_hex_str(ret)
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    print("{} parameters set successfully!".format(self.serialList[i]))
                    print("FrameRate: {}".format(self.FrameRate))
                    print("Exposure: {}".format(self.Exposure))
                    print("Gain: {}\n".format(self.Gain))
        else:
            if deviceNum >= len(self.obj_cam_operation):
                strError = "Cam" + str(deviceNum) + " could be detected."
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            else:
                ret = set_initial_param(self.obj_cam_operation[deviceNum], self.FrameRate, self.Exposure, self.Gain)

                if 0 != ret:
                    strError = self.serialList[deviceNum] + " failed to set parameters. Error code is: " + To_hex_str(ret)
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    print("{} parameters set successfully!".format(self.serialList[deviceNum]))
                    print("FrameRate: {}".format(self.FrameRate))
                    print("Exposure: {}".format(self.Exposure))
                    print("Gain: {}\n".format(self.Gain))



    def start_recording(self, all = True, deviceNum = -1):

        if(all):
            uiDebug.AllStopRecording.setEnabled(True)
            uiDebug.AllStartRecording.setEnabled(False)

            for i in range(len(self.obj_cam_operation)):
                if isRecording[i]:
                    strError = self.serialList[i] + " is already recording!"
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    isRecording[i] = True

                    ret = start_grabbing(self.obj_cam_operation[i], i, self.serialList[i], self.bufferList)

                    if 0 != ret:
                        strError = self.serialList[i] + " failed to start recording. Error code is: " + To_hex_str(ret)
                        QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                    else:
                        print("{} started recording successfully!\n".format(self.serialList[i]))
                        if i == 0:
                            uiDebug.Cam0StopRecording.setEnabled(True)
                            uiDebug.Cam0StartRecording.setEnabled(False)
                        elif i == 1:
                            uiDebug.Cam1StopRecording.setEnabled(True)
                            uiDebug.Cam1StartRecording.setEnabled(False)
                        elif i == 2:
                            uiDebug.Cam2StopRecording.setEnabled(True)
                            uiDebug.Cam2StartRecording.setEnabled(False)
                        else:
                            uiDebug.Cam3StopRecording.setEnabled(True)
                            uiDebug.Cam3StartRecording.setEnabled(False)
        else:
            if isRecording[deviceNum]:
                strError = self.serialList[deviceNum] + " is already recording!"
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            elif deviceNum >= len(self.obj_cam_operation):
                strError = "Cam" + str(deviceNum) + " could be detected."
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            else:
                isRecording[deviceNum] = True

                ret = start_grabbing(self.obj_cam_operation[deviceNum], deviceNum, self.serialList[deviceNum], self.bufferList)

                if 0 != ret:
                    strError = self.serialList[deviceNum] + " failed to start recording. Error code is: " + To_hex_str(ret)
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    print("{} started recording successfully!\n".format(self.serialList[deviceNum]))
                    if deviceNum == 0:
                        uiDebug.Cam0StopRecording.setEnabled(True)
                        uiDebug.Cam0StartRecording.setEnabled(False)
                    elif deviceNum == 1:
                        uiDebug.Cam1StopRecording.setEnabled(True)
                        uiDebug.Cam1StartRecording.setEnabled(False)
                    elif deviceNum == 2:
                        uiDebug.Cam2StopRecording.setEnabled(True)
                        uiDebug.Cam2StartRecording.setEnabled(False)
                    else:
                        uiDebug.Cam3StopRecording.setEnabled(True)
                        uiDebug.Cam3StartRecording.setEnabled(False)

                    if False not in isRecording[0: len(self.obj_cam_operation)]:
                        uiDebug.AllStopRecording.setEnabled(True)
                        uiDebug.AllStartRecording.setEnabled(False)



    def stop_recording(self, all = True, deviceNum = -1):

        if(all):
            uiDebug.AllStopRecording.setEnabled(False)
            uiDebug.AllStartRecording.setEnabled(True)

            for i in range(len(self.obj_cam_operation)):
                if not isRecording[i]:
                    strError = self.serialList[i] + " is no longer recording!"
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    isRecording[i] = False

                    ret = stop_grabbing(self.obj_cam_operation[i], i)

                    if 0 != ret:
                        strError = self.serialList[i] + " failed to stop recording. Error code is: " + To_hex_str(ret)
                        QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                    else:
                        print("\n{} stopped recording successfully!".format(self.serialList[i]))
                        if i == 0:
                            uiDebug.Cam0StopRecording.setEnabled(False)
                            uiDebug.Cam0StartRecording.setEnabled(True)
                        elif i == 1:
                            uiDebug.Cam1StopRecording.setEnabled(False)
                            uiDebug.Cam1StartRecording.setEnabled(True)
                        elif i == 2:
                            uiDebug.Cam2StopRecording.setEnabled(False)
                            uiDebug.Cam2StartRecording.setEnabled(True)
                        else:
                            uiDebug.Cam3StopRecording.setEnabled(False)
                            uiDebug.Cam3StartRecording.setEnabled(True)
        else:
            if not isRecording[deviceNum]:
                strError = self.serialList[deviceNum] + " is no longer recording!"
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            elif deviceNum >= len(self.obj_cam_operation):
                strError = "Cam" + str(deviceNum) + " could be detected."
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            else:
                isRecording[deviceNum] = False

                ret = stop_grabbing(self.obj_cam_operation[deviceNum], deviceNum)

                if 0 != ret:
                    strError = self.serialList[deviceNum] + " failed to stop recording. Error code is: " + To_hex_str(ret)
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    print("\n{} stopped recording successfully!".format(self.serialList[deviceNum]))
                    if deviceNum == 0:
                        uiDebug.Cam0StopRecording.setEnabled(False)
                        uiDebug.Cam0StartRecording.setEnabled(True)
                    elif deviceNum == 1:
                        uiDebug.Cam1StopRecording.setEnabled(False)
                        uiDebug.Cam1StartRecording.setEnabled(True)
                    elif deviceNum == 2:
                        uiDebug.Cam2StopRecording.setEnabled(False)
                        uiDebug.Cam2StartRecording.setEnabled(True)
                    else:
                        uiDebug.Cam3StopRecording.setEnabled(False)
                        uiDebug.Cam3StartRecording.setEnabled(True)
                    
                    if not True in isRecording[0: len(self.obj_cam_operation)]:
                        uiDebug.AllStopRecording.setEnabled(False)
                        uiDebug.AllStartRecording.setEnabled(True)



    def close_cameras(self, all = True, deviceNum = -1):

        if(all):
            print()
            for i in range(len(self.obj_cam_operation)):
                if not isOpen[i]:
                    strError = self.serialList[i] + " is no longer open!"
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    isOpen[i] = False

                    ret = close_device(self.obj_cam_operation[i], i)

                    if 0 != ret:
                        strError = self.serialList[i] + " failed to close. Error code is: " + To_hex_str(ret)
                        QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                    else:
                        print("{} closed successfully!\n".format(self.serialList[i]))
        else:
            if not isOpen[deviceNum]:
                strError = self.serialList[deviceNum] + " is no longer open!"
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            elif deviceNum >= len(self.obj_cam_operation):
                strError = "Cam" + str(deviceNum) + " could be detected."
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            else:
                isOpen[deviceNum] = False
        
                ret = close_device(self.obj_cam_operation[deviceNum], deviceNum)

                if 0 != ret:
                    strError = self.serialList[deviceNum] + " failed to close. Error code is: " + To_hex_str(ret)
                    QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
                else:
                    print("{} closed successfully!\n".format(self.serialList[deviceNum]))



    def get_buffer(self, all = True, deviceNum = -1):

        if(all):
            for i in range(len(self.obj_cam_operation)):
                bufferPath = self.bufferList[self.serialList[i]]
                img = readImage(bufferPath)
                printImage(img, CHW = False)
        else:
            if deviceNum >= len(self.obj_cam_operation):
                strError = "Cam" + str(deviceNum) + " could be detected."
                QMessageBox.warning(mainWindowDebugger, "Error", strError, QMessageBox.Ok)
            else:
                bufferPath = self.bufferList[self.serialList[deviceNum]]
                img = readImage(bufferPath)
                printImage(img, CHW = False)



    def promptGUI(self):

        if(len(cameras.serialList) == 1):
            uiDebug.Cam0.setTitle(cameras.serialList[0])
        elif(len(cameras.serialList) == 2):
            uiDebug.Cam0.setTitle(cameras.serialList[0])
            uiDebug.Cam1.setTitle(cameras.serialList[1])
        elif(len(cameras.serialList) == 3):
            uiDebug.Cam0.setTitle(cameras.serialList[0])
            uiDebug.Cam1.setTitle(cameras.serialList[1])
            uiDebug.Cam2.setTitle(cameras.serialList[2])
        elif(len(cameras.serialList) == 4):
            uiDebug.Cam0.setTitle(cameras.serialList[0])
            uiDebug.Cam1.setTitle(cameras.serialList[1])
            uiDebug.Cam2.setTitle(cameras.serialList[2])
            uiDebug.Cam3.setTitle(cameras.serialList[3])

        mainWindowDebugger.show()

        uiDebug.AllStartRecording.clicked.connect(lambda: cameras.start_recording(True))
        uiDebug.AllStopRecording.clicked.connect(lambda: cameras.stop_recording(True))
            
        uiDebug.Cam0StartRecording.clicked.connect(lambda: cameras.start_recording(False, 0))
        uiDebug.Cam0StopRecording.clicked.connect(lambda: cameras.stop_recording(False, 0))
        uiDebug.Cam1StartRecording.clicked.connect(lambda: cameras.start_recording(False, 1))
        uiDebug.Cam1StopRecording.clicked.connect(lambda: cameras.stop_recording(False, 1))
        uiDebug.Cam2StartRecording.clicked.connect(lambda: cameras.start_recording(False, 2))
        uiDebug.Cam2StopRecording.clicked.connect(lambda: cameras.stop_recording(False, 2))
        uiDebug.Cam3StartRecording.clicked.connect(lambda: cameras.start_recording(False, 3))
        uiDebug.Cam3StopRecording.clicked.connect(lambda: cameras.stop_recording(False, 3))

        cameras.open_cameras()
        cameras.set_parameters()

        appDebug.exec_()

### Sample Usage ###

## CAUTION: clearDirectory WILL DELETE EVERYTHING !!!

if __name__ == "__main__":

    clearDirectory()

    cameras = Cameras()

    test = True
    multi = False
    GUIOption = True

    if test:
        if GUIOption:
            cameras.promptGUI()
        else:
            if multi:
                cameras.open_cameras()
                cameras.set_parameters()
                cameras.start_recording()
                time.sleep(5)
                cameras.get_buffer()
                time.sleep(3)
                cameras.get_buffer()
                time.sleep(3)
                cameras.stop_recording()
            else:
                cameras.open_cameras(False, 2)
                cameras.open_cameras(False, 0)
                cameras.open_cameras(False, 1)
                cameras.set_parameters()
                cameras.start_recording(False, 0)
                time.sleep(2)
                cameras.get_buffer(False, 0)
                time.sleep(3)
                cameras.start_recording(False, 1)
                time.sleep(2)
                cameras.get_buffer(False, 1)
                cameras.get_buffer(False, 0)
                time.sleep(1)
                cameras.stop_recording(False, 0)
                time.sleep(4)
                cameras.stop_recording(False, 1)
                cameras.start_recording(False, 0)
                time.sleep(4)
                cameras.stop_recording(False, 0)

    cameras.close_cameras() # close camera before exitting

    sys.exit()