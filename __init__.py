from PyQt5.QtWidgets import QApplication
import sys
from PyQt5.QtWidgets import QGridLayout, QWidget, QApplication
import sys
from frontend import sidebar, timeline, video_label
from backend import video


"""
MainWindow class
It has a grid layout, where the video sits on the top right corner, the buttons sit on the left side, the content of
the buttons sit to the right of the buttons, and the edit video section sits on the bottom of the screen

The proportions of each widget are passed in to their constructors
"""
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._initializeWidgets()
        self._linkWidgets()

    def _initializeWidgets(self):
        main_layout = QGridLayout()
        # create the video capture thread and gui

        self.setWindowTitle("Video Player")
        self.display_width = 1920
        self.display_height = 1080
        
        self.resize(self.display_width, self.display_height)

        self.video_label = video_label.VideoLabelWidget()
        self.video_player = video.VideoPlayer(self.video_label)
        self.edit_video = timeline.EditVideo()
        self.sidebar = sidebar.MySidebar()
        self.sidebar_content = sidebar.SidebarContent(self.sidebar, self.video_player, self.edit_video.tracks)

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

    def _linkWidgets(self):
        self.edit_video.pause_resume_button.clicked.connect(self.video_player.thread.pause_resume)
        self.edit_video.back_button.clicked.connect(self.video_player.thread.back)
        self.edit_video.front_button.clicked.connect(self.video_player.thread.front)
        self.edit_video.add_slot_button.clicked.connect(self.edit_video.tracks.slots_manager.addSlot)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()