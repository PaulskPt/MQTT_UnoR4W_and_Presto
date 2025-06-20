# 2025-06-17 Downloaded from: https://github.com/digitalurban/Presto_MQTT_Display/blob/main/mqtt_presto.py
# by Andy Hudson-Smith going by @digitalurban
# Changes by Paulus Schulinck going by @PaulskPt
#
import ujson
#import ubinascii
import time
from presto import Presto
from umqtt.simple import MQTTClient

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

print("Connecting to WiFi...")
wifi = presto.connect()  # Ensure this is configured for your network
print("WiFi connected.")

msg_rcvd = False
msg_drawn = False

# MQTT callback function
def mqtt_callback(topic, msg):
    global message_string, last_update_time, msg_rcvd
    message_string = msg.decode('utf-8')  # Decode the MQTT message
    # print(f"message_string = {message_string}")
    last_update_time = time.time()  # Reset the update timer
    if not my_debug:
        print(f"\nReceived message on topic {topic.decode()},\nmsg: {message_string}")

    if len(message_string) > 0:
        msg_rcvd = True
        
def split_msg():
    global message_string , msg_rcvd, temp, pres, alti, humi, publisher_datetime, publisher_time, publisher_msgID
    if not msg_rcvd:
        return
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
    
    if publisher_time is not None:
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
    
def setup():
    global client, CLIENT_ID, BROKER, PORT, TOPIC, msg_drawn
    # MQTT client setup
    print(f"Connecting to MQTT broker at {BROKER} on port {PORT}...")
    client = MQTTClient(CLIENT_ID, BROKER, port=PORT)
    client.set_callback(mqtt_callback)
    display.clear()
    try:
        client.connect()
        print(f"Successfully connected to MQTT broker.") # at {BROKER}.")
        client.subscribe(TOPIC)
        print(f"Subscribed to topic: \"{TOPIC.decode()}\"")
        msg_drawn = False
        
        display.set_layer(0)
        display.set_pen(display.create_pen(0, 0, 0))  # Black background
        display.clear()
        presto.update()
        
    except Exception as e:
        print(f"Failed to connect to MQTT broker: {e}")
    except KeyboardInterrupt as e:
        print(f"KeyboardInterrupt. Exiting...")
        raise

# Here begins the "main()" part:
# def main():
# global client, msg_rcvd, last_update_time, publisher_msgID
# for compatibility with the Presto "system" the line "def main()" and below it the "globals" line have been removed
setup()
draw(0) # Ensure the default message "Waiting for Messages..." is displayed

while True:
    try:
        # Wait for MQTT messages (non-blocking check)
        client.check_msg()

        # Refresh the display periodically
        if msg_rcvd:
            split_msg()
            print(f"MQTT message: {publisher_msgID} received")
            draw(1) # Display the new message in mode "PaulskPt"
            msg_rcvd = False
        elif time.time() - last_update_time > MESSAGE_DISPLAY_DURATION:
            draw(1)  # Refresh the screen with the current message
            last_update_time = time.time()
    except Exception as e:
        if e.args[0] == 103:
            print(f"Error ECONNABORTED")
            raise RuntimeError
        else:
            print(f"Error while waiting for MQTT messages: {e}")
            raise RuntimeError
    except KeyboardInterrupt as e:
        print(f"KeyboardInterrupt: exiting...")
        raise

# for compatibility with the Presto "system" the next two lines have been commented out
# if __name__ == '__main__':
#   main()
