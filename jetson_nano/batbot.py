#!/usr/bin/python3

from bluedot.btcomm import BluetoothServer
from datetime import datetime
from signal import pause

import serial
import socket
import struct
import subprocess
import time


#The following line is for serial over GPIO
port = '/dev/ttyACM0' # note I'm using Jetson Nano

arduino = serial.Serial(port,9600,timeout=5)
time.sleep(3) # wait for Arduino

camera_angle      = 90

uparrow           = 'F' # Foward
downarrow         = 'B' # Back
rightarrow        = 'R' # Right
leftarrow         = 'L' # Left

lookright         = '1' # Function 1
lookahead         = '2' # Function 2
lookleft          = '3' # Function 3

lookfullright     = '4' # Function 4
map_world         = '5' # Function 5
lookfullleft      = '6' # Function 6

slower            = '7' # Function 7
values            = '8' # Function 8
faster            = '9' # Function 9

monitor           = '0' # Function 0

settime           = 'X' # Time
setjoystick       = 'Y' # Joystick
allstop           = 'H' # Halt
run_star          = '*' # Star
run_sharp         = '#' # Sharp

SLD_MAX_VALUE     = 80.0
JOY_MAX_VALUE     = 70.0
JOY_NULL_REGION   = 10.0

joystick          = 0 # maps to the 90 degree camera_angle
slider            = 5 # maps to the 90 degree camera_angle
prev_slider       = 5
prev_joystick     = 0
state             = 'default'
joy_direction     = 'stopped'
slider_direction  = 'stopped'

hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)


def batbot_help():
    data = '\n--->: here are some key words i know:\n'
    data = data + 'look ahead, '
    data = data + 'look right, '
    data = data + 'look left, '
    data = data + 'forward, '
    data = data + 'back, '
    data = data + 'right, '
    data = data + 'left, '
    data = data + 'stop, '
    data = data + 'faster, '
    data = data + 'slower, '
    data = data + 'follow, '
    data = data + 'find, '
    data = data + 'avoid, '
    data = data + 'values, '
    data = data + 'identify, '
    data = data + 'learn, '
    data = data + 'map, '
    data = data + 'monitor, '
    data = data + 'photo, '
    data = data + 'fortune, '
    data = data + 'name, '
    data = data + 'IP address, '
    data = data + 'ping, '
    data = data + 'and help.\n\n'
    return data

def read_data_from_arduino():
    arduino.flush()
    robot_data = ''
    if arduino.inWaiting() > 0:
        robot_data = ''
        try:
            # read all characters in buffer
            robot_data = arduino.read(arduino.inWaiting()).decode('ascii')
            print(robot_data.strip())
            arduino.flush()
        except Exception as e:
            print("ERROR: read_data_from_arduino: e=" + str(e))
    return robot_data

def read_all_data_from_arduino():
    arduino.flush()
    result = ''
    while True:
        data = read_data_from_arduino()
        if len(data) == 0:
            break
        result = result + data
    return result

def write_commands(command_array):
    i = 0
    while (i < len(command_array)):
        arduino.flush()
        command = str(command_array[i])
        encoded_command = command.encode()
        arduino.write(encoded_command)
        #print(encoded_command)
        i = i + 1

def execute_commands(command_array):
    i = 0
    data = ''
    while (i < len(command_array)):
        data = data + read_data_from_arduino()

        # Serial write section
        arduino.flush()
        print("--> wrote command: ")
        command = str(command_array[i])
        encoded_command = command.encode()
        arduino.write(encoded_command)
        print(encoded_command)

        i = i + 1

    time.sleep(1) # I shortened this to match the new value in your Arduino code
    data = data + read_all_data_from_arduino()
    return data

def do_star():
    global state
    state = 'avoid'
    command_array = [run_star]
    result = execute_commands(command_array)
    return result

def do_stop():
    global state
    state = 'default'
    command_array = [allstop]
    result = execute_commands(command_array)
    return result

def do_sharp():
    global state
    state = 'following'
    command_array = [run_sharp]
    result = execute_commands(command_array)
    return result

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

def arduino_write_integer(value):
    # send 4 bytes of integer in network byte order
    commdata = arduino.write(struct.pack('>L', value))
    time.sleep(1) # wait for Arduino
    arduino.flush()
    result = read_all_data_from_arduino()
    return result

