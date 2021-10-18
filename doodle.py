import math
import copy
import cv2
import _thread
import time
import multiprocessing

G_skin = None
G_flag = None

FatherAndSon = {
    'thorax':'centerpoint',
    'upper_neck':'thorax',
    'head_top':'upper_neck',

    'left_shoulder':'thorax',
    'left_elbow':'left_shoulder',
    'left_wrist':'left_elbow',

    'right_shoulder':'thorax',
    'right_elbow':'right_shoulder',
    'right_wrist':'right_elbow',

    'pelvis':'centerpoint',
    'left_hip':'pelvis',
    'left_knee':'left_hip', 
    'left_ankle':'left_knee',

    'right_hip':'pelvis',
    'right_knee':'right_hip',
    'right_ankle':'right_knee',

    'centerpoint':'centerpoint'
}

def complexres(res, FatherAndSon):
    cres = copy.deepcopy(res)
    for key,pos in res.items():
        father = FatherAndSon[key]
        if father == key:
            continue
        if key[0] == 'm' or father[0] == 'm':
            midkey = 'm'+key+'_'+father
        else:
            kn = ''
            for t in key.split('_'):
                kn += t[0]
            fn = ''
            for t in father.split('_'):
                fn += t[0]
            midkey = 'm_'+kn+'_'+fn
        midvalue = [(pos[0] + res[father][0]) / 2, (pos[1] + res[father][1])/2]
        FatherAndSon[key] = midkey
        FatherAndSon[midkey] = father
        cres[midkey] = midvalue
    return cres, FatherAndSon

def complexres2(res, FatherAndSon):
    cres = copy.deepcopy(res)
    for key, pos in res.items():
        father = FatherAndSon[key]
        if father == key:
            continue
        midvalue1 = [pos[0] * 2 / 3 + res[father][0] / 3, pos[1] * 2 / 3 + res[father][1] / 3]
        midvalue2 = [pos[0] / 3 + res[father][0] * 2 / 3, pos[1] / 3 + res[father][1] * 2 / 3]
        kn = ''
        for t in key.split('_'):
            kn += t[0]
        fn = ''
        for t in father.split('_'):
            fn += t[0]
        midkey = 'm_'+kn+'_'+fn
        valuekey1 = midkey + "13"
        valuekey2 = midkey + "23"

        FatherAndSon[key] = valuekey1
        FatherAndSon[valuekey1] = valuekey2
        FatherAndSon[valuekey2] = father

        cres[valuekey1] = midvalue1
        cres[valuekey2] = midvalue2
    return cres, FatherAndSon

def distance(a, b):
    return math.sqrt(math.pow(a[0]-b[0], 2) + math.pow(a[1]-b[1], 2))


def dist2weight(md):
    if len(md) == 1:
        return [1]
    maxx = max(md)
    minx = min(md) 
    s = 0
    f = []
    for imd in md:
        x = 0.1 + 0.9 * (imd - minx) / (maxx - minx)
        s += x
        f.append(x)
    
    return [x/s for x in f]


class skinItem():
    def __init__(self, x, y, init, color, cirRad):
        super(skinItem, self).__init__()
        self.x = x
        self.y = y
        self.init = init
        self.color = color
        self.cirRad = cirRad
        self.anchor = []

    def getPos(self):
        return (self.x, self.y)

    def appendAnchor(self, anchor):
        self.anchor.append(anchor)

    def getAnchor(self):
        return self.anchor


class anchorItem():
    def __init__(self, node, th, r, w):
        super(anchorItem, self).__init__()
        self.node = node
        self.th = th
        self.r = r
        self.w = w


class nodeItem():
    def __init__(self, x, y, name):
        super(nodeItem, self).__init__()
        self.x = x
        self.y = y
        self.name = name
        
        self.parent = None
        self.parentName = None
        self.children = []
        self.lastUpdate = 0

    def getPos(self):
        return [self.x, self.y]

    def setParent(self, parent, parentName):
        self.parent = parent
        self.parentName = parentName

    def appendChildren(self, child):
        self.children.append(child)

    def setInfo(self, th, r, thabs, th0):
        self.th = th
        self.r = r
        self.thabs = thabs
        self.th0 = th0
    
    def getInfo(self):
        return [self.th, self.r, self.thabs, self.th0]


def getScale():
    pass

def addcenterPoint(res):
    thorax = res['thorax']
    pelvis = res['pelvis']
    x = (thorax[0] + pelvis[0]) / 2
    y = (thorax[1] + pelvis[1]) / 2
    res['centerpoint'] = [x,y]
    return res



