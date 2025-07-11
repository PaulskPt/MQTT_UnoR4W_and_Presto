
# MQTT messages displayed on a Pimoroni Presto device

Original version by: @digitalurban [repo](https://github.com/digitalurban/Presto_MQTT_Display/blob/main/mqtt_presto.py)

Modified version by: Paulus Schulinck (Github handle: @PaulskPt) [repo](https://github.com/PaulskPt/MQTT_UnoR4W_and_Presto/tree/main)

This repository contains MicroPython code and Arduino C++ code designed to display messages received via MQTT on a [Pimoroni Presto device](https://shop.pimoroni.com/products/presto?variant=54894104019323).
The MQTT messages are published from an Arduino [Uno R4 WiFi](https://store.arduino.cc/products/uno-r4-wifi?srsltid=AfmBOoqFJln_4hqTS9kODV5BzuSx9C1apLP3kX2z5igzQhok9Gm-LYJ8)  device that has connected a Pimoroni BME280 [breakout](https://shop.pimoroni.com/products/bme280-breakout?variant=29420960677971) temperature, pressure and humidity sensor.


## Features

- **MQTT Integration**:
  ```
  Device 1: Arduino Uno R4 WiFi: connects to a MQTT Broker as Publisher device;
  Device 2: Pimoroni Presto: connects to the same MQTT Broker.
            Then subscribes to the MQTT topic that device #1 publishes.
            It displays received messages on the screen.
```
- **Customizable Display**:
```
Messages are shown in orange text on a black background.

In this moment the time (hh:mi:ss) and the msgID, both extracted from the received message, will be shown on the screen.
```
- **Message Timing**: Ensures each message is displayed for at least 20 seconds.
```
## Requirements

- **Hardware**:
  - Pimoroni Presto device with a 4 inch square display [details](https://shop.pimoroni.com/products/presto?variant=54894104019323);
  - Arduino Uno R4 WiFi [details](https://store.arduino.cc/products/uno-r4-wifi?srsltid=AfmBOorz1WUvgkV5g0bJ7K10-pgHiDBGq3Fy6wc5KB5iB8YFUMf7pP0h);
  - Pimoroni BME280 breakout [details](https://shop.pimoroni.com/products/bme280-breakout?variant=29420960677971);
  - StemmaQt/Qwiic [cable](https://www.adafruit.com/product/4210?srsltid=AfmBOop4XAzdxPfaLartPs8cdARyylU9Bc9dpsJzbvw9bjFX0x_Wen2O)

- **Software**:

- For device 1:
  - Arduino IDE v2.3.5;
  - Arduino sketch "Uno_WiFi_R4_MQTT_test.ino"
  - secrets.h containing default data
  - The following Arduino libraries:
  ```
    #include <ArduinoMqttClient.h>
    #include <WiFiS3.h>
    #include <NTPClient.h>
    #include <WiFiUdp.h>
    #include <Adafruit_BME280.h>
    #include <Wire.h>
    #include <time.h>
    #include "RTC.h"
    #include "secret.h"
  ``` 
  [RTC library for device 1](https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/RTC/examples/RTC_NTPSync/RTC_NTPSync.ino)

- For device 2:

  - A Micropython IDE, e.g.: Thonny.
  - Pimoroni's version of MicroPython for Presto: [firmware](https://github.com/pimoroni/presto/tree/main?tab=readme-ov-file#download-firmware);
  - Micropython script ```mqtt_presto.py```
  - secrets.json containing default data
  - `umqtt.simple` library for MQTT communication;
  - other libraries like: ujson.
  
## Installation

- For device 1
1. Connect the external BME280 I2C sensor to the StemmaQT/Qwiic port of the Uno R4 WiFi;
2. Connect the Uno R4 WiFi via a USB cable to your PC;
3. Copy the arduino sketch to a folder of your choice:
   ```
   (on a MS Windows 11 PC e.g.: C:\Users\<Username>\Documents\Arduino\Uno_WiFi_R4_MQTT_test)
   ```
5. Run the Arduino IDE v2.3.5 (or the online create.arduino.cc) and load the sketch;
6. In the Arduino IDE > Select other board and port. Fill-in "Arduino uno r4 WiFi". Select when the board was found. Choose the port the Uno R4 WiFi is connected to.
7. Build and upload the sketch.

- For device 2
1. Clone or download this repository:
   ```bash
   git clone https://github.com/PaulskPt/MQTT_UnoR4W_and_Presto.git
   ```
   Or download the ZIP file directly from GitHub.

2. Upload the Micropython script and the file secret.json to your device using a tool like [Thonny](https://thonny.org/), [ampy](https://github.com/scientifichackers/ampy), or [rshell](https://github.com/dhylands/rshell).

3. If needed, customize the items in the file ```secret.json``` (defaults, see paragraph "Software functionalities" below)

After the installation of each device has been successful, you can disconnect the devices from your pc. Then power each device from a 5 Volt DC source or a battery.

## Usage

1. Device 1 will start upon applying power or pushing the reset button.
2. On device 2 you have to swipe until the "Mqtt Presto" logo appears in front. Then tap this icon.
   See: [Mqtt Presto](https://imgur.com/a/xOUvd57)
3. Both devices will connect to the Wi-Fi access point of your choice. For the Presto device, if needed, see the guide [EzWiFi](https://github.com/pimoroni/presto/blob/main/docs/wifi.md)
4. Both devices will connect to the specified MQTT broker. The Uno R4 WiFi as publisher. The Presto as subscriber to the defined topic.
5. Incoming messages will be displayed on the screen of the Presto for 20 seconds each.
   In the current state of this micropython sketch, running on the Presto,
   the following information will be displayed:
   ```
   MQTT pub : UnoR4W
   14:18:16   msgID = 47

   Temperature = 27.11 °C
   Pressure = 1005.66 hPa
   Altitude = 64.54 m
   Humidity = 49.63 %rH
   ```
   The payload of the MQTT message contains a datetime string and a msgID at the end in the format (e.g.:) "datetime":"2025-06-20T11:56:34" and "msgID":"125".

## Example

See the text file(s) with the log output in the folder [logfile](https://github.com/PaulskPt/MQTT_UnoR4W_and_Presto/tree/main/docs).

## Software functionalities:
- Device 1:

To get the sketch running in the Arduino Uno R4 Wifi you need to fill-in the following variables in the file ```secrets.h```:

```
#define SECRET_SSID "<Your WiFi SSID here>"
#define SECRET_PASS "<Your WiFi PASSWORD here>"
#define SECRET_TIMEZONE_OFFSET "1" // Europe/Lisbon
#define SECRET_NTP_SERVER1 "1.pt.pool.ntp.org"
#define SECRET_MQTT_BROKER "5.196.78.28" // test.mosquitto.org"
#define SECRET_MQTT_PORT "1883
#define SECRET_MQTT_TOPIC "sensors/UnoR4W/ambient"

```

After booting up or a reset, the Uno R4 WiFi device will try to connect to the WiFi access point of your choice.
Then the device will connect to a NTP server of your choice. 
The built-in RTC of the Arduino Uno R4 WiFi will be synchronized with the NTP unixtime.
Then the device will connect to the MQTT broker and port of your choice.
As soon as the connection with the MQTT broker is established, the sending of MQTT messages will start.
The sending of these messages will repeat with an interval of 1 minute.
The built-in RTC will be synchronized from an NTP unixtime every 15 minutes (see: unsigned long ntp_interval_t )
The NTPClient will be set with a utc-offset with can be changed in the file secret.h.
With help of Microsoft Copilot I added the function ```void serialPrintf(const char *format, ...) ```, to 
facilitate a C++ style printf() functionality because the Arduino Serial (UART) doesn't have a printf() function.
Example:
```
  IPAddress ip = WiFi.localIP();
  serialPrintf(PSTR("IP Address: %s\n"), ip.toString().c_str());
```
An instance of the NTPClient is created as follows:
```
NTPClient timeClient(ntpUDP, SECRET_NTP_SERVER1, utc_offset, ntp_interval_t);  // line 38
```

- Device 2:
  
To get the micropython script in the Pimoroni Presto running you need to fill-in the following valiables in the file ´´´secrets.json´´´

```
{
  "mqtt": {
    "broker": "5.196.78.28",
    "port": "1883",
    "topic": "sensors/UnoR4W/ambient/#"
    "client_id":  "PrestoMQTTClient",
    "publisher_id": "UnoR4W"
  },
  "wifi" : {
    "ssid" : "<Your WiFi SSID>",
    "pass" : "<Your WiFi Password>"
  }
}
```
Update 2025-06-23:

After booting up or a reset device #2 will try to open on the SD-Card a file in the directory: ```/sd``` with the name: ```mqtt_latest_log.txt```.
If found, the script will check if this file contains the name of the most recent used log file, e.g.: ```mqtt_log_2025-06-22T130731.txt```
If the name of a log file is found in the file "mqtt_latest_log.txt", the script will try to open this log file.
If the file "mqtt_latest_log.txt" does not exist, it will be created.
If no log filename is found in the file "mqtt_latest_log.txt", it will be created.
When a MQTT message is received from the publisher, the payload of this message will be saved in the log file.
At the moment the script is stopped, either by pressing the "stop" button in the Thonny IDE, or pressing the key-combo ```<Ctrl+C>```,
the contents of the active log file will be printed to the shell (serial output).
Older logfiles on the SD-Card will be deleted.

Every five minutes, in the main loop the algorithm will check if the size of the active logfile has passed the maximum file size limit (50 kBytes).
If so, a new empty log will be created. See an example of this below:
```
[...]
loop(): MQTT message: 573 received
loop(): MQTT message: 574 received
loop(): MQTT message: 575 received
rotate_log_if_needed(): rotate log file not needed yet   <<<=== parameter/flag "show_size" False 
loop(): MQTT message: 576 received
loop(): MQTT message: 577 received
loop(): MQTT message: 578 received
loop(): MQTT message: 579 received
loop(): MQTT message: 580 received
rotate_log_if_needed(): size of "mqtt_log_2025-06-24T020539.txt" is: 21549 bytes. Max size is: 51200 bytes.
rotate_log_if_needed(): rotate log file not needed yet
loop(): MQTT message: 581 received
loop(): MQTT message: 582 received
loop(): MQTT message: 583 received
Traceback (most recent call last):
  File "<stdin>", line 706, in <module>
KeyboardInterrupt:
```

After the ```stop``` button of the Thonny IDE has been pressed, the MicroPython script will print the contents of the active log file, as shown below:
```
setup(): Subscribed to topic: "sensors/UnoR4W/ambient/#"
loop(): MQTT message:  90 received
loop(): MQTT message:  91 received
loop(): MQTT message:  92 received

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
loop(): KeyboardInterrupt: exiting...

pr_ref(): Contents of ref file: "/sd/mqtt_latest_log_fn.txt":
   01) mqtt_log_2025-06-23T172345.txt
--------------------------------------------------
Size of log file: 1102. Max log file size can be: 51200 bytes
Contents of log file: "/sd/mqtt_log_2025-06-23T172345.txt"
---Log created on: 2025-06-23T18:13:52---

{Temperature:27.53,Pressure:1001.65,Altitude:97.05,Humidity:45.02,datetime:2025-06-23T18:13:50,msgID:76}
{Temperature:27.56,Pressure:1001.63,Altitude:97.18,Humidity:44.95,datetime:2025-06-23T18:14:52,msgID:77}
{Temperature:27.54,Pressure:1001.57,Altitude:97.69,Humidity:44.97,datetime:2025-06-23T18:15:53,msgID:78}
{Temperature:27.51,Pressure:1001.65,Altitude:96.99,Humidity:44.98,datetime:2025-06-23T18:16:54,msgID:79}
{Temperature:27.50,Pressure:1001.72,Altitude:96.46,Humidity:44.95,datetime:2025-06-23T18:17:55,msgID:80}
{Temperature:27.53,Pressure:1001.69,Altitude:96.73,Humidity:44.93,datetime:2025-06-23T18:18:56,msgID:81}
{Temperature:27.55,Pressure:1001.67,Altitude:96.88,Humidity:44.89,datetime:2025-06-23T18:19:57,msgID:82}
{Temperature:27.54,Pressure:1001.67,Altitude:96.73,Humidity:44.72,datetime:2025-06-23T18:28:07,msgID:90}
{Temperature:27.57,Pressure:1001.70,Altitude:96.60,Humidity:44.59,datetime:2025-06-23T18:28:54,msgID:91}
{Temperature:27.54,Pressure:1001.66,Altitude:96.93,Humidity:44.62,datetime:2025-06-23T18:29:55,msgID:92}
--------------------------------------------------
Traceback (most recent call last):
  File "<stdin>", line 699, in <module>
KeyboardInterrupt: 

MPY: soft reboot
MicroPython feature/presto-wireless-2025,   on 2025-03-21; Presto with RP2350

Type "help()" for more information.

>>>
```


The structure of the payload of the mqtt messages used in this project is:
```
     {Temperature:27.66,Pressure:1002.06,Altitude:93.59,Humidity:45.57,datetime:2025-06-23T16:58:47,msgID:1}
```

## Reset for device 1
It happened already a few times that the BME280 readings were unreliable. I experienced that the faulty readings
did not correct. I don't know yet if these faulty readings are caused by an error on the I2C-bus.
In the mean time I created a resetPin12() function that will be called as soon as there are unreliable readings.
Note that you must connect a wire betwen the RST-pin and pin 12 to be able to perform a reset from within this
sketch.

## Debug info
- If you want to see more log output (Arduino IDE: Serial Monitor or Thonny IDE: Shell), set variable ```my_debug``` to:
  ```
  device 1, line 17: ```bool my_debug = true;```;
  device 2, line 29: ```my_debug = True```
  ```

## Suggestions (ToDo)
- Add functionality to set, and with intervals, update the RTC of device 2 (Presto) using the datetime string received from device 1 (Uno R4 WiFi).
- Save the received MQTT messsage data to a spreadsheet for analisys purposes.

## Contributing

Feel free to fork the repository, open issues, or submit ideas.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