def set_arduino_time():
    arduino.flush()
    command = settime
    encoded_command = command.encode()
    arduino.write(encoded_command)
    arduino.flush()
    time.sleep(2)
    arduino.flush()
    result = read_all_data_from_arduino()
    #print("result=" + result)
    time.sleep(2)
    now = datetime.now()
    timestamp = 'T' + str(int(datetime.timestamp(now))) + '\n'
    encoded_timestamp = timestamp.encode()
    arduino.write(encoded_timestamp)
    arduino.flush()
    #print("SET_TIME offset sent: ")
    #print(timestamp)
    result = result + read_all_data_from_arduino()
    return result

def send_joystick_09_to_arduino(joystick):
    print("DBG: send_joystick_09_to_arduino=" + str(joystick))
    command = setjoystick
    encoded_command = command.encode()
    arduino.write(encoded_command)
    # send 4 bytes of integer in network byte order
    now = datetime.now()
    commdata = arduino.write(struct.pack('>L', joystick))
    print("SET_JOYSTICK sent: " + str(joystick))

def move_arduino_using_joystick(direction):
    print("DBG: move_arduino_using_joystick=" + direction)
    if direction == 'STOP':
        command_array = [allstop]
        write_commands(command_array)
    elif direction == 'AHEAD':
        command_array = [uparrow]
        write_commands(command_array)
    elif direction == 'BACK':
        command_array = [downarrow]
        write_commands(command_array)
    elif direction == 'RIGHT':
        command_array = [rightarrow]
        write_commands(command_array)
    elif direction == 'LEFT':
        command_array = [leftarrow]
        write_commands(command_array)

def change_camera_angle_using_slider_value(slider, slider_direction):
    print("DBG: change_camera_angle_using_slider_value=" + str(slider) + ", direction=" + slider_direction)
    go_right = slider_direction == 'RIGHT'
    if (slider == 0):
        pass
    elif (slider == 1):
        camera_angle = 90
        command_array = [lookahead]
        write_commands(command_array)
    elif (slider == 2):
        camera_angle = 90
        command_array = [lookahead]
        write_commands(command_array)
    elif (slider == 3):
        if go_right:
            camera_angle = 55
            command_array = [lookright]
        else:
            camera_angle = 125
            command_array = [lookleft]
        write_commands(command_array)
    elif (slider == 4):
        if go_right:
            camera_angle = 55
            command_array = [lookright]
        else:
            camera_angle = 125
            command_array = [lookleft]
        write_commands(command_array)
    elif (slider == 5):
        if go_right:
            camera_angle = 55
            command_array = [lookright]
        else:
            camera_angle = 125
            command_array = [lookleft]
        write_commands(command_array)
    elif (slider == 6):
        if go_right:
            camera_angle = 55
            command_array = [lookright]
        else:
            camera_angle = 125
            command_array = [lookleft]
        write_commands(command_array)
    elif (slider == 7):
        if go_right:
            camera_angle = 20
            command_array = [lookfullright]
        else:
            camera_angle = 160
            command_array = [lookfullleft]
        write_commands(command_array)
    elif (slider == 8):
        if go_right:
            camera_angle = 20
            command_array = [lookfullright]
        else:
            camera_angle = 160
            command_array = [lookfullleft]
        write_commands(command_array)
    elif (slider == 9):
        if go_right:
            camera_angle = 20
            command_array = [lookfullright]
        else:
            camera_angle = 160
            command_array = [lookfullleft]
        write_commands(command_array)

def process_blue_dot_slider(movementCommand):
    movementData = movementCommand.split(',')
    global camera_angle
    global slider
    global prev_slider
    global slider_direction
    try:
        if len(movementData) >= 3:
            x = int(float(movementData[1]) * 100)
            if x > 0:
                slider_direction = 'RIGHT'
            else:
                slider_direction = 'LEFT'

            # assume the 'slider' value be be between 0 and ~80
            # we will scale that to be from 0 to 9 like this:
            # x/9 = slider/80. solve for x. any x > 9 becomes 9

            slider = int((abs(x) / SLD_MAX_VALUE) * 9)
            if slider > 9:
                slider = 9
            print("DBG: calculated slider=" + str(slider))
            print("DBG: calculated slider_direction=" + slider_direction)

            if slider != prev_slider:
                prev_slider = slider
                change_camera_angle_using_slider_value(slider, slider_direction)

    except Exception as e:
        print("ERROR: process_blue_dot_slider: e=" + str(e))
    return str(slider)

