""" Module for controlling the Zaber T-OMG stage.

Before moving the stages, sending all devices home is highly recommended.
For that, the 'send_home' function should be used with the 'device_id'
parameter set to '0' (the command will be sent to all devices).

This file can also be imported as a module and contains the following
functions:

    * send_home - function for sending the stage home. Takes the device ID as
    a parameter.
    
    * reset_settings - restore all Zaber stage settings to the default
    ones. Should be used when the device does not respond or function
    properly.
    
    * move_to_relative - function for moving the stage to the relative
    position, which is the sum of the current position plus the distance
    inputted.
    
    * get_current_position - returns the curret position in hexadecimal.

"""

import time

import numpy as np
import serial


def send_home(device_id: int = 0, com: str = "COM5"):
    """
    Function for sending the stage home. Takes the device ID as a parameter.

    Parameters
    ----------
    device_id : int, optional
        Device ID. In the case of multiple devices, by default they
        should get IDs in a chain starting from 1. Choosing 0 will send
        the command to all devices. The default is 0 to send all devices
        home. Numbers from 0 to 254 are allowed. For the T-OMG stage,
        '1' should be the azimuth, '2' - for the elevation.
    com : str, optional
        Name of the port to which the Zaber stage is connected. On
        Windows, check 'Device Manager' under 'Ports (COM & LPT)'.

    Returns
    -------
    None.

    """

    # A total of 6 bytes is sent to the device
    to_device = bytearray()

    # First byte is the device number
    if device_id == 0:
        to_device.append(0x00)
    elif device_id == 1:
        to_device.append(0x01)
    elif device_id == 2:
        to_device.append(0x02)
    else:
        to_device.append(0x03)

    # The second byte is the command number
    to_device.append(0x01)  # command 1

    # For the command '1' (send home) the data bytes are ignored, hence they
    # are left empty
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)

    # Open the appropriate USB port
    # Zaber devices typically communicate over RS-232 at 9600 baud
    try:
        serialZABER = serial.Serial(com, baudrate=9600)
    except serial.SerialException:
        print("No device has been found at the chosen port")

    # Send the byte string to the device
    serialZABER.write(to_device)


def reset_settings(com: str = "COM5"):
    """
    Restore all settings to the default ones.

    Parameters
    ----------
    com : str, optional
        Name of the port to which the Zaber stage is connected. On
        Windows, check 'Device Manager' under 'Ports (COM & LPT)'.

    Returns
    -------
    None.

    """

    # A total of 6 bytes is sent to the device
    to_device = bytearray()

    # Send to all devices - device number is '0'
    to_device.append(0x00)

    # The byte chain for the command
    to_device.append(0x24)  # command 36
    # for the command '1' (send home) the data bytes are ignored, hence
    # they are left empty
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)

    # Open the appropriate USB port
    # Zaber devices typically communicate over RS-232 at 9600 baud
    try:
        serialZABER = serial.Serial(com, baudrate=9600)
    except serial.SerialException:
        print("No device has been found at the chosen port")

    # Send the byte string to the device
    serialZABER.write(to_device)


