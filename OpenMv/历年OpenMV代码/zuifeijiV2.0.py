# Untitled - By: 86188 - 周日 7月 25 2021
import sensor, image, time , math
from pyb import UART,LED,Pin,Timer,LED
from struct import pack, unpack
import json

uart = UART(3, 115200)
uart.init(115200, bits=8, parity=None, stop=1, timeout_char=1000)

uart1 = UART(1, 115200)
uart1.init(115200, bits=8, parity=None, stop=1)

led1 = LED(1)
sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.
clock = time.clock()



color_thesholds = [(31, 56, 33, 91, 23, 69)]


class receive(object):
    uart_buf = []
    state = 0
    rx_data = 0
    #red_pole_distance = 0
R = receive()
Rec = receive()

#通信协议


Rec_data = [0,0,0,0,0,0,0,0]
d = 0


def rx_receive530(data):
    global d
    global Rec_data
    #print("data is ",data)
    #print("R.state is ",R.state)
    if Rec.state==0:
        if data == 0x5A:
            Rec.state = 1
            Rec.uart_buf.append(data)
            #print(data)
            #print("the data received :",Rec.rx_data)
            #print("the data received :",Rec.uart_buf)
        else:
            Rec.state = 0
    elif Rec.state==1:
        if data == 0x5A:
            Rec.state = 2
            Rec.uart_buf.append(data)
            #print("the data received :",Rec.rx_data)
            #print("the data received :",Rec.uart_buf)
        else:
            Rec.state = 0
            Rec.uart_buf = []
    elif Rec.state==2:
        if data == 0x15:
            Rec.state = 3
            Rec.uart_buf.append(data)
            #print("the data received :",Rec.rx_data)
            #print("the data received :",Rec.uart_buf)
        else:
            Rec.state = 0
            Rec.uart_buf = []
    elif Rec.state==3:
        if data == 0x03:
            Rec.state = 4
            Rec.uart_buf.append(data)
            #print("the data received :",Rec.rx_data)
            #print("the data received :",Rec.uart_buf)
        else:
            Rec.state = 0
            Rec.uart_buf = []
    elif Rec.state==4:
        if Rec.rx_data == 0:
            Rec.uart_buf.append(data)
            #print("the data received :",Rec.uart_buf)
            Rec.state = 5
        else:
            Rec.state = 0
            Rec.uart_buf = []
    elif Rec.state==5:
        if Rec.rx_data == 0:
            Rec.uart_buf.append(data)
            #print("the data received :",Rec.uart_buf)
            Rec.state = 6
        else:
            Rec.state = 0
            Rec.uart_buf = []
    elif Rec.state==6:
        if Rec.rx_data == 0:
            Rec.uart_buf.append(data)
            #print("the data received :",Rec.uart_buf)
            Rec.state = 7
        else:
            Rec.state = 0
            Rec.uart_buf = []
    elif Rec.state==7:
        if data== (Rec.uart_buf[0] + Rec.uart_buf[1] + Rec.uart_buf[2] + Rec.uart_buf[3] + Rec.uart_buf[4] + Rec.uart_buf[5] + Rec.uart_buf[6]) & 0xFF :
            Rec.uart_buf.append(data)
            Rec.rx_data = 1
            #数据处理部分
            #print("the data received :",Rec.rx_data)
            Rec_data = Rec.uart_buf
            #print("Rec_data ",Rec_data)
            d = distance(Rec_data)
            #print("the data received :",Rec.rx_data)
            #print("the distance is ",d)
            Rec.uart_buf=[]
            #print("the data received :",Rec.uart_buf)
            Rec.state = 0
            #print(R.uart_buf)
        else:
            Rec.state = 0
            Rec.uart_buf = []


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
        #读取串口数据

def uart1_read_buf(uart):
    i = 0
    dis = 0
    buf_size = uart1.any()
    while i<buf_size:
        rx_receive530(uart1.readchar())
        i = i + 1

        #这里将串口读取的数据返回到find_mode 里面

def pack_data_text(data): #数据打包
    datalist = [0xAA,0x55,0x18,0x01,data]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    return data


def send_data(data_1,data_2,data_3,data_4):
#
#   data_3  ---> k
#   data_4  ---> distance
    datalist = [0xAA,0x55,0x12,0x04,data_1,data_2,data_3,data_4]
    datalist.append(sum_checkout(datalist))
    data = bytearray(datalist)
    uart.write(data)



def sum_checkout(data_list):
    data = 0
    for temp in data_list:
        data = temp + data
    #print(data)
    return data

def distance(Rec_data):
    distance = (Rec_data[4] << 8) |  Rec_data[5]
    Rec.rx_data = 0
    distance = int(distance / 10)
    return distance



while(1):
    led1.off()
    clock.tick()
    img = sensor.snapshot().histeq(adaptive=True, clip_limit=3)
    #uart1_read_buf(uart1)
    #print("The distance is ", d)
    #寻找blob
    blobs = img.find_blobs(color_thesholds,pixels_threshold = 50)
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
                err_x = blobs[largest_blob].cx()
                err_y = blobs[largest_blob].cy()
                k = math.atan((160 - blobs[largest_blob].cx())/(240 - blobs[largest_blob].cy()))
                K = int(-math.degrees(k))
                uart1_read_buf(uart1)
                #print("the distance is ",d)
        img.draw_cross(blobs[largest_blob].cx(),blobs[largest_blob].cy())#调试使用
        img.draw_rectangle(blobs[largest_blob].rect())
        send_data(err_x,err_y,K,d)
        print("The number of K is ",K)
        print("The x is ",err_x," The y is ",err_y,"the distance is",d)
    else:
       err_x = 0
       err_y = 0
       d = 0
       k = 0xff
       send_data(err_x,err_y,k,d)
       print("The x is ",err_x," The y is ",err_y,"the distance is",d)
    #数组中数据写入

    #uart_buf = bytearray([0x55,0xAA,err_x>>8,err_x,err_y>>8,err_y,0xA1])
    #print(err_x,err_x>>8)
    #print(err_x,err_y)


##################################################################################


    #if ((err_x < 245 and err_x > 75) and (err_y < 185 and err_y > 25 )):
    #    led1.on()
    #    uart1_read_buf(uart1)
    #    print("the distance is ",d)
    #    send_data(err_x,err_y,K,d)
    #    print(err_x,err_y,K,d)


##################################################################################

    #uart.write(uart_buf)

