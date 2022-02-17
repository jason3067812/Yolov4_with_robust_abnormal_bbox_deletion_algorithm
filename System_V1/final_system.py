from collections import deque
import datetime
import cv2
import os
import time
import numpy as np
import torch
import xml.etree.ElementTree as ET
import shutil
import glob
from tools.cocotools import get_classes
from model.yolov4 import YOLOv4
from model.decode_np import Decode
import logging
from final_module import *

from timeit import default_timer as timer
import socketserver, socket, struct, time, pickle


class TCP_Server(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.request.recv(4096).strip()
        messageData = self.data.decode()
        print('{} sent message: '.format(self.client_address[0]) + messageData)
        img_path = './images/'
        image = cv2.imread(img_path + messageData)

        # IDresult = detect_image(messageData, image, area_model, area_inputImgShape, area_classnames)
        IDresult = detect_image(image, model_path_1, classes_path_1, LABELS_1)

        if IDresult:
            encodeMessage = IDresult.encode()
            self.request.sendall(encodeMessage)
            print('Finish~!! \n')

def detect_image(image, class_model, classes_path_1, class_names):
    start = timer()

    # part1: 判斷area

    # image = cv2.imread(r'D:\project\yolov3_mobilenet\area_adding_data\val\NG-001001-(11-15-50)-3GV04-4061-(2xn01-3052).jpg')  # 測試用
    #測試圖片開啟################################
    # cv2.imshow('My Image', image)
    # cv2.waitKey(0)
    # ############################################
    boxes, scores, classes = yolov4(image, class_model, classes_path_1)
    if boxes is not None:
        print('找到{}個字元區域:{}'.format(len(boxes), boxes))
        # part1.5: crop area and padding
        crop_img = image[int(boxes[0][1]):int(boxes[0][3]), int(boxes[0][0]):int(boxes[0][2])]
        size = crop_img.shape
        x = size[1]
        y = size[0]
        z = x - y

        BLACK = [0, 0, 0]
        constant = cv2.copyMakeBorder(crop_img, 0, z, 0, 0, cv2.BORDER_CONSTANT, value=BLACK)

        # part2: 判斷ID
        # image = cv2.imread(path_name + '/' + filename)       #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        img_flip_along_xy = cv2.flip(constant, -1)

        a1 = yolov4(constant, model_path_2, classes_path_2)
        a2 = recognize_overlapping_bbox_algorithm(a1[0], a1[1], a1[2], LABELS_2, unusual_distance)

        b1 = yolov4(img_flip_along_xy, model_path_2, classes_path_2)
        b2 = recognize_overlapping_bbox_algorithm(b1[0], b1[1], b1[2], LABELS_2, unusual_distance)

        # 判斷flip區
        c = flip_algorithm(a2[0], b2[0], a2[1], b2[1])
        # list to string
        d = "".join(c)
        print("final ID:", d)
        # print("ID_a:", a2[0])
        # print("ID_b:", b2[0])
        # print("score_a:",a2[1])
        # print("score_b:", b2[1])

        end = timer()
        print('花費時間：{}\n'.format(end - start))
        return d
    else:
        print('沒找到字元區域, box={}\n'.format(boxes))

#######################################################

if __name__ == '__main__':
    FORMAT = '%(asctime)s-%(levelname)s: %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    logger = logging.getLogger(__name__)
    # 6G的卡，训练时如果要预测，则设置use_gpu = False，否则显存不足。
    use_gpu = True

    # 調參區 ############################################################################################################
    model_path_1 = './weights/step00310000.pt'        # area weight
    model_path_2 = './weights/addsize_model.pt'     # ID weight
    classes_path_1 = './data/area_classes.txt'      # area class
    classes_path_2 = './data/new_classes.txt'     # ID class

    unusual_distance = 10 # 字串最大長度
    LABELS_1 = ["box"]
    LABELS_2 = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
              "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]

    # 前置準備 ########################################################################################################
    print(" ")
    print(f"loading yolov4 model_1:'{model_path_1}'")
    print(" ")
    print(f"loading yolov4 model_2:'{model_path_2}'")
    print(" ")
    print("start detecting!")
    print(" ")

    # Server ######################################################################################################
    HOST, PORT = socket.gethostname(), 54321
    print('HOST: ', HOST)
    print('Port: ', PORT)

    server = socketserver.TCPServer((HOST, PORT), TCP_Server)
    server.serve_forever()

