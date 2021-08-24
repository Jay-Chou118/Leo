import sensor,image,time,math
from pyb import UART,Pin,Timer,LED
from struct import pack, unpack
import json
import time






led1 = LED(1)
led2 = LED(2)
led3 = LED(3)

yellow_threshold   =(100, 0, -128, 125, 16, 127)
                    #(100, 8, -9, 127, 17, 127)
quar_threshold = (100, 8, -2, 127, -6, -29)

light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))
light.pulse_width_percent(0) # 控制亮度 0~100


#感光元件测试使用部分
sensor.reset()
sensor.set_pixformat(sensor.RGB565)#初始设定后面会更改
sensor.set_framesize(sensor.QVGA)  #320*240
sensor.skip_frames(time = 2000)
sensor.set_auto_whitebal(False)
sensor.set_auto_gain(False)
clock = time.clock()

#######################各个数据##################################

count_change = 0
change_flag = False
bar_flag = False

uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1, timeout_char=1000)
quar_flag = True

rx_mode = 0
bar_count = 0


##################通信模块##############################

class receive(object):
    uart_buf = []
    state = 0
    rx_data=0
R=receive() #R是一个结构体


##########校验数据和################
def sum_checkout(data_list):
    data_sum = 0
    for temp in data_list:
        data_sum = data_sum + temp
    return (data_sum)




def rx_receive(data):
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
        if data == 0x18:
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
        if data == 0x01 or data == 0x02 or data == 0x03:
            R.state =5
            R.uart_buf.append(data)
        else:
            R.state = 0
    elif R.state==5:
        if data== (R.uart_buf[0] + R.uart_buf[1] + R.uart_buf[2] + R.uart_buf[3] + R.uart_buf[4])%256 :
            R.state = 0
            R.uart_buf.append(data)
            R.rx_data=R.uart_buf[4]
            #print(R.rx_data)
            R.uart_buf=[]
        else:
            R.state = 0


def uart_mode_secelt():
    find_mode = R.rx_data
    R.rx_data = 0
    return find_mode


def uart_read_buf(uart):
    i = 0
    buf_size = uart.any()
    while i<buf_size:
        rx_receive(uart.readchar())
        i = i + 1





def communcation_write(model):
#   model  -->
#     1    -->     发现黄色条形码悬停
#     2    -->     黄色条形码拍照完成
#     3    -->     二维码拍照完成
#     4    -->     未使用
    head = [0xaa,0x55,0x13,0x01]

    if model==0:
        motion_bit = [0x00]
    elif model==1:
        motion_bit = [0x01]
    elif model==2:
        motion_bit = [0x02]
    elif model==3:
        motion_bit = [0x03]
    elif model == 4 :
        motion_bit = [0x04]

    check_sum = [sum(head + motion_bit)%256]
    data = head + motion_bit + check_sum
    msg = bytearray(data)
    uart.write(msg)

####################################################

def find_max(blobs):
    max_size = 0
    for blob in blobs:
        if blob.w() * blob.h() > max_size:
            max_blob = blob
            max_size = blob.w()*blob.h()

    return max_blob,max_size

#################################################

#AA 55 18 02 01 1A --> 寻找黄色条形码
#AA 55 18 03 01 1B --> 寻找二维码


#clock = time.clock()
#time类
#使用time.sleep比较多
#


#clock.tick()    开始追踪时间



def find_yellow(img):
    print("Frist ")
    light.pulse_width_percent(5) # 控制亮度 0~100
    #img.rotation_corr( z_rotation=90)  #旋转视角进行寻找
    img.median(1, percentile=0.5)
    blobs = img.find_blobs([yellow_threshold])
    #led1.on()
    #print("The length is ",len(blobs))
    if blobs:
        max_blob,max_size = find_max(blobs)
        print("The blob is ",max_blob)
        #img.draw_rectangle(max_blob.rect())
        #print("The length is ",len(max_blob))
        density = max_blob.density()
        #img.draw_rectangle(max_blob.x(),max_blob.y(),max_blob.cx)

        #print("rectangle")
        #led1.off()
        print("The max_size is ",max_size," and the density is ",density)
        led2.on()
        if max_size > 3000 and density>0.40:
            led2.off()
            led3.on()
            communcation_write(1)     #发送回MCU使得 飞机 悬停
            #tx_send_data(1,0,0,0,19)


            img.laplacian(1, sharpen=True)#通过边缘检测拉普拉斯核来对图像进行卷积。

            print("Now ")
            img.save('1.1.bmp')
            time.sleep_ms(50)
            print('get')
            #img.save('1.2.png')
            time.sleep_ms(50)

            print("frist tiaoxingma")
            led3.off()
            communcation_write(2)

