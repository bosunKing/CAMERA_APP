import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import uic
import cv2, imutils
import time
from PyQt5.QtCore import QThread, pyqtSignal,Qt, QBuffer,QIODevice
from PyQt5.QtWidgets import QMessageBox,QFrame
import numpy as np
import qimage2ndarray
import datetime


main_class = uic.loadUiType("/home/bo/amr_ws/PyQt/src/photo_main.ui")[0]
cut_class = uic.loadUiType("/home/bo/amr_ws/PyQt/src/photo_cut.ui")[0]
adjust_class = uic.loadUiType("/home/bo/amr_ws/PyQt/src/photo_adjust.ui")[0]


class Camera(QThread): 
    update = pyqtSignal()
    
    def __init__(self, sec = 0, parent = None):
        super().__init__()
        self.main = parent
        self.running = True
        
    def run(self):
        while self.running == True:
            self.update.emit()
            time.sleep(0.1) #하드 코딩, 제대로된 코딩은 0.1을 인자로받아 경우에따라 처리
        
    def stop(self):
        self.running == False
        
            
class WindowClass(QMainWindow, main_class):
    def __init__ (self, pixmap=None):
        super().__init__()
        self.setupUi(self)
        
        self.isCameraOn = False
        self.isRecStart = False
        self.btnCap.hide()
        
        
        self.pixmap = QPixmap() if pixmap is None else pixmap
        
        self.camera = Camera(self)
        self.camera.daemon = True
        
        
        self.btnOpen.clicked.connect(self.openFile)
        self.btnCamera.clicked.connect(self.clickCamera)
        self.camera.update.connect(self.updateCamera)
        self.btnCap.clicked.connect(self.cameraStop)
        self.btnAdjust.clicked.connect(self.btn_adjust)
        self.btnCut.clicked.connect(self.btn_cut)
        self.btnStore.clicked.connect(self.capture)
        
        
        
    def capture(self):
        
        self.now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.now + '.png'
        if filename:
            self.pixmap.save(filename)
        
    
    def updateCamera(self):
        retval, image = self.video.read()
        
        if retval:
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            h, w, c = self.image.shape
            qimage = QImage(self.image.data, w, h, w*c, QImage.Format_RGB888)
            
            self.pixmap = self.pixmap.fromImage(qimage)
            self.pixmap = self.pixmap.scaled(self.labelMain.width(), self.labelMain.height())
            
            self.labelMain.setPixmap(self.pixmap)
            
        else :   # 이전에 읽은 마지막 프레임을 계속해서 표시
            qimage = QImage(self.image.data, w, h, w*c, QImage.Format_RGB888)

            self.pixmap = self.pixmap.fromImage(qimage)
            self.pixmap = self.pixmap.scaled(self.labelMain.width(), self.labelMain.height())

            self.labelMain.setPixmap(self.pixmap)
            

            
    def clickCamera(self):
        if self.isCameraOn == False:
            self.btnCamera.setText('Camera off')
            self.isCameraOn = True
            self.btnCap.show()
            
            self.cameraStart()
        else :
            self.btnCamera.setText('Camera on')
            self.isCameraOn = False
            
            self.cameraStop()
            
    def cameraStart(self):
        self.image = None
        self.camera.running = True
        self.camera.start()
        self.video = cv2.VideoCapture(0)
        
    def cameraStop(self):
        self.camera.running = False
        self.video.release()
            
    
    def openFile(self):
        file = QFileDialog.getOpenFileName(filter = 'Image (*.png *.img)')
        if file[0] :
            image = cv2.imread(file[0])
            image =cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            h, w, c = image.shape
            qimage = QImage(image.data, w, h, w*c, QImage.Format_RGB888)
            
            self.pixmap = self.pixmap.fromImage(qimage)
            self.pixmap = self.pixmap.scaled(self.labelMain.width(), self.labelMain.height())
            
            
            self.labelMain.setPixmap(self.pixmap)
        else:
            QMessageBox.warning(self, "Warning", "No file selected.")
    def showMain(self, pixmap):
        self.pixmap = pixmap
        self.show()
        self.labelMain.setPixmap(self.pixmap)
    
    def btn_adjust(self):
        self.hide()
        self.adjust = adjustWindow(self.pixmap, parent = self)
        self.adjust.show()
        
    def btn_cut(self):
        self.hide()
        self.cut = cutWindow(self.pixmap, parent = self)
        self.cut.show()
        
        
