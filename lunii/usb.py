import libusb
import ctypes as ct

_DEBUG = True

VENDOR_ID = 0x0c45
PRODUCT_ID_V1 = 0x6820 # Firmware Version 1
PRODUCT_ID = 0x6840 # Firmware Version 2
IN_ENDPOINT = 0x81 # -127 little endian
OUT_ENDPOINT = 0x2
INTERFACE = 0

def init_libusb():
    """init libusb"""
    if _DEBUG: print("initializing libusb...")
    r = libusb.init(None)
    if r != 0:
        err = libusb.error_name(r)
        raise Exception("unable to initialize libusb code=%s" % err)

def close_device(device_handle):
    """close usb device"""
    if _DEBUG: print("release interface")
    r = libusb.release_interface(device_handle, INTERFACE)
    libusb.close(device_handle)
    if r != 0:
        err = libusb.error_name(r)
        raise Exception("closing handler failed code=%s" % err)
        
def open_device():
    """open usb device"""
    if _DEBUG: print("opening device {:04X}:{:04X}...".format(VENDOR_ID, PRODUCT_ID))

    dev_handle = libusb.open_device_with_vid_pid(None, VENDOR_ID, PRODUCT_ID)
    if not dev_handle:
        raise Exception("error to find Lunii USB device")

    if _DEBUG: print("detach")
    d = libusb.detach_kernel_driver(dev_handle, INTERFACE)

    if _DEBUG: print("claim interface")
    r = libusb.claim_interface(dev_handle, INTERFACE)
    if r != 0:
        err = libusb.error_name(r)
        raise Exception("cannot claim interface code=%s" % err)
        
        
    dev = libusb.get_device(dev_handle)
    bus_number = libusb.get_bus_number(dev)
    dev_address = libusb.get_device_address(dev)
    port_number = libusb.get_port_number(dev)

    if _DEBUG:
        print("Bus number=%s" % bus_number)
        print("Port number=%s" % port_number)
        print("Device address=%s" % dev_address)
        
    return (dev_handle, dev_address, bus_number, port_number)
    
def bulk_transfer(device_handle, device_endpoint, data_buffer, timeout=5000):
    """bulk transfer"""
    if _DEBUG: print("bulk transfer endpoint=%s" % device_endpoint)
    size = ct.c_int()
    code = libusb.bulk_transfer(dev_handle=device_handle,
                                endpoint=device_endpoint, 
                                data=ct.cast(ct.pointer(data_buffer), ct.POINTER(ct.c_ubyte)), 
                                length=len(data_buffer),
                                actual_length=ct.byref(size),
                                timeout=timeout)
    if code != 0:
        r = libusb.clear_halt(device_handle, device_endpoint)
        if r != 0:
            err = libusb.error_name(r)
            raise Exception("bulk transfer error on clear halt with code=%s" % err)
        err = libusb.error_name(code)
        raise Exception("bulk transfer error with code=%s" % err)
  