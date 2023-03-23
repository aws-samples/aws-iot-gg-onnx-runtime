"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import os
import time
import json
import numpy as np
import onnx
import onnxruntime
from PIL import Image

import awsiot.greengrasscoreipc
import awsiot.greengrasscoreipc.client as client
from awsiot.greengrasscoreipc.model import (
    QOS,
    PublishToIoTCoreRequest
)

ipc_client = awsiot.greengrasscoreipc.connect()
scriptPath = os.path.abspath(os.path.dirname(__file__))
#define the topic on which we will publish the inference results and the quality of service
topic = "demo/onnx"
qos = QOS.AT_LEAST_ONCE

#define the paths for the model, labels and images that will be used by the inferencing script
modelPath = scriptPath + "/model/resnet50v2.onnx"
labelsPath = scriptPath + "/labels/imagenet-simple-labels.json"
imagesPath = scriptPath + "/images"



#some utility functions used for inferencing
def load_labels(path):
    with open(path) as f:
        data = json.load(f)
    return np.asarray(data)

#starts an inferencing session and classifies the image, the output will include the class, and the inferencing time in ms
def predict(modelPath, labelsPath, image):
    labels = load_labels(labelsPath)
    # Run the model on the backend
    session = onnxruntime.InferenceSession(modelPath, None)

    # get the name of the first input of the model
    input_name = session.get_inputs()[0].name
    image_data = np.array(image).transpose(2, 0, 1)
    input_data = preprocess(image_data)

    start = time.time()
    raw_result = session.run([], {input_name: input_data})
    end = time.time()

    #calculating the inference time and determining the label for classification
    inference_time = np.round((end - start) * 1000, 2)
    idx = np.argmax(postprocess(raw_result))
    inferenceResult = {
        "label": labels[idx],
        "inference_time": inference_time
        }
    
    return json.dumps(inferenceResult)
    
#utility function that normalizes the image for inferencing
def preprocess(input_data):
    # convert the input data into the float32 input
    img_data = input_data.astype('float32')

    #normalize
    mean_vec = np.array([0.485, 0.456, 0.406])
    stddev_vec = np.array([0.229, 0.224, 0.225])
    norm_img_data = np.zeros(img_data.shape).astype('float32')
    for i in range(img_data.shape[0]):
        norm_img_data[i,:,:] = (img_data[i,:,:]/255 - mean_vec[i]) / stddev_vec[i]
        
    #add batch channel
    norm_img_data = norm_img_data.reshape(1, 3, 224, 224).astype('float32')
    return norm_img_data

def softmax(x):
    x = x.reshape(-1)
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum(axis=0)

def postprocess(result):
    return softmax(np.array(result)).tolist()

while True:
#loops through all the images in the folder, classifies them and sends all the results to the IoT Core topic
    for img in os.listdir(imagesPath):
        request = PublishToIoTCoreRequest()
        request.topic_name = topic
        image = Image.open(imagesPath + "/" + img)
        pred = predict(modelPath, labelsPath, image)
        request.payload = pred.encode()
        request.qos = qos
        operation = ipc_client.new_publish_to_iot_core()
        operation.activate(request)
        future_response = operation.get_response().result(timeout=5)
        print("successfully published message: ", future_response)
        time.sleep(5)