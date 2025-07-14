# 2025-06-17 Downloaded from: https://github.com/digitalurban/Presto_MQTT_Display/blob/main/mqtt_presto.py
# by Andy Hudson-Smith going by @digitalurban
# Changes by Paulus Schulinck going by @PaulskPt
#
import ujson
#import ubinascii
import time
from presto import Presto
from umqtt.simple import MQTTClient
import os
import sys # See: https://github.com/dhylands/upy-examples/blob/master/print_exc.py
import time

# Setup for the Presto display
presto = presto = Presto(ambient_light=False)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

BRIGHTNESS = 0.0 # The brightness of the LCD backlight (from 0.0 to 1.0)
display.set_backlight(BRIGHTNESS)

# Couple of colours for use later
BLACK = display.create_pen(0, 0, 0)
ORANGE = display.create_pen(255, 180, 0)
BACKGROUND = display.create_pen(255, 250, 240)

# We do a clear and update here to stop the screen showing whatever is in the buffer.
display.set_pen(BLACK)
display.clear()
presto.update()

my_debug = False
delete_logs = False

temp = None
pres = None
alti = None
humi = None
publisher_datetime = None
publisher_time = None
publisher_msgID = None


# Get the external definitions
with open('secrets.json') as fp:
    secrets = ujson.loads(fp.read())
    
# Test the existance of a logfile
log_fn = None # Note: log_fn is set in the function create_logfile()
log_path = None # "/sd/" + log_fn
log_size_max = 50 * 1024  # 51200 bytes # 50 kB max log file size
log_obj = None
log_exist = False
new_log_fn = None
new_log_path = None
new_log_obj = None
new_log_exist = False

def get_prefix():
    return "/sd/"

# Note: err_log_fn is used in the function create_err_log_file()
err_log_fn = "mqtt_err_log.txt"
err_log_path = get_prefix() + err_log_fn
err_log_obj = None
# Note: ref_fn is used in the function create_ref_file()
ref_fn = "mqtt_latest_log_fn.txt"
ref_path = get_prefix() + ref_fn
ref_obj = None

ref_file_checked = False
log_file_checked = False

def do_line():
    ln = "----------" * 5
    print(ln)

def create_err_log_file():
    global err_log_fn, err_log_path, err_log_obj
    TAG = "create_err_log_file(): "
    try:
        if not ck_log(err_log_fn):
            # If the error log file does not exist, create it
            # err_log_fn = "err_log.txt"
            if err_log_obj:
                err_log_obj.close()
            with open(err_log_path, 'w') as ref_obj:
                err_log_obj.write('--- Error log file created on: {} ---\n'.format(get_iso_timestamp()))
                print(TAG+f"Error log file: \"{err_log_fn}\" created")
            if err_log_obj:
                err_log_obj.close() 
    except OSError as exc:
        print(TAG+f"OSError: {exc}")

def create_ref_file():
    global ref_path, ref_obj, ref_fn
    TAG = "create_ref_file(): "
    try:
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'w') as ref_obj:
            ref_obj.write('--- Reference file created on: {} ---\n'.format(get_iso_timestamp()))
            print(TAG+f"reference file: \"{ref_fn}\" created")
    except OSError as exc:
        print(TAG+f"OSError: {exc}")
        
def ref_file_exists():
    global ref_path, ref_obj, ref_fn
    ret = False
    TAG = "ref_file_exists(): "
    try:
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'r') as ref_obj:
            ret = True
        if ref_obj:
            ref_obj.close()
    except OSError as exc:
        print(TAG+f"Reference file not found or unable to open. Error: {exc}")
    return ret

