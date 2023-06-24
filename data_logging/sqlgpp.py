import sqlite3
import time
import datetime
from time import sleep
import serial

conn = sqlite3.connect("gppdb.db")
c = conn.cursor()

serialcomm = serial.Serial(
    port="/dev/ttyUSB0",
    baudrate=115200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1,
)

serialcomm.xonxoff = False
serialcomm.isOpen()


def create_table():
    c.execute(
        "CREATE TABLE IF NOT EXISTS gppdb( \
            chan1volt REAL,                      \
            chan1curr REAL,                      \
            chan1powr REAL,                      \
            chan2volt REAL,                      \
            chan2curr REAL,                      \
            chan2powr REAL,                      \
            chan3volt REAL,                      \
            chan3curr REAL,                      \
            chan3powr REAL,                      \
            chan4volt REAL,                      \
            chan4curr REAL,                      \
            chan4powr REAL,                      \
            timestamp TEXT                       \
         )"
    )
    # c.close()


def db_entry():
    unix = time.time()
    parameters = {1: [0, 0, 0], 2: [0, 0, 0], 3: [0, 0, 0], 4: [0, 0, 0]}
    # parameters index
    # 0 - voltage
    # 1 - current
    # 2 - power

    parameters[1][0] = get_serial(":MEASure1:VOLTage?")
    parameters[1][1] = get_serial(":MEASure1:CURRent?")
    parameters[1][2] = get_serial(":MEASure1:POWEr?")
    parameters[2][0] = get_serial(":MEASure2:VOLTage?")
    parameters[2][1] = get_serial(":MEASure2:CURRent?")
    parameters[2][2] = get_serial(":MEASure2:POWEr?")
    parameters[3][0] = get_serial(":MEASure3:VOLTage?")
    parameters[3][1] = get_serial(":MEASure3:CURRent?")
    parameters[3][2] = get_serial(":MEASure3:POWEr?")
    parameters[4][0] = get_serial(":MEASure4:VOLTage?")
    parameters[4][1] = get_serial(":MEASure4:CURRent?")
    parameters[4][2] = get_serial(":MEASure4:POWEr?")

    gpp_params = parameters
    date = str(datetime.datetime.fromtimestamp(unix).strftime("%d-%m-%Y_%X"))
    c.execute(
        "INSERT INTO gppdb (  chan1volt,  \
                                    chan1curr,  \
                                    chan1powr,  \
                                    chan2volt,  \
                                    chan2curr,  \
                                    chan2powr,  \
                                    chan3volt,  \
                                    chan3curr,  \
                                    chan3powr,  \
                                    chan4volt,  \
                                    chan4curr,  \
                                    chan4powr,  \
                                    timestamp )   VALUES (  ?, ?, ?,    \
                                                            ?, ?, ?,    \
                                                            ?, ?, ?,    \
                                                            ?, ?, ?,    \
                                                                  ? )",
        (
            gpp_params[1][0],
            gpp_params[1][1],
            gpp_params[1][2],
            gpp_params[2][0],
            gpp_params[2][1],
            gpp_params[2][2],
            gpp_params[3][0],
            gpp_params[3][1],
            gpp_params[3][2],
            gpp_params[4][0],
            gpp_params[4][1],
            gpp_params[4][2],
            date,
        ),
    )

    conn.commit()


def get_serial(command):
    # input command and expect the output in return
    sleep(0.5)
    serialcomm.reset_input_buffer()
    out = ""
    command = command + "\r\n"
    serialcomm.write(command.encode())
    sleep(1)
    while serialcomm.inWaiting() > 0:
        out += serialcomm.read(1).decode()
    print(out)
    serialcomm.reset_output_buffer()
    return out


if __name__ == "__main__":
    create_table()
    db_entry()
