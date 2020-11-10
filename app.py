import os
import sys
import csv
import ini
from ctypes import *
from time import sleep
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox, QPushButton, QCheckBox
from PyQt5 import *


#for image processing
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage, misc
import cv2
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

#for windows path
from pathlib import Path


#variable declaration
i2csid = 0x80
ImgWidth = 1920
ImgHeight = 1080
ImgFormat = 1
ImgInterface = 2
mipiclk = 408.0
ImgHdrMode = 0
mImgByteSize = c_longlong(0)
pagemode = 0
ImgNum = 1
pimgdata = 0
Sensor_AVDD = 2.8
Sensor_DVDD = 0.0
Sensor_DOVDD = 2.8
Sensor_Mclk = 24.0
Sensor_init_reg = ""
IniFileName = ""

cwd = Path.cwd()
print(cwd)
# Load DLL into memory.
hllDll = CDLL(str(cwd)+"\\SOI_PlatformManagerLib.dll")

def CallFunctionStatus(value):
    if value!=0:
        msgbox = QMessageBox()
        msgbox.setText('Call Function fail')
        msgbox.exec_()
        raise WindowsError()
    return value

def InitSensorRegWithFile():
    global IniFileName
    flg = 0
    file = open(IniFileName)
    all_lines = file.readlines()
    for line in all_lines:
        if "[INI_Register]" in line:#sensor ini reg start
            flg = 1
            continue #jump to next line
        if ";PC:" in line:#sensor ini reg end
            flg = 0
            continue

        if flg == 1:
            if not line.strip():
                continue
            else:
                #print(line)
                if 'sleep' in line:
                    regdata = line.split(' ')
                    data = int(regdata[1])
                    sleep(data/1000.0)
                else:
                    regdata = line.split(',')
                    addr = int(regdata[0], base=16)
                    data = int(regdata[1], base=16)
                    #for debug
                    print(hex(addr))#addr
                    print(hex(data))#data
                    ret = hllDll.I2C_Write(c_int(0), c_int(i2csid), c_int(addr), c_int(data))
                    CallFunctionStatus(ret)

