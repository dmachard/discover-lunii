
import imghdr
import uuid
import logging 
import wave
import yaml
import os
import subprocess

SECTOR_SIZE = 512

FFMPEG_PATH_WINDOW = "./ffmpeg/bin/ffmpeg.exe"
FFMPEG_PATH_LINUX = "/usr/bin/ffmpeg"

# init end sector
END_SECTOR =  b'_\xce\xd6~\x0ePF\xb8\xaeU\xda\x8cE\xc8\x98\x8a\xa3\x87\xa51;wGv'
END_SECTOR += b'\xb0\x81S}\xd5\x96/4\xdd8\x88\x05\xcaND\xe1\xb1TY\xbe\xb3H\x9a\xd7_S'
END_SECTOR += b'\xaa\x17\xf66N8\xaa!I\xb2\xa7\xc1\xdc\x06s\x11h\x92e\xecI\x18\x827'
END_SECTOR += b'\x8b\xb4\xe9\xb8\x9b3\x01\x15\xcc5N\xdcNz\x92MJ\x03\x03\xd9M"\xec'
END_SECTOR += b'\xc0#\xceZ\xad@\x04\xae\xa1\x06}@\x1fc\xf2\xe6\xe2\xb1\xc68\xa2N'
END_SECTOR += b'\xc2\xa7;-\x95\x97|\xe9\xc6\xcazj\xdb\xcb\x96M-\x9e\x86\xb6r\n\xd5Z'
END_SECTOR += b'\xca\xc2{\x853\x91bE\x86\x9d\xe7E\xc1\xe7\xd1\xc9\xdc\xba\x9b\xd4E'
END_SECTOR += b'\xc2\x00E]\xa1>\xfd\x8d \x97\xf6\x01\xff\x8d\xdd\xb9\x976G\x8b\x90'
END_SECTOR += b'\x83\x0fk\x98\xaf\xb7?\x0b\x9d\xc1)\xdd\x17Ls\xac\xa7\xb7\xdd\xf7\x89'
END_SECTOR += b'\x878G\xd6Y\xc9\xc9\xe7G\xcd\x91\xfb\xc7\xf6\xf6\xb4t\xf9\xaed\xd9'
END_SECTOR += b'\xf5WrIz\x9a\xe4\x90@f\xb8K\xe6\x85\xacCf\xb2\xd4M\xa7\x89n"\x0e\x92'
END_SECTOR += b'\x8e$I\xa1\xee5\x80\xd8\x93C\x0f\x87-V\xbb\xc5B\xff\xb5\xed\x13\xfb}%'
END_SECTOR += b'\xdfB\x82\xa6\xfe~\x18\x08iB\xb3P\x14\x0fb!XH\x08\xadJ\xc6\xfc\xcc#<9'
END_SECTOR += b'\xf3\x92\xd4\x94u\x8cG\xc4\x9b\xb5\xeb\xa8\x15\x90\xdax\x0fm\x82Aj'
END_SECTOR += b'\xc8Ho\x8cHg\x8aw\xa2\xdf\xf9;\x0f\xf8al\x99L\xe3\xa5f\xf7z@\x1b\xce'
END_SECTOR += b'\xad\xce\xb9\xe7\x883\\G-\x8f6\x9a\x1e\xe3s\xc2:\xaaM;\x8f\x97\x8fM\x83'
END_SECTOR += b'\x9a\x80\xba\'mm\x1c7j\'Fb-\xafE|\xb8n\xc2\xb5\xef{e\x0bX\xad\xf6\x99*&H)'
END_SECTOR += b'\xbe\xf5\xf1\xc3\xe9\xaf?$\x04\xee\xa8vC\xd8A\x83\x98\x0e%\xfa\xf79\xe4'
END_SECTOR += b'\x1c\xed\n\xf7\xe0\x9f\x8bH\xe4\x91\xb0\x1b\xcf\xcc9\xed$\'C6S\xc4\xb7I@'
END_SECTOR += b'\x99b\x10\x0fK\xacm\xad\xc2D\x11\xcf\x84\x82K\xa8\xa0\xaf\x89\xf5\xc3'
END_SECTOR += b'\x10W\xff\xe4y\xfe\x80\x90\x18L\xc5\x97\r\x1dp*\x19ygbE\xbfS,|L\xe5'
END_SECTOR += b'\x8bD\xc3\x1a\xc7\x83^\x1d'