def process_blue_dot_joystick(movementCommand, isRelease):
    movementData = movementCommand.split(',')
    global joy_direction
    global joystick
    global prev_joystick
    try:
        if len(movementData) >= 3:
            x = 0
            y = 0
            try:
                x = int(float(movementData[1]) * 100)
                y = int(float(movementData[2]) * 100)
                print("DBG: x=" + str(x) + ", y=" + str(y))
            except Exception as bad:
                print("ERROR: process_blue_dot_joystick: problem x/y: bad=" + str(bad))
                return "INVALID X/Y"

            if abs(x) <= JOY_NULL_REGION and abs(y) <= JOY_NULL_REGION:
                joy_direction = 'STOP'
            elif x > 0:
                if y > 0:
                    if x > y:
                        joystick = x - JOY_NULL_REGION
                        joy_direction = 'RIGHT'
                    else:
                        joystick = y - JOY_NULL_REGION
                        joy_direction = 'AHEAD'
                else:
                    if x > abs(y):
                        joystick = x - JOY_NULL_REGION
                        joy_direction = 'RIGHT'
                    else:
                        joystick = abs(y) - JOY_NULL_REGION
                        joy_direction = 'BACK'
            else:
                if y > 0:
                    if abs(x) > y:
                        joystick = abs(x) - JOY_NULL_REGION
                        joy_direction = 'LEFT'
                    else:
                        joystick = abs(y) - JOY_NULL_REGION
                        joy_direction = 'AHEAD'
                else:
                    if abs(x) > abs(y):
                        joystick = abs(x) - JOY_NULL_REGION
                        joy_direction = 'LEFT'
                    else:
                        joystick = abs(y) - JOY_NULL_REGION
                        joy_direction = 'BACK'

            # assume the 'joystick' value be be between 0 and ~70
            # we will scale that to be from 0 to 9 like this:
            # x/9 = joystick/70. solve for x. any x > 9 becomes 9

            joystick = int((joystick / JOY_MAX_VALUE) * 9)
            if joystick > 9:
                joystick = 9

            if isRelease:
                joy_direction = 'STOP'

            print("DBG: calculated joystick=" + str(joystick))
            print("DBG: calculated joy_direction=" + joy_direction)

            if isRelease or joystick != prev_joystick:
                prev_joystick = joystick
                send_joystick_09_to_arduino(joystick)
                move_arduino_using_joystick(joy_direction)

    except Exception as e:
        print("ERROR: process_blue_dot_joystick: e=" + str(e))
    return str(joystick) + ' ' + joy_direction

