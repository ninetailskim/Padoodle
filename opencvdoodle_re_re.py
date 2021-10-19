import cv2
import numpy as np
import doodle
import paddlehub as hub
import os
import copy
import time
from threading import Thread, Lock

os.environ["CUDA_VISIBLE_DEVICES"]="0"


isMouseLBDown = False
circleColor = (0, 0, 0)
circleRadius = 5
lastPoint = (0, 0)
img = None
comlines = 25

lines = []
colors = []
cirRads = []

drawNewLine = True

pplist = [
    "left_shoulder",
    "left_elbow",
    "left_hip",
    "left_knee",
    "left_wrist",
    "left_ankle"
]

lock = Lock()
results = None


class MyThread(Thread):
    def __init__(self, video_file = "mykeypointdetector/mine.mp4"):
        super(MyThread, self).__init__()
        
        self.md = hub.Module(name='human_pose_estimation_resnet50_mpii')
        self.video_file = video_file
        self.capture = cv2.VideoCapture(self.video_file)
        self.h = self.capture.get(4)
        self.w = self.capture.get(3)
        

    def run(self):
        global results
        global lock
        while (1):
            ret, frame = self.capture.read()
            if not ret:
                break
            frame = cv2.flip(frame, 1)

            tresults = self.md.keypoint_detection(images=[frame], use_gpu=True)
            
            lock.acquire()
            results = tresults[0]['data']
            lock.release()       

    def doest(self, frame):
        res = self.md.keypoint_detection(images=[frame], use_gpu=True)
        return res[0]['data'] 
            






def preprocess(res):
    # print(res)
    tres = copy.deepcopy(res)
    for node in pplist:
        conode = "right" + node[4:]
        if res[conode][0] < res[node][0]:
            tmp = res[node]
            res[node] = res[conode]
            res[conode] = tmp
            # print(res[conode], res[node])
            # input()
    # print(res)
    if tres != res:
        # input()
        pass
    return res

class estUtil():
    def __init__(self):
        super(estUtil, self).__init__()
        self.module = hub.Module(name='human_pose_estimation_resnet50_mpii')

    def do_est(self, frame):
        res = self.module.keypoint_detection(images=[frame], use_gpu=True)
        return res[0]['data']

def drawOnCanvas(canvas, skins):
    lp = None
    for skin in skins:
        if skin.init:
            pos = skin.getPos()
            lp = (int(pos[0]), int(pos[1]))
        else: 
            pos = skin.getPos()
            cv2.line(canvas, pt1=lp, pt2=(int(pos[0]), int(pos[1])), color=skin.color, thickness=skin.cirRad)
            lp = (int(pos[0]), int(pos[1]))
    return canvas


def linesFilter():
    global lines
    for line in lines:
        linelen = len(line)
        sindex = 0
        mindex = 1
        while mindex < len(line):
            eindex = mindex + 1
            if eindex >= len(line):
                break
            d1 = line[mindex][0] - line[sindex][0]
            d2 = line[mindex][1] - line[sindex][1]
            d3 = line[eindex][0] - line[sindex][0]
            d4 = line[eindex][1] - line[sindex][1]
            if abs(d1*d4-d2*d3) <= 1e-6:
                line.pop(mindex)
            else:
                sindex += 1
                mindex += 1

def linesCompose():
    global lines
    tlines = []
    for line in lines:
        tlines.append([line[0]])
        for i in range(1,len(line)):
            l_1 = tlines[-1][-1]
            tlines[-1].append(((l_1[0] + line[i][0]) / 2,(l_1[1] + line[i][1]) / 2))
            tlines[-1].append((line[i]))
    lines = tlines

