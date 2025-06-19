/*
  Sunday 2025-06-16 20h07 utc +1
  Arduino Uno WiFi R4 MQTT test
  This sketch is a first try to send BME280 sensor data to a MQTT broker
  and to receive these MQTT messages with a Unexpected Maker SQUiXL device
*/
#include <ArduinoMqttClient.h>
#include <WiFiS3.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Adafruit_BME280.h>
#include <Wire.h>
#include <EEPROM.h>
#include <time.h>
#include "RTC.h" // See: https://github.com/arduino/ArduinoCore-renesas/blob/main/libraries/RTC/examples/RTC_NTPSync/RTC_NTPSync.ino
//#include <RTClib.h>
#include "secrets.h"

//char sID[21];
char sID[] = "UnoR4W";  // length 6 + 1

///////please enter your sensitive data in the Secret tab/arduino_secrets.h
char ssid[] = SECRET_SSID;        // your network SSID (name)
char pass[] = SECRET_PASS;    // your network password (use for WPA, or use as key for WEP)

unsigned int localPort = 2390;      // local port to listen for UDP packets

WiFiClient wifiClient;
MqttClient mqttClient(wifiClient);

// this IP did not work: "85.119.83.194" // for test.mosquitto.org
// 5.196.0.0 - 5.196.255.255 = FR-OVH-20120823, Country code: FR (info from https://lookup.icann.org/en/lookup)
const char broker[]  = "5.196.78.28"; // test.mosquitto.org"; // "192.168.1.96";
int        port      = 1883;

int wifiStatus = WL_IDLE_STATUS;
WiFiUDP ntpUDP; // A UDP instance to let us send and receive packets over UDP
int tzOffset = atoi(SECRET_TIMEZONE_OFFSET); // can be negative or positive (hours)
signed long utc_offset = tzOffset * 3600;    // Attention: signed long! Can be negative or positive
unsigned long ntp_interval_t = 15 * 60 * 1000L; // 15 minutes
NTPClient timeClient(ntpUDP, SECRET_NTP_SERVER1, utc_offset, ntp_interval_t);

//IPAddress timeServer(162, 159, 200, 123); // pool.ntp.org NTP server
// const int NTP_PACKET_SIZE = 48; // NTP timestamp is in the first 48 bytes of the message
//byte packetBuffer[NTP_PACKET_SIZE]; //buffer to hold incoming and outgoing packets
// A UDP instance to let us send and receive packets over UDP
//WiFiUDP Udp;
//unsigned long epoch;

int led =  LED_BUILTIN;
int status = WL_IDLE_STATUS;

int count = 0;

#define SEALEVELPRESSURE_HPA (1013.25)

Adafruit_BME280 bme; // I2C

unsigned long delayTime;

void printWifiStatus() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print("IP Address: ");
  Serial.println(ip);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.print(rssi);
  Serial.println(" dBm");
}