def clear_ref_file():
    global ref_path, ref_obj, ref_fn
    TAG = "clear_ref_file(): "
    txt1 = "reference file: "
    try:
        ref_exist = ref_file_exists() # Check if the reference file exists
        if ref_exist:
            if not my_debug:
                print(TAG+txt1+f"\"{ref_fn}\" exists, making it empty")
            # If the reference file exists, make it empty
            # Note: This will overwrite the existing file, so be careful!
            if ref_obj:
                ref_obj.close()
            with open(ref_path, 'w') as ref_obj:
                pass  # Create an empty reference file
            ref_obj.close()
            ref_size = os.stat(ref_path)[6]  # File size in bytes
            if ref_size == 0:
                print(TAG+txt1+f"\"{ref_fn}\" is empty")
            else:
                print(TAG+txt1+f"\"{ref_fn}\" is not empty, size: {ref_size} bytes")
        else:
            if not my_debug:
                print(TAG+txt1+f"\"{ref_fn}\" does not exist, creating it")
            create_ref_file()    
    except OSError as exc:
        print(TAG+f"OSError: {exc}")

def get_active_log_filename():
    global ref_path, ref_obj, ref_fn, ref_file_checked, log_fn, log_path, log_exist
    TAG = "get_active_log_filename(): "
    txt1 = "Active log "
    txt2 = "reference file"
    txt3 = "in the directory:"
    ret = None
    active_log_fn = None
    active_log_path = None
    active_log_exist = False
    active_log_size = 0
    try:
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'r') as ref_obj:
            active_log_fn = ref_obj.readline().strip()  # Read the first line and remove trailing newline
        if ref_obj:
            ref_obj.close()
        ref_file_checked = True
        
        if active_log_fn:
            print(TAG + txt1 + f"filename read from " + txt2 + f": \"{active_log_fn}\"")
            # Check if the log file exists in the specified directory
            if active_log_fn in os.listdir(get_prefix()):
                active_log_path = get_prefix() + active_log_fn
                print(TAG + txt1 + f"file: \"{active_log_fn}\" exists in " + txt3 + f"\"{get_prefix()}\"")
                active_log_size = os.stat(active_log_path)[6]  # File size in bytes
                print(TAG+f"Active log file size: {active_log_size} bytes")
                # Set the log path and log exist flag
                active_log_path = get_prefix() + active_log_fn
                active_log_exist = True
                #ret = active_log_fn  # Return the active log filename
            else:
                print(TAG + txt1 + f"file: \"{active_log_fn}\" does not exist " + txt3 + f"\"{get_prefix()}\"")
                # If the log file does not exist, we can create a new one
                active_log_exist = False
                active_log_path = None
                active_log_fn = None
                clear_ref_file()

            ret = active_log_fn
            log_fn = active_log_fn
            log_path = active_log_path 
            log_exist = active_log_exist
        else:
            print(TAG + txt1 + "filename not found in the " + txt2)
    except OSError as exc:
        print(TAG+f"Error reading the " + txt2 + ": {exc}")
    
    return ret

def pr_ref():
    global ref_path, ref_obj
    ret = 0
    TAG = "pr_ref(): "
    try:
        if ref_obj:
            ref_obj.close()
        
        if ref_path:
            print(TAG+f"Contents of ref file: \"{ref_path}\":")
            f_cnt = 0
            with open(ref_path, 'r') as ref_obj:
                for line in ref_obj:
                    f_cnt += 1
                    #f_cnt_str = "0" + str(f_cnt) if f_cnt < 10 else str(f_cnt)
                    #print(f"   {f_cnt_str}) {line.strip()}") 
                    print("{:s} {:02d}) {:s}".format(TAG, f_cnt, line.strip())) # Remove trailing newline for cleaner output
                do_line()
            ret = f_cnt  # Return the number of lines printed
    except OSError as exc:
        print(TAG+f"Reference file not found or unable to open. Error: {exc}")
    return ret

# Function to get current datetime as an ISO string
def get_iso_timestamp():
    t = time.localtime()
    return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(*t[:6])

def new_logname():
    fn = "mqtt_log_{}.txt".format(get_iso_timestamp())
    # Replace ":" with "" for compatibility with MS Windows file systems
    return fn.replace(":", "")

