# Untitled - By: 86188 - 周二 5月 25 2021

import sensor, image, time,pyb
from pyb import UART,LED
import json
import ustruct




#white_threshold_01 = ((95, 100, -18, 3, -8, 4));  #白色阈值
red_threshold_01 = ((2, 51, 11, 127, -128, 127))  #红色阈值

LED_R = pyb.LED(1) # Red LED = 1, Green LED = 2, Blue LED = 3, IR LEDs = 4.
LED_G = pyb.LED(2)
LED_B = pyb.LED(3)

LED_R.on()
LED_G.on()
LED_B.on()



sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_gain(False) # must be turned off for color tracking
sensor.set_auto_whitebal(False) # must be turned off for color tracking


clock = time.clock()

LED_R.off()
LED_G.off()
LED_B.off()

uart = UART(3,115200)   #定义串口3变量
uart.init(115200, bits=8, parity=None, stop=1) # init with given parameters



def find_max(blobs):    #定义寻找色块面积最大的函数
    max_size=0
    for blob in blobs:
        if blob.pixels() > max_size:
            max_blob=blob
            max_size = blob.pixels()
    return max_blob


def send_data_packet(x,y,z,w):
    temp = ustruct.pack("<bbhhhh",                #格式为俩个字符俩个整型
                   0x2C,                       #帧头1
                   0x12,                       #帧头2
                   int(x), # up sample by 4    #数据1
                   int(y), # up sample by 4    #数据2
                   int(z),
                   int(w))
                   #0x5B)
    uart.write(temp);                           #串口发送
    #led.on()
    #time.sleep_ms(1000)




while(True):
    img = sensor.snapshot()
    #time.sleep_ms(1000)
    #send_data_packet(x,y)
    blobs = img.find_blobs([red_threshold_01]);

    #FH = bytearray([0x2C,0x12])
    #uart.write(FH)
    cx=0;cy=0;
    if blobs:
                #如果找到了目标颜色
                max_b = find_max(blobs);
                # Draw a rect around the blob.
                img.draw_rectangle(max_b[0:4]) # rect
                #用矩形标记出目标颜色区域
                img.draw_cross(max_b[5], max_b[6]) # cx, cy
                #img.draw_cross(160, 120) # 在中心点画标记
                #在目标颜色区域的中心画十字形标记
                cx=max_b[5];
                cy=max_b[6];
                cw=max_b[2];
                ch=max_b[3];

    #data = bytearray([x,y])
    #uart.write('a')
                send_data_packet(cx,cy,cw,ch)
    #time.sleep_ms(1000)



    #uart.write("blue\r\n")
    #uart.write("1\r\n")
    #print("send")
    #led.off()
    #time.sleep_ms(1000)






#pack各字母对应类型
#x   pad byte        no value            1
#c   char            string of length 1  1
#b   signed char     integer             1
#B   unsigned char   integer             1
#?   _Bool           bool                1
#h   short           integer             2
#H   unsigned short  integer             2
#i   int             integer             4
#I   unsigned int    integer or long     4
#l   long            integer             4
#L   unsigned long   long                4
#q   long long       long                8
#Q   unsilong long   long                8
#f   float           float               4
#d   double          float               8
#s   char[]          string              1
#p   char[]          string              1
#P   void *          long
