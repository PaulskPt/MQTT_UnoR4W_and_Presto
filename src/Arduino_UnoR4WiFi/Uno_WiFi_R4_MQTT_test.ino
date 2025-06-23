/*
  Sunday 2025-06-16 20h07 utc +1
  Arduino Uno WiFi R4 MQTT test
  This sketch is a first try to send BME280 sensor data to a MQTT broker
  and to receive and display these MQTT messages onto the display of a Pimoroni Presto device
*/
#include <ArduinoMqttClient.h>
#include <WiFiS3.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Adafruit_BME280.h>
#include <Wire.h>
#include <time.h>
#include "RTC.h" // See: https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/RTC/examples/RTC_NTPSync/RTC_NTPSync.ino
#include "secrets.h"

// Note: RTC.h is a library for the Renesas RA4M1 MCU, which is used in the Arduino Uno WiFi R4
// It provides functions to get the current time and date from the RTC (Real Time Clock)

bool my_debug = false;

char sID[] = "UnoR4W";  // length 6 + 1
unsigned long msgID = 0L;
unsigned long msgID_max = 999L;

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;    // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)

// unsigned int localPort = 2390;  // local port to listen for UDP packets

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

// this IP did not work: "85.119.83.194" // for test.mosquitto.org
// 5.196.0.0 - 5.196.255.255 = FR-OVH-20120823, Country code: FR (info from https://lookup.icann.org/en/lookup)
const char broker[]  = SECRET_MQTT_BROKER; // test.mosquitto.org";
int        port      = atoi(SECRET_MQTT_PORT);   // 1883;

int wifiStatus = WL_IDLE_STATUS;
WiFiUDP ntpUDP; // A UDP instance to let us send and receive packets over UDP
int tzOffset = atoi(SECRET_TIMEZONE_OFFSET); // can be negative or positive (hours)
signed long utc_offset = tzOffset * 3600;    // Attention: signed long! Can be negative or positive
unsigned long ntp_interval_t = (15 * 60 * 1000L) - 5; // 15 minutes - 5 secs
NTPClient timeClient(ntpUDP, SECRET_NTP_SERVER1, utc_offset, ntp_interval_t);

int led =  LED_BUILTIN;

bool led_is_on = false;

#define led_sw_cnt 20  // Defines limit of time count led stays on

int status = WL_IDLE_STATUS;

int count = 0;

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BME280 bme; // I2C

unsigned long delayTime;

void serialPrintf(const char *format, ...) {
  char buffer[160]; // You can increase this if you need larger output
  va_list args;
  va_start(args, format);
  vsnprintf(buffer, sizeof(buffer), format, args);
  va_end(args);
  Serial.print(buffer);
}

void printWifiStatus() {
  // print the SSID of the network you're attached to:
  serialPrintf(PSTR("SSID: %s\n"), WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  serialPrintf(PSTR("IP Address: %s\n"), ip.toString().c_str());

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  serialPrintf(PSTR("signal strength (RSSI): %ld dBm\n"), rssi);
}

bool connectToWiFi(){
  bool ret = false;
  // check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println(F("Communication with WiFi module failed!"));
    // don't continue
    //while (true);
    return ret;
  }

  String fv = WiFi.firmwareVersion();
  if (fv < WIFI_FIRMWARE_LATEST_VERSION) {
    Serial.println(F("Please upgrade the firmware"));
    return ret;
  }

  // attempt to connect to WiFi network:
  while (wifiStatus != WL_CONNECTED) {
    serialPrintf(PSTR("Attempting to connect to SSID: %s\n"), ssid);
    // Connect to WPA/WPA2 network. Change this line if using open or WEP network:
    wifiStatus = WiFi.begin(ssid, pass);

    // wait 10 seconds for connection:
    delay(10000);
  }

  if (wifiStatus == WL_CONNECTED)
  {
    Serial.print(F("Connected to "));
    printWifiStatus();
    ret = true;
  }
  return ret;
}

void do_line(uint8_t le = 4)
{
  // Default
  if (le == 4)
  {
    for (uint8_t i= 0; i < le; i++)
    {
      Serial.print(F("----------")); // length 10
    }
  }
  // Variable
  else
  {
    for (uint8_t i= 0; i < le; i++)
    {
      Serial.print('-'); // length 1
    }
  }
  Serial.println();
}

