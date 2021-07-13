# -*- coding: utf-8 -*-
"""RTFMD_Image_Detection.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YjUYnTnClWA_X3M_mxC21XgBPYNEJJAY
"""

from google.colab import drive 
drive.mount('/content/MyDrive', force_remount=True)

from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from google.colab.patches import cv2_imshow
import numpy as np
import cv2
import os

prototxtPath = os.path.sep.join([r'MyDrive/MyDrive/Real Time Face Mask Detection', 'deploy.prototxt'])
weightsPath = os.path.sep.join([r'MyDrive/MyDrive/Real Time Face Mask Detection', 'res10_300x300_ssd_iter_140000.caffemodel'])

prototxtPath

weightsPath

net = cv2.dnn.readNet(prototxtPath, weightsPath)

model = load_model(r'/content/MyDrive/MyDrive/Real Time Face Mask Detection/RTFMD_model.h5')

image = cv2.imread(r'/content/MyDrive/MyDrive/Real Time Face Mask Detection/Test_Images/image 9.jpg')

image

image.shape

(h, w) = image.shape[:2]

(h, w)

blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), (104.0, 177.0, 123.0))

blob

net.setInput(blob)
detections = net.forward()

detections

for i in range(0, detections.shape[2]):
   confidence = detections[0, 0, i, 2]

   if confidence > 0.6:
       box = detections[0, 0, i, 3:7]*np.array([w, h, w, h])
       (startX, startY, endX, endY) = box.astype('int')
       (startX, startY) = (max(0, startX), max(0, startY))
       (endX, endY) = (min(w-1, endX), min(h-1, endY))
       
       face = image[startY:endY, startX:endX]
       face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

       face = cv2.resize(face, (224, 224))
       face = img_to_array(face)
       face = preprocess_input(face)
       face = np.expand_dims(face, axis=0)

       (With_Mask, Without_Mask) = model.predict(face)[0]
       
       label = 'Mask' if With_Mask>Without_Mask else 'NoMask'
       color = (0, 255, 0) if label == 'Mask' else (0, 0, 225)

       label = "{}:{:.2f}%".format(label, max(With_Mask,Without_Mask)*100)
       cv2.putText(image, label, (startX, startY-10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 2)
       cv2.rectangle(image, (startX, startY), (endX, endY), color, 2)

cv2_imshow(image)
cv2.waitKey(0)
cv2.destroyAllWindows()

