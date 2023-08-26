import typing
from PyQt5 import QtWidgets, QtGui, QtCore
#from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton, QGridLayout, QTabWidget, QStackedWidget
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt,QObject, QThread, QMutex, QWaitCondition
from PyQt5.QtWidgets import QWidget
import numpy as np
import sys
import cv2

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, inputpath, fps):
        super().__init__()
        self.inputpath = inputpath
        self.frame_interval_ms = int((1 / fps) * 1000) # turn seconds to ms
        self.mutex = QMutex()
        self.condv = QWaitCondition()
        self.running = True
        self.paused = False


    def run(self):
        # capture from web cam
        cap = cv2.VideoCapture(self.inputpath)

        if (cap.isOpened()== False): 
            print("camera not opened")
            return
            # Give a error message
            
        while cap.isOpened():
            self.mutex.lock()
            if not self.running:
                # the video is paused, this thread waits
                self.condv.wait(self.mutex)
            self.mutex.unlock()

            ret, cv_img = cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
                self.msleep(self.frame_interval_ms)  # Add a delay between frames

                # cant use this with opencv-python-headless!!!
                # Press Q on keyboard to exit
                #if cv2.waitKey(25) & 0xFF == ord('q'):
                #    break
            else:
                break

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
    def __init__(self, display_width, display_height, parent=None):
        super().__init__(parent)

        self.thread = VideoThread('input/video2.mp4', 25)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

        self.display_width = display_width
        self.display_height = display_height
        self.video_width = int(0.7*display_width)
        self.video_height = int(0.7*display_height)

        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(int(self.video_width), int(self.video_height))
        self.setStyleSheet("background-color: black;")

    def pause_resume(self):
        self.thread.pause_resume()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the video_label with a new opencv image"""
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

class EditVideo(QWidget):
    def __init__(self, video, parent=None):
        super().__init__(parent)

        self.video = video
        layout = QGridLayout()

        self.pause_resume_button = QPushButton('Pause/Resume Video')
        self.pause_resume_button.clicked.connect(self.pause_resume_video)
        self.setFixedSize(int(0.9 * self.video.display_width), int(0.3 * self.video.display_height))
        layout.addWidget(self.pause_resume_button)

        self.setLayout(layout)


    def pause_resume_video(self):
        self.video.pause_resume()

class MySidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        sidebar_layout = QVBoxLayout()

        self.btn_options = QPushButton("Options")
        self.btn_media = QPushButton("Media")
        self.btn_audio = QPushButton("Audio")

        sidebar_layout.addWidget(self.btn_options)
        sidebar_layout.addWidget(self.btn_media)
        sidebar_layout.addWidget(self.btn_audio)

        self.sidebar_widget = QWidget()
        self.sidebar_widget.setLayout(sidebar_layout)

class SidebarContent(QStackedWidget):
    def __init__(self, sidebar, video, parent=None):
        super().__init__(parent)

        self.sidebar = sidebar
        self.video = video

        self.setFixedSize(int(0.2 * self.video.display_width), int(0.7 * self.video.display_height))
        self.content_options = QLabel("Options")
        self.content_media = QLabel("Media")
        self.content_audio = QLabel("Audio")

        content_style = """
            QLabel {
                border: 3px solid gray;
                background-color: white;
                min-height: 150px;
                min-width: 150px;
            }
        """
        self.content_options.setStyleSheet(content_style)
        self.content_media.setStyleSheet(content_style)
        self.content_audio.setStyleSheet(content_style)

        self.addWidget(self.content_options)
        self.addWidget(self.content_media)
        self.addWidget(self.content_audio)
        
        self.sidebar.btn_options.clicked.connect(lambda: self.setCurrentWidget(self.content_options))
        self.sidebar.btn_media.clicked.connect(lambda: self.setCurrentWidget(self.content_media))
        self.sidebar.btn_audio.clicked.connect(lambda: self.setCurrentWidget(self.content_audio))

class App(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QGridLayout()
        # create the video capture thread and gui

        self.setWindowTitle("Video Player")
        self.display_width = 1920
        self.display_height = 1080

        self.video_label = VideoLabelWidget(self.display_width, self.display_height)
        
        self.edit_video = EditVideo(self.video_label)
        
        self.sidebar = MySidebar()
        self.sidebar_content = SidebarContent(self.sidebar, self.video_label)

        main_layout.addWidget(self.sidebar, 0, 0)
        main_layout.addWidget(self.sidebar_content, 0, 1) # first row, snd column
        main_layout.addWidget(self.video_label, 0, 2)
        main_layout.addWidget(self.edit_video, 1, 1, 1, 2) #spans one row, two columns

        #main_layout.setColumnStretch(0, 1) #10% first column
        #main_layout.setColumnStretch(1, 1)
        #main_layout.setColumnStretch(2, 1)

        self.setLayout(main_layout)


app = QApplication(sys.argv)
a = App()
# a.showFullScreen()
a.resize(1920, 1080)
a.show()
sys.exit(app.exec_())