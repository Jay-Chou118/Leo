#m包头引用部分
import sensor, image, time , math
from pyb import UART,LED,Pin ,Timer
import time
from struct import pack, unpack
import json

# 50kHz pin6 timer2 channel1
light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
light.pulse_width_percent(10) # 控制亮度 0~100

#感光元件测试使用部分
sensor.reset()
sensor.set_pixformat(sensor.RGB565)#初始设定后面会更改
sensor.set_framesize(sensor.QVGA)  #320*240
sensor.skip_frames(time = 2000)
sensor.set_auto_whitebal(False)
sensor.set_auto_gain(False)
clock = time.clock()


rlmin=0
rlmax=39
ramin=-31
ramax=48
rbmin=-46
rbmax=47
hlmin=0
hlmax=13
hamin=-14
hamax=16
hbmin=-17
hbmax=10
thresholds1 = [(0, 38, -44, 47, -46, 64),
                (0, 46, -40, 47, -46, 64),
               (0, 32, -41, 28, -6, 60),
              (rlmin,rlmax,ramin,ramax,rbmin,rbmax),
              (hlmin,hlmax,hamin,hamax,hbmin,hbmax)
              ]
              #(30, 100, -44, 39, -91, 98),
              #(30, 75, -44, 39, -91, 98) ,
# Tracks a black line. Use [(128, 255)] for a tracking a white line.
GRAYSCALE_THRESHOLD = [(0, 64)]
#设置阈值，如果是黑线，GRAYSCALE_THRESHOLD = [(0, 64)]；
#如果是白线，GRAYSCALE_THRESHOLD = [(128，255)]

Black = [(6, 76, -128, 127, -76, 127)]


#配置设定参数部分
uart = UART(3,115200)#这里的uart是 3串口 波特率115200
uart.init(115200,bits = 8,parity = None ,stop = 1 ,timeout_char =1000)#初始化
# [ROI, weight
ROIS_over = [(30, 24, 275, 180) ]    #左# You'll need to tweak the weights for you app
ROIS_down = [(0, 150, 160, 20) ]    #中# depending on how your robot is setup.
            #(0,100,160,20,0.2)  #上
ROIS = [ # [ROI, weight]
         (0, 0, 20, 120, 1), #左# You'll need to tweak the weights for you app
         (70, 0, 20, 120, 1), #中# depending on how your robot is setup.
        (140, 0, 20, 120, 1)  #上
          ]#上、中、下三部分

weight_sum = 0 #权值和初始化
#for r in ROIS: weight_sum += r[4] # r[4] is the roi weight.
#计算权值和。遍历上面的三个矩形，r[4]即每个矩形的权值。

thresholds = [(70, 100, -128, 127, -128, 127)]

roi_find_red =(6, 89, 23, 127, -50, 127)
#(10, 100, 16, 115, 15, 95)#当前使用的红色杆版本2.0
#(6, 89, 23, 127, -50, 127)#当前使用的红色杆版本1.0
roi_find_balck = [(0, 5, -117, 58, -80, 66)]

roi_find_blue =(23, 76, -76, -7, -46, 3)
                #(23, 78, -84, -12, -36, -5)#蓝色版本的杆识别V3.0
                #(23, 78, -84, -17, -44, -2) #蓝色版本的杆识别V2.0
                #(23, 76, -76, -7, -46, 3)#蓝色版本的杆识别V1.0

red = 1
blue = 2

roi_blobs_1 = [110,100,100,40] #这里先不改了
roi_blobs_2 = []

predict_threshold_200  = 200
predict_threshold_500  = 500



list_num = 0
f_array = []
f_i = 0
lenth_1 = 0
led1 = LED(1)
led2 = LED(2)
led3 = LED(3)
select_mode = 0
false_read = 0x11
now_Work_mode = 1
Work_mode = 0    #初始设置始终为0
#初始使用的是工作在0，归零状态
# == 11时，工作在距离判断状态
# == 22时，工作在二维码识别
# == 33时，工作在条形码识别
# == 44时，工作在下降识别模式
# == 55时，工作在寻找pole模式
#未识别到 返回数据 0x11


