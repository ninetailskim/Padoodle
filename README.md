# Paddle + doodle = *Padoodle*

![](https://ai-studio-static-online.cdn.bcebos.com/e9240dc452104c049c8c2df737d1d3c31bf9118fed644a98b18da5ba89c8f7dc)
# Padoodle: 使用人体关键点检测让涂鸦小人动起来   
大家好我是桨师磊giegie,今天给大家带来一个pose相关的小项目，就是如何让涂鸦跟着我动起来。   
其实，这个任务可以分为两个部分：   
第一部分获取人的pose信息      
第二部分就是骨骼动画   
   
## 获取人的pose信息   
获取人的pose信息比较容易，直接使用paddlehub中的一些pose estimation的方法就可以做到。   
这里我们可以直接调用，我这里使用的是human_pose_estimation_resnet50_mpii。    
当然，这个后端的算法可以替换成任何可以估计人体pose的算法。   
PaddleDetection中现在也提供了人体关键点检测的算法，在下一个项目中，我应该会介绍相关的内容。   
   
## 骨骼动画   
我画了几张简单的图给大家说一下   
![](https://ai-studio-static-online.cdn.bcebos.com/7dc0d866a0d24bf79de6b981f9bd74a8f4ff2f0212794a55bc73589314a8cbb3)   
首先就是要确定我们皮肤点和骨骼点的相对关系。这个关系包括了角度关系，距离关系等等。   
![](https://ai-studio-static-online.cdn.bcebos.com/74971904f83040e3b70b8bae068754a9852042a06e1e422cba07e3df189cdec4)   
皮肤上的点始终和骨骼是有相对位置的，也就是在每帧中我们都要去计算我们的皮肤点，然后画上去。所以这里涉及了一个**初始化**的过程，就是正确的把皮肤点和骨骼点绑定这样一个过程。    
在实际的使用中，一个皮肤点会和多个骨骼点绑定，最后皮肤点的位置，是几个相对位置的加权平均。   
![](https://ai-studio-static-online.cdn.bcebos.com/c99d3d1d4315498eafd20b594a13059b414fa52df9f04f3ca4ecf7d21e714d54)   
![](https://ai-studio-static-online.cdn.bcebos.com/f28944751d43441e9a02b34ebfe4fa145d3b3b2f2bc64f1897d239d02d868933)   
想了解更详细的可以参考这篇文章[骨骼动画的原理及在Unity中的使用](https://www.cnblogs.com/blueberryzzz/p/9960131.html)   
或者参考我的doodle.py文件   

话不多说，一起来看看效果吧   
<iframe style="width:98%;height: 800px;" src="//player.bilibili.com/player.html?aid=848653491&bvid=BV1EL4y1B7HK&cid=428344959&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true"> </iframe>   

   
# 完整项目见：[Padoodle](https://github.com/ninetailskim/Padoodle)

## 使用方法（因为需要用鼠标来画涂鸦，所以现在没办法在aistudio上运行）


```python
!python opencvdoodle_re.py
```

在画完你的涂鸦后，英文输入法下按‘c’。涂鸦小人就开始跳舞啦~

这里面的视频我上传了一个案例，马保国的。如果想换成别的视频
把videoStream = "mabaoguo.mp4"这行里换成你的视频名字就好。
如果想用摄像头测试的话，可以试试opencvdoodle_re_re.py这个，分成多线程写了，可能效果会更好一丢丢。

## 总结：
这个项目其实三月份就做完了，但是效果一直不满意。   
最近几天突然想到一些优化方法，大大提升了效果，所以算是完成了理想状态的80%。   
这个项目其实从去年年底就策划着做，期间搞了几天的骨骼动画，也算是搞懂了一点。   
其实这个很依赖关键点检测模型的效果。这里我是用的这个模型训练的数据集貌似和coco是不一样的，所以人像的关键点的标注也是不同的。   
所以，如果后端想换成coco数据集训练出来的人体关键点模型，那需要把doodle.py文件改一下。   
好了好了，不多说了，下次估计依然是关键点检测模型的项目，咱们下个项目见~   

# 个人简介

> 百度飞桨开发者技术专家 PPDE

> 飞桨上海领航团团长

> 百度飞桨官方帮帮团、答疑团成员

> 国立清华大学18届硕士

> 以前不懂事，现在只想搞钱～欢迎一起搞哈哈哈

我在AI Studio上获得至尊等级，点亮9个徽章，来互关呀！！！<br>
[https://aistudio.baidu.com/aistudio/personalcenter/thirdview/311006]( https://aistudio.baidu.com/aistudio/personalcenter/thirdview/311006)

B站ID： 玖尾妖熊

### 其他趣味项目：  
#### [利用PaddleHub制作"王大陆"滤镜](https://aistudio.baidu.com/aistudio/projectdetail/2083416)
#### [利用Paddlehub制作端午节体感小游戏](https://aistudio.baidu.com/aistudio/projectdetail/2079016)
#### [熊猫头表情生成器[Wechaty+Paddlehub]](https://aistudio.baidu.com/aistudio/projectdetail/1869462)
#### [如何变身超级赛亚人(一)--帅气的发型](https://aistudio.baidu.com/aistudio/projectdetail/1180050)
#### [【AI创造营】是极客就坚持一百秒？](https://aistudio.baidu.com/aistudio/projectdetail/1609763)    
#### [在Aistudio，每个人都可以是影流之主[飞桨PaddleSeg]](https://aistudio.baidu.com/aistudio/projectdetail/1173812)       
#### [愣着干嘛？快来使用DQN划船啊](https://aistudio.baidu.com/aistudio/projectdetail/621831)    
#### [利用PaddleSeg偷天换日～](https://aistudio.baidu.com/aistudio/projectdetail/1403330)    