def find_quarter(img):


    light.pulse_width_percent(50) # 控制亮度 0~100
    print('two_quar')

    led1.on()
    led3.off()
    #img = sensor.snapshot()

    #b_flag = False
    #img.rotation_corr(z_rotation=90)   #旋转视角进行寻找
    blobs = img.find_blobs([quar_threshold])

    if blobs:
        #communcation_write(3)
        max_blob,max_size = find_max(blobs)
        density = max_blob.density()
        if max_size > 4000 and density>0.35:
            #pass
        #quar_flag = False
    #if send_flag3:
    #    send_flag3 = False
    #img.draw_rectangle(max_blob.rect())
            img.laplacian(1, sharpen=True)
            img.save('2_1.bmp')
    for code in img.find_qrcodes():
        print(code)
       #b_flag = True
        img.laplacian(1, sharpen=True)
        img.save('2_2.bmp')
        time.sleep_ms(1000)
        img.save('2_3.bmp')
    #ewm_off = False
    print('second_tiaoxingma')
    communcation_write(3)

Work_mode = 0
now_Work_mode = 1

# 50kHz pin6 timer2 channel1
light = Timer(2, freq=50000).channel(1, Timer.PWM, pin=Pin("P6"))


while(True):

    #time.sleep_ms(1000)
    while(Work_mode == 0):
            clock.tick()
            uart_read_buf(uart)#这里读取串口数据
            select_mode = uart_mode_secelt()#这里将数据返回
            #print(select_mode)
            if (select_mode != 0):
                Work_mode = select_mode
                if Work_mode == 2:  #二维码
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.QVGA)
                    #sensor.set_windowing((200,200))
                if Work_mode == 1:  #条形码
                    sensor.set_pixformat(sensor.RGB565)
                    sensor.set_framesize(sensor.VGA)
                    sensor.set_windowing((200,200))
                if Work_mode == 33:  #红色杆识别
                    pass
                if Work_mode == 44:  #蓝色杆识别
                    pass
                if Work_mode == 55:  #巡线模式
                    pass
            else:
                led1.on()
                time.sleep_ms(1000)
                led1.off()
                time.sleep_ms(1000)
    while(Work_mode == 2 ):
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            #sensor.set_windowing((200,200))
            clock.tick()
            uart_read_buf(uart)
            now_Work_mode = uart_mode_secelt()
            if  now_Work_mode == 0:
                img = sensor.snapshot()
                find_quarter(img)
            else:
                Work_mode = now_Work_mode
                led3.off()
                pass



    while( Work_mode == 1 ):
            sensor.set_pixformat(sensor.RGB565)
            sensor.set_framesize(sensor.QVGA)
            sensor.set_windowing((200,200))
            clock.tick()
            uart_read_buf(uart)
            now_Work_mode = uart_mode_secelt()
            #img = sensor.snapshot().histeq(adaptive = True , clip_limit = 2)

            if  now_Work_mode == 0:
                img = sensor.snapshot()
                find_yellow(img)
            else:
                Work_mode = now_Work_mode
                led2.off()
                pass















####################################################
##############返程途中拍照############################
###############黄色条形码############################

while(False):
    img = sensor.snapshot()
    img.rotation_corr( z_rotation=90)  #旋转视角进行寻找
    img.median(1, percentile=0.5)
    blobs = img.find_blobs([yellow_threshold])
    if blobs:
        max_blob,max_size = find_max(blobs)
        density = max_blob.density()
        if max_size > 3000 and density>0.40:
            communcation_write(1)
            img.laplacian(1, sharpen=True)
            img.save('1_2.png')
            print('get1')
            break