#这里定义了一个R结构体，不会的重新看python
class receive(object):
    uart_buf = []
    state = 0
    rx_data = 0
    #red_pole_distance = 0
R = receive()

class dot(object):
    x = 0
    y = 0
    pixels = 0
    ok = 0
Dot = dot()

#下面是通信协议
def rx_receive(data):#接收包头以及协议
    if R.state==0:
        if data == 0xAA:
            R.state = 1
            R.uart_buf.append(data)
        else:
            R.state = 0
    elif R.state==1:
        if data == 0x55:
            R.state = 2
            R.uart_buf.append(data)
        else:
            R.state = 0
    elif R.state==2:
        if data == 24:
            R.state = 3
            R.uart_buf.append(data)
        else:
            R.state = 0
    elif R.state==3:
        if data == 0x02:
            R.state = 4
            R.uart_buf.append(data)
        else:
            R.state = 0
    elif R.state==4:
        R.state =5
        R.uart_buf.append(data)
    elif R.state==5:
        if data== (R.uart_buf[0] + R.uart_buf[1] + R.uart_buf[2] + R.uart_buf[3] + R.uart_buf[4])%256 :
            R.state = 0
            R.uart_buf.append(data)
            R.rx_data=R.uart_buf[4]#这里是数据的关键返回参数
            R.uart_buf=[]
        else:
            R.state = 0


        #读取串口数据
def uart_read_buf(uart):
    i = 0
    buf_size = uart.any()
    while i<buf_size:
        rx_receive(uart.readchar())
        i = i + 1
        #这里将串口读取的数据返回到find_mode 里面


def uart_mode_secelt():
    find_mode = R.rx_data
    R.rx_data = 0
    return find_mode


    #写出数据
def tx_send_data(data_1,data_2,data_3,k,index_type_order):
    index_type = index_type_order
    if index_type == 18:
        uart.write(pack_data_18(data_1,data_2))
    elif index_type == 15:
        uart.write(pack_data_15(data_1))
    elif index_type == 1:
        uart.write(pack_data_text(data_1))
    elif index_type == 20:
        uart.write(pack_line_data(data_1,data_2,data_3,k))
    elif index_type == 19:
        pass



def pack_data_18(data_1,data_2):#这个是发送杆距离的
    datalist = [0xAA,0x55,0x18,0x02,data_1,data_2]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    return data

def pack_data_15(data):#这个是发送识别到杆的
    datalist = [0xAA,0x55,0x15,0x01,data]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    return data


def pack_data_text(data):#这个是发送识别到杆的
    datalist = [0xAA,0x55,0x18,0x01,data]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    return data



def pack_line_data(cy_1,cy_2,cy_3,k):
    datalist = [0xAA,0x55,0x20,0x04,cy_1,cy_2,cy_3,k]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    return data

#检验数据和  ？数据校验位？
def sum_checkout(data_list):
    data_sum = 0
    for temp in data_list:
        data_sum =  data_sum + temp
    return data_sum


def find_max(blobs):    #定义寻找色块面积最大的函数
    max_size=0
    for blob in blobs:
        if blob.pixels() > max_size:
            max_blob=blob
            max_size = blob.pixels()
    return max_blob


#滤值算法：
def filtrate_index(data):
    global f_i
    if len(f_array) <= 20:
        f_array.append(data)
    else:
       diff_num = sum(f_array)/20 - data
       if diff_num <15 and diff_num>-15:
            list_num = f_i % 20
            f_array[list_num] = data
            f_i = f_i +1
            return sum(f_array)/20


###################################################
#画线

def draw_line():
    line = img.get_regression([(0,0,0,0,0,0)], robust = True)


####################################################

#杆距离算法

#测距

def get_distance_ratio(blob_pixels ,set_reallength , object_width  ):
    tan_a = object_width/(2*set_reallength)
    #k = tan_a / tan_b = blob_pixels/(320*80)
    k = blob_pixels/(639*40)
    tan_b = tan_a / k
    return tan_b#计算距离比例

