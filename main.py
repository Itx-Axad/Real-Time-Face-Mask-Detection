import sys

import imutils
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils.video import VideoStream
from pygame import mixer
import numpy as np
import cv2

from GUI import Ui_MainWindow

prototxt = "deploy.prototxt"
weights = "res10_300x300_ssd_iter_140000.caffemodel"
net = cv2.dnn.readNet(prototxt, weights)
model = load_model('RTFMD_model.h5')


class Main:

    def __init__(self):

        self.main_window = QtWidgets.QMainWindow()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.main_window)

        self.image_path = ""
        self.ui.pushButton_3.clicked.connect(self.upload_image)
        self.ui.pushButton_2.clicked.connect(self.predict_image_results)
        self.ui.pushButton.clicked.connect(self.detect_on_video)
        self.ui.pushButton_4.clicked.connect(sys.exit)
        self.streaming = False

    # Maximize and minimize function
    def maximize_minimize_window(self):
        if self.main_window.isMaximized():
            self.main_window.showNormal()
        else:
            self.main_window.showMaximized()

    def upload_image(self):
        # open the dialogue box to select the file
        options = QtWidgets.QFileDialog.Options()

        # open the Dialogue box to get the images paths
        image = QtWidgets.QFileDialog.getOpenFileName(caption="Select the image", directory="",
                                                      filter="Image Files (*.jpg);;Image Files (*.png);;All files (*.*)",
                                                      options=options)

        # If user don't select any image then return without doing any thing
        if image[0] == '':
            self.image_path = image[0]
            return

        self.ui.label_3.setPixmap(QtGui.QPixmap(image[0]))
        self.image_path = image[0]

    def predict_image_results(self):
        result = self.detect_on_image()
        result = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
        height, width, channel = result.shape
        step = channel * width
        qImg = QImage(result.data, width, height, step, QImage.Format_RGB888)
        self.ui.label_3.setPixmap(QtGui.QPixmap(qImg))

    def detect_and_predict_mask(self, frame, faceNet, maskNet):
        # grab the dimensions of the frame and then construct a blob
        # from it
        (h, w) = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0, (224, 224),
                                     (104.0, 177.0, 123.0))

        # pass the blob through the network and obtain the face detections
        faceNet.setInput(blob)
        detections = faceNet.forward()
        print(detections.shape)

        # initialize our list of faces, their corresponding locations,
        # and the list of predictions from our face mask network
        faces = []
        locs = []
        preds = []

        # loop over the detections
        for i in range(0, detections.shape[2]):
            # extract the confidence (i.e., probability) associated with
            # the detection
            confidence = detections[0, 0, i, 2]

            # filter out weak detections by ensuring the confidence is
            # greater than the minimum confidence
            if confidence > 0.5:
                # compute the (x, y)-coordinates of the bounding box for
                # the object
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype("int")

                # ensure the bounding boxes fall within the dimensions of
                # the frame
                (startX, startY) = (max(0, startX), max(0, startY))
                (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

                # extract the face ROI, convert it from BGR to RGB channel
                # ordering, resize it to 224x224, and preprocess it
                face = frame[startY:endY, startX:endX]
                face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
                face = cv2.resize(face, (224, 224))
                face = img_to_array(face)
                face = preprocess_input(face)

                # add the face and bounding boxes to their respective
                # lists
                faces.append(face)
                locs.append((startX, startY, endX, endY))

        # only make a predictions if at least one face was detected
        if len(faces) > 0:
            # for faster inference we'll make batch predictions on *all*
            # faces at the same time rather than one-by-one predictions
            # in the above `for` loop
            faces = np.array(faces, dtype="float32")
            preds = maskNet.predict(faces, batch_size=32)

        # return a 2-tuple of the face locations and their corresponding
        # locations
        return locs, preds

    def detect_on_video(self):

        if self.ui.pushButton.text() == "Open Webcam":
            self.ui.pushButton.setText("Close Webcam")
            self.streaming = True
            self.vs = VideoStream(src=0).start()
            # initialize the video stream
            print("[INFO] starting video stream...")
            mixer.init()
            sound = mixer.Sound('alarm.mp3')

            # loop over the frames from the video stream
            while True:
                # grab the frame from the threaded video stream and resize it
                # to have a maximum width of 400 pixels
                frame = self.vs.read()
                frame = imutils.resize(frame, width=400)

                # detect faces in the frame and determine if they are wearing a
                # face mask or not
                (locs, preds) = self.detect_and_predict_mask(frame, net, model)

                # loop over the detected face locations and their corresponding
                # locations
                for (box, pred) in zip(locs, preds):
                    # unpack the bounding box and predictions
                    (startX, startY, endX, endY) = box
                    (mask, withoutMask) = pred

                    # determine the class label and color we'll use to draw
                    # the bounding box and text
                    if mask > withoutMask:
                        label = "Mask"
                    else:
                        label = "No Mask"
                        sound.play()
                    color = (0, 255, 0) if label == "Mask" else (0, 0, 255)

                    # include the probability in the label
                    label = "{}: {:.2f}%".format(label, max(mask, withoutMask) * 100)

                    # display the label and bounding box rectangle on the output
                    # frame
                    cv2.putText(frame, label, (startX, startY - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
                    cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)

                # show the output frame
                result = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = result.shape
                step = channel * width
                qImg = QImage(result.data, width, height, step, QImage.Format_RGB888)
                self.ui.label_3.setPixmap(QtGui.QPixmap(qImg))

                if not self.streaming:
                    self.ui.label_3.setPixmap(QtGui.QPixmap([]))
                    break
                cv2.waitKey(1) & 0xFF

        elif self.ui.pushButton.text() == "Close Webcam":
            self.ui.pushButton.setText("Open Webcam")
            self.vs.stop()
            self.streaming = False

    def detect_on_image(self):

        image = cv2.imread(self.image_path)

        (h, w) = image.shape[:2]

        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))

        net.setInput(blob)
        detections = net.forward()

        for i in range(0, detections.shape[2]):
            confidence = detections[0, 0, i, 2]

            if confidence > 0.6:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (startX, startY, endX, endY) = box.astype('int')
                (startX, startY) = (max(0, startX), max(0, startY))
                (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

                face = image[startY:endY, startX:endX]
                face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

                face = cv2.resize(face, (224, 224))
                face = img_to_array(face)
                face = preprocess_input(face)
                face = np.expand_dims(face, axis=0)

                (With_Mask, Without_Mask) = model.predict(face)[0]

                label = 'Mask' if With_Mask > Without_Mask else 'NoMask'
                color = (0, 255, 0) if label == 'Mask' else (0, 0, 225)

                label = "{}:{:.2f}%".format(label, max(With_Mask, Without_Mask) * 100)
                cv2.putText(image, label, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
                cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)

        return image


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.main_window.show()
    sys.exit(app.exec_())