class Ui(QtWidgets.QMainWindow):    
    def __init__(self):        
        super(Ui, self).__init__() # Call the inherited classes __init__ method
        cwd = Path.cwd()
        uic.loadUi(str(cwd)+'\\UI\\DllTestUI.ui', self) # Load the .ui file        
        
        # Find the button with the name "Version"
        self.versionbutton = self.findChild(QtWidgets.QPushButton, 'Version')
        # Remember to pass the definition/method, not the return value!
        self.versionbutton.clicked.connect(self.VersionButtonPressed)

        self.versionbutton = self.findChild(QtWidgets.QPushButton, 'LoadSensorIni')
        self.versionbutton.clicked.connect(self.LoadSensorIniButtonPressed)

        self.i2creadbutton = self.findChild(QtWidgets.QPushButton, 'I2C_Read')
        self.i2creadbutton.clicked.connect(self.I2cReadButtonPressed)

        self.i2cwritebutton = self.findChild(QtWidgets.QPushButton, 'I2C_Write')
        self.i2cwritebutton.clicked.connect(self.I2cWriteButtonPressed)

        self.opendevicebutton = self.findChild(QtWidgets.QPushButton, 'OpenDevice')
        self.opendevicebutton.clicked.connect(self.OpenDeviceButtonPressed)

        self.closedevicebutton = self.findChild(QtWidgets.QPushButton, 'CloseDevice')
        self.closedevicebutton.clicked.connect(self.CloseDeviceButtonPressed)

        self.getimagebutton = self.findChild(QtWidgets.QPushButton, 'GetImage')
        self.getimagebutton.clicked.connect(self.GetImageButtonPressed)

        self.mipicalibrationbutton = self.findChild(QtWidgets.QPushButton, 'MipiCalibration')
        self.mipicalibrationbutton.clicked.connect(self.MipiCalibrationButtonPressed)

        self.consecutivebutton = self.findChild(QtWidgets.QPushButton, 'Consecutive')
        self.consecutivebutton.clicked.connect(self.ConsecutiveButtonPressed)

        self.gpioreadbutton = self.findChild(QtWidgets.QPushButton, 'GPIO_Read')
        self.gpioreadbutton.clicked.connect(self.GpioReadButtonPressed)

        self.gpiowritebutton = self.findChild(QtWidgets.QPushButton, 'GPIO_Write')
        self.gpiowritebutton.clicked.connect(self.GpioWriteButtonPressed)

        self.showimagebutton = self.findChild(QtWidgets.QPushButton, 'ShowImage')
        self.showimagebutton.clicked.connect(self.ShowImageButtonPressed)

        self.i2csid = self.findChild(QtWidgets.QLineEdit, 'I2C_Sid')
        self.i2caddr = self.findChild(QtWidgets.QLineEdit, 'I2C_Addr')
        self.i2cdata = self.findChild(QtWidgets.QLineEdit, 'I2C_Data')        
        self.imgnum = self.findChild(QtWidgets.QLineEdit, 'ImageNum')
        self.gpioid = self.findChild(QtWidgets.QLineEdit, 'GPIO_Id')
        self.gpiodata = self.findChild(QtWidgets.QLineEdit, 'GPIO_Data')
        self.avdd = self.findChild(QtWidgets.QLineEdit, 'AVDD')
        self.dvdd = self.findChild(QtWidgets.QLineEdit, 'DVDD')
        self.dovdd = self.findChild(QtWidgets.QLineEdit, 'DOVDD')

        #get the related information from sensor ini
        self.i2csid.setText(hex(i2csid))
        self.i2caddr.setText('0x0A')
        self.i2cdata.setText('0x00')
        self.imgnum.setText('1')
        self.gpioid.setText('21') #fx3 status led
        self.gpiodata.setText('1')
        self.avdd.setText(str(Sensor_AVDD))
        self.dvdd.setText(str(Sensor_DVDD))
        self.dovdd.setText(str(Sensor_DOVDD))

        self.i2cpage = self.findChild(QtWidgets.QCheckBox, 'I2C_Page')
        self.i2cpage.setChecked(False)  
        self.i2cpage.toggled.connect(self.I2cPageCheckBoxToggle)

        self.show() # Show the GUI

    def ShowImageButtonPressed(self):
        #TODO: load image from selection dialog
        global ImgWidth, ImgHeight
        path = 'image0.raw'
        f = open(path,'rb')
        bin_image = np.fromstring(f.read(), dtype=np.uint16)
        bin_image_shift = np.right_shift(bin_image, 2);
        bin_image_8 = bin_image_shift.astype(np.uint8)
        bin_image_8.shape = (ImgHeight, ImgWidth)
        color_image = cv2.cvtColor(bin_image_8, cv2.COLOR_BayerRG2RGB) #color image
        gray_image = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)    #gray image
        
        color = ('b','g','r')
        plt.figure()
        for i, col in enumerate(color):
            hist_color = cv2.calcHist([color_image],[i],None,[256],[0, 256])
            plt.plot(hist_color, color = col)
            plt.xlim([0, 256])

        hist_gray = cv2.calcHist(color_image,[0], None,[256], [0, 256])
        plt.figure()
        plt.subplot(221), plt.imshow(color_image)
        plt.subplot(222), plt.imshow(gray_image, cmap='gray')
        plt.subplot(223), plt.plot(hist_color)
        plt.subplot(224), plt.plot(hist_gray)   
        plt.xlim([0, 256])        

        plt.figure()
        plt.imshow(color_image)
        plt.show(block=True)

    def GpioReadButtonPressed(self):
        data = c_int(0)
        pdata = pointer(data)
        gid = int(self.gpioid.text(), base=10)
        ret = hllDll.GetGpioValue(c_int(gid), pdata)
        CallFunctionStatus(ret)     
        strdata = str(data.value)
        self.gpiodata.setText(strdata)        

    def GpioWriteButtonPressed(self):
        gid = int(self.gpioid.text(), base=10)
        gdata = int(self.gpiodata.text(), base = 10)
        ret = hllDll.SetGpioValue(c_int(gid), c_int(gdata))
        CallFunctionStatus(ret)  

    def MipiCalibrationButtonPressed(self):
        ret = hllDll.FPGA_MipiPhaseCalibration()
        CallFunctionStatus(ret)

    def ConsecutiveButtonPressed(self):
        global ImgNum
        global pimgdata
        global mImgByteSize
        ImgNum = self.imgnum.text()    
        ImgNum = int(ImgNum, base=10)
        pimgdata = b'0'*mImgByteSize.value*ImgNum
        tmpdata = b'0'*mImgByteSize.value        
        ret = hllDll.FPGA_ConsecutiveFrameCapture(ImgNum, pimgdata, c_int(2000))
        CallFunctionStatus(ret)
        for x in range(ImgNum):
            st = mImgByteSize.value * x
            end = mImgByteSize.value * (x + 1)
            tmpdata = pimgdata[st : end]
            fname = 'conimage{:d}.raw'.format(x)
            f = open(fname, mode="wb")            
            f.write(tmpdata)            
            f.close()   

    def GetImageButtonPressed(self):
        global ImgNum
        global pimgdata
        global mImgByteSize
        delay_time = c_int(2000)
        p_delay_time = pointer(delay_time)
        ImgNum = self.imgnum.text()    
        ImgNum = int(ImgNum, base=10)
        pimgdata = b'0'*mImgByteSize.value        
        for x in range(ImgNum):
            ret = hllDll.ImageCapture(pimgdata, mImgByteSize, p_delay_time)
            CallFunctionStatus(ret)
            fname = 'image{:d}.raw'.format(x)
            f = open(fname, "wb")
            f.write(pimgdata)
            f.close()
            sleep(0.1)

    def I2cPageCheckBoxToggle(self, state):
        global pagemode
        if state:
            pagemode = 1
        else:
            pagemode = 0
    
    def I2cReadButtonPressed(self):   
        global pagemode      
        # debug       
        # msgbox = QMessageBox()
        # msgbox.setText('I2cRead('+self.i2csid.text() + ',' + self.i2caddr.text() +  ')')
        # msgbox.exec_()
        data = c_int(0)
        pdata = pointer(data)
        sid = int(self.i2csid.text(), base=16)
        addr = int(self.i2caddr.text(), base=16) 
        if(pagemode ==1):
            page = ( addr >> 8 ) & 0xFF
            ret = hllDll.I2C_Write(c_int(0), c_int(sid), c_int(0xFF), c_int(page))    #write page value
        ret = hllDll.I2C_Read(c_int(0), c_int(sid), c_int(addr), pdata)
        CallFunctionStatus(ret)
        print(data)
        strdata = str(hex(data.value))
        self.i2cdata.setText(strdata)        
        
    def I2cWriteButtonPressed(self):        
        global pagemode
        # msgbox = QMessageBox()
        # msgbox.setText('I2cWrite('+self.i2csid.text() + ',' + self.i2caddr.text() + ',' + self.i2cdata.text() + ')')
        # msgbox.exec_()
        sid = int(self.i2csid.text(), base=16)
        addr = int(self.i2caddr.text(), base=16) 
        data = int(self.i2cdata.text(), base=16)
        if(pagemode ==1):
            page = ( addr >> 8 ) & 0xFF
            ret = hllDll.I2C_Write(c_int(0), c_int(sid), c_int(0xFF), c_int(page))    #write page value
        ret = hllDll.I2C_Write(c_int(0), c_int(sid), c_int(addr), c_int(data))
        CallFunctionStatus(ret)

    def CloseDeviceButtonPressed(self):
        ret = hllDll.CloseDevice()
        CallFunctionStatus(ret)
        ret = hllDll.FreeDevice()
        CallFunctionStatus(ret)
        msgbox = QMessageBox()
        msgbox.setText('CloseDevice Done!')
        msgbox.exec_()

    def VersionButtonPressed(self):
        # This is executed when the button is pressed
        #print('VersionButtonPressed')
        fw_ver = c_char_p()
        fw_ver.value = b'0'*16
        fpga_ver = c_char_p()
        fpga_ver.value = b'0'*32
        ret = hllDll.GetFwVersion(fw_ver)
        CallFunctionStatus(ret)
        print(fw_ver.value)
        ret = hllDll.GetFpgaVersion(fpga_ver)
        CallFunctionStatus(ret)
        print(fpga_ver.value)        

    def LoadSensorIniButtonPressed(self):
        # This is executed when the button is pressed
        print('LoadSensorIniButtonPressed')
        global ImgWidth, ImgHeight, ImgFormat, ImgInterface, mipiclk, Sensor_Mclk
        global ImgHdrMode, Sensor_init_reg, IniFileName
        dialog = QtWidgets.QFileDialog(self)
        dialog.setWindowTitle('Open File')
        dialog.setNameFilter('INI files (*.ini)')
        dialog.setDirectory(QtCore.QDir.currentPath())
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            IniFileName = str(dialog.selectedFiles()[0])
            print(IniFileName);
            ini_config = ini.parse(open(IniFileName).read());
            sensor_type = ini_config["SensorType"]["0"]
            ImgWidth = int(ini_config[sensor_type]["Width"])
            ImgHeight = int(ini_config[sensor_type]["Height"])
            ImgFormat = int(ini_config[sensor_type]["SrOutputFormats"])
            ImgInterface = int(ini_config[sensor_type]["Interface"])
            mipiclk = float(ini_config[sensor_type]["MipiClkRate"])
            Sensor_Mclk = float(ini_config[sensor_type]["MclkRate"])
            ImgHdrMode = int(ini_config[sensor_type]["HDR_Mode"])
            #Sensor_init_reg = ini_config["INI_Register"] #issue: lost some repeat string
        else:
            return None
    
    def OpenDeviceButtonPressed(self):  
        global mImgByteSize, ImgWidth, ImgHeight,  ImgInterface
        global ImgFormat, ImgHdrMode, mipiclk
        global Sensor_AVDD, Sensor_DVDD, Sensor_DOVDD, Sensor_Mclk
        cwd = Path.cwd()
        cwdpath = str(cwd) + '\\'        
        print(cwdpath)
        filepath = c_char_p()
        filepath.value = cwdpath.encode(encoding="utf-8")
        print(filepath.value)
        ret = hllDll.SetExecutionPath(filepath)
        CallFunctionStatus(ret)
        ret = hllDll.InitDevice() 
        CallFunctionStatus(ret)                        
        filepath = c_char_p()
        filepath.value = b"ccccccccccccccccccccccccccccccccccccccccccccccccccc"
        ret = hllDll.GetExecutionPath(filepath)
        print(filepath.value)
        ret = hllDll.ConnectDevice()
        CallFunctionStatus(ret)
        ret = hllDll.SetSensorResolution(ImgWidth, ImgHeight)
        CallFunctionStatus(ret)
        ret = hllDll.SetBusWidthMode(c_int(2))#32bit bus
        CallFunctionStatus(ret)
        ret = hllDll.SetOutFormat(c_int(0))#ByPass mode
        CallFunctionStatus(ret)
        ret = hllDll.SetSensorInterface(ImgInterface)
        CallFunctionStatus(ret)
        ret = hllDll.SetOutChannel(c_int(1))#FX3 series: 1:DVP
        CallFunctionStatus(ret)
        ret = hllDll.SetSensorOutputFormat(ImgFormat)
        CallFunctionStatus(ret)
        ret = hllDll.SetHDRmode(ImgHdrMode)
        CallFunctionStatus(ret)
        ret = hllDll.SetSensorMipiClkRate(c_float(mipiclk))
        CallFunctionStatus(ret)
        pmImgByteSize = pointer(mImgByteSize)
        ret = hllDll.GetGrabSize(pmImgByteSize)
        print(mImgByteSize)                
        CallFunctionStatus(ret)        
        ret = hllDll.OpenDevice()
        CallFunctionStatus(ret)
        #Sensor Power On Sequence
        ret = hllDll.SetSensorPwdn(1)
        CallFunctionStatus(ret)
        #AVDD(0), 2.8v
        Sensor_AVDD = float(self.avdd.text());
        ret = hllDll.SetPower(c_int(0), c_float(Sensor_AVDD))
        CallFunctionStatus(ret)
        #DVDD(0), 0.0v
        Sensor_DVDD = float(self.dvdd.text());
        ret = hllDll.SetPower(c_int(1), c_float(Sensor_DVDD))
        CallFunctionStatus(ret)
        #DOVDD(0), 2.8v
        Sensor_DOVDD = float(self.dovdd.text());
        ret = hllDll.SetPower(c_int(2), c_float(Sensor_DOVDD))
        CallFunctionStatus(ret)

        sleep(0.01)#10ms = 0.01s
        ret = hllDll.SetFpgaMclk(c_float(24.0))
        CallFunctionStatus(ret)

        sleep(0.01)#10ms = 0.01s
        ret = hllDll.SetSensorMclk(c_float(Sensor_Mclk))
        CallFunctionStatus(ret)

        sleep(0.01)#10ms = 0.01s
        ret = hllDll.SetPclkPolarity(c_int(0))
        CallFunctionStatus(ret)
        sleep(0.01)#10ms = 0.01s        

        #Set I2C Clock
        ret = hllDll.SetI2cClockRate(c_int(1)) #I2C_RATE_400K
        sleep(0.01)
        CallFunctionStatus(ret)

        #reset sensor
        ret = hllDll.SetSensorReset(c_int(1))
        CallFunctionStatus(ret)
        ret = hllDll.SetSensorReset(c_int(0))
        CallFunctionStatus(ret)
        sleep(0.3) #300ms = 0.3s
        ret = hllDll.SetSensorReset(c_int(1))
        CallFunctionStatus(ret)
        ret = hllDll.SetSensorPwdn(c_int(0))
        CallFunctionStatus(ret)
                
        #initFPGA
        ret = hllDll.InitFpgaRegister()
        CallFunctionStatus(ret)

        #SensorIniReg
        InitSensorRegWithFile()
        
        msgbox = QMessageBox()
        msgbox.setText('OpenDevice Finish!')
        msgbox.exec_()

app = QtWidgets.QApplication(sys.argv) # Create an instance of QtWidgets.QApplication
window = Ui() # Create an instance of our class
app.exec_() # Start the application