def get_distance(blob_pixels , tan_B):
    mean_width = blob_pixels/40 #平均宽度
    length = 3*639/(2*tan_B*mean_width)#计算实际长度
    return length#返还计算出来的数据

def distance_pole(color):
        led3.on()
        if color == red :
            blobs = img.find_blobs([roi_find_red] ,
            pixels_threshold = predict_threshold_200 )#这个是查找红色  #若一个色块的像素数小于 pixel_threshold ，则会被过滤掉。
            if len(blobs) == 1:

                #blob.x() 返回色块的外框的x坐标（int），也可以通过blob[0]来获取。
                #blob.y() 返回色块的外框的y坐标（int），也可以通过blob[1]来获取。
                #blob.w() 返回色块的外框的宽度w（int），也可以通过blob[2]来获取。
                #blob.h() 返回色块的外框的高度h（int），也可以通过blob[3]来获取。
                #blob.pixels() 返回色块的像素数量（int），也可以通过blob[4]来获取。
                #blob.cx() 返回色块的外框的中心x坐标（int），也可以通过blob[5]来获取。
                #blob.cy() 返回色块的外框的中心y坐标（int），也可以通过blob[6]来获取。

                object_color= blobs[0]
                pixels_color = object_color[4]
                x_location = object_color[5]#返还识别到的物体的中心x轴位置
                if pixels_color > 200 :  #这里判断有没有在识别的范围
                    img.draw_rectangle(object_color.rect())
                    #print(pixels_color)
                    ratio_a = get_distance_ratio(899.167,83.5,3.0)#这里是已知距离的像素模块，摄像头距离，拍照杆的宽度  这步在求K
                    lenth = get_distance(pixels_color,ratio_a)
                    real_lenth = filtrate_index(lenth)
                   # time.sleep_ms(500) #20hz
                    interpolation_x = int((x_location - 320)/10)
                    if real_lenth:
                        real_lenth = int(real_lenth)-5
                        tx_send_data(real_lenth,interpolation_x,0,0,18)
                        print("The distance is ",real_lenth) #返还数值
                        #print(interpolation_x)
        elif color == blue:
            blobs = img.find_blobs([roi_find_blue] , pixels_threshold = predict_threshold_200 , merge = True )#这个是查找蓝色
            if len(blobs) == 1:
                object_color= blobs[0]
                pixels_color = object_color[4]
                x_location = object_color[5]#返还识别到的物体的中心x轴位置
                if pixels_color > 300 :  #这里判断有没有在识别的范围
                    img.draw_rectangle(object_color.rect())
                    print(pixels_color)
                    ratio_a = get_distance_ratio(307.64,143,3.0)#这里是已知距离的像素模块，摄像头距离，拍照杆的宽度
                    lenth = get_distance(pixels_color,ratio_a)
                    real_lenth = filtrate_index(lenth)
                   # time.sleep_ms(500) #20hz
                    interpolation_x = int((x_location - 320)/10)
                    if real_lenth:
                        real_lenth = int(real_lenth)
                        tx_send_data(real_lenth,interpolation_x,0,0,18)
                        print("The distance is ",real_lenth) #返还数值
                       # print(interpolation_x)


    #以1/3 为长度，将图片压缩
    #blob_pixels : 调试前的色块总像素数 目前测得红杆 1170.8421
    #blob_pixels / 80 -> 获取平均宽度
    #object_width : 物体的实际宽度
    #set_reallength : 拍照的时候，摄像头到杆的距离
    #下面宽度都以cm为设置单位
    #获取距离比例



#识别杆   320*240
def identify_pole_red():
    blobs = img.find_blobs([roi_find_red] , \
    pixels_threshold = predict_threshold_500 , merge = True )
    print("the list of blobs is ",len(blobs))
    if len(blobs) == 1:
        object_red = blobs[0]
        pixels_red = object_red[4]
        x_location = object_red[5]
        if pixels_red > 300:  #这里判断有没有在识别的范围
            img.draw_rectangle(object_red.rect())
            if x_location >= 106 and x_location <=160:
                print("x is ",x_location)
                tx_send_data(1,0,0,0,15)
                led2.on()

