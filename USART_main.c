/*----------------------------------------------------
	串口1发送字符串控制LED   
				
				BaudRate	--	115200
				WordLength--	8b
				StopBit		--	1
				Parity		--	No
	 
				发送 LED1+ON 点亮LED1
				发送 LED1+OFF 关闭LED1
				发送其他字符串翻转LED2状态
				
				需要串口 调试助手上勾选发送新行，因为串口接收是以/n作为接收完成标志的
------------------------------------------------------*/
#include "stm32f10x.h"
#include "led.h"
#include "key.h"
#include "usart.h"
#include "delay.h"
#include "string.h"




extern char Rec_Buffer[];
extern char SendData[];

extern u8 USART_REC_Finish_FLAG;



int main(void)
{
	
	char ch;
	char LED1ON[] = "LED1+ON\r";				//定义相关的字符串     \n 被吃掉了
	char LED1OFF[] = "LED1+OFF\r";
	

	LED_GPIO_Config();								//初始化LED相关的IO 
	LED_ALL_OFF();										//并关闭所有的LED 

//	KEY_Config();										//按键初始化
	
	USART_Config();										//串口的初始化
	USART_NVIC_Config();							//串口的中断配置
	
	printf("USART TEST\r\n");					

	
	while(1)
	{
		/*             按键测试程序         */
//		if(!GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_1))	 
//	{  delay_ms(20);
//		if(!GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_1))
//		{
//		
//		printf(SendData);printf("\r\n");
//		
//		while(!GPIO_ReadInputDataBit(GPIOA, GPIO_Pin_1)){}
//		}
//	}
		/* -----------------------------*/

		
		
		while(USART_REC_Finish_FLAG == 1)						//等待串口接收完成标志位置1
		{	
			delay(1000);			//延时1ms
			
			USART_REC_Finish_FLAG = 0;		//使用完成后将串口标志位置〇
			
			
			
			if(strcmp(SendData, LED1ON)==0)						//比较字符串 
				ch = '1';
			else if(strcmp(SendData, LED1OFF)==0)
				ch = '2';
			else
				ch = '3';
			printf("%c  \r\n",ch);
		
	
			switch(ch)
			{
				case '1':
					LED1_ON;
					printf("LED1 ON\r\n");
				break;
				case '2':
					LED1_OFF;
					printf("LED1 OFF\r\n");
				break;
				case '3':
					LED2_TOGGLE;
					printf("LED2 TOGGLE\r\n");
				break;
				default:
					printf("Error!\r\n");
				break;
			}
			
		}
	}
}