def draw_circle(event, x, y, flags, param):
    global circleColor
    global img
    global isMouseLBDown
    global lastPoint
    global comlines
    if drawNewLine is True:
        if event == cv2.EVENT_LBUTTONDOWN:
            isMouseLBDown = True
            cv2.circle(img, (x, y), int(circleRadius/2), circleColor, -1)
            lastPoint = (x, y)
            lines.append([(x,y)])
            colors.append(circleColor)
            cirRads.append(circleRadius)
        elif event == cv2.EVENT_LBUTTONUP:
            isMouseLBDown = False
        elif event == cv2.EVENT_MOUSEMOVE:
            if isMouseLBDown:
                if lastPoint is not None:
                    cv2.line(img, pt1=lastPoint, pt2=(x,y), color=circleColor, thickness=circleRadius)
                    
                    for scale in range(1, comlines):
                        lines[-1].append((lastPoint[0] * (comlines - scale) / comlines + x * scale / comlines ,lastPoint[1] * (comlines - scale) / comlines + y * scale / comlines))
                    lines[-1].append((x,y))
                    lastPoint = (x, y)

def updateCircleColor(x):
    global circleColor
    # global colorPreviewImg
    r = cv2.getTrackbarPos('Channel_Red', 'Palette')
    g = cv2.getTrackbarPos('Channel_Green', 'Palette')
    b = cv2.getTrackbarPos('Channel_Blue', 'Palette')
    circleColor = (b, g, r)
    # colorPreviewImg[:] = circleColor

def updateCircleRadius(x):
    global circleRadius
    # global radiusPreview
    circleRadius = cv2.getTrackbarPos('Circle_Radius', 'Palette')
    # radiusPreview[:] = (255, 255, 255)
    # cv2.circle(radiusPreview, center=(50, 50), radius=int(circleRadius / 2), color=(0,0,0), thickness=-1)

def drawTemplate(canvas, detectThread):
    global results
    global lock
    img = cv2.imread("template2.png")
    
    oh, ow = canvas.shape[:2]
    th, tw = img.shape[:2]
    img = cv2.resize(img, (int(oh * 0.75 / th * tw), int(oh * 0.75)))
    th, tw = img.shape[:2]
    ih = (oh - th) / 2
    iw = (ow - tw) / 2
   
    tres = detectThread.doest(img)
        
    tres = preprocess(tres)
    for key, value in tres.items():
        tres[key] = [int(value[0] + iw), int(value[1] + ih)]
        cv2.circle(canvas,(tres[key][0], tres[key][1]), 5, (0,0,255), -1)

    return tres