# a primitive language parser
def data_received(commandsFromPhone):
    global camera_angle
    global state
    pokeLogs = (commandsFromPhone == ' ')
    commandList = commandsFromPhone.splitlines()
    for data in commandList:
        result = read_data_from_arduino()
        printResult = False
        valid = False
        if pokeLogs:
            data = '' # don't echo the space used to poke the logs
            result = result + read_all_data_from_arduino()
            valid = True
        elif 'ping' in data:
            result = result + batbot_help()
            printResult = True
            valid = True
        elif 'IP address' in data:
            result = result + 'host=' + hostname + ', IP Address=' + IPAddr
            printResult = True
            valid = True
        elif 'click: *' in data:
            data = '*'
            result = result + do_star()
            printResult = True
            valid = True
        elif 'click: ok' in data:
            data = 'ok'
            result = result + do_stop()
            printResult = True
            valid = True
        elif 'click: #' in data:
            data = '#'
            result = result + do_sharp()
            printResult = True
            valid = True
        elif 'look ahead' in data:
            command_array = [lookahead]
            result = result + execute_commands(command_array)
            printResult = True
            camera_angle = 90
            valid = True
        elif 'look right' in data or 'turn right' in data:
            if camera_angle == 45:
                command_array = [lookfullright]
                result = result + execute_commands(command_array)
                camera_angle = 10
            else:
                command_array = [lookright]
                result = result + execute_commands(command_array)
                camera_angle = 45
            printResult = True
            valid = True
        elif 'right' in data:
            command_array = [rightarrow]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'look left' in data or 'turn left' in data:
            if camera_angle == 135:
                command_array = [lookfullleft]
                result = result + execute_commands(command_array)
                camera_angle = 170
            else:
                command_array = [lookleft]
                result = result + execute_commands(command_array)
                camera_angle = 135
            printResult = True
            valid = True
        elif 'left' in data:
            command_array = [leftarrow]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'forward' in data or 'ahead' in data:
            command_array = [uparrow]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'back' in data or 'reverse' in data:
            command_array = [downarrow]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'stop' in data or 'halt' in data:
            result = result + do_stop()
            printResult = True
            valid = True
        elif 'faster' in data or 'speed up' in data:
            command_array = [faster]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'slower' in data or 'slow down' in data:
            command_array = [slower]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'sensor' in data or 'value' in data:
            command_array = [values]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'fortune' in data or 'joke' in data:
            # sudo apt-get install fortunes
            for line in run_command('/usr/games/fortune'):
                try:
                    text = line.decode('ascii')
                    result = result + text
                except Exception as e:
                    print("ERROR: data_received: e=" + str(e))
            printResult = True
            valid = True
        elif 'follow' in data: # FIXME: run Elegoo line following
            result = result + do_sharp()
            printResult = True
            valid = True
        elif 'avoid' in data: # FIXME: run Elegoo collision avoidance
            result = result + do_star()
            printResult = True
            valid = True
        elif 'monitor' in data or 'security' in data: # FIXME: security monitor
            command_array = [monitor]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'photo' in data or 'picture' in data: # FIXME: optional item
            result = result + 'FIXME: take a picture'
            printResult = True
            valid = True
        elif 'find' in data or 'search' in data: # FIXME: next word is object
            result = result + 'FIXME: find some object'
            printResult = True
            valid = True
        elif 'identify' in data: # FIXME: identify what robot is looking at
            result = result + 'FIXME: learn to identify'
            printResult = True
            valid = True
        elif 'learn' in data: # FIXME: teach item name
            result = result + 'FIXME: learn about object'
            printResult = True
            valid = True
        elif 'map' in data: # FIXME: map the world
            state = 'map'
            command_array = [map_world]
            result = result + execute_commands(command_array)
            printResult = True
            valid = True
        elif 'name' in data:
            result = result + 'i am ' + hostname + '. i live at ' + IPAddr
            printResult = True
            valid = True
        elif 'help' in data or 'commands' in data:
            result = batbot_help()
            printResult = True
            valid = True

        #--------------------------------------------
        data = data.strip()
        if len(data) > 0:

            # don't echo back the movement commands
            if not valid:
                if (state == 'default'):
                    if data.startswith('2,'): # BlueDot onMove
                        data = 'JOYSTICK: ' + process_blue_dot_joystick(data, False)
                        result = result + read_all_data_from_arduino()
                        valid = True
                    elif data.startswith('1,'): # BlueDot onPress
                        data = 'CLICK: ' + process_blue_dot_joystick(data, False)
                        result = result + read_all_data_from_arduino()
                        valid = True
                    elif data.startswith('0,'): # BlueDot onRelease
                        data = 'RELEASE: ' + process_blue_dot_joystick(data, True)
                        result = result + read_all_data_from_arduino()
                        valid = True
                else:
                    if data.startswith('2,'): # BlueDot onMove
                        data = 'SLIDER: ' + process_blue_dot_slider(data)
                        result = result + read_all_data_from_arduino()
                        valid = True
                    elif data.startswith('1,'): # BlueDot onPress
                        data = 'CLICK: ' + process_blue_dot_slider(data)
                        result = result + read_all_data_from_arduino()
                        valid = True
                    elif data.startswith('0,'): # BlueDot onRelease
                        data = 'RELEASE: ' + process_blue_dot_slider(data)
                        result = result + read_all_data_from_arduino()
                        valid = True

            if valid:
                data = '--> ' + data.upper()
            else:
                # ignore bluedot numbers here
                if data[0].isdigit() or data[0] in ['-', ',', '.']:
                    data = ''
                else:
                    data = '??? ' + data.upper()
            print(data)

        else:
            arduino.flush()
        if len(result) > 0:
            result = result + read_all_data_from_arduino()
            if printResult:
                print(result.strip())
        if len(data) > 0:
            s.send(data + '\n' + result)
        else:
            s.send(result)
        #--------------------------------------------


def client_connect():
    print("*** BLUETOOTH CLIENT CONNECTED ***")

def client_disconnect():
    print("*** BLUETOOTH CLIENT DISCONNECTED ***")

try:

    result = read_all_data_from_arduino()
    #print(result)

    result = set_arduino_time()
    #print("ARDUINO TIME: " + result)
    result = read_all_data_from_arduino()
    #print(result)

    time.sleep(3)
    result = read_all_data_from_arduino()
    #print(result)

    result = do_stop()
    #print(result)
    result = read_all_data_from_arduino()
    #print(result)

    time.sleep(3)
    command_array = [values]
    result = execute_commands(command_array)
    #print("SENSOR VALUES: " + result)
    result = read_all_data_from_arduino()
    #print(result)

    s = BluetoothServer(data_received_callback = data_received,
            when_client_connects=client_connect,
            when_client_disconnects=client_disconnect)

    print('---> waiting for connection <---')
    pause()

except Exception as ex:
    print("PROGRAM ERROR: ex=" + str(ex))