def ck_log(fn):
    if isinstance(fn, str) and len(fn) > 0:
        if fn in os.listdir(get_prefix()):
            return True
    return False

# Create a new log file and add its filename to the ref file
def create_logfile():
    global log_fn, log_path, log_obj, log_exist, ref_path, ref_obj, new_log_fn, new_log_path, new_log_obj
    TAG = "create_logfile(): "
    
    new_log_fn = new_logname()
    if not my_debug:
        print(f"new_logname() = {new_log_fn}")
    
    new_log_path = get_prefix() + new_log_fn
    try:
        if log_obj:
            log_obj.close()
        with open(new_log_path, 'w') as log_obj:
            log_obj.write('---Log created on: {}---\n'.format(get_iso_timestamp()))
        print(TAG+f"created new log file: \"{new_log_fn}\"")
        # Check existance of the new log file
        if ck_log(new_log_fn):
            print(TAG+f"check: new log file: \"{new_log_fn}\" exists")
        else:
            print(TAG+f"check: new log file: \"{new_log_fn}\" not found!")
        # Make empty the ref file
        if ref_obj:
            ref_obj.close()
        with open(ref_path, 'w') as ref_obj: # Make empty the ref file
            pass
        if ref_obj:
            ref_obj.close()
        # Add the filename of the new logfile to the ref file
        with open(ref_path, "w") as ref_obj:
            ref_obj.write(new_log_fn)
            print(TAG+f"added to ref file: \"{ref_fn}\" the new active log filename \"{new_log_fn}\"")
            pr_ref()  # Print the contents of the ref file
    except OSError as exc:
        print(TAG+f"OSError: {exc}")
    """
    if new_log_fn is not None:
        log_fn = new_log_fn # Update the global log_fn variable
    if new_log_path is not None:
        log_path = new_log_path # Update the global log_path variable
    """

# Function to close a log file that is too long
# Then create a new log file
# Add the new log filename in the ref file
def rotate_log_if_needed(show: bool = False):
    global log_path, log_fn, log_size_max, log_obj, log_exist, ref_path, ref_fn, ref_obj, new_log_fn, new_log_path, new_log_obj
    TAG = "rotate_log_if_needed(): "
    if new_log_fn is not None: # new_log_fn could have be created in the part MAIN
        if ck_log(new_log_fn):
            log_fn = new_log_fn # Update the global log_fn variable
            current_log = new_log_fn # copy the current log filename
            current_log_path = new_log_path # copy the current log path
            log_exist = True
    elif log_exist and log_fn is not None:
        current_log = log_fn # copy the current log filename
        current_log_path = get_prefix() + current_log # copy the current log path
    if current_log:
        if my_debug:
            print(TAG+f"current log filename = \"{current_log}\"")
        if ck_log(current_log):
            log_size = os.stat(current_log_path)[6]  # File size in bytes
            if my_debug or show:
                print(TAG+f"size of \"{current_log}\" is: {log_size} bytes. Max size is: {log_size_max} bytes.")
            if log_size > log_size_max:
                if my_debug:
                    print(TAG+f"Log file: \"{current_log}\" is too long, creating a new log file")
                create_logfile()
                if my_debug:
                    print(TAG+f"Current log file: \"{current_log}\" is closed")
                    print(TAG+f"Log rotated to new log file: \"{log_path}\"")  # log_fn, log_path changed in create_logfile()
            else:
                print(TAG+"rotate log file not needed yet")
        else:
            print(TAG+f"log_file: \"{log_fn}\" not found in listdir(\"{get_prefix()}\")")
            print(TAG+"creating a new log file")
            create_logfile() # log_fn, log_path changed in create_logfile()
    else:
        # log_fn is None
        print(TAG+"creating a new log file")
        create_logfile() # log_fn, log_path changed in create_logfile()
   
    if log_fn is None:
        print(TAG+"Log rotation failed:")