def move_to_relative(device_id: int = 1, com: str = "COM5", theta: float = 1):
    """
    Function for moving the Zaber T-OMG stage to a relative position.

    Works with both negative and positive input values. The communication
    is done via 6 byte words: 1st byte for the device number the command
    is send to, 2nd byte is for the command (see Zaber binary protocol
    manual), and the 4 bytes are the data. The data are read starting
    from the LSB.

    Parameters
    ----------
    device_id : int, optional
        Device ID. In the case of multiple devices, by default they
        should get IDs in a chain starting from 1. Choosing 0 will send
        the command to all devices. The default is 0 to send all devices
        home. Numbers from 0 to 254 are allowed. For the T-OMG stage,
        '1' should be the azimuth, '2' - for the elevation. The
        default is '1'.
    com : str, optional
        Name of the port to which the Zaber stage is connected. On
        Windows, check 'Device Manager' under 'Ports (COM & LPT)'.
        The default is 'COM5'.
    theta : float, optional
        The angle of the desired shift in degrees. The default is 1.

    Returns
    -------
    None.

    """

    # A total of 6 bytes is sent to the device
    to_device = bytearray()

    # First byte is the device number
    if device_id == 0:
        to_device.append(0x00)
    elif device_id == 1:
        to_device.append(0x01)
    elif device_id == 2:
        to_device.append(0x02)
    else:
        to_device.append(0x03)

    # The second byte is the command number
    to_device.append(0x15)  # command 21

    # Set the distance between the actuator and the axis of rotation
    # based on the device number
    if device_id == 1:
        A = 11825e-6  # azimuthal
    elif device_id == 2:
        A = 23650e-6  # elevation

    R = 64  # microsteps/step; default is '64'
    L = 1.524e-6  # the linear motion for one full step of the actuator

    # For converting the input angle in degrees to radians for the
    # np.tan
    deg_to_rad = np.pi / 180

    # Shift in the positive direction - from the home position
    if theta > 0:

        # Convert the angle to the data for the actuator
        data = int(np.tan(theta * deg_to_rad) * A * R / L)

        # Cut the '0x' from the hexadecimal notation
        data_hex = hex(data)[2:]

        # Byte length control
        if len(data_hex) == 1:
            data_hex = "000" + data_hex
        if len(data_hex) == 2:
            data_hex = "00" + data_hex
        elif len(data_hex) == 3:
            data_hex = "0" + data_hex

        # Only 'int' values can be appended to bytearrays; convert the strings
        # to int
        to_device.append(int(data_hex[2:4], 16))
        to_device.append(int(data_hex[0:2], 16))

        # Positive values will have first two bytes empty
        to_device.append(0x00)
        to_device.append(0x00)

    # Shift in the negative direction - towards home
    else:

        # Convert the angle to the data for the actuator
        data = int(np.tan(theta * deg_to_rad) * A * R / L)

        # If the input is a negative value, signed data should be converted
        # to unsigned before sending the command to the device
        data_hex = hex(data + (1 << 32))

        # Take the lower two bytes with the actual data
        data_hex = data_hex[-4:]

        # Only 'int' values can be appended to bytearrays; convert the strings
        # to int
        to_device.append(int(data_hex[2:4], 16))
        to_device.append(int(data_hex[0:2], 16))

        # Negative values will have first two bytes of 0xFF from the
        # signed-to-unsigned conversion
        to_device.append(0xFF)
        to_device.append(0xFF)

    # Open the appropriate USB port
    # Zaber devices typically communicate over RS-232 at 9600 baud
    try:
        serialZABER = serial.Serial(com, baudrate=9600)
    except serial.SerialException:
        print("No device has been found at the chosen port")

    # Send the byte string to the device
    serialZABER.write(to_device)

    # Print the byte chain that was sent to the device
    print(to_device)


# TODO: from hex to angle
def get_current_position(device_id: int = 1, com: str = "COM1"):
    """Return the current position of the stage.

    Return the current position in hexadecimal notation based on the
    device number inputted.

    Parameters
    ----------
    device_id : int, optional
        Device ID. In the case of multiple devices, by default they
        should get IDs in a chain starting from 1. Choosing 0 will send
        the command to all devices. The default is 0 to send all devices
        home. Numbers from 0 to 254 are allowed. For the T-OMG stage,
        '1' should be the azimuth, '2' - for the elevation. The
        default is '1'.
    com : str, optional
        Name of the port to which the Zaber stage is connected. On
        Windows, check 'Device Manager' under 'Ports (COM & LPT)'. The
        default is 'COM5'.

    Returns
    -------
    msg : bytearray
        The byte chain with, starting from LSB, device number,
        command number, position of the device.
    """

    # A total of 6 bytes is sent to the device
    to_device = bytearray()

    # First byte is the device number
    if device_id == 0:
        to_device.append(0x00)
    elif device_id == 1:
        to_device.append(0x01)
    elif device_id == 2:
        to_device.append(0x02)
    else:
        to_device.append(0x03)

    # The second byte is the command number
    to_device.append(0x3C)  # command 60

    # The command data are ignored, hence left epmty
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)
    to_device.append(0x00)

    # Open the appropriate USB port
    # Zaber devices typically communicate over RS-232 at 9600 baud
    try:
        serialZABER = serial.Serial(com, baudrate=9600, timeout=5)
    except serial.SerialException:
        print("No device has been found at the chosen port")

    # Send the byte string to the device
    serialZABER.write(to_device)

    # Read the response from the device
    msg = serialZABER.readline()

    return msg