nodes = {}
def toNodes(tree,FatherAndSon):
    nodes = {}
    for key in FatherAndSon:
        nodes[key] = nodeItem(tree[key][0], tree[key][1], key)
    return nodes

def connectNodes(nodes, FatherAndSon):
    for key,node in nodes.items():
        if key == 'centerpoint':
            continue
        if node.parent is not None:
            continue
        node.setParent(nodes[FatherAndSon[key]], FatherAndSon[key])
        nodes[FatherAndSon[key]].appendChildren(node)
    return nodes

def travelTree(node,gen=0):
    print("-" * gen*2,node.name, node.getPos(), node.getInfo())
    for ch in node.children:
        travelTree(ch, gen+1)

def setInfo(node):
    if node.parent is None:
        node.setInfo(0,0,0,0)
    else:
        #和父节点之间的角度
        th = math.atan2(node.y-node.parent.y, node.x-node.parent.x)
        #和父节点之间的距离
        r = distance(node.parent.getPos(), node.getPos())
        #用和父节点之间的角度 剪掉 父节点的thabs
        #所以这个node.th是计算相对于父节点的相对角度,这个
        # node.th = th - node.parent.thabs
        # #和父节点的距离
        # node.r = r
        # #和父节点的相对角度
        # node.thabs = th
        # #th0应该被认为是th的初始值,后来就没有再改变过
        # node.th0 = node.th 
        node.setInfo(th - node.parent.thabs, r, th, th - node.parent.thabs)
    
    for n in node.children:
        setInfo(n)

#这里需要一个函数,拿到最新的骨骼图,
#从根节点去更新所有骨头的相对角度,那TMD不就是setInfo吗?好像问题就这么解决了

def updateNodesXY(nodes, res, th):

    sumdis = 0
    for key, value in res.items():
        sumdis += distance(nodes[key].getPos(), value)
    averagedis = sumdis / len(nodes)

    for key, value in res.items():
        if distance(nodes[key].getPos(), value) < min(1.1 * averagedis, th) or nodes[key].lastUpdate == 2:
            nodes[key].x = value[0]
            nodes[key].y = value[1]
            nodes[key].lastUpdate = 0
        else:
            nodes[key].lastUpdate += 1

def updateNodesXY2(nodes, res, th):

    for key, value in res.items():
        nodes[key].x = value[0]
        nodes[key].y = value[1]



def judge(li):
    maxm = 0
    maxi = 0
    for index in range(len(li)):
        if li[index] == float("inf"):
            maxi = index 
            break
        if li[index] > maxm:
            maxm = li[index]
            maxi = index
    # print(li)
    # print(maxi, maxm)
    return maxi

def buildskin(lines, colors, cirRads, nodes):
    if lines is None or nodes is None or len(lines) == 0 or len(nodes) == 0:
        return []
    skins = []
    print("doodle node length", len(nodes))

    for lineindex in range(len(lines)):
        init = True
        line = lines[lineindex]
        color = colors[lineindex]
        cirRad = cirRads[lineindex]
        for p in line:
            if init:
                skins.append(skinItem(p[0], p[1], True, color, cirRad))
                init = False
            else:
                skins.append(skinItem(p[0], p[1], False, color, cirRad))
    
    for skin in skins:
        md = [float("inf"), float("inf"), float("inf"), float("inf")]
        mn = [None, None, None, None]
        mdlen = 0
        for key,node in nodes.items():
            d = distance(skin.getPos(), node.getPos())
            maxi = judge(md)
            if d < md[maxi]:
                md[maxi] = d
                mn[maxi] = node
                mdlen += 1
        # skin.setAnchors 
        if mdlen < 4:
            md = md[:mdlen]
            mn = mn[:mdlen]
        ws = dist2weight(md)
        # print(mdlen)
        # print(mn)
        for j in range(len(mn)):
            th = math.atan2(skin.y-mn[j].y, skin.x-mn[j].x)
            r = distance(skin.getPos(), mn[j].getPos())
            w = ws[j]
            skin.appendAnchor(anchorItem(mn[j], th-mn[j].thabs, r, w))

    return skins


def calculateSkin(skins, scale):
    for skin in skins:
        xw = 0
        yw = 0
        for anchor in skin.getAnchor():
            x = anchor.node.x + math.cos(anchor.th+anchor.node.thabs) * anchor.r * scale
            y = anchor.node.y + math.sin(anchor.th+anchor.node.thabs) * anchor.r * scale
            xw += x * anchor.w
            yw += y * anchor.w
        skin.x = xw
        skin.y = yw
    return skins

