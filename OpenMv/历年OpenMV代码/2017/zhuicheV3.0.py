# Untitled - By: 86188 - 周日 7月 25 2021
import sensor, image, time , math
from pyb import UART,LED,Pin ,Timer
import time
from struct import pack, unpack
import json

uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1, timeout_char=1000)

sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.
clock = time.clock()


ROI = [(0,0,320,80,1),
       (0,120,320,80,1),
       (0,240,320,80,1)
        ]

color_thesholds = (19, 52, -19, -4, -14, 3)

class receive(object):
    uart_buf = []
    state = 0
    rx_data = 0
    #red_pole_distance = 0
R = receive()


#通信协议
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


def pack_data_text(data): #数据打包
    datalist = [0xAA,0x55,0x18,0x01,data]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    return data


def send_data(data_1,data_2,data_3):
#
#   data_3  ---> k
#
    datalist = [0xAA,0x55,0x12,0x03,data_1,data_2,data_3]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    uart.write(data)



def sum_checkout(data_list):
    data = 0
    for temp in data_list:
        data = temp + data
    return data

while(True):

    clock.tick()
    img = sensor.snapshot()
    img.rotation_corr( z_rotation=180)  #旋转视角进行寻找
    #寻找blob
    blobs = img.find_blobs([color_thesholds])
    if blobs:
        most_pixels = 0
        largest_blob = 0
        for i in range(len(blobs)):
            #目标区域找到的颜色块可能不止一个，找到最大的一个
            if blobs[i].pixels() > most_pixels:
                most_pixels = blobs[i].pixels()
                largest_blob = i
                #img.draw_line(blobs[largest_blob].cx(),blobs[largest_blob].cy(),160,240)
                #位置环用到的变量
                #err_x = int( 160 - blobs[largest_blob].cx())
                #err_y = int(180 - blobs[largest_blob].cy())
                err_x = blobs[largest_blob].cx()
                err_y = blobs[largest_blob].cy()
                k = math.atan((160 - blobs[largest_blob].cx())/(240 - blobs[largest_blob].cy()))
                K = int(-math.degrees(k))
        img.draw_cross(blobs[largest_blob].cx(),blobs[largest_blob].cy())#调试使用
        img.draw_rectangle(blobs[largest_blob].rect())
        send_data(err_x,err_y,K)
        print("The number of K is ",K)
    else:
       err_x = 0
       err_y = 0
       k = 0xff
       send_data(err_x,err_y,k)
    #数组中数据写入

    #uart_buf = bytearray([0x55,0xAA,err_x>>8,err_x,err_y>>8,err_y,0xA1])
    #print(err_x,err_x>>8)
    print(err_x,err_y)
    #uart.write(uart_buf)

