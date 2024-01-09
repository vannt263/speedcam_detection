import numpy as np
from ultralytics import YOLO
import cv2
from object_detection import ObjectDetection
from sort import *

# Khai báo phát hiện đối tượng
od = ObjectDetection()
class_names = od.load_class_names()

# Khởi tạo tracker dùng thuật toán Sort
tracker = Sort(max_age=20, min_hits=3, iou_threshold=0.3)


# Tạo từ điển
vehicles_entering = {} # Lưu trữ đối tượng
vehicles_elapsed_time = {} # Lưu trữ thời gian của đối tượng

# Đọc video
cap = cv2.VideoCapture("../../data/videoTest.mp4")
fps = cap.get(cv2.CAP_PROP_FPS) # Số lượng frame trong 1s

# Tạo đường line
line1 = [(200, 350), (1100, 350)]
line2 = [(400, 200), (850, 200)]

while True:
    ret, frame = cap.read()
    if not ret:
        break

    result = od.detect(frame)
    boxes = result[0].boxes

    detections = np.empty((0, 5))
    for box in boxes:
        (x1, y1, x2, y2) = np.array(box.xyxy[0], dtype=int)
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        w, h = x2 - x1, y2 - y1

        conf = np.array(boxes.conf[0], dtype=float)
        cls = np.array(boxes.cls[0], dtype=int)
        currentClass = class_names[cls]

        if currentClass in ["car", "truck", "bus"] and conf > 0.3:
                currentArray = np.array([x1, y1, x2, y2, conf])
                detections = np.vstack((detections, currentArray))
    resultsTracker = tracker.update(detections)

    # Ước lượng vận tốc
    for result in resultsTracker:
        x1, y1, x2, y2, id = result
        x1, y1, x2, y2, id = int(x1), int(y1), int(x2), int(y2), int(id)
        w, h = x2 - x1, y2 - y1

        cx, cy  = x1 + w//2, y1 + h//2

        if id not in vehicles_entering and id not in vehicles_elapsed_time:
            if cy >= line2[0][1]:
                vehicles_entering[id] = 0

        if id in vehicles_entering:
            if cy < line1[1][1]:
                vehicles_entering[id] = vehicles_entering[id] + 1
            else:
                # print(id, ":", vehicles_entering[id])
                elapsed_time = vehicles_entering[id]*1/fps

                distance = 35
                a_speed_ms = distance/elapsed_time
                a_speed_kh = a_speed_ms* 3.6

                vehicles_elapsed_time[id] = elapsed_time
                # del vehicles_entering[id]

    if id in vehicles_elapsed_time:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (245, 170, 66), 2)
        cv2.rectangle(frame, (x1, y1), (x1+100, y1-20), (245, 170, 66), -1)
        cv2.putText(frame, str(round(a_speed_kh, 2)) + "km/h", (x1, y1-5), 0, 0.5, (255, 255, 255), 2)
        cv2.circle(frame, (cx, cy), 5, (245, 170, 66), -1)

    cv2.line(frame, line1[0], line1[1], (15, 220, 10), 2)
    cv2.line(frame, line2[0], line2[1], (15, 220, 10), 2)

    cv2.imshow("Image", frame)
    key = cv2.waitKey(1)
    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()
