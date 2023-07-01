
import ctypes as ct

from lunii import rawdevice

def require_padding(block):
    """require padding"""
    if len(block) == 512:
        return block
    nb_pad = rawdevice.SECTOR_SIZE - len(block)
    return block + b'\x00'*nb_pad
    
def load():
    """load lunii device information"""
    handle = rawdevice.open()
    
    fw = rawdevice.get_fw_version(handle=handle)
    sd = rawdevice.get_sdcard_size(handle=handle)
    packs = rawdevice.get_packs_index(handle=handle)

    rawdevice.close(handle=handle)
    
    return (fw,sd,packs)
    
def download_pack(pack_uuid, cb_progress=None):
    """download pack from device"""
    handle = rawdevice.open()
    
    packs = rawdevice.get_packs_index(handle=handle)

    pack_exists = False
    for p in packs:
        if p["uuid"] == pack_uuid:
            pack_exists = True
            break
    
    if not pack_exists:
        raise Exception("Pack=%s does not exist on device" % pack_uuid)

    total_work = p["size"] * rawdevice.SECTOR_SIZE
    work_done = 0
    work_done_percent = 0
    
    chunk_size = 20000
    pack_binary = b""
    s = p["size"] // chunk_size
    r = p["size"] % chunk_size
    
    cb_progress(0)
    
    for i in range(s):
        data_chunk = (ct.c_uint8 * (rawdevice.SECTOR_SIZE*chunk_size))()
        rawdevice.read_data(handle=handle, 
                            sector_addr=rawdevice.PACKS_INDEX_SECTOR_ADDRESS + p["start-sector"]+ (i*chunk_size),
                            sector_cnt=chunk_size,
                            sector_data=data_chunk)
        pack_binary += data_chunk
        work_done += (rawdevice.SECTOR_SIZE*chunk_size)
        work_done_percent = (work_done*100)//total_work

        cb_progress(work_done_percent/100)
        
    if r != 0:
        data_chunk = (ct.c_uint8 * (rawdevice.SECTOR_SIZE*r))()
        rawdevice.read_data(handle=handle, 
                            sector_addr=rawdevice.PACKS_INDEX_SECTOR_ADDRESS + p["start-sector"]+ (s*chunk_size),
                            sector_cnt=r,
                            sector_data=data_chunk)
        pack_binary += data_chunk
        work_done += (rawdevice.SECTOR_SIZE*r)
        work_done_percent = (work_done*100)//total_work
        
        cb_progress(work_done_percent/100)

    rawdevice.close(handle=handle)
    return pack_binary
    
def upload_pack(pack_binary, cb_progress=None):
    """upload pack to device"""
    handle = rawdevice.open()
    
    packs = rawdevice.get_packs_index(handle=handle)
    latest_pack = packs[-1:][0]
    
    new_pack_addr = latest_pack["start-sector"] + latest_pack["size"]
    
    sector_cnt = len(pack_binary) // 512
    if len(pack_binary) % 512 != 0:
        sector_cnt += 1
        
    chunk_size = 100
    s = sector_cnt // chunk_size
    r = sector_cnt % chunk_size
    
    total_work = len(pack_binary)
    work_done = 0
    
    for i in range(s):
        start_index = i*(chunk_size*rawdevice.SECTOR_SIZE)
        stop_index = i*(chunk_size*rawdevice.SECTOR_SIZE)+(chunk_size*rawdevice.SECTOR_SIZE)
        data_ba = bytearray( pack_binary[start_index:stop_index] )
        data_ctype = (ct.c_uint8 * len(data_ba)).from_buffer(data_ba)

        rawdevice.write_data(handle=handle, 
                             sector_addr=rawdevice.PACKS_INDEX_SECTOR_ADDRESS + new_pack_addr + (i*chunk_size),
                             sector_cnt=chunk_size, 
                             sector_data=data_ctype)

        work_done += (rawdevice.SECTOR_SIZE*chunk_size)
        work_done_percent = (work_done*100)//total_work
        
        cb_progress(work_done_percent/100)
    
    if r != 0:
        data_ba = bytearray( pack_binary[s*(chunk_size*rawdevice.SECTOR_SIZE):] )
        data_ctype = (ct.c_uint8 * len(data_ba)).from_buffer(data_ba)
        
        rawdevice.write_data(handle=handle, 
                             sector_addr=rawdevice.PACKS_INDEX_SECTOR_ADDRESS + new_pack_addr + (s*chunk_size),
                             sector_cnt=r, 
                             sector_data=data_ctype)

        work_done += (rawdevice.SECTOR_SIZE*r)
        work_done_percent = (work_done*100)//total_work
        
        cb_progress(work_done_percent/100)
    
    new_pack = {}
    new_pack["start-sector"] = new_pack_addr
    new_pack["pack-size"] = 0
    new_pack["stats-offset"] = latest_pack["stats-offset"] + latest_pack["nb-elements"]
    new_pack["sampling-rate"] = 0
    new_pack["size"] = sector_cnt
    packs.append(new_pack)
    
    # rewrite packs index
    packs_index = b""
    packs_index += len(packs).to_bytes(2, byteorder="big", signed=True)
    for p in packs:
        packs_index += p["start-sector"].to_bytes(4, byteorder="big", signed=True)
        packs_index += p["size"].to_bytes(4, byteorder="big", signed=True)
        packs_index += p["stats-offset"].to_bytes(2, byteorder="big", signed=True)
        packs_index += p["sampling-rate"].to_bytes(2, byteorder="big", signed=True)
        
    # add padding
    packs_index = require_padding(block=packs_index)

    # write to device
    data_ba = bytearray(packs_index)
    data_ctype = (ct.c_uint8 * len(data_ba)).from_buffer(data_ba)
    
    rawdevice.write_data(handle=handle, 
                         sector_addr=rawdevice.PACKS_INDEX_SECTOR_ADDRESS,
                         sector_cnt=1, 
                         sector_data=data_ctype)
                           
    rawdevice.close(handle=handle)
    
def delete_pack(pack_uuid):
    """delete pack"""
    handle = rawdevice.open()
    
    # read packs index from device
    packs = rawdevice.get_packs_index(handle=handle)
    
    pack_exists = False
    for i in range(len(packs)):
        if packs[i]["uuid"] == pack_uuid:
            pack_exists = True
            break
    
    if not pack_exists:
        raise Exception("Pack=%s does not exist on device" % pack_uuid)
    else:   
        packs.pop(i)
        
    # rewrite packs index
    packs_index = b""
    packs_index += len(packs).to_bytes(2, byteorder="big", signed=True)
    for p in packs:
        packs_index += p["start-sector"].to_bytes(4, byteorder="big", signed=True)
        packs_index += p["size"].to_bytes(4, byteorder="big", signed=True)
        packs_index += p["stats-offset"].to_bytes(2, byteorder="big", signed=True)
        packs_index += p["sampling-rate"].to_bytes(2, byteorder="big", signed=True)
        
    # add padding
    packs_index = require_padding(block=packs_index)

    # write to device
    data_ba = bytearray(packs_index)
    data_ctype = (ct.c_uint8 * len(data_ba)).from_buffer(data_ba)
    
    rawdevice.write_data(handle=handle, 
                         sector_addr=rawdevice.PACKS_INDEX_SECTOR_ADDRESS,
                         sector_cnt=1, 
                         sector_data=data_ctype)
                         
    rawdevice.close(handle=handle)
    