void rtc_sync() 
{
  do_line(44);
  timeClient.update();  // This prints also the text "Update from NTP Server"

  // Get the current date and time from an NTP server and convert
  // it to UTC +1 by passing the time zone offset in hours.
  // You may change the time zone offset to your local one.
  //int timeZoneOffsetHours = SECRET_TIMEZONE_OFFSET[0] - '0';
  auto unixTime = timeClient.getEpochTime(); // + (timeZoneOffsetHours * 3600);
  serialPrintf(PSTR("NTP Unix time = %lu\n"), unixTime);
  // Set RTC with received NTP datetime stamp
  RTCTime timeToSet = RTCTime(unixTime);
  RTC.setTime(timeToSet);

  // Retrieve the date and time from the RTC and print them
  RTCTime currentTime;
  RTC.getTime(currentTime); 
  serialPrintf(PSTR("The RTC was just set to: %s\n"), String(currentTime).c_str());
  do_line(44);
}

// Function created by MS Copilot
// It is called by send_msg()
void composeMQTTMessage(char* topic, size_t topicSize, char* msg, size_t msgSize,
                        float Rvalue0, float Rvalue1, float Rvalue2, float Rvalue3,
                        unsigned long msgID, const char* mqttTopicBase) {
  static constexpr const char txt0[] PROGMEM = "composeMQTTMessage(): ";
  char floatStr0[15], floatStr1[15], floatStr2[15], floatStr3[15];
  char datetimeStr[32];
  char numStr[32];

  // Format float values
  dtostrf(Rvalue0, 4, 2, floatStr0);
  dtostrf(Rvalue1, 4, 2, floatStr1);
  dtostrf(Rvalue2, 4, 2, floatStr2);
  dtostrf(Rvalue3, 4, 2, floatStr3);

  // Get datetime string
  RTCTime currentTime;
  RTC.getTime(currentTime);
  strncpy(datetimeStr, String(currentTime).c_str(), sizeof(datetimeStr) - 1);
  datetimeStr[sizeof(datetimeStr) - 1] = '\0';  // Ensure null-termination

  // Format message ID
  snprintf(numStr, sizeof(numStr), "%lu", msgID);

  // Format topic
  snprintf(topic, topicSize, "%s", mqttTopicBase);

  // Format JSON-like message
  snprintf(msg, msgSize,
  "{Temperature:%s,Pressure:%s,Altitude:%s,Humidity:%s,datetime:%s,msgID:%s}",
  floatStr0, floatStr1, floatStr2, floatStr3, datetimeStr, numStr);

  if (my_debug)
    serialPrintf(PSTR("%sMQTT message = \"%s\"\n"), txt0, msg);
}