# | --------------------------------------------------
# | pack (nb elements, is factory, version)
# | --------------------------------------------------
# | xx element(s) (uuid, image offset, image size, 
# |                audio offset, audio size, 
# |                next offset, nb next, next index,
# |                home offset, nb home, home index,
# |                ctrl wheel, ctrl ok, ctrl_home, 
# |                ctrl_pause, ctrl_autonext)
# | --------------------------------------------------
# | xx transition(s) (element id, ... )
# | --------------------------------------------------
# | data ... images                                         
# | --------------------------------------------------
# | data ... audio                                          
# | --------------------------------------------------
# | end
# | --------------------------------------------------

def require_padding(block):
    if len(block) == 512:
        return block
    nb_pad = SECTOR_SIZE - len(block)
    return block + b'\x00'*nb_pad
    
def encode_pack(pack_yaml, pack_name):
    """encode pack"""
    # try to detect ffmpeg
    if os.path.exists(FFMPEG_PATH_WINDOW):
        ffmpeg_exist = FFMPEG_PATH_WINDOW
    elif os.path.exists(FFMPEG_PATH_LINUX):
        ffmpeg_exist = FFMPEG_PATH_LINUX        
    else:
        ffmpeg_exist = None

    if ffmpeg_exist is None:
        logging.warning("warning: ffmpeg not detected on this system")
    
    # convert media mp3/m4a
    if ffmpeg_exist is not None:
        with os.scandir("./working/%s/audio/" % pack_name) as entries:
            for entry in entries:
                logging.info("> converting audio file=%s" % entry.name)
                cmd = ffmpeg_exist
                cmd += ' -i "./working/%s/audio/%s"' % (pack_name, entry.name)
                cmd += ' -filter:a "volume=5dB"'
                cmd += ' -acodec pcm_s16le'
                cmd += ' -ac 1 -ar 32000'
                cmd += ' -y "./working/%s/audio/%s.wav"' % (pack_name, os.path.splitext(entry.name)[0])
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        with os.scandir("./working/%s/image/" % pack_name) as entries:
            for entry in entries:
                logging.info("> converting image file=%s" % entry.name)
                cmd = ffmpeg_exist
                cmd += ' -i "./working/%s/image/%s"' % (pack_name, entry.name)
                cmd += ' -vf scale=320:240,format=gray'
                cmd += ' -pix_fmt bgr24'
                cmd += ' -y "./working/%s/image/%s.bmp"' % (pack_name, os.path.splitext(entry.name)[0])
                r = subprocess.run(cmd)
   
    # load the yaml description
    try:
        pack = yaml.load(pack_yaml, Loader=yaml.FullLoader)
    except Exception as e:
        raise Exception("encode pack failed, bad yaml file: %s" % e)
    
    # start to encode
    pack_binary = b""
    nb_elements = len(pack["elements"])
    
    for e,d in pack["elements"].items():
        
        if os.path.exists('./working/%s/image/%s.bmp' % (pack_name,e)):
            with open('./working/%s/image/%s.bmp' % (pack_name,e), "rb") as f:
                img_data = f.read()
        
            # add padding ?
            nb_padding = len(img_data)%SECTOR_SIZE
            if nb_padding != 0:
                img_data += b'\x00'*(SECTOR_SIZE-nb_padding)
            
            d["image-binary"] = img_data
            
        if os.path.exists('./working/%s/audio/%s.wav' % (pack_name,e)):
            with open('./working/%s/audio/%s.wav' % (pack_name,e), "rb") as f:
                aud_data = f.read()
                
            # add padding ?
            nb_padding = len(aud_data)%SECTOR_SIZE
            if nb_padding != 0:
                aud_data += b'\x00'*(SECTOR_SIZE-nb_padding)

            d["audio-binary"] = aud_data
            
    # init offset for transition 
    nb_transitions = len(pack["transitions"])
    next_offset = nb_elements
    for e,d in pack["transitions"].items():
        d["offset"] = next_offset
        next_offset += 1

    logging.debug("Pack from JSON:")
    logging.debug("\t - number of elements: %s" % nb_elements)
    logging.debug("\t - number of unique transition: %s" % nb_transitions)
    
    # prepare header sector
    pack_hdr = nb_elements.to_bytes(2, byteorder="big")
    pack_hdr += (0).to_bytes(1, byteorder="big") # factory
    pack_hdr += (1).to_bytes(2, byteorder="big") # version
    pack_hdr = require_padding(block=pack_hdr)

    pack_binary += pack_hdr

    # compute offset for data
    data_image_offset = nb_elements + nb_transitions
    data_audio_offset = data_image_offset
    for e,d in pack["elements"].items():
        if "image-binary" in d:
            data_audio_offset += (len(d["image-binary"])//512)
            
    # init elements sectors
    for e,d in pack["elements"].items():
        element_sector = b""
        
        # init uuid for this element
        element_sector += uuid.uuid4().bytes
    
        # add image if exist
        if "image-binary" in d:
            size_img = (len(d["image-binary"])//512)
            element_sector += data_image_offset.to_bytes(4, byteorder="big", signed=True)
            element_sector += size_img.to_bytes(4, byteorder="big", signed=True)
            data_image_offset += size_img
        else:
            element_sector += (-1).to_bytes(4, byteorder="big", signed=True)
            element_sector += (-1).to_bytes(4, byteorder="big", signed=True)
        
        # add audio if exist
        if "audio-binary" in d:
            size_aud = (len(d["audio-binary"])//512)
            element_sector += data_audio_offset.to_bytes(4, byteorder="big", signed=True)
            element_sector += size_aud.to_bytes(4, byteorder="big", signed=True)
            data_audio_offset += size_aud
        else:
            element_sector += (-1).to_bytes(4, byteorder="big", signed=True)
            element_sector += (-1).to_bytes(4, byteorder="big", signed=True)
        
        # add next transition
        if d["transition-index"] != None:
            t = pack["transitions"][d["transition-index"]]
            element_sector += t["offset"].to_bytes(2, byteorder="big", signed=True)
            element_sector += len(t["next"]).to_bytes(2, byteorder="big", signed=True)
            element_sector += (0).to_bytes(2, byteorder="big", signed=True)
        else:
            element_sector += (-1).to_bytes(2, byteorder="big", signed=True)
            element_sector += (-1).to_bytes(2, byteorder="big", signed=True)
            element_sector += (-1).to_bytes(2, byteorder="big", signed=True)
            
        # add home transition, not used for now
        element_sector += (-1).to_bytes(2, byteorder="big", signed=True)
        element_sector += (-1).to_bytes(2, byteorder="big", signed=True)
        element_sector += (-1).to_bytes(2, byteorder="big", signed=True)
    
        # controls
        if "wheel" in d["controls-enabled"]:
            element_sector += (1).to_bytes(2, byteorder="big", signed=True)
        else:
            element_sector += (0).to_bytes(2, byteorder="big", signed=True)
        
        if "ok" in d["controls-enabled"]:
            element_sector += (1).to_bytes(2, byteorder="big", signed=True)
        else:
            element_sector += (0).to_bytes(2, byteorder="big", signed=True)
            
        if "home" in d["controls-enabled"]:
            element_sector += (1).to_bytes(2, byteorder="big", signed=True)
        else:
            element_sector += (0).to_bytes(2, byteorder="big", signed=True)
            
        if "pause" in d["controls-enabled"]:
            element_sector += (1).to_bytes(2, byteorder="big", signed=True)
        else:
            element_sector += (0).to_bytes(2, byteorder="big", signed=True)
            
        if "autojump" in d["controls-enabled"]:
            element_sector += (1).to_bytes(2, byteorder="big", signed=True)
        else:
            element_sector += (0).to_bytes(2, byteorder="big", signed=True)
            
        element_sector = require_padding(block=element_sector)
        pack_binary += element_sector
        
    # add transitions
    for i,t in pack["transitions"].items():
        transition_sector = b""
        for n in t["next"]:
            transition_sector += n.to_bytes(2, byteorder="big", signed=True)
        transition_sector = require_padding(block=transition_sector)
        
        pack_binary += transition_sector 
        
    # add images
    for e,d in pack["elements"].items():
        if "image-binary" in d:
            pack_binary += d["image-binary"]

    # add audios        
    for e,d in pack["elements"].items():
        if "audio-binary" in d:
            pack_binary += d["audio-binary"]
            
    # add final sector
    pack_binary += END_SECTOR
    
    if len(pack_binary)%SECTOR_SIZE!= 0:
        raise Exception("bad block size")
        
    logging.debug("Pack file:")
    logging.debug("\t - size: %s" % len(pack_binary))
    logging.debug("\t - number of sector: %s" % (len(pack_binary)//512))

    # write the pack
    with open("./packs/%s" % pack_name, "wb") as f:
        f.write(pack_binary)
    
def decode_pack(pack_binary, pack_name):
    """decode pack"""
    pack = {"elements": {}, "transitions": {}}
    transitions = []
    
    # chuncking by SECTOR_SIZE   
    sectors = [pack_binary[i:i + SECTOR_SIZE] for i in range(0, len(pack_binary), SECTOR_SIZE)] 
    logging.debug("File (%s):" % pack_name) 
    logging.debug("\t - Size: %s" % len(pack_binary))
    logging.debug("\t - Number of sectors: %s" % len(sectors))

    # read first sector
    sector0 = sectors[0]
    nb_elements = int.from_bytes(sector0[0:2], byteorder="big")
    is_factory = sector0[2]
    version = int.from_bytes(sector0[3:5], byteorder="big")
    logging.debug("Header (sector 0)")
    logging.debug("\t - Number of elements: %s" % nb_elements)
    logging.debug("\t - Factory: %s" % is_factory)
    logging.debug("\t - Version: %s" % version)

    # init offsets
    first_image_offset = 0
    last_image_offset = 0

    first_audio_offset = 0
    last_audio_offset = 0

    start_element_offset = 1
    end_element_offset = nb_elements

    first_transition_offset = 0
    end_transition_offset = 0
    
    for e in range(nb_elements):
        pack["elements"][e] = {}
        
        el = {}
        
        cur_sector = sectors[e+1]
        
        # get uuid element
        msb = int.from_bytes(cur_sector[0:8], byteorder='big')
        lsb = int.from_bytes(cur_sector[8:16], byteorder='big')
        el_uuid = uuid.UUID(int=(msb << 64) | lsb)
        logging.debug("element uuid: %s" % el_uuid)
        
        # image ?
        img_offset = int.from_bytes(cur_sector[16:20], byteorder='big', signed=True) 
        img_size = int.from_bytes(cur_sector[20:24], byteorder='big', signed=True)
        if img_offset != -1:
            if first_image_offset == 0:
                first_image_offset = img_offset
            logging.debug("\t- image offset: %s" % img_offset)
            logging.debug("\t- image size: %s" % img_size)
            
            # save image to file
            with open("./working/%s/image/%s.bmp" % (pack_name,e), "wb") as f:
                f.write(b"".join(sectors[ img_offset+1: img_offset+1+img_size]))
        
            # checking if the image is valid, bmp expected
            img_type = imghdr.what("./working/%s/image/%s.bmp" % (pack_name,e))
            if img_type != "bmp":
                raise Exception("bad image extracted: %s" % img_type)

            # save end offset
            if img_offset + img_size > last_image_offset:
                last_image_offset = img_offset + img_size
                
        aud_offset = int.from_bytes(cur_sector[24:28], byteorder='big', signed=True)
        aud_size = int.from_bytes(cur_sector[28:32], byteorder='big', signed=True)  
        if aud_offset != -1:
            if first_audio_offset == 0:
                first_audio_offset = aud_offset
            logging.debug("\t- audio offset: %s" % aud_offset)
            logging.debug("\t- audio size: %s" % aud_size)
            
            with open("./working/%s/audio/%s.wav" % (pack_name,e), "wb") as f:
                f.write( b"".join(sectors[ aud_offset+1: aud_offset+1+aud_size]) )
      
            try:
                fd_wave = wave.open("./working/%s/audio/%s.wav" % (pack_name,e))
                fd_wave.close()
            except Exception as err:
                raise Exception("bad audio extracted: %s" % err)

            if aud_offset + aud_size > last_audio_offset:
                last_audio_offset = aud_offset + aud_size   
                
        nextel_offset = int.from_bytes(cur_sector[32:34], byteorder='big', signed=True)
        nextel_nb = int.from_bytes(cur_sector[34:36], byteorder='big', signed=True)
        nextel_index = int.from_bytes(cur_sector[36:38], byteorder='big', signed=True)
        
        logging.debug("\t- Next Transition(s):")
        logging.debug("\t\t- transition offset: %s" % nextel_offset)
        logging.debug("\t\t- number of transition: %s" % nextel_nb)
        logging.debug("\t\t- transition index: %s" % nextel_index)
        
        if nextel_offset != -1:
            if first_transition_offset == 0:
                first_transition_offset = nextel_offset
                
            if nextel_offset > end_transition_offset:
                end_transition_offset = nextel_offset

            tr_sector = b"".join(sectors[nextel_offset+1: nextel_offset+1+1])

            elids = []
            for n in range(nextel_nb):
                elid = int.from_bytes(tr_sector[(n*2):(n*2)+2], byteorder='big', signed=True)
                elids.append( elid)

            if elids not in transitions:
                transitions.append(elids)
                pack["transitions"][transitions.index(elids)] = {"next": elids }
            el["transition-index"] =  transitions.index(elids)
                
                
        hometran_offset = int.from_bytes(cur_sector[38:40], byteorder='big', signed=True)
        hometran_nb = int.from_bytes(cur_sector[40:42], byteorder='big', signed=True)
        hometran_index = int.from_bytes(cur_sector[42:44], byteorder='big', signed=True)
        
        logging.debug("\t- Back transition(s):")
        logging.debug("\t\t- transition offset: %s" % hometran_offset)
        logging.debug("\t\t- transition size: %s" % hometran_nb)
        logging.debug("\t\t- transition index: %s" % hometran_index)
        
        if hometran_offset != -1:
            tr_sector =  b"".join(sectors[hometran_offset+1: hometran_offset+1+hometran_nb])
            
            elids = []
            for n in range(hometran_nb):
                elid = int.from_bytes(tr_sector[(n*2):(n*2)+2], byteorder='big', signed=True)
                elids.append( elid)

            if elids not in transitions:
                transitions.append(elids)
                pack["transitions"][transitions.index(elids)] =  {"next": elids }
            el["transition-index"] =  transitions.index(elids)
            
        ctrl_wheel_enabled = int.from_bytes(cur_sector[44:46], byteorder='big', signed=True)
        ctrl_ok_enabled = int.from_bytes(cur_sector[46:48], byteorder='big', signed=True)
        ctrl_home_enabled = int.from_bytes(cur_sector[48:50], byteorder='big', signed=True)
        ctrl_pause_enabled = int.from_bytes(cur_sector[50:52], byteorder='big', signed=True)
        ctrl_autojump_enabled = int.from_bytes(cur_sector[52:54], byteorder='big', signed=True)
        
        el["controls-enabled"] = []
        if ctrl_wheel_enabled:
            el["controls-enabled"].append("wheel")
        if ctrl_ok_enabled:
            el["controls-enabled"].append("ok")
        if ctrl_home_enabled:
            el["controls-enabled"].append("home")
        if ctrl_pause_enabled:
            el["controls-enabled"].append("pause")
        if ctrl_autojump_enabled:
            el["controls-enabled"].append("autojump")

        pack["elements"][e] = el
        
    logging.debug("")
    logging.debug("Resume File format:")
    logging.debug("header: 0")

    logging.debug("element start offset: %s" % start_element_offset)
    logging.debug("element end offset: %s" % end_element_offset)

    logging.debug("transition start offset: %s" % (first_transition_offset+1) )
    logging.debug("transition end offset: %s" % (end_transition_offset+1) )


    logging.debug("image start offset: %s" % (first_image_offset+1) )
    logging.debug("\t> size images: %s" % ((last_image_offset-(first_image_offset+1))+1) )
    logging.debug("image end offset: %s" % (last_image_offset) )
      
    logging.debug("audio start offset: %s" % (first_audio_offset+1) )
    logging.debug("\t> size audio: %s" % ((last_audio_offset-(first_audio_offset+1))+1) )
    logging.debug("audio end offset: %s" % (last_audio_offset))
         
    logging.debug("end offset: %s" % (last_audio_offset+1))


    end_sector = b"".join(sectors[last_audio_offset+1: ])
    if end_sector != END_SECTOR:
        print(end_sector)
        raise Exception("Bad pack file - end sector missing ?")
    
    if (last_audio_offset+2) != len(sectors):
        raise Exception("bad file ? %s - %s" % ( (last_audio_offset+2), len(sectors) ) )
        
    # save pack as yaml
    with open("./working/%s/pack.yaml" % pack_name, "w") as f:
        f.write( yaml.dump(pack) )