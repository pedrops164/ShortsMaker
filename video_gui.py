from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import sys
from video import VideoLabelWidget, EditVideo
from sidebar import SidebarContent, MySidebar


"""
App class
It has a grid layout, where the video sits on the top right corner, the buttons sit on the left side, the content of
the buttons sit to the left of the buttons, and the edit video section sits on the bottom of the screen

The proportions of each widget are passed in to their constructors
"""
class App(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QGridLayout()
        # create the video capture thread and gui

        self.setWindowTitle("Video Player")
        self.display_width = 1920
        self.display_height = 1080
        
        self.resize(self.display_width, self.display_height)

        self.video_label = VideoLabelWidget()
        self.edit_video = EditVideo(self.video_label)
        self.sidebar = MySidebar()
        self.sidebar_content = SidebarContent(self.sidebar, self.video_label)

        main_layout.addWidget(self.sidebar, 0, 0)
        main_layout.addWidget(self.sidebar_content, 0, 1) # first row, snd column
        main_layout.addWidget(self.video_label, 0, 2)
        main_layout.addWidget(self.edit_video, 1, 1, 1, 2) #spans one row, two columns

        # set row stretch factors
        main_layout.setRowStretch(0, 7)  # 70%
        main_layout.setRowStretch(1, 3)  # 30%

        # set column stretch factors
        main_layout.setColumnStretch(0, 5)  # 5%
        main_layout.setColumnStretch(1, 25)  # 25%
        main_layout.setColumnStretch(2, 70)  # 70%

        self.setLayout(main_layout)

        #self.edit_video.update_view()

app = QApplication(sys.argv)
a = App()
# a.showFullScreen()
a.show()
sys.exit(app.exec_())