class adjustWindow(QMainWindow, adjust_class):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.pixmap = pixmap
        self.labelMain.setPixmap(self.pixmap)
        self.parent = parent                    # 부모 윈도우의 인스턴스 저장
        self.frame = QFrame(self)
        self.x, self.y = None, None
        self.pencil_state = None
        self.erase_state = None
        self.color_state = 1
        self.after_pixmap = None

        self.btnHome.clicked.connect(self.btn_home)
        self.btnPencil.clicked.connect(self.togglePencil)
        self.btnErase.clicked.connect(self.toggleErase)
        
        
        self.cbColor.setCurrentText("RGB")
        self.cbColor.currentIndexChanged.connect(self.ColorChange)

        min_max = [0, 100]
        self.HSV = [min_max[1], min_max[1], min_max[1]]
        self.RGB = [min_max[1], min_max[1], min_max[1]]
        
        self.sdRed.setRange(min_max[0], min_max[1])
        self.sdRed.setValue(self.RGB[0])
        self.sdGreen.setRange(min_max[0], min_max[1])
        self.sdGreen.setValue(self.RGB[1])
        self.sdBlue.setRange(min_max[0], min_max[1])
        self.sdBlue.setValue(self.RGB[2])
        
        # self.sdBrithness.setRange(min_max[0], min_max[1])
        
        self.sdRed.valueChanged.connect(self.slider)
        self.sdGreen.valueChanged.connect(self.slider)
        self.sdBlue.valueChanged.connect(self.slider)
        # self.sdBrithness.valueChanged.connect(self.slider)
        
        # self.sdContrast.setRange(0, 101)
        # self.sdContrast.setValue(0)
        # self.lbContrast.setText("0")
        # self.sdContrast.valueChanged.connect(self.change)
        
        self.sdRed.valueChanged.connect(self.change)
        self.sdGreen.valueChanged.connect(self.change)
        self.sdBlue.valueChanged.connect(self.change)
        
    def slider(self):
        self.RGB[0] = self.sdRed.value()
        self.RGB[1] = self.sdGreen.value()
        self.RGB[2] = self.sdBlue.value()
    
    def ColorChange(self):
        self.pixmap = self.after_pixmap if self.after_pixmap else self.pixmap
        content = self.cbColor.currentText()
        qimage = self.pixmap.toImage()
        numpy_arr = qimage2ndarray.rgb_view(qimage)
        
        if self.color_state == 1 and content == "HSV":
            img = cv2.cvtColor(numpy_arr, cv2.COLOR_RGB2HSV)
            self.sdRed.setValue(self.HSV[1])
            self.sdGreen.setValue(self.HSV[2])
            
            self.sdBlue.hide()
            self.lbBlue.hide()
            self.labelB.hide()
            self.labelR.setText("S")
            self.labelG.setText("V")
            
            
            self.color_state = 2
            
        elif self.color_state == 1 and content == "BGR":
            img = cv2.cvtColor(numpy_arr, cv2.COLOR_RGB2BGR)
            self.sdBlue.show()
            self.lbBlue.show()
            self.labelB.show()
            self.labelR.setText("R")
            self.labelG.setText("G")
            
            self.color_state = 3
            
        elif self.color_state == 2 and content == "RGB":
            img = cv2.cvtColor(numpy_arr, cv2.COLOR_HSV2RGB)
            self.sdBlue.show()
            self.lbBlue.show()
            self.labelB.show()
            self.labelR.setText("R")
            self.labelG.setText("G")
            
            self.color_state = 1
            
        elif self.color_state == 2 and content == "BGR":
            img = cv2.cvtColor(numpy_arr, cv2.COLOR_HSV2BGR)
            self.sdBlue.show()
            self.lbBlue.show()
            self.labelB.show()
            self.labelR.setText("R")
            self.labelG.setText("G")

            self.color_state = 3
            
        elif self.color_state == 3 and content == "RGB":
            img = cv2.cvtColor(numpy_arr, cv2.COLOR_BGR2RGB)
            self.sdBlue.show()
            self.lbBlue.show()
            self.labelB.show()
            self.labelR.setText("R")
            self.labelG.setText("G")
            self.color_state = 1
            
        elif self.color_state == 3 and content == "HSV":
            img = cv2.cvtColor(numpy_arr, cv2.COLOR_BGR2HSV)
            self.sdRed.setValue(self.HSV[1])
            self.sdGreen.setValue(self.HSV[2])
            self.sdBlue.hide()
            self.lbBlue.hide()
            self.labelB.hide()
            self.labelR.setText("S")
            self.labelG.setText("V")
            
            self.color_state = 2 
                    
        else:
            QMessageBox.warning(self, "Select Again.")
            return 
        

        qimage_change = qimage2ndarray.array2qimage(img)
        self.pixmap = QPixmap.fromImage(qimage_change)
        self.after_pixmap = self.pixmap
        self.labelMain.setPixmap(self.after_pixmap)

    def change(self, img):
        if self.color_state == 1:
            before_pixmap= self.pixmap.copy()
            qimage = before_pixmap.toImage()
            numpy_arr = qimage2ndarray.rgb_view(qimage)
            
            numpy_arr[:, :, 0] = numpy_arr[:, :, 0] * (self.RGB[0] / 100)
            numpy_arr[:, :, 1] = numpy_arr[:, :, 1] * (self.RGB[1] / 100)
            numpy_arr[:, :, 2] = numpy_arr[:, :, 2] * (self.RGB[2] / 100)
            
            self.lbRed.setText(str(self.RGB[0]))
            self.lbGreen.setText(str(self.RGB[1]))
            self.lbBlue.setText(str(self.RGB[2]))
        elif self.color_state == 2:
            before_pixmap= self.pixmap.copy()
            qimage = before_pixmap.toImage()
            numpy_arr = qimage2ndarray.rgb_view(qimage)
            
            numpy_arr[:, :, 1] = numpy_arr[:, :, 1] * (self.HSV[1] / 100)
            numpy_arr[:, :, 2] = numpy_arr[:, :, 2] * (self.HSV[2] / 100)
            
            self.lbRed.setText(str(self.HSV[1]))
            self.lbGreen.setText(str(self.HSV[2]))
        elif self.color_state == 3:
            before_pixmap= self.pixmap.copy()
            qimage = before_pixmap.toImage()
            numpy_arr = qimage2ndarray.rgb_view(qimage)
            
            numpy_arr[:, :, 0] = numpy_arr[:, :, 0] * (self.RGB[0] / 100)
            numpy_arr[:, :, 1] = numpy_arr[:, :, 1] * (self.RGB[1] / 100)
            numpy_arr[:, :, 2] = numpy_arr[:, :, 2] * (self.RGB[2] / 100)
            
            self.lbRed.setText(str(self.RGB[0]))
            self.lbGreen.setText(str(self.RGB[1]))
            self.lbBlue.setText(str(self.RGB[2]))
            
        qimage_change = qimage2ndarray.array2qimage(numpy_arr)
        self.after_pixmap = QPixmap.fromImage(qimage_change)
        self.labelMain.setPixmap(self.after_pixmap)
        
        # img = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
        # img[:, :, 1] = img[:, :, 1] * (self.HSV[1] / 100)
        # img[:, :, 2] = img[:, :, 2] * (self.HSV[2] / 100)
        # img = cv2.cvtColor(img, cv2.COLOR_HSV2RGB)
        

        # QImage를 NumPy 배열로 변환

        # 밝기 조절
        # actualValue1 = self.sdBrithness.value()
        # self.lbBrithness.setText(str(actualValue1))
        # numpy_arr = self.adjust_brightness(numpy_arr, actualValue1)

        # # 대조 조절
        # actualValue2 = self.sdContrast.value()
        # self.lbContrast.setText(str(actualValue2))
        # numpy_arr = self.adjust_contrast(numpy_arr, actualValue2)

    def togglePencil(self):
        self.pencil_state = not self.pencil_state
        if self.pencil_state == True:
            self.pencilReleaseEvent
            
    def toggleErase(self):
        self.erase_state =  not self.erase_state
        if self.erase_state == True:
            self.eraseReleaseEvent
            
    def mouseMoveEvent(self, event):
        if self.pencil_state:
            if self.x is None:
                self.x = event.x()
                self.y = event.y()
                return
            painter = QPainter(self.labelMain.pixmap())
            self.pen = QPen(Qt.red, 15, Qt.SolidLine)
            painter.setPen(self.pen)
            painter.drawLine(self.x , self.y-74, event.x(), event.y()-74)
            painter.end()
            self.update()
            self.x = event.x()
            self.y = event.y()
            print(event.x(), event.y())
        elif self.erase_state:
            if self.x is None:
                self.x = event.x()
                self.y = event.y()
                return
            
            try:
                painter = QPainter(self.labelMain.pixmap())
                # 계산된 시작점과 종료점을 사용하여 직사각형 영역을 지웁니다.
                painter.eraseRect(self.x, self.y-74, 10, 10)
                self.update()
                self.x = event.x()
                self.y = event.y()
            except TypeError as e:
                print(f"Error in eraseRect: {e}")

            
    def pencilReleaseEvent(self, event):
        self.x = None
        self.y = None
        
    def eraseReleaseEvent(self, event):
        self.x = None
        self.y = None

    def btn_home(self):
        self.close()
        self.parent.showMain(self.after_pixmap if self.after_pixmap else self.pixmap)
        