bool send_msg()
{
  static constexpr const char txt0[] PROGMEM = "send_msg(): ";
  const char *txts[] PROGMEM = { "reading",       // 0
                                 "temperature",   // 1
                                 "pressure",      // 2
                                 "altitude",      // 3
                                 "humidity",      // 4
                                 "is extreme",    // 5
                                 "resetting" };   // 6
  bool ret = false;
  float Rvalue0 = bme.readTemperature();
  float Rvalue1 = bme.readPressure() / 100.0F;
  // According to Copilot the calculation for height is:
  // altitude = 44330.0 * (1.0 - pow(pressure / seaLevelhPa, 0.1903));
  float Rvalue2 = bme.readAltitude(SEALEVELPRESSURE_HPA);
  float Rvalue3 = bme.readHumidity();
  
  bool do_test_reset = false;
  /*
  if (do_test_reset)
  {
    Rvalue0 = 0.0;
    Rvalue1 = 1010.0;
    Rvalue2 = 0.0;
    Rvalue3 = 100.0;
  }
  */

  if (Rvalue0 == 0.0 && Rvalue1 == 1010.0 && Rvalue2 == 0.0 && Rvalue3 == 100.0)
  {
    Serial.println(F("BME280 values are unreliable. Going to reset in 5 seconds..."));
    delay(5000);
    NVIC_SystemReset();
  }

  if (do_test_reset)
    Rvalue0 = -20.0; // For testing purposes only

  if (Rvalue0 < -10.0 || Rvalue0 > 50.0)
  {
    // Temperature:
    serialPrintf(PSTR("%s%s %s %s\n"), txt0, txts[0], txts[1], txts[5]);
    Rvalue0 = 0.0;
    serialPrintf(PSTR("%s%s %s to %3.1f\n"), txt0, txts[6], txts[1], Rvalue0);
  }

  if (do_test_reset)
    Rvalue1 = 1200.0;  // For test purposes only

  if (Rvalue1 < 800.0 || Rvalue1 > 1100.0)
  {
    // Pressure:
    serialPrintf(PSTR("%s%s %s %s: %7.2f\n"), txt0, txts[0], txts[2], txts[5], Rvalue1);
    Rvalue1 = 1010.0;
    serialPrintf(PSTR("%s%s %s to %6.1f\n"), txt0, txts[6], txts[2], Rvalue1);
    
    // return ret; // don't accept unrealistic extremes
  }

  if (do_test_reset)
    Rvalue2 = NAN;

  if (isnan(Rvalue2)) {
    // Altitude:
    serialPrintf(PSTR("%s%s %s %s %F\n"), txt0, txts[0], txts[3], "resulted in", Rvalue2);
    Rvalue2 = 0.0; // or some sentinel value
    serialPrintf(PSTR("%s%s %s to %3.1f\n"), txt0, txts[6], txts[3], Rvalue2);
    // Log or handle safely  
  }

  if (do_test_reset)
    Rvalue3 = 200.0;

  if (Rvalue3 > 100.0)
  {
    // Humidity:
    serialPrintf(PSTR("%s%s %s %s\n"), txt0, txts[0], txts[4], txts[5]);
    Rvalue3 = 100.0;
    serialPrintf(PSTR("%s%s %s to %4.1f\n"), txt0, txts[6], txts[4], Rvalue3);
  }
  
  char topic[32];
  char msg[128];
  
  msgID++;
  if (msgID > msgID_max)
    msgID = 1;

  composeMQTTMessage(topic, sizeof(topic), msg, sizeof(msg),
                     Rvalue0, Rvalue1, Rvalue2, Rvalue3,
                     msgID, SECRET_MQTT_TOPIC);

  if (my_debug)
  {
    // Calculate real topic length
    uint8_t topic_cnt = 0;
    for (uint8_t i = 0; topic[i] != '\0'; i++)
    {
      if (topic[i] != '\0')
        topic_cnt++;
    }
    // Note: Serial.printf("%3d", msgID) does not work with Serial UART of the Uno
    // serialPrintf() is MS Copilot's "solution"
    serialPrintf(PSTR("\nmsg topic   length = %3d\n"), topic_cnt);
    
    // Calculate the real payload length
    uint8_t payload_cnt = 0;
    for (uint8_t i = 0; msg[i] != '\0'; i++)
    {
      if (msg[i] != '\0')
        payload_cnt++;
    }
    serialPrintf(PSTR("msg payload length = %3d\n"), payload_cnt);
  }

  mqttClient.beginMessage(topic);
  mqttClient.print(msg);
  mqttClient.endMessage();
  
  serialPrintf(PSTR("MQTT message: %3d sent\n"), msgID);

  if (my_debug)
    serialPrintf(PSTR("\ntopic: \"%s\",\npayload: \"%s\"\n"), topic, msg);

  ret = true;

  return ret;
}

// Function to turn the built-in LED on
void led_on() {
  //blinks the built-in LED every second
  digitalWrite(LED_BUILTIN, HIGH);
  led_is_on = true;
  //delay(1000);
}

// Function to turn the built-in LED off
void led_off()
{
  digitalWrite(LED_BUILTIN, LOW);
  led_is_on = false;
  //delay(1000);
}

