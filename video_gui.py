from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QTabWidget, QTabBar
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt,QObject, QThread, QMutex, QWaitCondition
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
        #self.wait()

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Player")
        self.display_width = 1920
        self.display_height = 1080
        # create the label that holds the image
        self.image_label = QLabel(self)
        # create a text label
        self.pause_resume_button = QPushButton('Pause/Resume Video')
        self.pause_resume_button.clicked.connect(self.pause_resume_video)

        self.sidebar = QTabWidget()
        self.sidebar.setFixedWidth(500)
        self.sidebar.setTabPosition(QTabWidget.West)

        square_button_style = """
        QTabBar::tab {
            width: 100px;
            height: 100px;
            border: 1px solid #555;
            margin: 2px;
            padding: 5px;
            border-radius: 5px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #EDEDED, stop: 1.0 #DDDDDD);
        }

        QTabBar::tab:selected {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #DDDDDD, stop: 1.0 #EDEDED);
        }
        """

        self.sidebar.setStyleSheet(square_button_style)

        # Create the tabs for the sidebar
        self.options_tab = QWidget()
        self.video_tab = QWidget()
        self.text_tab = QWidget()
        self.subtitles_tab = QWidget()
        self.audio_tab = QWidget()

        self.sidebar.addTab(self.options_tab, "Options")
        self.sidebar.addTab(self.video_tab, "Video")
        self.sidebar.addTab(self.text_tab, "Text")
        self.sidebar.addTab(self.subtitles_tab, "Subtitles")
        self.sidebar.addTab(self.audio_tab, "Audio")

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.pause_resume_button)
        # set the vbox layout as the widgets layout

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.sidebar)
        main_layout.addLayout(vbox)

        self.setLayout(main_layout)

        # create the video capture thread
        self.thread = VideoThread('input/video2.mp4', 25)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def pause_resume_video(self):
        self.thread.pause_resume()

    #def closeEvent(self, event):
    #    self.stop_video()
    #    event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

app = QApplication(sys.argv)
a = App()
# a.showFullScreen()
a.resize(1920, 1440)
a.show()
sys.exit(app.exec_())