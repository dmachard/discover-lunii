import argparse
import pathlib
import logging
import shutil
import os

import lunii

parser = argparse.ArgumentParser()
parser.add_argument("--content", 
                    help="display lunii device content",
                    action="store_true")
parser.add_argument("--download", 
                    help="download pack from device",
                    type=str)
parser.add_argument("--upload", 
                    help="upload pack to device",
                    type=str)
parser.add_argument("--decode", 
                    help="decode binary pack",
                    type=str) 
parser.add_argument("--encode", 
                    help="encode pack to binary format",
                    type=str) 
parser.add_argument("--delete", 
                    help="delete pack on the device",
                    type=str)
parser.add_argument("--verbose", help="increase output verbosity",
                    action="store_true")
                    
args = parser.parse_args()

if args.verbose:
    logging_level = logging.DEBUG
else:
    logging_level = logging.INFO
logging.basicConfig(format='%(message)s', level=logging_level)


def update_progress(p):
    print("\r[{0:50s}] {1:.1f}%".format('#' * int(p * 50), p*100), end="", flush=True)
    
if __name__ == "__main__":
    # do the job according to the argument
    if args.content:
        try:
            (fw,sd,packs) = lunii.load()
        except Exception as e:
            logging.error("%s" % e)
        
        else:
            logging.info("Firwmare:")
            logging.info("\tVersion: %d.%d" % fw)
            
            logging.info("SD Card (bytes):")
            logging.info("\tTotal: %s" % sd[0])
            logging.info("\tUsed: %s" % sd[1])
            logging.info("\tFree: %s" % sd[2])
            
            logging.info("Packs:")
            logging.info("\tTotal: %s" % len(packs))
            logging.info("\tStories:")
            for p in packs:
                logging.info("\t\t%s" % p["uuid"] )
            
    elif args.download:
        # create packs folder if missing
        pathlib.Path('./packs').mkdir(exist_ok=True) 

        try:
            pack_binary = lunii.download_pack(pack_uuid=args.download,
                                              cb_progress=update_progress)
  
            with open("./packs/%s.pack" % args.download, "wb") as f:
                f.write(pack_binary)
        except Exception as e:
            logging.error("download failed: %s" % e)
        else:
            logging.info("download terminated")
        
    elif args.encode:
        if not os.path.exists('./working/%s' % args.encode):
            logging.error("encode failed, pack=%s not found!" % args.encode)
        else:
            try:
                with open('./working/%s/pack.yaml' % args.encode, "r") as f:
                    pack_yaml = f.read()
            except FileNotFoundError:
                logging.error("encode failed, pack.yaml not found!")
            else:
                lunii.encode_pack(pack_yaml=pack_yaml,
                                  pack_name=args.encode)
                logging.info("pack successfully encoded")
                
    elif args.decode:
        try:
            with open("./packs/%s" % args.decode, "rb") as f:
                pack_binary = f.read()
        except FileNotFoundError:
            logging.error("decode failed, pack=%s not found!" % args.decode)
        else:
            # create folders in working directory
            pathlib.Path('./working').mkdir(exist_ok=True) 
            
            if os.path.exists('./working/%s' % args.decode):
                shutil.rmtree('./working/%s' % args.decode)
                
            pathlib.Path('./working/%s' % args.decode).mkdir()
            pathlib.Path('./working/%s/image/' % args.decode).mkdir()
            pathlib.Path('./working/%s/audio/' % args.decode).mkdir()
            
            # then decode the pack
            lunii.decode_pack(pack_binary=pack_binary, pack_name=args.decode)
        
            logging.info("pack successfully decoded")
            
    elif args.upload:
        try:
            with open("./packs/%s" % args.upload, "rb") as f:
                pack_binary = f.read()
        except FileNotFoundError:
            logging.error("upload failed, pack=%s not found!" % args.upload)
        else:
            try:
                lunii.upload_pack(pack_binary=pack_binary,
                                  cb_progress=update_progress)
            except Exception as e:
                logging.error("upload failed: %s" % e)       
            else:
                logging.info("upload terminated")
        
    elif args.delete:
        try:
            pack_binary = lunii.delete_pack(pack_uuid=args.delete)
        except Exception as e:
            logging.error("delete failed: %s" % e)
        else:
            logging.info("pack successfully deleted")    
        
    else:
        parser.print_help()