import cv2
import numpy as np
import doodle
import paddlehub as hub
import os
import copy
import time

os.environ["CUDA_VISIBLE_DEVICES"]="0"


isMouseLBDown = False
circleColor = (0, 0, 0)
circleRadius = 5
lastPoint = (0, 0)

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

def drawTemplate(canvas, eu):
    img = cv2.imread("template2.png")
    
    oh, ow = canvas.shape[:2]
    th, tw = img.shape[:2]
    img = cv2.resize(img, (int(oh * 0.75 / th * tw), int(oh * 0.75)))
    th, tw = img.shape[:2]
    ih = (oh - th) / 2
    iw = (ow - tw) / 2
    tres = eu.do_est(img)
    tres = preprocess(tres)
    for key, value in tres.items():
        tres[key] = [int(value[0] + iw), int(value[1] + ih)]
        cv2.circle(canvas,(tres[key][0], tres[key][1]), 5, (0,0,255), -1)

    return tres



    
cv2.namedWindow('Doodle')
cv2.namedWindow('Palette')
cv2.createTrackbar('Channel_Red', 'Palette', 0, 255, updateCircleColor)
cv2.createTrackbar('Channel_Green', 'Palette', 0, 255, updateCircleColor)
cv2.createTrackbar('Channel_Blue', 'Palette', 0, 255, updateCircleColor)
cv2.createTrackbar('Circle_Radius', 'Palette',1, 20, updateCircleRadius)

cv2.setMouseCallback('Doodle', draw_circle)

drawMode = True
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

eu = estUtil()
templatekeypoint = drawTemplate(img, eu)

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

        drawNewLine = not drawNewLine
        isMouseLBDown = not isMouseLBDown
        lastPoint= None
        initmatch = True
        if drawNewLine is False:
            #???????????????,????????????addcenterPoint
            ckeypoint = doodle.addcenterPoint(templatekeypoint)
            ack, fas = doodle.complexres(ckeypoint, copy.deepcopy(doodle.FatherAndSon))
            ack, fas = doodle.complexres(ack, fas)
            print("complexres")
            #??????????????????nodeItem??????,?????????toNodes
            nodes = doodle.toNodes(ack, fas)
            print("toNodes")
            print("nodes: ", len(nodes))
            #??????node?????????????????????
            nodes = doodle.connectNodes(nodes, fas)
            print("connectNodes")
            print("nodes: ", len(nodes))
            #?????????????????????????????????setinfo
            doodle.setInfo(nodes['centerpoint'])
            print("setInfo")
            print("nodes: ", len(nodes))
            #buildskin ??????????????????drawline?????????????????????
            # doodle.debugNodes(nodes, np.ones((height, width, 3)) * 255, 1)
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

            keypoint = eu.do_est(frame)
            #??????scale
            keypoint = preprocess(keypoint)
            scale = doodle.distance(keypoint['thorax'],keypoint['pelvis']) / doodle.distance(templatekeypoint['thorax'],templatekeypoint['pelvis'])
            #???????????????,????????????addcenterPoint
            ckeypoint = doodle.addcenterPoint(keypoint)
            ack, fas = doodle.complexres(ckeypoint, copy.deepcopy(doodle.FatherAndSon))
            ack, _ = doodle.complexres(ack, fas)
            #update nodes???POS???info#???????????????node???x,y,thabs
            # doodle.debugNodesInfo(nodes, copy.deepcopy(doodle.FatherAndSon), skins)
            tt = time.time()
            doodle.updateNodesXY2(nodes, ack, 50)
            doodle.setInfo(nodes['centerpoint'])
            print("setInfo:", time.time() - tt)
            #calculateSkin???????????????????????????
            tt = time.time()
            # tskins = doodle.calculateSkin(copy.deepcopy(skins), 1)
            # tskins = doodle.calculateSkinAsync(copy.deepcopy(skins), 1)
            tskins = doodle.calculateSkinMultiprocess(copy.deepcopy(skins), 1)
            
            print("calculateSkin:", time.time() - tt)
            # newimg???????????????,???????????????newimg??????
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