#------------------ MAIN START HERE ------------------
# The main function is not used in this script
# but the code is structured to allow for easy integration into a larger system.
TAG = "main(): "
my_list = None 
try:
    # Note: os.listdir('/sd') and os.listdir('/sd/') have the same result! 
    # Check the existance of a reference file
    # in which we save the file name of the latest log file created
    if ref_file_exists():
        # Reference file exists;   
        # File exists; open for appending
        active_log_fn = None
        active_log_path = None
        active_log_exist = False
        ref_exist = True
        ref_size = os.stat(ref_path)[6]  # File size in bytes
        if not my_debug:
            print(TAG+f"ref file: \"{ref_fn}\" exists. Size: {ref_size} bytes")
        if ref_size > 0:
            nr_log_files = pr_ref()
            print(TAG+f"Number of log files listed in reference file: {nr_log_files}")
            if nr_log_files > 0:
                # read the log filename from the reference file
                active_log_fn = get_active_log_filename()  # Get the active log filename from the reference file
                # print(TAG+f"Active log filename extracted from reference file: \"{log_fn}\"")
                if active_log_fn is None:
                    # No log filename found in the reference file
                    print(TAG+f"No active log filename found in the reference file: \"{ref_fn}\"")
                else:
                    # Check if the active log file exists
                    if ck_log(active_log_fn):
                        active_log_path = get_prefix() + log_fn
                        active_log_exist = True
               
                # If the active log file exists, we can use it
                # Otherwise, we create a new log file
                if active_log_exist:
                    print(TAG+f"Active log file: \"{active_log_fn}\" does exist in the directory: \"{get_prefix()}\"")
                    active_log_path = get_prefix() + active_log_fn
                    active_log_size = os.stat(active_log_path)[6]  # File size in bytes 
                    log_fn = active_log_fn  # Update the global log_fn variable
                    log_path = active_log_path  # Update the global log_path variable
                else:
                    print(TAG+f"Active log file: \"{active_log_fn}\" does not exist in the directory: \"{get_prefix()}\"")
                    print(TAG+f"creating a new log file")
                
                    active_log_exist = False
                    active_log_path = None
                    create_logfile()
        else:
            # There is no last log filename in the ref file.
            # Create a new log file and add to the ref file
            if log_fn and ck_log(log_fn):
                pass  # The log file exists, so we do not need to create a new one
            else:
                log_fn = new_logname() # "mqtt_log_{}.txt".format(get_iso_timestamp())
                log_path = get_prefix() + log_fn
            try:
                if ref_obj:
                    ref_obj.close()
                with open(ref_path, 'w') as ref_obj:
                    ref_obj.write(log_fn) # Add the log filename to the ref file
            except OSError as exc:
                print(TAG+f"OSError: {exc}")
    else:
        # ref_fn does not exist; create and write header
        # First:  create a new log filename
        # Second: add the log filename to the ref file
        log_fn = new_logname() # "mqtt_log_{}.txt".format(get_iso_timestamp())
        log_path = get_prefix() + log_fn
        try:
            if ref_obj:
                ref_obj.close()
            with open(ref_path, 'w') as ref_obj:
                ref_obj.write('--- Reference file created on: {} ---\n'.format(get_iso_timestamp()))
                ref_obj.write(log_fn) # And add the log filename to the ref file
            ref_exist = True
            if not my_debug:
                print(TAG+f"reference file: \"{ref_path}\" created")
                print(TAG+f"current log filename: \"{log_fn}\" added to ref file")
        except OSError as exc:
            print(TAG+f"OSError: {exc}")
        # rotate_log_if_needed() # create a new log file and add it to th ref file
except OSError as exc:
    print(TAG+f"OSError occurred: {exc}")

if my_list:
    my_list = None # Clear memory

