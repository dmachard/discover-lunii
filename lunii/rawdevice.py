
import random
import ctypes as ct
import uuid

from lunii import usb

SECTOR_SIZE = 512

FIRMWARE_VERSION_AND_SD_CARD_SIZE_SECTOR_ADDRESS = 2
PACKS_INDEX_SECTOR_ADDRESS = 100000

usb.init_libusb()

def open():
    """open device"""
    (dev_handle, _, _, _) = usb.open_device()
    return dev_handle
    
def close(handle):
    """close device"""
    usb.close_device(device_handle=handle)
    
def get_fw_version(handle):
    """get firmware version"""
    sector_data = (ct.c_uint8 * SECTOR_SIZE)()
    read_data(handle=handle, 
              sector_addr=FIRMWARE_VERSION_AND_SD_CARD_SIZE_SECTOR_ADDRESS,
              sector_cnt=1,
              sector_data=sector_data)
    return (sector_data[16], sector_data[20])

def get_sdcard_size(handle):
    """get sd card size"""
    # read from sd card the size of the sd
    sector_data = (ct.c_uint8 * SECTOR_SIZE)()
    read_data(handle=handle, 
              sector_addr=FIRMWARE_VERSION_AND_SD_CARD_SIZE_SECTOR_ADDRESS,
              sector_cnt=1,
              sector_data=sector_data)
              
    s = int.from_bytes([sector_data[26], sector_data[27], 
                        sector_data[24], sector_data[25]],
                        byteorder='big')
    sd_size = (s - 20480)
    usable_size = sd_size - PACKS_INDEX_SECTOR_ADDRESS

    # read packs index to get each size of them
    sector_data = (ct.c_uint8 * SECTOR_SIZE)()
    read_data(handle=handle, 
              sector_addr=PACKS_INDEX_SECTOR_ADDRESS,
              sector_cnt=1,
              sector_data=sector_data)

    nb_packs = int.from_bytes(sector_data[0:2], byteorder='big')
    taken_space = 0
    i = 2
    for p in range(nb_packs):
        pack_size = int.from_bytes(sector_data[i+4:i+8], byteorder='big')
        i += 12
        taken_space += pack_size
       
    # finally prepare storage space information
    sd_size_bytes = sd_size*SECTOR_SIZE
    total_size_bytes = usable_size*SECTOR_SIZE
    taken_space_bytes = taken_space*SECTOR_SIZE
    free_space_bytes = total_size_bytes - taken_space_bytes
    
    return (total_size_bytes, taken_space_bytes, free_space_bytes)
    
def get_packs_index(handle):
    """get pack index"""
    # read packs index to get each size of them
    sector_data = (ct.c_uint8 * SECTOR_SIZE)()
    read_data(handle=handle, 
              sector_addr=PACKS_INDEX_SECTOR_ADDRESS,
              sector_cnt=1,
              sector_data=sector_data)
    
    nb_packs = int.from_bytes(sector_data[0:2], byteorder='big')
    
    i = 2
    packs = []
    for p in range(nb_packs):
        pack = {}
        
        pack_start_sector = int.from_bytes(sector_data[i:i+4], byteorder='big')
        pack_size = int.from_bytes(sector_data[i+4:i+8], byteorder='big')
        pack_stats_offset = int.from_bytes(sector_data[i+8:i+10], byteorder='big')
        pack_sampling_rate = int.from_bytes(sector_data[i+10:i+12], byteorder='big')
        i += 12
        
        sector_pack = (ct.c_uint8 * (SECTOR_SIZE*2))()
        read_data(handle=handle,
                  sector_addr=PACKS_INDEX_SECTOR_ADDRESS + pack_start_sector, 
                  sector_cnt=2,
                  sector_data=sector_pack)
        
        pack_nb_elements = int.from_bytes(sector_pack[0:2], byteorder='big')
        pack_is_factory = sector_pack[2]
        pack_version = int.from_bytes(sector_pack[3:5], byteorder='big')
    
        msb = int.from_bytes(sector_pack[SECTOR_SIZE:SECTOR_SIZE+8], byteorder='big')
        lsb = int.from_bytes(sector_pack[SECTOR_SIZE+8:SECTOR_SIZE+16], byteorder='big')
        pack_uuid = uuid.UUID(int=(msb << 64) | lsb)
    
        pack["uuid"] = str(pack_uuid)
        pack["start-sector"] = pack_start_sector
        pack["size"] = pack_size
        pack["stats-offset"] = pack_stats_offset
        pack["sampling-rate"] = pack_sampling_rate
        pack["nb-elements"] = pack_nb_elements
        pack["version"] = pack_version
        pack["is-factory"] = pack_is_factory
        
        packs.append(pack)
    return packs
    