def identify_pole_blue():
    blobs = img.find_blobs([roi_find_blue] , \
    pixels_threshold = predict_threshold_500 )

    if len(blobs) == 1:
        object_red = blobs[0]
        pixels_red = object_red[4]
        x_location = object_red[5]

        if pixels_red > 300:  #这里判断有没有在识别的范围
            img.draw_rectangle(object_red.rect())
            if x_location >= 106 and x_location <=150:
                print("x is ",x_location)
                tx_send_data(1,0,0,0,15)
                led2.on()


#点检测函数
def check_dot(img):

    #thresholds为黑色物体颜色的阈值，是一个元组，需要用括号［ ］括起来可以根据不同的颜色阈值更改；pixels_threshold 像素个数阈值，
    #如果色块像素数量小于这个值，会被过滤掉;area_threshold 面积阈值，如果色块被框起来的面积小于这个值，会被过滤掉；merge 合并，如果
    #设置为True，那么合并所有重叠的blob为一个；margin 边界，如果设置为5，那么两个blobs如果间距5一个像素点，也会被合并。60
    for blob in img.find_blobs(thresholds, pixels_threshold=50, area_threshold=10, merge=True, margin=2):
        if Dot.pixels<blob.pixels():#寻找最大的黑点
            ##先对图像进行分割，二值化，将在阈值内的区域变为白色，阈值外区域变为黑色
            img.binary(thresholds)
            #对图像边缘进行侵蚀，侵蚀函数erode(size, threshold=Auto)，size为kernal的大小，去除边缘相邻处多余的点。threshold用
            #来设置去除相邻点的个数，threshold数值越大，被侵蚀掉的边缘点越多，边缘旁边白色杂点少；数值越小，被侵蚀掉的边缘点越少，边缘
            #旁边的白色杂点越多。
            img.erode(1)
            dot.pixels=blob.pixels() #将像素值赋值给dot.pixels
            workflag =1
            if(dot.pixels >50 and dot.pixels <1500):
                    dot.x = (int)(blob.cx()/2) #将识别到的物体的中心点x坐标赋值给dot.x
                    dot.y = (int)(blob.cy()/2) #将识别到的物体的中心点x坐标赋值给dot.x
            else:
                    dot.x = 40 #将识别到的物体的中心点x坐标赋值给dot.x
                    dot.y = 30 #将识别到的物体的中心点x坐标赋值给dot.x
           # if (30<dot.x and dot.x<50 and dot.y>20 and dot.y<40):
                # pin8.value(True)
            #else:
               #  pin8.value(False)

            print(dot.pixels)
            print("(x,y)=",dot.x,dot.y)
            dot.ok= 1
            #在图像中画一个十字；x,y是坐标；size是两侧的尺寸；color可根据自己的喜好设置
            img.draw_cross(dot.x*2, dot.y*2, color=127, size = 10)
            #在图像中画一个圆；x,y是坐标；5是圆的半径；color可根据自己的喜好设置
            img.draw_circle(dot.x*2, dot.y*2 , 5, color = 127)

#####################################################

def find_over():
    for blob in ROIS_over:
        blobs = img.find_blobs(GRAYSCALE_THRESHOLD,pixel_threshold=1000,merge=True)
    print("The length is ",len(blobs))
    most_pixels = 0
    x_sum = 0
    y_sum = 0
    x_average = 0
    y_average = 0
    number = 0
    for i in range(len(blobs)):
       # print(" i  = ", i )
        number = +1
        x_sum = + blobs[i].cx()
        y_sum = + blobs[i].cy()
       #print("the number is " , number)
       #print("the sum is ", x_sum)
        print("the sum of y is ", y_sum)
    #目标区域找到的颜色块（线段块）可能不止一个，找到最大的一个，作为本区域内的目标直线
        if blobs[i].pixels() > most_pixels:
            most_pixels = blobs[i].pixels()
            #merged_blobs[i][4]是这个颜色块的像素总数，如果此颜色块像素总数大于
            #most_pixels，则把本区域作为像素总数最大的颜色块。更新most_pixels和largest_blob
            largest_blob = i


            # Draw a rect around the blob.

            img.draw_rectangle(blobs[largest_blob].rect())

            #将此区域的像素数最大的颜色块画矩形和十字形标记出来
            img.draw_cross(blobs[largest_blob].cx(),blobs[largest_blob].cy())


    x_average = (int((x_sum / number)-160))
    y_average = (int((y_sum / number) - 120))
    tx_send_data(x_average,y_average,0,0,20)
    print("the average of x is ",x_average)
    print("the average of y is ",y_average)