# MQTT setup
BROKER = secrets['mqtt']['broker']
PORT = int(secrets['mqtt']['port'])
TOPIC = bytes(secrets['mqtt']['topic'], 'utf-8')
CLIENT_ID = bytes(secrets['mqtt']['client_id'], 'utf-8')
PUBLISHER_ID = secrets['mqtt']['publisher_id']

if my_debug:
    print(f"BROKER = {BROKER}")
    print(f"PORT = {PORT}, type(PORT) = {type(PORT)}")
    print(f"TOPIC = {TOPIC}")
    print(f"CLIENT_ID = {CLIENT_ID}")
    print(f"PUBLISHER_ID = {PUBLISHER_ID}")

client = None
# Initialize the default message
message_string = "Waiting for Messages..."
last_update_time = time.time()
MESSAGE_DISPLAY_DURATION = 20  # Duration to display each message in seconds

# WiFi setup

# Eventually (if needed)
#ssid = secrets['wifi']['ssid']
#password = secrets['wifi']['password']

print(TAG+"Connecting to WiFi...")
wifi = presto.connect()  # Ensure this is configured for your network
print(TAG+"WiFi connected.")

msg_rcvd = False
msg_drawn = False

# List log files starting with "mqtt_log"
def list_logfiles():
    TAG = "list_logfiles(): "
    list_log_prefix = 'mqtt_log'
    list_log_path = ""

    try:
        files = os.listdir(get_prefix())
        log_files = [f for f in files if f.startswith(list_log_prefix) and f.endswith('.txt')]
        files = None  # Clear memory
        # do_line()
        cnt = 0      
        print(TAG+"MQTT log files:")
        for fname in log_files:
            #if fname.beginswith(list_log_prefix) and fname.endswith('.txt'):
            cnt += 1
            #print(TAG+f"fname = \"{fname}\"")
            #if ck_log(fname):
            list_log_path = get_prefix() + fname
            log_size = os.stat(list_log_path)[6]
            print("{:2d}) {}, size {} bytes".format(cnt, fname, log_size), end='\n')
        do_line()
        if cnt == 0:
            print(TAG+"No log files found starting with \"{}\"".format(list_log_prefix))
        else:
            print(TAG+"Total number of log files found: {}".format(cnt))
        do_line()
    except OSError as e:
        print(TAG+"Error accessing directory:", e)

# Add data to log file
def add_to_log(txt:str = ""):
    global log_exist, log_path, log_fn, log_obj, log_size_max
    TAG = "add_to_log(): "
    param_type = type(txt)
    if isinstance(txt, str):
        if len(txt) > 0:
            size = os.stat(log_path)[6]  # File size in bytes
            if size >= log_size_max:
                rotate_log_if_needed() # check if we need to create a new log file
            
            if log_obj:
                log_obj.close()
            if ck_log(log_fn):
                try:
                    with open(log_path, 'a') as log_obj:  # 'a' for append mode
                        log_obj.write('\n ' + txt)  # Add received msg to file /sd/mqtt_log.txt
                    if my_debug:
                        print(TAG+f"data: \"{txt}\" appended successfully to the log file.")
                except OSError as exc:
                    print(TAG+f"add_to_log(): error while trying to open or write to the log file: {exc}")
            else:
                print(TAG+f"log file: \"{log_path}\" does not exist. Unable to add: \"{txt}\"")
    else:
        print(TAG+f"parameter txt needs to be of type str, received a type: {param_type}")