def thread_calculateSkin(threadName, s, e, idx, scale):
    global G_skin
    global G_flag
    for skin in G_skin[s:e]:
        xw = 0
        yw = 0
        for anchor in skin.getAnchor():
            x = anchor.node.x + math.cos(anchor.th+anchor.node.thabs) * anchor.r * scale
            y = anchor.node.y + math.sin(anchor.th+anchor.node.thabs) * anchor.r * scale
            xw += x * anchor.w
            yw += y * anchor.w
        skin.x = xw
        skin.y = yw
    G_flag[idx] = True
    print(str(idx), " end")

def calculateSkinMultiprocess(skin, scale):
    global G_skin
    global G_flag
    G_skin = skin
    
    slen = len(skin)
    step = math.floor(slen / 4)
    iterNN = list(range(0, slen, step))
    skiniter = []
    iterNum = len(iterNN)
    print(iterNN)
    G_flag = [False] * iterNum
    ps = [None] * iterNum
    for idx, i in enumerate(iterNN):
        print(str(idx), " run")
        if idx == len(iterNN) - 1:
            ps[idx] = multiprocessing.Process(target=thread_calculateSkin, args=("cal"+str(idx), i, slen, idx, scale))
            ps[idx].start()
            break
        else:
            ps[idx] = multiprocessing.Process(target=thread_calculateSkin, args=("cal"+str(idx), i, i + step, idx, scale))
            ps[idx].start()
    for pi in ps:
        pi.join()
    print("Done")
    return G_skin


def calculateSkinAsync(skin, scale):
    global G_skin
    global G_flag
    G_skin = skin
    
    slen = len(skin)
    step = math.floor(slen / 4)
    iter = list(range(0, slen, step))
    skiniter = []
    for idx, i in enumerate(iter):
        if idx == len(iter) - 1:
            skiniter.append(skin[i:slen]) 
            break
        else:
            skiniter.append(skin[i:i+step])
    
    G_flag = [False] * len(skiniter)
    for idx, i in enumerate(iter):
        print(str(idx), " run")
        if idx == len(iter) - 1:
            _thread.start_new_thread(thread_calculateSkin, ("cal"+str(idx), i, slen, idx, scale))
            break
        else:
            _thread.start_new_thread(thread_calculateSkin, ("cal"+str(idx), i, i + step, idx, scale))
    while False in G_flag:
        time.sleep(0.02)
    return G_skin
    
# 从这里看出来每次更新的时候其实要用到的,是anchor中的node的x,y,以及这个node的thabs
# 其实这里可以直接× scale

# anchor的xy肯定是要随着视频变化的,所以好像也不用去× scale???
# 错,还是需要×的,不然这个人会变得非常的细瘦, 而不是符合轮廓

# 这个scale要如何计算呢?一个是一开始的模板的长度,一个是现在视频里的长度,然后 anchor.r / templength * videolength

def debug(skins, canvas, scale):
    h,w = canvas.shape[:2]
    canvas = cv2.resize(canvas,(w * scale,h * scale))
    for skin in skins:
        if skin.init:
            pos = skin.getPos()
            lp = (int(pos[0]) * scale, int(pos[1]) * scale)
        else: 
            pos = skin.getPos()
            cv2.line(canvas, pt1=lp, pt2=(int(pos[0]) * scale, int(pos[1]) * scale), color=skin.color, thickness=skin.cirRad)
            lp = (int(pos[0]) * scale, int(pos[1]) * scale)
        for anchor in skin.getAnchor():
            pos = anchor.node.getPos()
            cv2.line(canvas, pt1=lp, pt2=(int(pos[0]) * scale, int(pos[1]) * scale), color=skin.color, thickness=1)
            cv2.circle(canvas,(int(pos[0]) * scale, int(pos[1]) * scale), 10, (0,0,255), -1)
    cv2.imshow("a", canvas)
    cv2.waitKey(0)

def debugNodesInfo(nodes, FatherAndSon, skins):
    for key, value in FatherAndSon.items():
        print(nodes[key].name,'--',nodes[key].getPos())
    for skin in skins:
        for anchor in skin.getAnchor():
            if anchor.node.name in FatherAndSon.keys():
                print(anchor.node.name,'--',anchor.node.getPos())

def debugNodes(nodes, canvas, scale):
    h,w = canvas.shape[:2]
    canvas = cv2.resize(canvas,(w * scale,h * scale))
    for key, value in nodes.items():
        pos = value.getPos()
        cv2.circle(canvas, (int(pos[0]) * scale , int(pos[1]) * scale), 8, (0,0,255), -1)
    cv2.imshow("a", canvas)
    cv2.waitKey(0)