def find_down():
    pass

def find_lineV1():

    #clock.tick() # Track elapsed milliseconds between snapshots().
    #img = sensor.snapshot() # Take a picture and return the image.
    centroid_sum = 0
    #利用颜色识别分别寻找三个矩形区域内的线段
    for r in ROIS:
        blobs = img.find_blobs(GRAYSCALE_THRESHOLD, roi=r[0:4],merge=True)


        # r[0:4] is roi tuple.
        #找到视野中的线,merge=true,将找到的图像区域合并成一个

        #目标区域找到直线
        if blobs:
            # Find the index of the blob with the most pixels.
            most_pixels = 0
            largest_blob = 0

            for i in range(len(blobs)):
            #目标区域找到的颜色块（线段块）可能不止一个，找到最大的一个，作为本区域内的目标直线
                if blobs[i].pixels() > most_pixels:
                    most_pixels = blobs[i].pixels()
                    #merged_blobs[i][4]是这个颜色块的像素总数，如果此颜色块像素总数大于
                    #most_pixels，则把本区域作为像素总数最大的颜色块。更新most_pixels和largest_blob
                    largest_blob = i

            # Draw a rect around the blob.

            img.draw_rectangle(blobs[largest_blob].rect())

            #img.draw_rectangle((0,0,30, 30))
            #将此区域的像素数最大的颜色块画矩形和十字形标记出来
            img.draw_cross(blobs[largest_blob].cx(),blobs[largest_blob].cy())

           # centroid_sum += blobs[largest_blob].cx() * r[4] # r[4] is the roi weight.

            #print("the middot is ",blobs[largest_blob].cx())
            #计算centroid_sum，centroid_sum等于每个区域的最大颜色块的中心点的x坐标值乘本区域的权值


    #print("The centroid_sum is ",centroid_sum)

    #center_pos = (centroid_sum / weight_sum) # Determine center of line.
    #print("The center_pos is ",center_pos)

def find_line(picture):
    global wheel_flag_b
    tx_buf = [0,0,0,0,0,0,0,0,0,0,0,0]
    blobs_num=0
    for r in ROIS:
        img = picture
        blobs = img.find_blobs([thresholds1[0]], roi=r[0:4], merge=True)
        blobs_num = blobs_num + 4
        if blobs:
            most_pixels = 0
            largest_blob = 0
            for i in range(len(blobs)):
                if blobs[i].pixels() > most_pixels:
                    most_pixels = blobs[i].pixels()
                    largest_blob = i
            img.draw_rectangle(blobs[largest_blob].rect())
            img.draw_cross(blobs[largest_blob].cx(),
                           blobs[largest_blob].cy())
            tx_buf[0 + blobs_num-4] = blobs[largest_blob].cx()
            tx_buf[1 + blobs_num-4] = blobs[largest_blob].cy()
            tx_buf[2 + blobs_num-4] = blobs[largest_blob].w()
            tx_buf[3 + blobs_num-4] = blobs[largest_blob].h()
        else:
            tx_buf[0 + blobs_num-4] = 0xff
            tx_buf[1 + blobs_num-4] = 0xff
            tx_buf[2 + blobs_num-4] = 0xff
            tx_buf[3 + blobs_num-4] = 0xff
    cx_1=tx_buf[0]
    cy_1 =tx_buf[1]
    w_1=tx_buf[2]
    h_1 =tx_buf[3]
    cx_2=tx_buf[4]
    cy_2 =tx_buf[5]
    w_2=tx_buf[6]
    h_2 =tx_buf[7]
    cx_3=tx_buf[8]
    cy_3 =tx_buf[9]
    w_3=tx_buf[10]
    h_3 =tx_buf[11]

    find_circle(picture)
    smooth(cx_1,cy_1,w_1,h_1,cx_2,cy_2,w_2,h_2,cx_3,cy_3,w_3,h_3)

    print(cx_1,cy_1,w_1,h_1,cx_2,cy_2,w_2,h_2,cx_3,cy_3,w_3,h_3)
    #print("k outside is " , k)