def del_logfiles():
    global ref_fn, ref_path, ref_obj, log_fn
    TAG = "del_logfiles(): "
    
    log_dir = get_prefix()
    t = time.localtime()
    # year, month, day = t[0], t[1], t[2]
    # Or even more compactly:
    yy, mo, dd, *_ = time.localtime()

    print(TAG+f"log_dir = {log_dir}")
    log_pfx = "mqtt_log_" + str(yy) + "-" + "0" + str(mo) if mo < 10 else str(mo)  # + "-" + "0" + str(dd) if dd < 10 else str(dd)  # Change to desired year-month-day
    print(TAG+f"log_pfx = {log_pfx}")
    deleted_files = []

    try:
        files = os.listdir(log_dir)
        for fname in files:
            if fname.startswith(log_pfx) and fname.endswith('.txt'):
                if my_debug:
                    print(TAG+f"fname = \"{fname}\", log_fn = \"{log_fn}\"")
                if fname in log_fn:
                    print(TAG+f"We\'re not deleting the current logfile: \"{log_fn}\"")
                    continue
                full_path = '{}/{}'.format(log_dir, fname)
                try:
                    os.remove(full_path)
                    deleted_files.append(fname)
                except OSError as exc:
                    print(TAG+f"Failed to delete: {fname}, error: {exc}")

        if len(deleted_files) > 0:
            print(TAG+"Deleted files:")
            for f in deleted_files:
                print("  ✔", f)
            
            if ref_obj:
                ref_obj.close()
            with open(ref_path, 'w') as ref_obj:  # Make empty the ref file
                pass
            ref_size = os.stat(ref_path)[6]  # File size in bytes
            if not my_debug:
                print(TAG+f"check ref file: \"{ref_fn}\" after making empty. Size: {ref_size} bytes")
        else:
            print(TAG+f"no logfile(s) found starting with \"{log_pfx}\" and ending with \".txt\"")
    
    except OSError as exc:
        print(TAG+f"Could not list directory: {log_dir} for deletion. Error: {exc}")
        
# MQTT callback function
def mqtt_callback(topic, msg):
    global message_string, last_update_time, msg_rcvd
    TAG = "mqtt_callback(): "
    message_string = msg.decode('utf-8')  # Decode the MQTT message
    # print(f"message_string = {message_string}")
    last_update_time = time.time()  # Reset the update timer
    if my_debug:
        print("\n"+TAG, end="")
        print(f"Received message on topic {topic.decode()},\nmsg: {message_string}")

    if len(message_string) > 0:
        msg_rcvd = True
        
def split_msg():
    global message_string , msg_rcvd, temp, pres, alti, humi, publisher_datetime, publisher_time, publisher_msgID, log_obj, log_exist
    if not msg_rcvd:
        return
    
    add_to_log(message_string)

    json_string = ujson.dumps(message_string, separators=(',', ':'))
    split_string = json_string.split(',')
    
    if my_debug:
        print(f"json_string = {json_string}")
        print(f"split_msg(): split_string = {split_string}")
        
    for i in range(6):
        if i == 0:
            temp = split_string[0][2:]  # cut the "(
        if i == 1:
            pres = split_string[1]
        if i == 2:
            alti = split_string[2]
        if i == 3:
            humi = split_string[3]
        if i == 4:
            publisher_datetime = split_string[4]
        if i == 5:
            publisher_msgID = split_string[5][:-2] # cut the )"

    for i in range(6):
        if i == 0:
            tmp = temp
        elif i == 1:
            tmp = pres
        elif i == 2:
            tmp = alti
        elif i == 3:
            tmp = humi
        elif i == 4:
            tmp = publisher_datetime
        elif i == 5:
            tmp = publisher_msgID
        
        n = tmp.find(":")
        if n >= 0:
            if i == 5:
                tmp = tmp[n+1:]  # slice-off the "msgID:"
            else:
                tmp = tmp[:n] + " = " + tmp[n+1:]        
            
        if i == 0:
            temp = tmp + " °C"
        elif i == 1:
            pres = tmp + " hPa"
        elif i == 2:
            alti = tmp + " m"
        elif i == 3:
            humi = tmp + " %rH"
        elif i == 4:
            publisher_datetime = tmp
        elif i == 5:
            publisher_msgID = tmp
            
        publisher_time = publisher_datetime[-8:]
        
            
    if my_debug:
        print(f"temp = {temp}")
        print(f"pres = {pres}")
        print(f"alti = {alti}")
        print(f"humi = {humi}")
        print(f"publisher_datetime = {publisher_datetime}")
        print(f"publisher_time = {publisher_time}")
        print(f"publisher_msgID = {publisher_msgID}")