void setup() {

  //Initialize serial and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial2.begin(115200);  // WiFi/BT AT command processor on ESP32-S3

  delay(1000);

  pinMode(led, OUTPUT);      // set the LED pin mode
  //define LED_BUILTIN as an output
  pinMode(LED_BUILTIN, OUTPUT);

  // attempt to connect to WiFi network:
  if (!connectToWiFi())
  {
    Serial.println(F("Connect to WiFi failed. Going into permanent loop..."));
    while (true)
      delay(5000);
  }

  RTC.begin();
  timeClient.begin();
  Serial.print(F("\nTimezone offset = "));
  if (tzOffset < 0)
    Serial.print("-");
  Serial.print(abs(utc_offset)/3600);
  Serial.println(F(" hour(s)"));
  Serial.println(F("Starting connection to NTP server..."));
  //rtc_sync();

  Wire1.begin();

  unsigned status;
  
  // default settings
  status = bme.begin(0x76, &Wire1);  
  // You can also pass in a Wire library object like &Wire2
  // status = bme.begin(0x76, &Wire2)
  if (!status) {
      Serial.println(F("Could not find a valid BME280 sensor, check wiring, address, sensor ID!"));
      Serial.print(F("SensorID was: 0x")); 
      Serial.println(bme.sensorID(),16);
      Serial.print(F("        ID of 0xFF probably means a bad address, a BMP 180 or BMP 085\n"));
      Serial.print(F("   ID of 0x56-0x58 represents a BMP 280,\n"));
      Serial.print(F("        ID of 0x60 represents a BME 280.\n"));
      Serial.print(F("        ID of 0x61 represents a BME 680.\n"));
      while (1) delay(10);
  }

  serialPrintf(PSTR("\nAttempting to connect to the MQTT broker: %s:%s\n"), broker, String(port).c_str());

  bool mqtt_connected = false;
  for (uint8_t i=0; i < 10; i++)
  {
    if (!mqttClient.connect(broker, port))
    {
      serialPrintf(PSTR("MQTT connection failed! Error code = %s\n"), String(mqttClient.connectError()).c_str());
      delay(1000);
    }
    else
    {
      mqtt_connected = true;
    }
  }
  if (!mqtt_connected)
  {
    Serial.print(F("unable to connect to MQTT broker in LAN. Going into infinite loop..."));
    while (true)
      delay(5000);
  }

  Serial.println(F("You're connected to the MQTT broker!"));
  Serial.println();

}

void loop() 
{
  static constexpr const char txt0[] PROGMEM = "loop(): ";
  //set interval for sending messages (milliseconds)
  unsigned long mqtt_start_t = millis();
  unsigned long mqtt_curr_t = 0L;
  unsigned long mqtt_elapsed_t = 0L;
  unsigned long mqtt_interval_t = 60 * 1000; // 1 minute

  unsigned long ntp_start_t = mqtt_start_t;
  unsigned long ntp_curr_t = 0L;
  unsigned long ntp_elapsed_t = 0L;
  unsigned long ntp_interval_t = 15 * 60 * 1000; // 15 minutes
  bool start = true;

  RTCTime currentTime;
  
  serialPrintf(PSTR("board ID = \"%s\"\n"), sID);

  uint8_t interval_in_mins = mqtt_interval_t / (60 * 1000);
  serialPrintf(PSTR("%sMQTT message send interval = %d minute%s\n"), txt0, interval_in_mins, interval_in_mins <= 1 ? "" : "s");

  while (true)
  {
    // call poll() regularly to allow the library to send MQTT keep alive which
    // avoids being disconnected by the broker
    mqttClient.poll();

    unsigned long ntp_curr_t = millis();
    ntp_elapsed_t = ntp_curr_t - ntp_start_t;
    if (start || ntp_curr_t - ntp_start_t >= ntp_interval_t)
    {
      ntp_start_t = ntp_curr_t;
      rtc_sync();
    }

    mqtt_curr_t = millis();
    mqtt_elapsed_t = mqtt_curr_t - mqtt_start_t;
    if (start || mqtt_elapsed_t >= mqtt_interval_t) 
    {
      start = false;
      // save the last time a message was sent
      mqtt_start_t = mqtt_curr_t;

      uint8_t try_cnt = 0;
      uint8_t try_cnt_max = 10;
      led_on();
      while (!send_msg())
      {
        try_cnt++;
        if (try_cnt >= try_cnt_max)
          break;
        delay(1000);
      }
      led_off();
    }
  }
}