def smooth(cx_1,cy_1,w_1,h_1,cx_2,cy_2,w_2,h_2,cx_3,cy_3,w_3,h_3):
    global k
    k = 0
    a=0 #the mark to tell the flyer it found the right angle

    if h_1>20 or w_1<15:
        cy_1=0xff
    if h_2>20 or w_2<15:
        cy_2=0xff
    if h_3>20 or w_3<15:
        cy_3=0xff
    if h_1<=20 and h_2<=20 and h_3<=20:
        if w_1>5 and w_2>5 and w_3>5:
            k=(cy_1-cy_2)/(cx_1-cx_2)
    elif h_1<=20 and h_2<=20 and h_3==0xff:
        if w_1>5 and w_2>5 and w_3==0xff:
            k=(cy_1-cy_2)/(cx_1-cx_2)
    elif h_1==0xff and h_2<=20 and h_3<=20:
        if w_1==0xff and w_2>5 and w_3>5:
            k=(cy_2-cy_3)/(cx_2-cx_3)
    elif h_1<=20 and h_2==0xff and h_3<=20:
        if w_1>5 and w_2==0xff and w_3>5:
            k=(cy_1-cy_3)/(cx_1-cx_3)
    elif h_1==0xff and h_2==0xff and h_3<=20:
        if w_1==0xff and w_2==0xff and w_3>5:
             k=0xff
    elif h_1<=20 and h_2==0xff and h_3==0xff:
        if w_1>5 and w_2==0xff and w_3==0xff:
            k=0xff
    elif h_1==0xff and h_2<=20 and h_3==0xff:
        if w_1==0xff and w_2>5 and w_3==0xff:
            k=0xff
    elif h_1==0xff and h_2==0xff and h_3==0xff:
        if w_1==0xff and w_2==0xff and w_3==0xff:
            k=0xff
    elif h_1 >= 200 and( h_2 >= 30 and h_2 < 90 )and h_3 <= 20:
        if w_1 >= 200 and( w_2 >= 5 and w_2 < 20 )and w_3 >= 5:
            a = 100
            k = a
            print("Find right angle")
            print("The K of the right angle is ",k)
            tx_send_data(cy_1,cy_2,cy_3,k,20)
    #elif h_1 <= 20 and h_2 >= 30 and h_3 <= 20:
     #   if w_1 >= 200 and w_2 >= 5 and w_3 >= 5:


    else:
        k=0xff
        #print("The k is ",k)
    if k!=0xff and cy_1 <= 120 and cy_2 <= 120 and cy_3 <= 120 :
        print("I don't find the right angle: ",k,cy_1,cy_2,cy_3)
        k = int(math.degrees(-math.atan(k)))
        print("K = ",k)
        tx_send_data(cy_1,cy_2,cy_3,k,20)



def find_circle(picture):
   a = 0
   img = picture.lens_corr(1.8)
   for c in img.find_circles(ROI =([90,0,70,120]),threshold = 4000, x_margin = 10, y_margin = 10, r_margin = 10,r_min = 2, r_max = 100, r_step = 2):
        if c.magnitude() > 4000:
            img.draw_circle(c.x(), c.y(), c.r(), color = (255, 0, 0))
            print("I find the circle.")
            a = 120
            k = a
            print("Circle's k = ",k)
            tx_send_data(c.x(),c.y(),c.r(),k,20)
            print("The circle " ,c.x(),c.y(),c.r(),c.magnitude())
            print(" 2nd Circle's k = ",k)
        else :
            pass

