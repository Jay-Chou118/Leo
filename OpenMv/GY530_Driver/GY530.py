# Hello World Example
#
# Welcome to the OpenMV IDE! Click on the green run arrow button below to run the script!

import sensor, image, time
from pyb import UART

uart = UART(1, 115200)
uart.init(115200, bits=8, parity=None, stop=1)

sensor.reset()                      # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565) # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)   # Set frame size to QVGA (320x240)
sensor.skip_frames(time = 2000)     # Wait for settings take effect.
clock = time.clock()                # Create a clock object to track the FPS.


class receive(object):
    uart_buf = []
    state = 0
    rx_data = 0  #标记串口接收完成
    #red_pole_distance = 0
R = receive()


global Rec_data
Rec_data = [0,0,0,0,0,0,0,0]

def rx_receive(data):
    #print("data is ",data)
    #print("R.state is ",R.state)
    if R.state==0:
        if data == 0x5A:
            R.state = 1
            R.uart_buf.append(data)
            #print(data)
            #print("the data received :",R.rx_data)
            #print("the data received :",R.uart_buf)
        else:
            R.state = 0
    elif R.state==1:
        if data == 0x5A:
            R.state = 2
            R.uart_buf.append(data)
            #print("the data received :",R.rx_data)
            #print("the data received :",R.uart_buf)
        else:
            R.state = 0
            R.uart_buf = []
    elif R.state==2:
        if data == 0x15:
            R.state = 3
            R.uart_buf.append(data)
            #print("the data received :",R.rx_data)
            #print("the data received :",R.uart_buf)
        else:
            R.state = 0
            R.uart_buf = []
    elif R.state==3:
        if data == 0x03:
            R.state = 4
            R.uart_buf.append(data)
            #print("the data received :",R.rx_data)
            #print("the data received :",R.uart_buf)
        else:
            R.state = 0
            R.uart_buf = []
    elif R.state==4:
        if R.rx_data == 0:
            R.uart_buf.append(data)
            #print("the data received :",R.uart_buf)
            R.state = 5
        else:
            R.state = 0
            R.uart_buf = []
    elif R.state==5:
        if R.rx_data == 0:
            R.uart_buf.append(data)
            #print("the data received :",R.uart_buf)
            R.state = 6
        else:
            R.state = 0
            R.uart_buf = []
    elif R.state==6:
        if R.rx_data == 0:
            R.uart_buf.append(data)
            #print("the data received :",R.uart_buf)
            R.state = 7
        else:
            R.state = 0
            R.uart_buf = []
    elif R.state==7:
        if data== (R.uart_buf[0] + R.uart_buf[1] + R.uart_buf[2] + R.uart_buf[3] + R.uart_buf[4] + R.uart_buf[5] + R.uart_buf[6]) & 0xFF :
            R.uart_buf.append(data)
            R.rx_data = 1
            #数据处理部分
            #print("the data received :",R.rx_data)
            Rec_data = R.uart_buf
            print("Rec_data ",Rec_data)
            d = distance(Rec_data)
            #print("the data received :",R.rx_data)
            print("the distance is ",d)
            R.uart_buf=[]
            #print("the data received :",R.uart_buf)
            R.state = 0
            #print(R.uart_buf)
        else:
            R.state = 0
            R.uart_buf = []

def uart_read_buf(uart):
    #uart.write()
    i = 0
    buf_size = uart.any()
    #print("buf_size = ",buf_size)
    uart.sendbreak()
    while i < buf_size:
        #Rec = uart.readchar()
        #print("I recieved : ",Rec)
        rx_receive(uart.readchar())
        #d = distance(rx_receive)
        i = i + 1

#例：一帧数据
#< 5A- 5A- 15- 03- 0A- 20- 06- FC >
#Distance =(0x0A<<8)|0x20=2592 mm(距离值 2.592 m)
def distance(Rec_data):
    distance = (Rec_data[4] << 8) |  Rec_data[5]
    R.rx_data = 0

    return distance


while(True):
    uart_read_buf(uart)
    #d = distance(Rec_data)
    #print("The distance is ",d)


    #d=distance(R.uart_buf)
    #print("the d is ",d)
    #print(uart.read(20))
    #time.sleep_ms(1000)
    #print(Rec_data)

    #clock.tick()                    # Update the FPS clock.
    #img = sensor.snapshot()         # Take a picture and return the image.

