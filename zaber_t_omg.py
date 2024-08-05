""" Script for controlling the Zaber T-OMG stage.

A 'pyserial' module is required to get access to a serial port.

Before moving the stages, sending all devices home is highly recommended.
For that, the 'send_home' function should be used with the device_id parameter
set to '0' (the command will be sent to all devices).

This file can also be imported as a module and contains the following
functions:
    * send_home - function for sending the stage home. Takes the device ID as
    a parameter.
    * move_to_relative - function for moving the stage to the relative
    position.

"""

import serial
import numpy as np

def send_home(device_id: int = 0):
    '''
    Function for sending the stage home. Takes the device ID as a parameter.

    Parameters
    ----------
    device_id : int, optional
        device_id : int, optional
            Device ID. In the case of multiple devices, by default they should
            get IDs in a chain starting from 1. Choosing 0 will send the
            command to all devices. The default is 0 to send all devices home.
            Numbers from 0 to 254 are allowed.

    Returns
    -------
    None.

    '''
    to_device = bytearray()
    if device_id == 0:
        to_device.append(0x00)
    elif device_id == 1:
        to_device.append(0x01)
    elif device_id == 2:
        to_device.append(0x02)
    else:
        to_device.append(0x03)

    to_device.append(0x01)
    # for the command '1' (send home) the data bytes are ignored, hence they
    # are left empty
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)


def move_to_relative(theta: int, device_id: int = 1):
    '''
    Function for moving the Zaber T-OMG stage to a relative position. Works
    with both negative and positive input values. The communication is done
    via 6 byte words: 1st byte for the device number the command is send to,
    2nd byte is for the command (see Zaber binary protocol manual), and the
    4 bytes are the data. The data are read starting from the LSB.

    Parameters
    ----------
    theta : int
        Relative angle to which the stage is desired to move.
    device_id : int
    
        Device ID. In the case of multiple devices, by default they should
        get IDs in a chain starting from 1. Choosing 0 will send the command
        to all devices. The default is 1 for the first device connected.
        Devices 1 and 2 should be attributed to the azimuthal and elevation actuators.

    Returns
    -------
    None.

    '''
    
    
    to_device = bytearray()
    if device_id == 0:
        to_device.append(0x00)
    elif device_id == 1:
        to_device.append(0x01)
    elif device_id == 2:
        to_device.append(0x02)
    else:
        to_device.append(0x03)

    to_device.append(0x15)  # command number '21' - move to the relative
    # position
    microstep_az = 11825  # microstep of the model T-OMG for azimuth 
    microstep_el = 23650  # microstep of the model T-OMG for elevation
    
    if device_id == 1: #1 corresponds to azimuthal actuator? TODO
        A = microstep_az
    elif device_id == 2:
        A = microstep_el 
    R = 64
    L = 1.524
    if theta > 0:
        data = int(np.tan(theta)*A*R/L)  # convert the relative position
        # desired to the internal data for the device
        data_hex = hex(data)[2:]

        if len(data_hex) == 3:
            data_hex = '0' + data_hex

        # only 'int' values can be appended to bytearrays; convert the strings
        # to int
        to_device.append(int(data_hex[0:2], 16))
        to_device.append(int(data_hex[2:4], 16))

        # positive values will have first two bytes empty
        to_device.append(0x00)
        to_device.append(0x00)
    else:
        # if the input is a negative value, signed data should be converted
        # to unsigned before sending the command to the device
        data = int(np.tan(theta)*A*R/L)  # convert the relative position
        # desired to the internal data for the device based on the microstep
        # of the model (T-OMG)
        data_hex = hex(data + (1 << 32))
        data_hex = data_hex[-4:]

        # only 'int' values can be appended to bytearrays; convert the strings
        # to int
        to_device.append(int(data_hex[0:2], 16))
        to_device.append(int(data_hex[2:4], 16))

        # negative values will have first two bytes of 0xFF from the
        # signed-to-unsigned conversion
        to_device.append(0xFF)
        to_device.append(0xFF)

    # open the appropriate USB port
    # Zaber devices typically communicate over RS-232 at 9600 baud
    try:
        serialZABER = serial.Serial('COM5', baudrate=9600)
    except serial.SerialException:
        print("No device has been found at the chosen port")
    serialZABER.write(to_device)
