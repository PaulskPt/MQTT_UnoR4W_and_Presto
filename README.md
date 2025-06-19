
# MQTT Message Display on Presto Display

Original version by: @digitalurban. [repo](https://github.com/digitalurban/Presto_MQTT_Display/blob/main/mqtt_presto.py)

Modified version by: Paulus Schulinck (Github handle: @PaulskPt). [repo](https://github.com/PaulskPt/MQTT_UnoR4W_and_Presto/tree/main)

This repository contains Python code and Arduino C++ code designed to display messages received via MQTT on a [Presto Display](https://shop.pimoroni.com/products/presto?variant=54894104019323).
The MQTT messages are published from an Arduino Uno R4 WiFi device that has connected a Pimoroni BME280 [breakout](https://shop.pimoroni.com/products/bme280-breakout?variant=29420960677971).


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

In this moment the time (hh:mi:ss), extracted from the received message, will be shown on the screen.
```
- **Message Timing**: Ensures each message is displayed for at least 20 seconds.
```
## Requirements

- **Hardware**:
  - Pimoroni Presto device with a 4 inch square display;
  - Arduino Uno R4 WiFi;
  - Pimoroni BME280 breakout;

- **Software**:
- For the Presto:
  A Micropython IDE, e.g.: Thonny.
  - MicroPython firmware;
  - `umqtt.simple` library for MQTT communication;
  - other libraries like: ujson.
  
- For the Arduino Uno R4 WiFi:
  - Arduino IDE v2.3.5;
  - Arduino sketch "Uno_WiFi_R4_MQTT_test.ino"
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
  ``` 
  [RTC library see](https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/RTC/examples/RTC_NTPSync/RTC_NTPSync.ino)
  
## Installation

1. Clone or download this repository:
   ```bash
   git clone https://github.com/PaulskPt/MQTT_UnoR4W_and_Presto.git
   ```
   Or download the ZIP file directly from GitHub.

2. Upload the files to your device using a tool like [Thonny](https://thonny.org/), [ampy](https://github.com/scientifichackers/ampy), or [rshell](https://github.com/dhylands/rshell).

3. Customize the MQTT broker, port, and topic in the code (see below)
   ```python
   BROKER = "your-mqtt-broker-address" e.g.: "5.196.78.28" // test.mosquitto.org
   PORT = 1883  # Port number
   TOPIC = b"your/topic/#"  # MQTT topic. The topic has to be equal to the topic used in the Arduino R4 WiFi device.
   ```

4. Run the code on your device.

## Usage

1. Connect both devices to Wi-Fi. Ensure the Presto device is properly connected and configured.
2. The devices will connect to the specified MQTT broker. The presto as subscriber to the defined topic. The Uno R4 as publisher.
3. Incoming messages will be displayed on the screen for 20 seconds each.
   In the current state of this micropython sketch, running on the Presto,
   the following will be displayed:
   ```
   MQTT pub : UnoR4W
   hh:mi:ss

   Temperature = 27.11 °C
   Pressure = 1005.66 hPa
   Altitude = 64.54 m
   Humidity = 49.63 %rH
   ```
   The payload of the MQTT message also contains a datetime string at the end in the format "yyyy-mo-ddThh:mi:ss"

## Example

See the text file(s) with the log output in the folder ```docs```.

## Software functionalities of the Publisher device (Arduino Uno R4 WiFi):

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

```
NTPClient timeClient(ntpUDP, SECRET_NTP_SERVER1, utc_offset, ntp_interval_t);  // line 38
```

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

## Contributing

Feel free to fork the repository, open issues, or submit ideas.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
