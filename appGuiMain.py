__authors__ = ["Just Yuri", 'Petaaar']

from appJar import gui
from threading import Thread
from PIL import Image
from serial import Serial
import os
import cv2
import numpy as np


class Gui:
    """"
        The Graphic User Interface class.
        Responsible for getting, setting and saving the caps as different template arguments.
        Code written by JustYuri.
        Code documentation, restrictions and bugfixes by Petaaar.
    """
    def __init__(self, cord_a, cord_b, cord_c, cord_d, video_device=None):
        """
            Creates a new instance of the Gui class with specified params:
            :param: coord_a: The upper left X coordinate
            :param: coord_b: The upper left Y coordinate
            :param: coord_c: The down right X coordinate
            :param: coord_d: The down right Y coordinate
            :param: video_device: The video device to be used. 0 by default.
        """

        #: The main gui object
        self.app = gui("Choose your action", "620x480")

        #: Image path for the full images
        self.FULL_IMAGE_PATH = "./result/"

        #: The images used for recognition path
        self.RECOGNIZE_PATH_IMAGES = "./src/"

        #: Coord A of the rectangle
        self._COORD_A = cord_a

        #: Coord B of the rectangle
        self._COORD_B = cord_b

        #: Coord C of the rectangle
        self._COORD_C = cord_c

        #: Coord D of the rectangle
        self._COORD_D = cord_d

        #: Set the video device properly
        if video_device is None:
            self._VIDEO_DEVICE = 0
        else:
            self._VIDEO_DEVICE = video_device

        #: The opencv object
        self.cap = cv2.VideoCapture(self._VIDEO_DEVICE)

        #: The capup Thread.
        self._UP_THREAD = None

        #: The capdown Thread.
        self._DOWN_THREAD = None

        #: The Real Time Recognition Thread
        self._REAL_TIME_THREAD = None

        # the serial port connection
        self._serialConnection = None

    @staticmethod
    def _handle_cap_cutting(picture, cords, loc):
        """
        Handle cap_up recognition
        :param picture: The picture to cut
        :param cords: The coordinates of the cap
        :param loc: Where to save it
        :return: Weather the operation succeeded
        """
        try:
            img = Image.open(picture)
            cropped_image = img.crop(cords)
            cropped_image.save(loc)
            return True
        except Exception as e:
            print(e)
            return False

    def _handle_cap_up_button(self):
        """
            Handles an upside bottle cap and saves it as a template image.
            :returns: boolean -> Whether the process was successful
        """
        _, frame = self.cap.read()
        try:
            cv2.imwrite(self.FULL_IMAGE_PATH+"capup.jpeg", frame)
            if self._handle_cap_cutting(self.FULL_IMAGE_PATH+"capup.jpeg", (self._COORD_A, self._COORD_B, self._COORD_C, self._COORD_D),
                                  self.RECOGNIZE_PATH_IMAGES+"cap_up.jpeg"):
                self.app.infoBox("Success", "The cap was saved. You can use it now.")
                self._UP_THREAD = None
                return True
            else:
                self.app.errorBox("Error", "Sorry, the cap was not saved, please try again.")
                return False
        except Exception as e:
            print(e)
            return False

    def _handle_cap_down_button(self):
        """
            Handles an upside-down bottle cap and saves it as a template image.
            :returns: boolean -> Whether the process was successful
        """
        _, frame = self.cap.read()
        _, frame = self.cap.read()
        try:
            cv2.imwrite(self.FULL_IMAGE_PATH + "DOWN.jpeg", frame)
            if self._handle_cap_cutting(self.FULL_IMAGE_PATH + "DOWN.jpeg", (self._COORD_A, self._COORD_B, self._COORD_C, self._COORD_D), self.RECOGNIZE_PATH_IMAGES + "cap_down.jpeg"):
                self.app.infoBox("Success", "The cap was saved. You can use it now.")
                self._DOWN_THREAD = None
                return True
            else:
                self.app.errorBox("Error", "Sorry, the cap was not saved, please try again.")
                return False
        except Exception as e:
            print(e)
            return False

    def _draw_square(self, upside, loc, frame, w, h, rect_color=(255, 255, 0), text_color=(0, 255, 0)):
        """
        Draws the square around the cap.
        Credits to Petaaar for writing this function.
        The function is from the unified.py file.
        :param loc: The location of the cap
        :param frame: The frame that we are going to draw to
        :param w: Width of the rectangle
        :param h: Height of the rectangle
        :param rect_color: Color of the rectangle (RGB)
        :param text_color: Color of the text (RGB)
        :returns: None
        """

        self._shut_down_lamps()

        if upside:
            text = "UPSIDE"
            color = b'G'
        else:
            text = "DOWNSIDE"
            color = b'R'
        for pt in zip(*loc[::-1]):
            cv2.rectangle(frame, pt, (pt[0] + w, pt[1] + h), rect_color, 1)
            cv2.putText(frame, text, (50, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, .7, text_color)
            self._serialConnection.write(color)

    def _shut_down_lamps(self):
        self._serialConnection.write(b'r')
        self._serialConnection.write(b'b')
        self._serialConnection.write(b'g')

    def _handle_image_recognition(self):
        """
        The real time image recognition functionality
        You can see this code in the unified.py file. Here is just used for the gui.
        Credits to Petaaar for writing it.
        :returns:
        """
        kill = False
        self._serialConnection = Serial('COM4', 9600)
        while 1:

            for directory, subdirectories, files in os.walk(self.RECOGNIZE_PATH_IMAGES):
                for filename in files:
                    template = cv2.imread(self.RECOGNIZE_PATH_IMAGES+filename, 0)
                    w, h = template.shape[::-1]
                    threshold = 0.9

                    _, frame = self.cap.read()
                    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    res = cv2.matchTemplate(frame_gray, template, cv2.TM_CCOEFF_NORMED)
                    loc = np.where(res > threshold)

                    if filename.endswith('_up.jpeg'):
                        self._draw_square(True, loc, frame, w, h)
                    elif filename.endswith('_down.jpeg'):
                        self._draw_square(False, loc, frame, w, h, (0, 0, 255))

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        kill = True

                    cv2.imshow("Camera view", frame)

            if kill:
                break
        self.cap.release()
        cv2.destroyAllWindows()
        self._REAL_TIME_THREAD = None  # clear the thread, so it can be used again.

    def _handle_buttons(self, button):
        """
            Handles the action of clicking a named button object.
            :param: button: the button to be checked for. If everything works the button spawns a new thread to work on.
            :returns: error box if something is not working properly
        """
        if button == "CapUp":
            # start working on 'CapUp' actions
            if self._UP_THREAD is None:
                self._UP_THREAD = Thread(name="CapUpThread", target=self._handle_cap_up_button)

            if self._UP_THREAD.is_alive():
                return self.app.errorBox("ERROR", "You need to wait the process to finish.")
            else:
                self._UP_THREAD.start()

        if button == "CapDown":
            # start working on 'CapDown' actions
            if self._DOWN_THREAD is None:
                self._DOWN_THREAD = Thread(name="CapDownThread", target=self._handle_cap_down_button)

            if self._DOWN_THREAD.is_alive():
                return self.app.errorBox("ERROR", "You need to wait the process to finish")
            else:
                self._DOWN_THREAD.start()

        if button == "RealTime":
            # start real-time capturing
            if self._REAL_TIME_THREAD is None:
                self._REAL_TIME_THREAD = Thread(name="RealTimeThread", target=self._handle_image_recognition)
                try:
                    self._REAL_TIME_THREAD.start()
                except Exception:
                    return self.app.errorBox('UNEXPECTED ERROR', 'Starting real-time capturing again raised an error.'
                                                                 ' Please, restart the program.')
            elif self._REAL_TIME_THREAD.is_alive():
                return self.app.errorBox("ERROR", "You need to close the process to first")
            else:
                self._REAL_TIME_THREAD.start()

    def _build_gui(self):
        """
            'Builds' the GUI for the program, sets the basis of the program's actions.
            :return: void
        """
        self.app.startLabelFrame("Functions")
        self.app.addButton("CapUp", func=self._handle_buttons)
        self.app.addButton("CapDown", func=self._handle_buttons)
        self.app.addButton("RealTime", func=self._handle_buttons)
        self.app.stopLabelFrame()

    def run_app(self):
        """
            The starting point of the application.
            :return:
        """
        self._build_gui()
        self.app.go()

    def __del__(self):
        self._shut_down_lamps()


if __name__ == '__main__':
    c = Gui(175, 103, 534, 427, video_device=1)
    c.run_app()
