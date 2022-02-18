import time
import struct
import numpy as np
import can

class PCAN_tool(object):

    def __init__(self):
        can.rc['interface'] = 'pcan'
        can.rc['channel'] = 'PCAN_USBBUS1'
        can.rc['bitrate'] = 1000000  
        from can.interface import Bus


        self.PCAN_bus = Bus()
    def send(self,_id = 0,d = [0,0,0,0,0,0,0,0]):
        # data = [0,0,0,0,0,0,0,0]
        msg = can.Message(arbitration_id = _id, data = d)
        self.PCAN_bus.flush_tx_buffer()
        self.PCAN_bus.send(msg)

    def read(self,raw=True, _bytes = True, verbose = False):
        """
        Raw will print out the default CAN structure msg

        Bytes determines if what is returned is a bytesarray or not

        Verbose prints out here, so you dont have to in your main script
        """
        try:
            msg = self.PCAN_bus.recv(1)
            PGN = (msg.arbitration_id >> 8) & 0xFFFF
            
            data = msg.data
            _id = msg.arbitration_id
            
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
                        print('{} ({})\t{}'.format(msg.arbitration_id,PGN,data))
                data = list(data)
        except AttributeError:
            # msg = 0
            # PGN = 0
            data = [0]
            _id = 0
            print("No Msgs Received")

        # return msg.arbitration_id ,list(data)
        return _id , data


    def _id_header(self,raw=True):
    
        msg = self.PCAN_bus.recv(1)
        
        # PGN = msg.arbitration_id

        PGN = (msg.arbitration_id >> 8) & 0xFFFF

        data = msg.data
        sph_data = []
        tracked_data = []
        _type = 'raw'
        target_id = 0
        pos_x = 0
        pos_y = 0
        pos_z = 0
        vel_x = 0
        vel_y = 0
        vel_z = 0
        SNR = 0
        target_range = 0
        target_speed = 0
        azimuth_angle = 0
        elevation_angle = 0
        if raw:
            data = [hex(x) for x in data]
            # print(data)
            print('{}\t{}'.format(PGN,data))

        else:
            if len(data) == 8:
                hdata = [hex(x) for x in data]
                if hdata[5] and hdata[6] and hdata[7] == '0xff':
                    track_id = (data[0] >> 8)*256 + (data[1] >> 8)
                    num_targets = (data[2] >> 8)*256 + (data[3] >> 8)
                    if (data[4] >> 8) == 0:
                        _type = 'raw'
                    elif (data[4] >> 8) == 1:
                        _type = 'Tracked Spher'
                    elif (data[4] >>8) == 4:
                        _type = 'Tracked Cart'
                    
                    print('{}\t{}\t{}'.format(track_id, num_targets,_type))
                elif hdata[5] and hdata[6] and hdata[7] != '0xff':
                    #Not a header frame
                    if _type == 'Tracked Spher':
                        #Tracked Spherical frame
                        target_id = (data[0] >> 8)
                        SNR = (data[1] >> 8)#dB
                        target_range = 0.01*((data[2] >> 8)*256 + (data[3] >> 8)) #m
                        target_speed = 0.005*((data[4] >> 8)*256 + (data[5] >> 8)) #m/s
                        azimuth_angle = (data[6] >> 8) #deg
                        elevation_angle = (data[7] >> 8) #deg
                        sph_data = [target_id,SNR,target_range,target_speed,azimuth_angle,elevation_angle]
                    elif _type == 'Tracked Cart' and (data[4] >> 1) == 0:
                        #Cartesian Frame A
                        target_id = (data[0] >> 8)
                        pos_x = 0.01*((data[2] >> 8)*256 + (data[3] >> 8)) #m
                        pos_y = 0.01*((data[4] >> 8)*256 + (data[5] >> 8)) #m
                        pos_z = 0.01*((data[6] >> 8)*256 + (data[7] >> 8)) #m
                    elif _type == 'Tracked Cart' and (data[4] >> 1) == 1:
                        #Cartesian Frame B
                        target_id = (data[0] >> 8)
                        vel_x = 0.01*((data[2] >> 8)*256 + (data[3] >> 8)) #m
                        vel_y = 0.01*((data[4] >> 8)*256 + (data[5] >> 8)) #m
                        vel_z = 0.01*((data[6] >> 8)*256 + (data[7] >> 8)) #m
                    tracked_data = [target_id,pos_x,pos_y,pos_z,vel_x,vel_y,vel_z]
                else:
                    pass

            # print('{}\t{}'.format(PGN,data))
            
            print(sph_data, end ='\n')
            print(tracked_data, end = '\n')
        return [sph_data,tracked_data]


    def angle_msg(self):
        msg = self.PCAN_bus.recv(1)
        _id = msg.arbitration_id
        
        PGN = (msg.arbitration_id >> 8) & 0xFFFF

        data = msg.data
 
        if PGN == 65523:

            if len(data) == 8:
                data = struct.unpack('hhhh', data)
                data = list(data)
                data[0] = data[0]/10
                data[1] = data[1]/20
                data[2] = data[2]/10
                data[3] = data[3]/20
                print("ID:\t{} Roll:\t{} RollRate:\t{}".format(_id,data[0],data[1]))

        return list(data)
    
    def reset(self):
        # _id = FFF2A3
        data = 0x00
        # send a message
        message = can.Message(arbitration_id=0xFFF2A3, is_extended_id=True,
                              data=data)
        self.PCAN_bus.send(message, timeout=0.2)
        return

    def orientation_set_msg(self):
        data = [0x38,0x00,0x00,0x20,0x07,0x00,0x00,0x00]

        message = can.Message(arbitration_id=0xFFF2A3, is_extended_id=True,
                              data=data)
        self.PCAN_bus.send(message, timeout=0.2)
        return 
                    
if __name__ == "__main__":

    self = PCAN_tool()