#openmv框架构建，程序进行的设置:
while(True):
    while(Work_mode == 0):#Work_mode 初始工作在1状态
            clock.tick()
            uart_read_buf(uart)#这里读取串口数据
            select_mode = uart_mode_secelt()#这里将数据返回
    #        print(select_mode)
            if select_mode != 0:
                Work_mode = select_mode
                if Work_mode == 11:  #红色杆距离
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.VGA)
#                    sensor.set_windowing((0,220,639,40))
                if Work_mode == 22:  #蓝色杆距离
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.VGA)
                if Work_mode == 33:  #红色杆识别
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.QVGA)
                if Work_mode == 44:  #蓝色杆识别
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.QVGA)
                if Work_mode == 55:  #巡线模式
                    sensor.set_pixformat(sensor.GRAYSCALE)
                    sensor.set_framesize(sensor.QVGA)
            else:
                led1.on()
                time.sleep_ms(1000)
                led1.off()
                time.sleep_ms(1000)
                #tx_send_data(33,0,18)
                # 11 -> AA 55 18 02 0B 24
                # 22 -> AA 55 18 02 16 2F
                # 33 -> AA 55 18 02 21 3A
                # 44 -> AA 55 18 02 2C 44
                # 55 -> AA 55 18 02 37 50
    while(Work_mode == 11):#红色距离返回
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.VGA)
        sensor.set_windowing((0,220,639,40))
        clock.tick()
        uart_read_buf(uart)
        now_Work_mode = uart_mode_secelt()#这里再次赋值，进行操作判断，通过重新赋值为0，再次进入选择模式状态
        if  now_Work_mode == 0:
            img = sensor.snapshot().histeq(adaptive = True , clip_limit = 3)
            distance_pole(red) #直接进行操作 这里进行数据的发送
        else:
            Work_mode = now_Work_mode
            led3.off()
            pass


    while(Work_mode == 22):#蓝色距离返回
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.VGA)
        sensor.set_windowing((0,220,639,40))
        clock.tick()
        uart_read_buf(uart)
        now_Work_mode = uart_mode_secelt()#这里再次赋值，进行操作判断，通过重新赋值为0，再次进入选择模式状态
        if  now_Work_mode == 0:
            img = sensor.snapshot().histeq(adaptive = True , clip_limit = 3)
            distance_pole(blue) #直接进行操作 这里进行数据的发送
        else:
            Work_mode = now_Work_mode
            led3.off()
            pass

    while(Work_mode == 33):#这是找到红色目标
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            sensor.set_windowing((0,0,320,240))
            clock.tick()
            uart_read_buf(uart)
            now_Work_mode = uart_mode_secelt()
            if  now_Work_mode == 0:
                img = sensor.snapshot().histeq(adaptive = True , clip_limit = 2)
                identify_pole_red() #杆识别
                f_array = []
            else:
                Work_mode = now_Work_mode
                led2.off()
                pass
    while(Work_mode == 44):#这是找到蓝色目标
             sensor.set_pixformat(sensor.RGB565)
             sensor.set_framesize(sensor.QVGA)
             sensor.set_windowing((0,0,320,240))
             clock.tick()
             uart_read_buf(uart)
             now_Work_mode = uart_mode_secelt()
             if  now_Work_mode == 0:
                 img = sensor.snapshot().histeq(adaptive = True , clip_limit = 2)
                 identify_pole_blue() #杆识别
                 f_array = []
             else:
                 Work_mode = now_Work_mode
                 led2.off()
                 pass
    while(Work_mode == 55): #巡线
            sensor.set_pixformat(sensor.RGB565) # use grayscale.
            sensor.set_framesize(sensor.QQVGA) # use QQVGA for speed.
            sensor.set_brightness(-1)
            clock.tick()
            uart_read_buf(uart)
            now_Work_mode = uart_mode_secelt()#这里再次赋值，进行操作判断，通过重新赋值为0，再次进入选择模式状态
            if  now_Work_mode == 0:
                #img = sensor.snapshot().histeq(adaptive = True , clip_limit = 2)
                img = sensor.snapshot()

                #check_dot(img)
                #find_over()
                find_line(img)

            else:
                Work_mode = now_Work_mode
                led2.off()
                pass
