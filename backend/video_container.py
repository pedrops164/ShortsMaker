import cv2
from enum import Enum

class Video():
    def __init__(self, id, total_frames, fps, length_seconds) -> None:
        self.id = id
        self.total_frames = total_frames
        self.fps = fps
        self.length_seconds = length_seconds
        pass

class VideoContainer():
    def __init__(self):
        self.videos = []
        self.container = AVLTree()
        self.videos_counter = 0

    def addVideo(self, video_path):
        # Capture video
        cap = cv2.VideoCapture(video_path)
        # Get total number of frames
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Get fps of the video
        fps = cap.get(cv2.CAP_PROP_FPS)
        # Get the length of the video in seconds
        length_seconds = total_frames / fps

        video = Video(self.videos_counter, total_frames, fps, length_seconds)
        self.videos.append(video)

        self.videos_counter += 1

        # returns the id of the created video, and the length in seconds
        return video.id, video.length_seconds
        
        cap.release()

class TrackFlag(Enum):
    START=1
    END=2

class TreeNode:
    def __init__(self, time, track, height=1):
        """
        Creates a Node for the AVLTree, which represents a start or end time in a track
        """
        # time 
        self.time = time
        # video track associated with this node
        self.track = track
        # height of the current tree
        self.height = height

        # left subtree
        self.left = None
        # right subtree
        self.right = None

class AVLTree:
    def __init__(self):
        self.root = None

    def get_height(self, node):
        if not node:
            return 0
        return node.height

    def get_balance(self, node):
        if not node:
            return 0
        return self.get_height(node.left) - self.get_height(node.right)

    def left_rotate(self, z):
        y = z.right
        T2 = y.left

        y.left = z
        z.right = T2

        z.height = 1 + max(self.get_height(z.left), self.get_height(z.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))

        return y

    def right_rotate(self, y):
        x = y.left
        T2 = x.right

        x.right = y
        y.left = T2

        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))

        return x

    def insert(self, time):
        if not self.root:
            self.root = TreeNode(time)
            return

        self.root = self._insert(self.root, time)

    def _insert(self, node, time):
        if not node:
            return TreeNode(time)

        if time < node.time:
            node.left = self._insert(node.left, time)
        else:
            node.right = self._insert(node.right, time)

        node.height = 1 + max(self.get_height(node.left), self.get_height(node.right))

        balance = self.get_balance(node)

        # Left heavy
        if balance > 1:
            if time < node.left.time:  # Left-Left
                return self.right_rotate(node)
            else:  # Left-Right
                node.left = self.left_rotate(node.left)
                return self.right_rotate(node)

        # Right heavy
        if balance < -1:
            if time > node.right.time:  # Right-Right
                return self.left_rotate(node)
            else:  # Right-Left
                node.right = self.right_rotate(node.right)
                return self.left_rotate(node)

        return node

    def search(self, time):
        return self._search(self.root, time)

    def _search(self, node, time):
        if node is None or node.time == time:
            return node
        if time < node.time:
            return self._search(node.left, time)
        return self._search(node.right, time)

    def next_larger(self, time):
        node = self.search(time)
        return self._next_larger(self.root, node)

    def _next_larger(self, root, node):
        if node.right:
            return self._min_value_node(node.right)
        successor = None
        while root:
            if node.time < root.time:
                successor = root
                root = root.left
            elif node.time > root.time:
                root = root.right
            else:
                break
        return successor

    def _min_value_node(self, node):
        current = node
        while current.left:
            current = current.left
        return current
    
    def delete(self, key):
        self.root = self._delete(self.root, key)

    def _delete(self, root, key):
        if not root:
            return root

        # First, handle standard BST delete
        if key < root.key:
            root.left = self._delete(root.left, key)
        elif key > root.key:
            root.right = self._delete(root.right, key)
        else:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left
            root.key = self._min_value_node(root.right).key
            root.right = self._delete(root.right, root.key)

        # Update height of the current node
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))

        # Now handle AVL rotations if needed
        balance = self.get_balance(root)

        # Left heavy
        if balance > 1:
            if self.get_balance(root.left) >= 0:  # Left-Left
                return self.right_rotate(root)
            else:  # Left-Right
                root.left = self.left_rotate(root.left)
                return self.right_rotate(root)

        # Right heavy
        if balance < -1:
            if self.get_balance(root.right) <= 0:  # Right-Right
                return self.left_rotate(root)
            else:  # Right-Left
                root.right = self.right_rotate(root.right)
                return self.left_rotate(root)

        return root