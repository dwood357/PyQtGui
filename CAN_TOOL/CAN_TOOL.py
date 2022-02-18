import time
import struct
import numpy as np
import can

class CAN_TOOL(object):

    def __init__(self, deviceType, baudrate = 250000):
        """
        deviceType: The physical Hardware your using.

        Pcan Device == 'PCAN'
        waveshare RS485 Hat == 'RS485HAT'
        valueCAN Device == 'VALUECAN'

        """
        self.deviceType = deviceType
        self.baudrate = baudrate

        if self.deviceType == 'PCAN':
            can.rc['interface'] = 'pcan'
            can.rc['channel'] = 'PCAN_USBBUS1'
            can.rc['bitrate'] = self.baudrate  
            from can.interface import Bus

            self.bus = Bus()
        
        if self.deviceType == 'RS485HAT':
            self.bus = can.interface.Bus(channel= 'can0', bustype= 'socketcan_ctypes')
        
    def send(self,_id = 0,d = [0,0,0,0,0,0,0,0]):
        # data = [0,0,0,0,0,0,0,0]
        msg = can.Message(arbitration_id = _id, data = d)
        self.bus.flush_tx_buffer()
        self.bus.send(msg)

    def read(self,raw=True, _bytes = True, verbose = False):
        """
        Raw will print out the default CAN structure msg

        Bytes determines if what is returned is a bytesarray or not

        Verbose prints out here, so you dont have to in your main script
        """
        try:
            msg = self.bus.recv(0.5)
            PGN = (msg.arbitration_id >> 8) & 0xFFFF
            
            data = msg.data
            _id = msg.arbitration_id
            # print(data)
            if _bytes:
                #return byte array
                if verbose:
                    print(_id,data)
                pass
            else:
                if raw and verbose:
                    print(data)
                else:
                    #This will return a list
                    # data = struct.unpack('<8c', data)
                    data = [hex(x) for x in data]
                    if verbose:
                        print('{} ({})\t{}'.format(hex(msg.arbitration_id),PGN,data))
                data = list(data)
        except AttributeError:
            # msg = 0
            # PGN = 0
            data = [0]
            _id = 0
            print("No Msgs Received")

        # return msg.arbitration_id ,list(data)
        return _id , data

if __name__ == "__main__":

    self = CAN_TOOL()