if __name__ == '__main__':
    # global img
    # global drawNewLine
    # global isMouseLBDown
    # global lastPoint
    # global results
    # global lock

    cv2.namedWindow('Doodle')
    cv2.namedWindow('Palette')
    cv2.createTrackbar('Channel_Red', 'Palette', 0, 255, updateCircleColor)
    cv2.createTrackbar('Channel_Green', 'Palette', 0, 255, updateCircleColor)
    cv2.createTrackbar('Channel_Blue', 'Palette', 0, 255, updateCircleColor)
    cv2.createTrackbar('Circle_Radius', 'Palette',1, 20, updateCircleRadius)

    cv2.setMouseCallback('Doodle', draw_circle)


    drawNode = False
    drawOrigin = False
    videoStream = "mabaoguo.mp4"
    # videoStream = 0
    videoScale = 1
    cap = cv2.VideoCapture(videoStream)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * videoScale
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * videoScale
    img = np.ones((height, width, 3)) * 255
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    detectThread = MyThread('mabaoguo.mp4')
    templatekeypoint = drawTemplate(img, detectThread)

    initmatch = None
    skins = []

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter("res/"+str(comlines)+"doodle"+videoStream, fourcc, fps, (width*2, height))
    print("origin", width, height)

    moveimg = None
    

    while True:
        if drawNewLine:
            cv2.imshow('Doodle', img)

        waitKey = cv2.waitKey(1)

        if waitKey == ord('q'):
            break
        
        if waitKey == ord('o'):
            drawOrigin = not drawOrigin

        if waitKey == ord('n'):
            drawNode = not drawNode

        if waitKey == ord('c'):
            detectThread.start()
            drawNewLine = not drawNewLine
            isMouseLBDown = not isMouseLBDown
            lastPoint= None
            initmatch = True
            if drawNewLine is False:
                #丰富关键点,增加中点addcenterPoint
                ckeypoint = doodle.addcenterPoint(templatekeypoint)
                ack, fas = doodle.complexres(ckeypoint, copy.deepcopy(doodle.FatherAndSon))
                ack, fas = doodle.complexres(ack, fas)
                print("complexres")
                #把关键点转成nodeItem格式,也就是toNodes
                nodes = doodle.toNodes(ack, fas)
                print("toNodes")
                print("nodes: ", len(nodes))
                #建立node之间的父子关系
                nodes = doodle.connectNodes(nodes, fas)
                print("connectNodes")
                print("nodes: ", len(nodes))
                #计算每个结点的角度信息setinfo
                doodle.setInfo(nodes['centerpoint'])
                print("setInfo")
                print("nodes: ", len(nodes))
                #buildskin 在每次切换到drawline之后只计算一次
                # doodle.debugNodes(nodes, np.ones((height, width, 3)) * 255, 1)
                for indd,line in enumerate(lines):
                    print(indd, "len of line", len(line))
                linesFilter()
                for indd,line in enumerate(lines):
                    print(indd, "len of line", len(line))
                input("test linesFilter")
                linesCompose()
                for indd,line in enumerate(lines):
                    print(indd, "len of line", len(line))
                input("test lineCompose")
                skins = doodle.buildskin(lines, colors, cirRads, nodes)

                # doodle.debug(skins,np.ones((height, width, 3)) * 255, 1)
                print("buildskin")
                #time.sleep(10)
                moveimg = None

        if drawNewLine is False:
            ret, frame = cap.read()
            if ret == True:

                if videoStream == 0:
                    frame = cv2.flip(frame, 1)

                frame = cv2.resize(frame, (width, height))
                tt = time.time()
                lock.acquire()
                if results is not None:
                    keypoint = copy.deepcopy(results)
                lock.release()

                # keypoint = eu.do_est(frame)
                print("pose keypoint:", time.time() - tt)
                #计算scale
                keypoint = preprocess(keypoint)
                scale = doodle.distance(keypoint['thorax'],keypoint['pelvis']) / doodle.distance(templatekeypoint['thorax'],templatekeypoint['pelvis'])
                #丰富关键点,增加中点addcenterPoint
                ckeypoint = doodle.addcenterPoint(keypoint)
                ack, fas = doodle.complexres(ckeypoint, copy.deepcopy(doodle.FatherAndSon))
                ack, _ = doodle.complexres(ack, fas)
                #update nodes的POS和info#其实主要是node的x,y,thabs
                # doodle.debugNodesInfo(nodes, copy.deepcopy(doodle.FatherAndSon), skins)
                tt = time.time()
                doodle.updateNodesXY2(nodes, ack, 50)
                doodle.setInfo(nodes['centerpoint'])
                print("setInfo:", time.time() - tt)
                #calculateSkin计算新的皮肤的位置
                tt = time.time()
                tskins = doodle.calculateSkin(copy.deepcopy(skins), 1)
                # tskins = doodle.calculateSkinAsync(copy.deepcopy(skins), 1)
                # tskins = doodle.calculateSkinMultiprocess(copy.deepcopy(skins), 1)
                
                print("calculateSkin:", time.time() - tt)
                # newimg每帧新生成,然后都画到newimg上去
                if drawOrigin == True:
                    moveimg = frame 
                else:
                    moveimg = np.ones((height, width, 3)) * 255

                if drawNode == True:
                    for key, value in ack.items():
                        cv2.circle(moveimg, (int(value[0]), int(value[1])), 8, (0,0,255), -1)
                tt = time.time()
                # print("moveimg", moveimg.shape)
                # input()
                moveimg = drawOnCanvas(moveimg, tskins)
                print("drawOnCanvas:", time.time() - tt)
                
                cv2.imshow("Doodle", moveimg)
                # input()
                # out.write(moveimg)
                res = np.concatenate((frame, moveimg.astype(np.uint8)), axis=1)
                out.write(res)
            else:
                break
        
    out.release()
    cv2.destroyAllWindows()

    detectThread.join()