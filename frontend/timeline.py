
from PyQt5.QtWidgets import QWidget, QGraphicsSceneMouseEvent, QStyleOptionGraphicsItem, \
                            QVBoxLayout, QHBoxLayout, QPushButton, QGraphicsRectItem, \
                            QGraphicsPathItem, QGraphicsScene, QGraphicsView, QGraphicsTextItem
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QPainter
from PyQt5.QtCore import Qt, QRectF
import time

class EditVideo(QWidget):
    """
    Class responsible for editing the video, such as cutting, adding visual effects, etc
    Also provides buttons for pausing, and going back and forth frame by frame
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout()
        layout_buttons = QHBoxLayout()

        self.tracks = TracksView()
        self.tracks.create_slot_manager()

        self.pause_resume_button = QPushButton('Pause/Resume Video')
        #self.pause_resume_button.clicked.connect(self.video.thread.pause_resume)

        self.back_button = QPushButton('Back')
        #self.back_button.clicked.connect(self.video.thread.back)

        self.front_button = QPushButton('Front')
        #self.front_button.clicked.connect(self.video.thread.front)

        self.add_slot_button = QPushButton('Add Slot')
        #self.add_slot_button.clicked.connect(self.tracks.slots_manager.addSlot)

        layout_buttons.setContentsMargins(0,0,0,0)
        layout_buttons.addWidget(self.pause_resume_button)
        layout_buttons.addWidget(self.back_button)
        layout_buttons.addWidget(self.front_button)
        layout_buttons.addWidget(self.add_slot_button)

        main_layout.setContentsMargins(0,0,0,0)
        main_layout.addLayout(layout_buttons)
        main_layout.addWidget(self.tracks)

        self.setLayout(main_layout)

class VideoTrackSlot(QGraphicsRectItem):
    """
    Represents a video slot in TrackView's scene
    """
    def __init__(self, id, x, y, width, height, tracks_view):
        super().__init__(x,y,width,height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.slot_id = id
        self.tracks = []
        self.tracks_view = tracks_view

        # We set the Z level of the track slots
        # We want the track rectangles to be drawn on top of the track slots
        # That's why we assign a lower z value to the slots
        self.setZValue(0)

    def addTrack(self, seconds):
        """
        Adds a Video Track to the current slot
        seconds -> length of the track in seconds
        """
        vt = VideoTrack(seconds, self.x, self.y, self.tracks_view)
        self.tracks.append(vt)

        #returns the rectangle in VideoTrack
        return vt

"""
Class TrackRectangle
Rectangle that represents the track visually
We extend from QGraphicsPathItem so that we can override the function mouseMoveEvent, and make it
so that the rectangle can only be moved laterally, and not vertically.
"""
class VideoTrack(QGraphicsPathItem):
    base_snap_threshold = 10 # base threshold for two tracks to snap together
    base_unsnap_threshold  = 10 # base threshold for two tracks to unsnap

    def __init__(self, duration, x0, y0, tracks_view):

        self.duration = duration
        self.start_time = 0

        # Initializes the "pointer" to the TracksView object received as argument
        self.tracks_view = tracks_view

        # Initializes the number of frames of this video track rectangle
        self.nframes = round(self.tracks_view.track_fps * duration)
        
        border_roundness = 10
        # Create a QPainterPath object
        path = QPainterPath()
        # Add a rounded rectangle to the path
        path.addRoundedRect(QRectF(0, 0, self.nframes, self.tracks_view.track_height), border_roundness, border_roundness)
        super().__init__(path)

        # We set the position of the rectangle to the coordinates passed in the constructor
        self.setPos(x0, y0)

        # We set the Z value of the track rectangles to be higher than the slots
        self.setZValue(1)


        # is_clicked variable defines if the user is click holding the track
        self.is_clicked = False
        # snapped variable defined the track that the current track is snapped to
        self.snapped = None
        #sets the current rectangle as a movable item
        self.setFlag(QGraphicsPathItem.ItemIsMovable)

        # is_clicked brush
        self.clicked_brush = QBrush(QColor("yellow").darker(180)) # yellow 80% darker
        # not clicked brush
        self.not_clicked_brush = QBrush(QColor("black")) # Set fill color to black
        
        self.new_x = self.x()
        self.new_y = self.y()

        pen = QPen(QColor("yellow"))  # Set outline color to yellow
        pen.setWidth(10)  # Set the outline width
        self.setPen(pen)  # Apply the outline settings

        self.setBrush(self.not_clicked_brush)  # Apply the fill settings

        self.setFlag(QGraphicsPathItem.ItemIsMovable)

    @property
    def SNAP_THRESHOLD(self):
        zoom_level = self.tracks_view.zoom
        return self.base_snap_threshold / zoom_level
    
    @property
    def UNSNAP_THRESHOLD(self):
        zoom_level = self.tracks_view.zoom
        return self.base_unsnap_threshold / zoom_level
    
    def screen_to_scene_pix(self, pixels):
        view = self.scene().views()[0]
        return view.mapToScene(pixels,0).x() - view.mapToScene(0,0).x()
    
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        #sets is_clicked flag to True
        self.is_clicked = True
        # updates the visual of the rectangle (calls paint)
        self.update()
        
        return super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        #sets is_clicked flag to False
        self.is_clicked = False
        # updates the visual of the rectangle (calls paint)
        self.update()

        return super().mouseReleaseEvent(event)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget | None = ...) -> None:
        # The rectangle's inner color is light yellow when it's being held by the user,
        # and it is black when not held
        if self.is_clicked:
            self.setBrush(self.clicked_brush)
        else:
            self.setBrush(self.not_clicked_brush)

        return super().paint(painter, option, widget)
    
    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        new_pos = event.scenePos() 
        old_pos = event.lastScenePos()
        dx = new_pos.x() - old_pos.x() # change in x (delta)
        dy = new_pos.y() - old_pos.y() # change in y (delta)

        self.new_x = self.new_x + dx # new_x is old_x + the difference (delta)
        self.new_y = self.new_y + dy # new_y is old_y + the difference (delta)

        # rounds the rectangle to the nearest frame
        self.current_frame = round(self.new_x)

        # Gets the slot that contains the y position of the mouse cursor
        new_slot = self.tracks_view.slots_manager.getSlot(new_pos.y())

        # Y coordinate of the slot on top of the mouse
        slot_y = new_slot.y

        if slot_y != self.y():
            # If the user moved the track to another slot, we change the y of the track to that of the new slot
            self.setPos(self.x(), slot_y)


        if self.current_frame < 0:
            # the track can't get out of the scene, so if the new_x is <0, we set it to 0
            self.new_x = 0
            self.current_frame = 0
        #elif self.new_x + self.boundingRect().width() > self.scene().sceneRect().width():
        elif self.current_frame + self.nframes >= self.tracks_view.max_frames:
            # since the track can't go out of the scene, this includes to the right of the scene
            # so we check if the rightmost edge of the rectangle goes out of scope
            # self.new_x = self.scene().sceneRect().width() - self.boundingRect().width()
            self.new_x = self.tracks_view.max_frames - self.nframes - 1
            self.current_frame = self.tracks_view.max_frames - self.nframes - 1
        if self.snapped:
            # if the track is snapped to another track, we check if the new_x value is enough to unsnap
            snapped_track = self.snapped

            current_track_start = self.current_frame # start of current track
            current_track_end = self.current_frame + self.nframes # end of current track

            neighbor_track_start = snapped_track.x() # start of neighbor track
            neighbor_track_end = snapped_track.x() + snapped_track.nframes # end of neighbor track

            # if the distance between the two is above the unsnap threshold, we unsnap them
            if abs(current_track_start - neighbor_track_end) > self.UNSNAP_THRESHOLD and abs(current_track_end - neighbor_track_start) > self.UNSNAP_THRESHOLD:
                self.unsnap()
                snapped_track.unsnap()
                self.setPos(self.current_frame, self.y())
        else:
            # if the track isn't snapped to any track, we check among the other tracks if it is within distance
            # to being snapped
            snapPosition = None

            # We iterate through all neighbor tracks, to check if the current track is withing snapping distance
            for neighbor_track in self.scene().items():
                if neighbor_track == self or not isinstance(neighbor_track, type(self)):
                    continue
                
                # start and end x of the current track
                current_track_start = self.current_frame
                current_track_end = self.current_frame + self.nframes

                # start and end x of the neighbor track
                neighbor_track_start = neighbor_track.x()
                neighbor_track_end = neighbor_track.x() + neighbor_track.nframes
                
                # snap beggining of current track to end of neighbor track
                threshold = self.SNAP_THRESHOLD
                if abs(current_track_start - neighbor_track_end) < self.SNAP_THRESHOLD:
                    snapPosition = neighbor_track_end
                    self.snap(neighbor_track)
                    neighbor_track.snap(self)
                    break
                # snap end of current track to beggining of neighbor track
                elif abs(current_track_end - neighbor_track_start) < self.SNAP_THRESHOLD:
                    snapPosition = neighbor_track_start - self.nframes
                    self.snap(neighbor_track)
                    neighbor_track.snap(self)
                    break
            if snapPosition is not None:
                self.setPos(snapPosition, self.y())
            else:
                self.setPos(self.current_frame, self.y())
        
        seconds = self.x() / self.tracks_view.track_fps
        self.start_time = seconds

    def snap(self, other_track):
        # Defines the track that self is snapped to
        self.snapped = other_track
    
    def unsnap(self):
        # Unsnaps the current track with whatever track it had
        self.snapped = None

"""
Tracks View widget
This widget displays the video and audio tracks, and the cursor for the user to click and select the current time
It contains an array with the loaded video tracks, a variable which holds
"""
class TracksView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)  # Initialize the superclass

        # Initialize zoom level
        self.zoom = 1.0

        # Base fps of TracksView
        self.track_fps = 30
        # List to store video track items
        self.video_tracks = []

        self.track_offset = 10
        self.track_height = 50

        # Initialize a multiplier for the scene size relative to the view
        self.scene_mult = 10 #means scene is initialized 10x bigger than the view
        self.max_duration_hours = 10
        self.initial_duration_hours = 1

        self.max_frames = self.track_fps * 60 * 60 * self.max_duration_hours
        self.initial_view_frames = self.track_fps * 60 * 60 * self.initial_duration_hours

        self.pixels_per_frame = 1

        self.scene_width = self.max_frames * self.pixels_per_frame
        self.scene_height = 200 # fixed value

        # Create the scene and the view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        self.scene.setSceneRect(0, 0, self.scene_width, self.scene_height)

        # Calculate minimum zoom level
        self.min_zoom = 1 / (self.max_frames / self.view.width())
        # Set the anchor point for zoom transformations
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # Setup layout and add the view to it
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Apply initial zoom level
        self.applyZoom()

    def create_slot_manager(self):
        self.slots_manager = VideoTrackSlotManager(self.track_offset, self.track_height, self.max_frames, self)

    def drawTimeMarker(self):
        # Clear existing time marker items
        for item in self.scene.items():
            if isinstance(item, QGraphicsTextItem):
                self.scene.removeItem(item)

        # Determine granularity based on zoom level
        if self.zoom < 0.5:
            interval, time_format = 60, "%H:%M"
        elif 0.5 <= self.zoom < 1:
            interval, time_format = 10, "%H:%M"
        elif 1 <= self.zoom < 2:
            interval, time_format = 1, "%M:%S"
        else:
            interval, time_format = 0.1, "%M:%S"

        # Calculate pixel interval based on zoom level
        pixel_interval = interval * 100 * self.zoom

        # Get visible area to determine start and end
        visible_rect = self.view.mapToScene(self.view.rect()).boundingRect()
        start_x = visible_rect.left()
        end_x = visible_rect.right()

        # Draw ticks and labels
        x = (start_x // pixel_interval + 1) * pixel_interval
        while x < end_x:
            time_val = x / (100 * self.zoom)
            time_str = time.strftime(time_format, time.gmtime(time_val))
            text_item = self.scene.addText(time_str, QFont("Arial", 10))
            text_item.setPos(x, 10)
            text_item.setDefaultTextColor(Qt.red)
            x += pixel_interval
        
    def resizeEvent(self, event):
        """Handle resize events for the widget."""

        # recalculate the minimum zoom, because it depends on the width of the view
        self.min_zoom = 1 / (self.max_frames / self.view.width())
        super().resizeEvent(event)  # call the base class method
        #self.drawTimeMarker()

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""

        delta = event.angleDelta().y()
        if delta > 0:
            self.setZoom(self.zoom * 2)
            self.applyZoom()
        else:
            # Zoom out
            self.setZoom(self.zoom * 0.5)
            self.applyZoom()
            # Get the position of the current top-left corner
            topLeft = self.view.mapToScene(self.view.rect()).boundingRect().topLeft()
            # If the x-coordinate is less than 0, shift the view
            if topLeft.x() < 0:
                shift_x = -topLeft.x()
                self.view.translate(shift_x, 0)
        #self.drawTimeMarker()

    """
    This function adds a video track to the Tracks section. The size of the track depends on length of the video track.
    """
    def addTrack(self, seconds, slot=0):
        """Add a new track to the scene."""
        number_of_frames = self.track_fps * seconds # sets the number of frames that the track has

        vt = self.slots_manager.addTrack(seconds, slot)

        # we multiply by 1.25 so that a bit more frames are shown
        new_zoom = 1 / (number_of_frames * 1.25 / self.view.width())
        self.setZoom(new_zoom)
        self.applyZoom()

        # returns the created video track
        return vt
        
    def setZoom(self, new_zoom):
        """Set the zoom level, constrained by a minimum value."""
        if new_zoom > self.min_zoom:
            self.zoom = new_zoom
        else:
            self.zoom = self.min_zoom
        self.applyZoom()

    def applyZoom(self):
        self.view.resetTransform()
        self.view.scale(self.zoom, 1)


class VideoTrackSlotManager:
    """
    Video Track Slot Manager
    Manages the Slots of the TracksView class
    Provides functions for adding and removing video tracks
    y_offset -> initial offset of the first slot
    y_size -> y height of each slot
    scene_width -> length of the scene (important to calculate size of each slot rectangle)
    """
    def __init__(self, y_offset, y_size, scene_width, tracks_view):
        self.y_offset = y_offset
        self.y_size = y_size
        self.width = scene_width

        # Number of slots and the list with the slots
        self.current_slots = 0
        self.slots = []

        # Initializes the "pointer" to the TracksView object received as argument
        self.tracks_view = tracks_view

        # Adds the first slot
        self.addSlot()

    def getSlot(self, y_cord):
        """
        Given a y coordinate, returns the slot nearest to the y coordinate
        """
        slot = int ( (y_cord - self.y_offset) // self.y_size )
        if slot <= 0:
            return self.slots[0]
        elif slot >= self.current_slots:
            return self.slots[self.current_slots - 1]
        else:
            return self.slots[slot]

    def addSlot(self):
        """
        Adds a slot to the TracksView object
        """
        # Dimensions of the new slot

        x = 0
        y = self.y_offset + self.current_slots * self.y_size

        # Creates slot with given dimensions
        slot = VideoTrackSlot(self.current_slots, x, y, self.width, self.y_size, self.tracks_view)
        # Adds the slot to the list of slots
        self.slots.append(slot)
        # Increments number of slots
        self.current_slots += 1

        # Adds the slot to the scene
        self.tracks_view.scene.addItem(slot)
        print("added slot")
        return slot
    
    def addTrack(self, seconds, slot=0):
        """
        Adds a Video Track to given slot
        seconds -> length of the track in seconds
        slot -> slot to add the track
        """
        vt = self.slots[slot].addTrack(seconds)
        self.tracks_view.scene.addItem(vt)

        # returns the created video track
        return vt

    def removeSlot(self):

        # Decreases the number of slots
        self.current_slots -= 1

        # Pops from the list of slots the last slot
        slot = self.slots.pop()

        # Removes the slot from the scene
        self.tracks_view.scene.removeItem(slot)
