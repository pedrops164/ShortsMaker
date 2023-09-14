import typing
from PyQt5 import QtWidgets, QtGui, QtCore
#from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton, QGridLayout, QTabWidget, QStackedWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QPen, QBrush, QColor, QPainterPath, QFont, QTransform
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QMutex, QWaitCondition, QRectF
from PyQt5.QtWidgets import QGraphicsSceneMouseEvent
import numpy as np
import sys
import cv2
import time
from tracks import TracksView

class Video:
    def __init__(self, inputpath, fps):
        self.frame_interval_ms = int((1 / fps) * 1000) # turn seconds to ms
        self.current_frame = -1
        self.nframes = 0
        self.frames = []

        cap = cv2.VideoCapture(inputpath)

        if (cap.isOpened()== False): 
            print("camera not opened")
            return
            # Give a error message
            
        while cap.isOpened():
            ret, cv_img = cap.read()
            if ret:
                self.frames.append(cv_img)
                self.nframes += 1
            else:
                break

    def previous_frame(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            return True, self.frames[self.current_frame]
        else:
            return False, None

    def next_frame(self):
        self.current_frame += 1
        if self.current_frame < self.nframes:
            return True, self.frames[self.current_frame]
        else:
            self.current_frame = -1
            return False, None
        
    def current_frame(self):
        if self.current_frame < 0:
            raise ValueError("Current frame index must be >= 0")
        if self.current_frame >= self.nframes:
            raise ValueError("Current frame index must be < number of frames")
        return True, self.frames[self.current_frame]
        
    def skip_front(self):
        self.current_frame += 1

    def skip_back(self):
        self.current_frame -= 1
    
    def get_frame(self, frame_idx):
        return self.frames[frame_idx]

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, inputpath, fps):
        super().__init__()
        self.mutex = QMutex()
        self.condv = QWaitCondition()
        self.running = True
        self.paused = False
        self.video = Video(inputpath, fps)

    def back(self):
        if not self.running:
            ret, cv_img = self.video.previous_frame()

            if ret:
                self.change_pixmap_signal.emit(cv_img)
    
    def front(self):
        if not self.running:
            ret, cv_img = self.video.next_frame()

            if ret:
                self.change_pixmap_signal.emit(cv_img)


    def run(self):

        while True:

            self.mutex.lock()
            if not self.running:
                # the video is paused, this thread waits
                self.condv.wait(self.mutex)
            self.mutex.unlock()

            ret, cv_img = self.video.next_frame()

            if ret:
                self.change_pixmap_signal.emit(cv_img)
                self.msleep(self.video.frame_interval_ms)  # Add a delay between frames

                # cant use this with opencv-python-headless!!!
                # Press Q on keyboard to exit
                #if cv2.waitKey(25) & 0xFF == ord('q'):
                #    break
            else:
                self.pause_resume()
                #break

    def stop(self):
        #sets running flag to false and waits for the thread to finish
        self.running = False
        self.wait()

    def pause_resume(self):
        #sets running flag to false and waits for the thread to finish
        self.mutex.lock()
        self.running = not(self.running)

        if self.running:
            # The video was resumed, need to wake up worker thread
            self.condv.wakeAll()
            
        self.mutex.unlock()

class VideoLabelWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.last_image = np.array(0)

        self.thread = VideoThread('input/video2.mp4', 25)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: black;")

    def pause_resume(self):
        self.thread.pause_resume()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the video_label with a new opencv image"""
        self.last_image = cv_img
        qt_img = self.convert_cv_qt(cv_img)
        self.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
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
        return QPixmap.fromImage(p)
    
    def resizeEvent(self, event):
        self.video_width = event.size().width()
        self.video_height = event.size().height()
        if self.last_image.any() > 0: # self.last_image is defined. change this
            self.update_image(self.last_image)

        return super().resizeEvent(event)


class EditVideo(QWidget):
    def __init__(self, video, parent=None):
        super().__init__(parent)

        self.video = video
        main_layout = QVBoxLayout()
        layout_buttons = QHBoxLayout()

        #self.scene = QGraphicsScene()
        #self.view = QGraphicsView(self.scene)
        self.tracks = TracksView()
        self.tracks.create_slot_manager()

        #self.video_track1 = QGraphicsRectItem(QRectF(0,0,100,50))
        #self.scene.setSceneRect(0,0,self.view.width(),self.view.height())
        #self.scene.addItem(self.video_track1)

        self.pause_resume_button = QPushButton('Pause/Resume Video')
        self.pause_resume_button.clicked.connect(self.video.pause_resume)

        self.back_button = QPushButton('Back')
        self.back_button.clicked.connect(self.video.thread.back)

        self.front_button = QPushButton('Front')
        self.front_button.clicked.connect(self.video.thread.front)

        self.add_track_button = QPushButton('Add Track')
        # Add an example track of length 1 hour to the first slot
        self.add_track_button.clicked.connect(lambda: self.tracks.addTrack(3600, 0))

        self.add_slot_button = QPushButton('Add Slot')
        self.add_slot_button.clicked.connect(self.tracks.slots_manager.addSlot)

        layout_buttons.setContentsMargins(0,0,0,0)
        layout_buttons.addWidget(self.pause_resume_button)
        layout_buttons.addWidget(self.back_button)
        layout_buttons.addWidget(self.front_button)
        layout_buttons.addWidget(self.add_track_button)
        layout_buttons.addWidget(self.add_slot_button)

        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addLayout(layout_buttons)
        main_layout.addWidget(self.tracks)

        self.setLayout(main_layout)

    def update_view(self):
        self.tracks.scene.setSceneRect(0,0,self.tracks.view.width()*2,self.tracks.view.height()*2)