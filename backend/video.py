from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QMutex, QWaitCondition
import numpy as np
import cv2
from backend import video_container

class Video:
    """
    The Video class is responsible for storing the metadata of a video (title, duration)
    It provides functionality for playing a video (from the beggining or from a certain frame)
    """
    def __init__(self, inputpath):
        # Capture video
        self.cap = cv2.VideoCapture(inputpath)
        # Get total number of frames
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Get fps of the video
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        # Get the length of the video in seconds
        self.length = self.total_frames / self.fps
        # Interval between frames in milisseconds
        self.frame_interval_ms = int((1 / self.fps) * 1000) # turn seconds to ms
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, -1)
        # self.current_frame = -1

        if (self.cap.isOpened() == False): 
            print("camera not opened")
            return
            

    def __del__(self):
        self.cap.release()

    def previous_frame(self):
        current_frame = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        if current_frame > 0:
            current_frame -= 1
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame-1)
            return self.cap.read()
        else:
            return False, None

    def next_frame(self):
        """ Reads the next frame as returns it """
        if self.cap.isOpened() and self.cap.get(cv2.CAP_PROP_POS_FRAMES) < self.total_frames-1:
            return self.cap.read()
        else:
            return False, None

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.mutex = QMutex()
        self.condv = QWaitCondition()
        self.running = False
        self.paused = True
        self.video = None

    def back(self):
        # if a video is loaded and it is running, return the previous frame
        if not self.running and self.video:
            ret, cv_img = self.video.previous_frame()

            if ret:
                self.change_pixmap_signal.emit(cv_img)
    
    def front(self):
        # if a video is loaded and it is running, return the next frame
        if not self.running and self.video:
            ret, cv_img = self.video.next_frame()

            if ret:
                self.change_pixmap_signal.emit(cv_img)

    def run(self):

        while True:

            self.mutex.lock()
            if not self.running or not self.video:
                # the video is paused, this thread waits
                self.condv.wait(self.mutex)
            self.mutex.unlock()

            if self.video:
                # if there is a video currently loaded, gets the next frame
                ret, cv_img = self.video.next_frame()
            else:
                # if there is no video currently loaded, returns no frame
                ret, cv_img = False, None

            if ret:
                self.change_pixmap_signal.emit(cv_img)
                self.msleep(self.video.frame_interval_ms)  # Add a delay between frames
            else:
                self.pause_resume()
                #break

    def setCurrentVideo(self, video, frame=0):
        """
        Sets the video being played by the thread to the video received in the argument, starting in 
        the frame received in the argument.
        """
        video.cap.set(cv2.CAP_PROP_POS_FRAMES, frame-1)
        self.video = video


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

class VideoPlayer:
    def __init__(self, video_widget) -> None:
        
        self.thread = VideoThread()
        # connects the change pixmap signal to the slot that is the update_image method of the video_widget
        self.thread.change_pixmap_signal.connect(video_widget.update_image)
        # start the thread
        self.thread.start()
        #self.thread.setCurrentVideo(Video('input/video2.mp4'))

        self.video_database = video_container.VideoContainer()

    def addVideo(self, video_path):
        # Adds a video to the database of videos, and returns the id and length in seconds of the video
        id, length = self.video_database.addVideo(video_path)
        return id, length