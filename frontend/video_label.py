from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap
import cv2
import numpy as np

class VideoLabelWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.last_image = np.array(0)
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the video_label with a new opencv image"""
        self.last_image = cv_img

        h, w, ch = cv_img.shape
        aspect_ratio = w/h

        new_w = self.video_width
        new_h = int(new_w / aspect_ratio)

        if new_h > self.video_height:
            new_h = self.video_height
            new_w = int(new_h * aspect_ratio)

        resized_img = cv2.resize(cv_img, (new_w, new_h))
        rgb_image = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)

        convert_to_Qt_format = QtGui.QImage(rgb_image.data, new_w, new_h, ch * new_w, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(new_w, new_h, Qt.KeepAspectRatio)
        qt_img = QPixmap.fromImage(p)
        self.setPixmap(qt_img)
    
    def resizeEvent(self, event):
        self.video_width = event.size().width()
        self.video_height = event.size().height()
        if self.last_image.any() > 0: # self.last_image is defined. change this
            self.update_image(self.last_image)

        return super().resizeEvent(event)
