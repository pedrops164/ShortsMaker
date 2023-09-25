from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QVBoxLayout, QFileDialog, QToolButton

class MySidebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        sidebar_layout = QVBoxLayout()

        self.btn_options = QPushButton("Options")
        self.btn_media = QToolButton()
        self.btn_audio = QPushButton("Audio")

        # Button style
        btn_style = """
            QToolButton {
                border-radius: 25px;
                background-color: #4CAF50;
                color: white;
                padding: 5px;  # Some padding for aesthetics
            }
        """
        
        self.btn_media.setIcon(QIcon('images/media.png'))
        self.btn_media.setIconSize(QSize(60, 60))
        self.btn_media.setText("Media")
        self.btn_media.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        #self.btn_media.setStyleSheet(btn_style)

        sidebar_layout.addWidget(self.btn_options)
        sidebar_layout.addWidget(self.btn_media)
        sidebar_layout.addWidget(self.btn_audio)

        self.setLayout(sidebar_layout)


class SidebarContent(QStackedWidget):
    def __init__(self, sidebar, video_player, tracks_view, parent=None):
        super().__init__(parent)

        self.sidebar = sidebar
        self.video_player = video_player
        self.tracks_view = tracks_view

        #self.setFixedSize(int(0.2 * self.video.display_width), int(0.7 * self.video.display_height))
        self.content_options = QLabel("Options")
        self.content_media = QLabel()
        self.content_audio = QLabel("Audio")

        self.import_video_btn = QPushButton("Import Video")
        self.import_video_btn.clicked.connect(self.import_video)

        self.content_media_layout = QVBoxLayout()
        self.content_media_layout.addWidget(self.import_video_btn)
        self.content_media.setLayout(self.content_media_layout)

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

    def import_video(self):
        """
        This function opens a File Dialog for the user to select the video, and after the user selects the video,
        the track with the video is added to the TracksView object
        """
        options = QFileDialog.Options()
        video_path, _ = QFileDialog.getOpenFileName(self, "Import Video", "", "Video Files (*.mp4 *.avi *.mkv *.mov);;All Files (*)", options=options)
        if video_path:
            # adds to the video player the video with the given path. Gets the id and length of the created video
            id, length = self.video_player.addVideo(video_path)

            # Adds a track to the tracks view section of the gui with duration 'length'
            self.tracks_view.addTrack(length)