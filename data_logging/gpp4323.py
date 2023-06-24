from time import sleep
import serial

# configure the serial connections (the parameters differs on the device you are connecting to)
ser = serial.Serial \
(
	port='/dev/ttyUSB0',
	baudrate=115200,
        parity=serial.PARITY_NONE,
	stopbits=serial.STOPBITS_ONE,
	bytesize=serial.EIGHTBITS
)

ser.xonxoff=False
#sleep(1)
#ser.open()
ser.isOpen()

print ('Enter your commands below.\r\nInsert "exit" to leave the application.')

inputval=''
while (inputval != 'exit'):
    inputval = input(">> ")
    if (inputval == 'exit'):
        ser.close()
        exit()
    else:
        out=""
        serialcmd = inputval + "\r\n" 
        ser.write(serialcmd.encode())
        #sleep(3)
        while ser.inWaiting() > 0:
            out+=ser.read(1).decode()
        print (">>" + out)