def write_data(handle, sector_addr, sector_cnt, sector_data):
    """write data to sd"""
    sd_header = (ct.c_uint8 * 31)(85, 83, 66, 67, -128, 56, 3, -61, 0, 2, 
                                  0, 0, 0, 0, 16, -10, -30, 0, 0, 0, 
                                  0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)

    sd_header[4] = random.randint(-128,128)
    sd_header[5] = random.randint(-128,128)
    sd_header[6] = random.randint(-128,128)
    sd_header[7] = random.randint(-128,128)
    
    nb_bytes_to_write = (sector_cnt * SECTOR_SIZE).to_bytes(length=4, byteorder="little", signed=True)
    sd_header[8] = nb_bytes_to_write[0]
    sd_header[9] = nb_bytes_to_write[1]
    sd_header[10] = nb_bytes_to_write[2]
    sd_header[11] = nb_bytes_to_write[3]
    
    sector_addr_bytes = sector_addr.to_bytes(length=4, byteorder="big")
    sd_header[18] = sector_addr_bytes[0]
    sd_header[19] = sector_addr_bytes[1]
    sd_header[20] = sector_addr_bytes[2]
    sd_header[21] = sector_addr_bytes[3]
    
    sector_cnt_bytes = sector_cnt.to_bytes(length=2, byteorder="big")
    sd_header[22] = sector_cnt_bytes[0]
    sd_header[23] = sector_cnt_bytes[1]
    
    usb.bulk_transfer(device_handle=handle, 
                      device_endpoint=usb.OUT_ENDPOINT,
                      data_buffer=sd_header)
                      
    usb.bulk_transfer(device_handle=handle, 
                      device_endpoint=usb.OUT_ENDPOINT,
                      data_buffer=sector_data)

    answer_data = (ct.c_uint8 * 13)()
    usb.bulk_transfer(device_handle=handle,
                      device_endpoint=usb.IN_ENDPOINT,
                      data_buffer=answer_data)
    if answer_data[12] != 0:
        raise Exception("write operation error occurred, code :%s" % answer_data[12])
        
def read_data(handle, sector_addr, sector_cnt, sector_data):
    """read data from sd"""
    sd_header = (ct.c_uint8 * 31)(85, 83, 66, 67, -128, 56, 3, -62, 0, 2, 
                                  0, 0, -128, 0, 16, -10, -31, 0, 0, 0, 
                                  0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0)
                 
    sd_header[4] = random.randint(-128,128)
    sd_header[5] = random.randint(-128,128)
    sd_header[6] = random.randint(-128,128)
    sd_header[7] = random.randint(-128,128)

    nb_bytes_to_write = (sector_cnt * SECTOR_SIZE).to_bytes(length=4, byteorder="little", signed=True)
    sd_header[8] = nb_bytes_to_write[0]
    sd_header[9] = nb_bytes_to_write[1]
    sd_header[10] = nb_bytes_to_write[2]
    sd_header[11] = nb_bytes_to_write[3]
    
    sector_addr_bytes = sector_addr.to_bytes(length=4, byteorder="big")
    sd_header[18] = sector_addr_bytes[0]
    sd_header[19] = sector_addr_bytes[1]
    sd_header[20] = sector_addr_bytes[2]
    sd_header[21] = sector_addr_bytes[3]
    
    sector_cnt_bytes = sector_cnt.to_bytes(length=2, byteorder="big")
    sd_header[22] = sector_cnt_bytes[0]
    sd_header[23] = sector_cnt_bytes[1]
    
    usb.bulk_transfer(device_handle=handle, 
                      device_endpoint=usb.OUT_ENDPOINT,
                      data_buffer=sd_header)
    print("op1 ok")
    usb.bulk_transfer(device_handle=handle,
                      device_endpoint=usb.IN_ENDPOINT,
                      data_buffer=sector_data)
    print("op2 ok")
    answer_data = (ct.c_uint8 * 13)()
    usb.bulk_transfer(device_handle=handle,
                      device_endpoint=usb.IN_ENDPOINT,
                      data_buffer=answer_data)
    
    if answer_data[12] != 0:
        raise Exception("read operation error occurred, code :%s" % answer_data[12])