void printWifiData() {
  // print your board's IP address:
  IPAddress ip = WiFi.localIP();
  Serial.print(F("IP Address: "));
  
  Serial.println(ip);

  // print your MAC address:
  byte mac[6];
  WiFi.macAddress(mac);
  Serial.print(F("MAC address: "));
  printMacAddress(mac);
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
    Serial.print(F("Attempting to connect to SSID: "));
    Serial.println(ssid);
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

void printCurrentNet() {
  // print the SSID of the network you're attached to:
  Serial.print(F("SSID: "));
  Serial.print("\"");
  Serial.print(WiFi.SSID());
  Serial.println("\"");

  // print the MAC address of the router you're attached to:
  byte bssid[6];
  WiFi.BSSID(bssid);
  Serial.print(F("MAC-address: "));
  printMacAddress(bssid);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print(F("Signal strength (RSSI): "));
  Serial.println(rssi);

  // print the encryption type:
  byte encryption = WiFi.encryptionType();
  Serial.print(F("Encryption Type: "));
  Serial.println(encryption, HEX);
  Serial.println();
}

void printMacAddress(byte mac[]) {
  for (int i = 0; i < 6; i++) {
    if (i > 0) {
      Serial.print(":");
    }
    if (mac[i] < 16) {
      Serial.print("0");
    }
    Serial.print(mac[i], HEX);
  }
  Serial.println();
}

void rtc_sync() 
{
  timeClient.update();

  // Get the current date and time from an NTP server and convert
  // it to UTC +1 by passing the time zone offset in hours.
  // You may change the time zone offset to your local one.
  //int timeZoneOffsetHours = SECRET_TIMEZONE_OFFSET[0] - '0';
  auto unixTime = timeClient.getEpochTime(); // + (timeZoneOffsetHours * 3600);
  Serial.print(F("NTP Unix time = "));
  Serial.println(unixTime);
  // Set RTC with received NTP datetime stamp
  RTCTime timeToSet = RTCTime(unixTime);
  RTC.setTime(timeToSet);

  // Retrieve the date and time from the RTC and print them
  RTCTime currentTime;
  RTC.getTime(currentTime); 
  Serial.print(F("The RTC was just set to: "));
  Serial.println(String(currentTime));
}

void setup() {

  //Initialize serial and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  
  delay(1000);

  pinMode(led, OUTPUT);      // set the LED pin mode

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

  Serial.print(F("\nAttempting to connect to the MQTT broker: "));
  Serial.print(broker);
  Serial.print(":");
  Serial.println(port);

  bool mqtt_connected = false;
  for (uint8_t i=0; i < 10; i++)
  {
    if (!mqttClient.connect(broker, port))
    {
      Serial.print(F("MQTT connection failed! Error code = "));
      Serial.println(mqttClient.connectError());
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
  const char *txts1[] PROGMEM = {"Temperature", "Pressure", "Altitude", "Humidity"};
  const char *txts2[] PROGMEM = {"°C", "hPa", "m", "%rH"};
  const char topicMsg[] PROGMEM = "Sending message to topic: ";
  const char *topics[] PROGMEM = {"temp", "pres", "alti", "humi"};
  const char mqtt_heading[] = "sensors/";
  //set interval for sending messages (milliseconds)
  const long mqtt_interval_t = 60 * 1000; // 1 minute
  unsigned long previousMillis = 0;
  bool start = true;
  unsigned long start_t = millis();
  unsigned long elapsed_t = 0;
  bool test_only = false;
  uint8_t mode = 1;

  RTCTime currentTime;
  
  Serial.print(F("board ID = \""));
  Serial.print(sID);
  Serial.println("\"");

  Serial.print(F("MQTT message send interval = "));
  uint8_t interval_in_mins = mqtt_interval_t / (60 * 1000);
  Serial.print(interval_in_mins);
  if (interval_in_mins <= 1)
    Serial.println(F(" minute.\n"));
  else
    Serial.println(F(" minutes.\n"));

  while (true)
  {
    // call poll() regularly to allow the library to send MQTT keep alive which
    // avoids being disconnected by the broker
    mqttClient.poll();

    unsigned long currentMillis = millis();
    if (start || currentMillis - start_t >= ntp_interval_t)
    {
      start_t = currentMillis;
      rtc_sync();
      //Serial.print(F("NTP formatted time: "));
      //Serial.println(timeClient.getFormattedTime());
    }

    if (start || currentMillis - previousMillis >= mqtt_interval_t) 
    {
      start = false;
      // save the last time a message was sent
      previousMillis = currentMillis;

      float Rvalue0 = bme.readTemperature();
      float Rvalue1 = bme.readPressure() / 100.0F;
      float Rvalue2 = bme.readAltitude(SEALEVELPRESSURE_HPA);
      float Rvalue3 = bme.readHumidity();
      if (Rvalue1 < 800.0 || Rvalue1 > 1100.0)
        continue; // don't accept unrealistic extremes
      
      char floatStr0[15];
      char floatStr1[15];
      char floatStr2[15];
      char floatStr3[15];

      // send messages, the Print interface can be used to set the message contents
      uint8_t i_max = (test_only) ? 1 : 4;
      if (mode == 0)
      {
        char msg[60];
        for (uint8_t i = 0; i < i_max; i++)
        {
          msg[0] = '\0';       // clear
          
          strcpy(msg, mqtt_heading); // "sensors/"                 (length  8 chars)
          strcat(msg, sID);          // "UnoR4W"                   (length  6 chars)
          strcat(msg, "/");          // "/"                        (length  1 char)
          strcat(msg, topics[i]);    // e.g: "temp"                (length  4 chars)
          strcat(msg, "/");          // "/"           "            (length  1 char)
          strcat(msg, txts1[i]);     // "Temperature"              (length 11 chars)
          strcat(msg, " = ");        // " = "                      (length  3 chars)
          //                                                       (total  20 chars) + 1

          if (i == 0)
          {   
            //Serial.println(Rvalue1);  
            floatStr0[0] = '\0';  // clear
            dtostrf(Rvalue0, 4, 2, floatStr0); //                  (length  7 char)
            strcat(msg, floatStr0);     // add value
          }
          if (i == 1)
          {   
            //Serial.println(Rvalue2);
            floatStr1[0] = '\0';  // clear
            dtostrf(Rvalue1, 4, 2, floatStr1);  //                 (length 7 char)
            strcat(msg, floatStr1);     // add value
          }
          if (i == 2)
          {   
            //Serial.println(Rvalue3);
            floatStr2[0] = '\0';  // clear
            dtostrf(Rvalue2, 4, 2, floatStr2);  //                 (length 7 char)
            strcat(msg, floatStr2);     // add value
          }
          if (i == 3)
          {   
            //Serial.println(Rvalue4);
            floatStr3[0] = '\0';  // clear
            dtostrf(Rvalue3, 4, 2, floatStr3);  //                  (length 7 char)
            strcat(msg, floatStr3);     // add value
          }
          strcat(msg, "\0");          // null-terminator            (total   8 chars)

          Serial.print(F("mqtt msg "));
          Serial.print(i+1);
          Serial.print(" = \"");
          Serial.print(msg);
          Serial.println("\"");
            
          mqttClient.beginMessage(msg);
          if (i == 0)
            mqttClient.print(floatStr0);
          else if (i == 1)
            mqttClient.print(floatStr1);
          else if (i == 2)
            mqttClient.print(floatStr2);
          else if (i == 3)
            mqttClient.print(floatStr3);

          mqttClient.endMessage();
          delay(40000);
        }
        Serial.println();
      }
      else if (mode == 1)
      {
        char topic[26]; //  = "\"sensors/UnoR4W/ambient\"";  // length 22 + 1 = 23 chars
        char msg[140];
        
        topic[0] = '\0';
        msg[0] = '\0';       // clear

        //strcpy(topic, "\"");                                  // (length  1 char)
        strcpy(topic, "sensors/UnoR4W/ambient");                // (length 22 chars)
        //strcat(topic, "\"");                                  // (length  1 char)
        strcat(topic, "\0");                                    // (length  1 char)    Total: 23 chars

        strcpy(msg, "{");          // "{"                        (length  1 char)
        strcat(msg, txts1[0]);     // "Temperature"                (length 11 chars)   31
        strcat(msg, ":");          // ":"                      (length  1 char)
        floatStr0[0] = '\0';  // clear
        dtostrf(Rvalue0, 4, 2, floatStr0); //                      (length  7 char)
        strcat(msg, floatStr0);    // add value
        strcat(msg, ",");          // ","                      (length  1 chars)
        strcat(msg, txts1[1]);     // "Pressure"                   (length  8 chars)   21
        strcat(msg, ":");          // ":"                      (length  1 chars)
        floatStr1[0] = '\0';  // clear
        dtostrf(Rvalue1, 4, 2, floatStr1);  //                     (length 7 char)
        strcat(msg, floatStr1);    // add value
        strcat(msg, ",");          // ","                      (length  1 chard)
        strcat(msg, txts1[2]);     // "Altitude"                   (length  8 chars)   21
        strcat(msg, ":");          // ":"                      (length  1 chard)
        floatStr2[0] = '\0';  // clear
        dtostrf(Rvalue2, 4, 2, floatStr2);  //                     (length 7 char)
        strcat(msg, floatStr2);    // add value
        strcat(msg, ",");          // ","                      (length  1 chars)
        strcat(msg, txts1[3]);     // "Humidity"                   (length  8 chars)   21
        strcat(msg, ":");          // ":"                      (length  1 chard)
        floatStr3[0] = '\0';  // clear
        dtostrf(Rvalue3, 4, 2, floatStr3);  //                     (length 7 char)      7
        strcat(msg, floatStr3);    // add value

        RTCTime currentTime;
        RTC.getTime(currentTime); 
        //Serial.print(F("RTC datetime: "));
        //Serial.println(String(currentTime));
        strcat(msg, ",");          //                                    (length  1 char)
        strcat(msg, "datetime");   //                                    (length  8 chars)
        strcat(msg, ":");          //                                    (length  1 char)
        strcat(msg, String(currentTime).c_str()); // e.g.: 2025-06-18T18:47:08   (length 19 chars)

        strcat(msg, "}");          // "}"                                (length  2 chars)
        strcat(msg, "\0");          // end-of-string delimiter           (length  1 char)


        mqttClient.beginMessage(topic);
        mqttClient.print(msg);
        mqttClient.endMessage();   //                            Total msg: 135 characters
        
        Serial.print(F("msg topic sent: "));
        Serial.print(topic);
        Serial.print(", payload: ");
        Serial.println(msg);
      }
    }
  }
}