def draw(mode:int = 1):
    global message_string, msg_drawn, temp, pres, alti, humi, PUBLISHER_ID, publisher_time, publisher_msgID
    display.set_font("bitmap8")
    display.set_layer(1)

    # Clear the screen with a black background
    display.set_pen(BLACK)  # Black background
    display.clear()

    # Display the message
    # See: https://doc-tft-espi.readthedocs.io/tft_espi/colors/
    display.set_pen(ORANGE)  # Orange text
    x = 10
    y = 25
    line_space = 30
    margin = 10
    
    hdg = "MQTT pub : "
    
    display.text(hdg+PUBLISHER_ID, x, y, WIDTH)
    
    if publisher_time:
        y += line_space
        display.text(publisher_time, x, y, WIDTH)
        display.text("msgID = "+ publisher_msgID, x+100, y, WIDTH)
    y += line_space * 2
    
    if mode == 0:
        # Word wrapping logic
        words = message_string.split()  # Split the message into words
        current_line = ""  # Start with an empty line
        
        for word in words:
            test_line = current_line + (word + " ")
            line_width = display.measure_text(test_line)

            if line_width > WIDTH - margin:
                display.text(current_line.strip(), x, y, WIDTH)
                y += line_space
                current_line = word + " "  # Start a new line with the current word
            else:
                current_line = test_line

        if current_line:
            display.text(current_line.strip(), x, y, WIDTH)
            
    elif mode == 1: # do the PaulskPt method
        
        if temp is None or pres is None or alti is None or humi is None:
            return

        for i in range(4):
            if i == 0:
                #temp += " °C"
                if my_debug:
                    print(f"temp = {temp}")
                display.text(temp, x, y, WIDTH)
            elif i == 1:
                #pres += " hPa"
                if my_debug:
                    print(f"pres = {pres}")
                display.text(pres, x, y, WIDTH)
            elif i == 2:
                #alti += " m"
                if my_debug:
                    print(f"alti = {alti}")
                display.text(alti, x, y, WIDTH)
            elif i == 3:
                #humi += " %rH"
                if my_debug:
                    print(f"humi = {humi}")        
                display.text(humi, x, y, WIDTH)
            y += line_space

    presto.update()
    temp = None
    pres = None
    alti = None
    humi = None
    msg_drawn = True
        

def pr_log():
    global log_path, log_obj, log_size_max
    TAG = "pr_log(): "
    try:
        if log_obj:
            log_obj.close()
        
        if log_path:
            log_size = os.stat(log_path)[6]  # File size in bytess
            if log_size > 0:
                print(f"Size of log file: {log_size}. Max log file size can be: {log_size_max} bytes.")
                print(f"Contents of log file: \"{log_path}\"")
                with open(log_path, 'r') as log_obj:
                    f_cnt = 0
                    for line in log_obj:
                        f_cnt += 1
                        print("{:s} {:02d}) {:s}".format(TAG, f_cnt, line.strip())) # Remove trailing newline for cleaner output
                    do_line()
            else:
                print(TAG+f"log file \"{log_path}\" is empty")
    except OSError as exc:
        print(TAG+f"No log file found or unable to open. Error: {exc}")

def cleanup():
    global ref_exist, ref_obj, ref_path, log_exist, log_obj, log_path
    if ref_obj: # and ref_path is not None and ref_exist:
        ref_obj.close()
    if log_obj: # and log_path is not None and log_exist:
        log_obj.close()