class cutWindow(QMainWindow, cut_class):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.pixmap = pixmap
        self.labelMain.setPixmap(self.pixmap)
        self.parent = parent
        qimage = self.pixmap.toImage()
        # QImage를 NumPy 배열로 변환
        self.numpy_arr = qimage2ndarray.rgb_view(qimage)

        self.btnApply.hide()
        self.btnHome.clicked.connect(self.btn_home)
        self.btnTwist.clicked.connect(self.twist)
        self.btnRotation.clicked.connect(self.rotation)
        self.btnBlur.clicked.connect(self.blur)
        self.cbRatio.currentIndexChanged.connect(self.ratio)
        self.btnApply.clicked.connect(self.apply_changes)

    def ratio(self):
        self.btnApply.show()
        state = self.cbRatio.currentText()
        if state == "16:9":
            new_width = int((16 / 9) * self.pixmap.height())
            pixmap_ratio = cv2.resize(self.numpy_arr, (new_width, self.pixmap.height()))
        elif state == "4:3":
            new_width = int((4 / 3) * self.pixmap.height())
            pixmap_ratio = cv2.resize(self.numpy_arr, (new_width, self.pixmap.height()))
        elif state == "1:1":
            min_dimension = min(self.pixmap.height(), self.pixmap.width())
            pixmap_ratio = self.numpy_arr[:min_dimension, :min_dimension]

        qimage_change = qimage2ndarray.array2qimage(pixmap_ratio)
        self.pixmap_temp = QPixmap.fromImage(qimage_change)

        # Scale the pixmap to fit the labelMain
        self.pixmap_temp = self.pixmap_temp.scaled(self.labelMain.size(), Qt.KeepAspectRatio)

        self.labelMain.setPixmap(self.pixmap_temp)

    def apply_changes(self):
        # Apply the changes to self.pixmap and update other variables if necessary
        self.pixmap = self.pixmap_temp
        self.numpy_arr = qimage2ndarray.rgb_view(self.pixmap.toImage())

        # Hide the Apply button again
        self.btnApply.hide()

    def rotation(self):
        angle = 90  # You can change this angle as needed
        self.numpy_arr = np.rot90(self.numpy_arr, k=1)  # Rotate 90 degrees clockwise

        qimage_change = qimage2ndarray.array2qimage(self.numpy_arr)
        self.pixmap_temp = QPixmap.fromImage(qimage_change)

        # Scale the pixmap to fit the labelMain
        self.pixmap_temp = self.pixmap_temp.scaled(self.labelMain.size(), Qt.KeepAspectRatio)

        self.labelMain.setPixmap(self.pixmap_temp)

    def twist(self):
        self.numpy_arr = np.flip(self.numpy_arr, axis=1)  # Flip horizontally

        qimage_change = qimage2ndarray.array2qimage(self.numpy_arr)
        self.pixmap_temp = QPixmap.fromImage(qimage_change)

        # Scale the pixmap to fit the labelMain
        self.pixmap_temp = self.pixmap_temp.scaled(self.labelMain.size(), Qt.KeepAspectRatio)

        self.labelMain.setPixmap(self.pixmap_temp)

    def blur(self):
        # Apply blur to self.numpy_arr and update the pixmap
        self.numpy_arr = cv2.blur(self.numpy_arr, (9, 9), anchor=(-1, -1), borderType=cv2.BORDER_DEFAULT)

        qimage_change = qimage2ndarray.array2qimage(self.numpy_arr)
        self.pixmap_temp = QPixmap.fromImage(qimage_change)

        # Scale the pixmap to fit the labelMain
        self.pixmap_temp = self.pixmap_temp.scaled(self.labelMain.size(), Qt.KeepAspectRatio)

        self.labelMain.setPixmap(self.pixmap_temp)

    def btn_home(self):
        self.close()
        self.parent.showMain(self.pixmap_temp)

    
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindows = WindowClass()
    myWindows.show()
    
    sys.exit(app.exec_())