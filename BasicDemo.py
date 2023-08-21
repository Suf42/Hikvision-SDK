# -- coding: utf-8 --

import os
import sys
import numpy as np
import time

from PyQt5.QtWidgets import *
from CamOperation_class import CameraOperation

from root import *
os.chdir(root + "\\Imports")
sys.path.append(root + "\\Imports")

from MvCameraControl_class import *
from MvErrorDefine_const import *
from CameraParams_header import *

from Debugger import Ui_MainWindow_Debugger

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

global deviceList
deviceList = MV_CC_DEVICE_INFO_LIST()
global nSelCamIndex
nSelCamIndex = 0

def enum_devices():
    global deviceList
    global obj_cam_operation

    deviceList = MV_CC_DEVICE_INFO_LIST()
    ret = MvCamera.MV_CC_EnumDevices(MV_GIGE_DEVICE | MV_USB_DEVICE, deviceList)

    if deviceList.nDeviceNum == 0:
        QMessageBox.warning(mainWindowDebugger, "Error", "No Device Found!", QMessageBox.Ok)
        # return ret

    devList = []
    serialList = []
    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            print("[%d]" % i)
            print("connection type: gige device")
            chUserDefinedName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chUserDefinedName:
                if 0 == per:
                    break
                chUserDefinedName = chUserDefinedName + chr(per)
            print("device user define name: %s" % chUserDefinedName)

            chModelName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                if 0 == per:
                    break
                chModelName = chModelName + chr(per)

            print("device model name: %s" % chModelName)

            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
            devList.append(
                "[" + str(i) + "]GigE: " + chUserDefinedName + " " + chModelName + "(" + str(nip1) + "." + str(
                    nip2) + "." + str(nip3) + "." + str(nip4) + ")")
            serialList.append(str(nip1) + "." + str(nip2) + "." + str(nip3) + "." + str(nip4))
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print("[%d]" % i)
            print("connection type: u3v device")
            chUserDefinedName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chUserDefinedName:
                if per == 0:
                    break
                chUserDefinedName = chUserDefinedName + chr(per)
            print("device user define name: %s" % chUserDefinedName)

            chModelName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if 0 == per:
                    break
                chModelName = chModelName + chr(per)
            print("device model name: %s" % chModelName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)
            devList.append("[" + str(i) + "]USB: " + chUserDefinedName + " " + chModelName
                           + "(" + str(strSerialNumber) + ")")
            serialList.append(str(strSerialNumber))

    return (ret, devList, serialList)

def open_device(camObject, camIndex):
    global deviceList
    global nSelCamIndex
    global obj_cam_operation

    nSelCamIndex = camIndex
    if nSelCamIndex < 0:
        QMessageBox.warning(mainWindowDebugger, "Error", 'Please select a camera!', QMessageBox.Ok)
        # return MV_E_CALLORDER

    obj_cam_operation = CameraOperation(camObject, deviceList, camIndex)
    ret = obj_cam_operation.Open_device()

    return (ret, obj_cam_operation)

def start_grabbing(camOperationObject, camIndex, chModelName, bufferList):
    global obj_cam_operation

    if(camIndex == 0):
        ret = camOperationObject.Start_grabbing(uiDebug.Cam0Panel.winId(), chModelName, bufferList)
    elif(camIndex == 1):
        ret = camOperationObject.Start_grabbing(uiDebug.Cam1Panel.winId(), chModelName, bufferList)
    elif(camIndex == 2):
        ret = camOperationObject.Start_grabbing(uiDebug.Cam2Panel.winId(), chModelName, bufferList)
    else:
        ret = camOperationObject.Start_grabbing(uiDebug.Cam3Panel.winId(), chModelName, bufferList)
    
    return ret

def stop_grabbing(camOperationObject, camIndex):
    global obj_cam_operation
    ret = camOperationObject.Stop_grabbing()

    return ret

def close_device(camOperationObject, camIndex):
    global obj_cam_operation
    ret = camOperationObject.Close_device()

    return ret

def set_initial_param(camOperationObject, FrameRate, Exposure, Gain):
    frame_rate = FrameRate
    exposure = Exposure
    gain = Gain
    ret = camOperationObject.Set_parameter(frame_rate, exposure, gain)
    if ret != MV_OK:
        return ret

    return MV_OK

appDebug = QApplication(sys.argv)
mainWindowDebugger = QMainWindow()
uiDebug = Ui_MainWindow_Debugger()
uiDebug.setupUi(mainWindowDebugger)