def setup():
    global client, CLIENT_ID, BROKER, PORT, TOPIC, msg_drawn
    # MQTT client setup
    TAG = "setup(): "
    if ck_log(err_log_fn):  # Check if the error log file exists
        print(TAG+f"Error log file: \"{err_log_fn}\" exists")
    else:
        print(TAG+f"Error log file: \"{err_log_fn}\" does not exist, creating it")
        create_err_log_file()
        
    print(TAG+f"Connecting to MQTT broker at {BROKER} on port {PORT}...")
    client = MQTTClient(CLIENT_ID, BROKER, port=PORT)
    client.set_callback(mqtt_callback)
    display.clear()
    if delete_logs:
        del_logfiles() # for test
    else:
        print(TAG+f"Not deleting log files, flag: \"delete_logs\" = {"True" if delete_logs else "False"}")
    try:
        client.connect()
        print(TAG+f"Successfully connected to MQTT broker.") # at {BROKER}.")
        client.subscribe(TOPIC)
        print(TAG+f"Subscribed to topic: \"{TOPIC.decode()}\"")
        msg_drawn = False
        
        display.set_layer(0)
        display.set_pen(display.create_pen(0, 0, 0))  # Black background
        display.clear()
        presto.update()
        
    except Exception as e:
        print(TAG+f"Failed to connect to MQTT broker: {e}")
    except KeyboardInterrupt as e:
        print(TAG+f"KeyboardInterrupt. Exiting...\n")
        pr_ref()
        pr_log()
        raise

# Here begins the "loop()" part:
# def main():
# global client, msg_rcvd, last_update_time, publisher_msgID
# for compatibility with the Presto "system" the line "def main()" and below it the "globals" line have been removed
rotate_log_if_needed() # check if we need to create a new log file
list_logfiles()
setup()
draw(0) # Ensure the default message "Waiting for Messages..." is displayed
TAG = "loop(): "
start_t = time.time()
current_t = start_t
elapsed_t = 0
interval_t = 5 * 60  # Interval to check for call rotate_log_if_needed() in seconds (300 seconds = 5 minutes)
last_triggered = -1
show_size = True  # Show the size of the current log file
while True:
    try:
        current_t = time.time()
        elapsed_t = current_t - start_t
        if my_debug:
            if elapsed_t % 10 == 0 and (elapsed_t != last_triggered or last_triggered == -1):
                last_triggered = elapsed_t
                print(TAG+f"elapsed_t = {elapsed_t:.2f} seconds")
                # print(TAG+f"current_t = {current_t}, start_t = {start_t}, elapsed_t = {elapsed_t:.2f} seconds")
        if elapsed_t >= interval_t:
            start_t = current_t  # Reset the start time
            # Check if we need to create a new log file
            # and show the size of the current log file
            rotate_log_if_needed(show=show_size)
            show_size = not show_size  # Toggle the display of the log file size  
        
        # Wait for MQTT messages (non-blocking check)
        client.check_msg()

        # Refresh the display periodically
        if msg_rcvd:
            split_msg()
            print(TAG+"MQTT message: {:>3s} received".format(publisher_msgID))
            draw(1) # Display the new message in mode "PaulskPt"
            msg_rcvd = False
        elif time.time() - last_update_time > MESSAGE_DISPLAY_DURATION:
            draw(1)  # Refresh the screen with the current message
            last_update_time = time.time()
    except Exception as exc:
        if err_log_fn is None:
            err_log_fn is "mqtt_err_log.txt"
        if err_log_path is None:
            err_log_path = get_prefix() + err_log_fn
        if exc.args[0] == 103:
            print(TAG+f"Error ECONNABORTED") # = Software caused connection abort
            cleanup()
            raise RuntimeError
        else:            
            print(TAG+f"Error while waiting for MQTT messages: {exc}")
            sys.print_exception(exc, err_log_path)
            err_log_path.flush()
            cleanup()        
            raise RuntimeError
    except KeyboardInterrupt as e:
        print(TAG+f"KeyboardInterrupt: exiting...\n")
        pr_ref()
        pr_log()
        raise

# for compatibility with the Presto "system" the next two lines have been commented out
# if __name__ == '__main__':
#   main()
