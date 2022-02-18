#include <Adafruit_NeoPixel.h>

#include <SPI.h>
#include "mcp2515_can.h"

#define LED_PIN    6

// How many NeoPixels are attached to the Arduino?
#define LED_COUNT 144
//#define LED_COUNT 20
//#define VERTICAL_PIXEL_OFFSET 9
//#define VERTICAL_PIXEL_COUNT 10
#define VERTICAL_PIXEL_OFFSET 83
#define VERTICAL_PIXEL_COUNT 56

#define LEFT_RADAR 0
#define RIGHT_RADAR 1
#define MACHINE_RADAR_OFFSET 0.545

#define MAX_SERIAL_DATA 40
char serialData[MAX_SERIAL_DATA];
int serialIndex = 0;
char serialOutData[MAX_SERIAL_DATA];

int speakerPin = 4; //Pin the buzzer is on THIS MATTERS FOR CHANGING FREQ

int modeFromMachine;
bool buzzerEnabled;
bool buzzOn;
unsigned long buzzTime;

char count = 0;
unsigned short controllerClock;

struct screenSettings {
  int mode;
  int freq;
  int pause;
  int distance;
  int derate;
  unsigned short controllerClock;
};

boolean newData = false;

//Define parameters of a radar target
struct radarTarget {
  bool currentTarget;
  uint16_t x, y;
};

// Declare our NeoPixel strip object:
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRBW + NEO_KHZ800);

const int SPI_CS_PIN = 9;
mcp2515_can CAN(SPI_CS_PIN); // Set CS pin

uint8_t mode = 1;
unsigned char len = 2;
unsigned char buf[2];
int x = 0;
int y = 0;

radarTarget target;

screenSettings settings;

bool receivedSerialData = false;
int receivedSerialDataCounter = 0;

void setup() {
  settings.mode = 1;
  settings.freq = 500;
  settings.pause = 200;
  settings.distance = 135;
  settings.derate = 0;
  settings.controllerClock = 0;

  modeFromMachine = 1;
  buzzerEnabled = false;
  buzzOn = false;
  buzzTime = 0;
  Serial.begin(115200);
  while (!Serial) {};
  Serial.println("Arduino is ready");

  //Set the intital white colors
  strip.begin();
  strip.fill(255);
  strip.setBrightness(32); //This is 0-255 fyi Dan, according to them, only call in setup
  strip.show();

  delay(1000);
  strip.clear();
  strip.show();

  while (CAN_OK != CAN.begin(CAN_250KBPS)) {             // init can bus
    // Serial.println("CAN BUS Shield init fail");
    // Serial.println(" Init CAN BUS Shield again");
    delay(100);
  }

  CAN.init_Filt(0, 1, 0x18FF9981);

  pinMode(speakerPin, OUTPUT);
}

unsigned char stmp[8] = {0, 0, 0, 0, 0, 0, 0, 0};

void loop() {
  delay(50);
  receiveCAN();
  sendCAN();

  readSerial();
  sendSerial();

  processData();

  //Debug serial received
  if (receivedSerialDataCounter++ > 3) {
    receivedSerialDataCounter = 0;
    receivedSerialData = false;
  }

  processData();

}

void outputRadarToLED()
{
  if (target.currentTarget)
  {
    double range;

    range = target.y;

    strip.clear();

    // double map_y = linearMap(machY, -1.255, 1.255, 0.0, 139.0); //1.255 comes from the machine width+track width that the radar unit is using
    double map_y = linearMap(target.x, 0, 1000, 0.0, VERTICAL_PIXEL_OFFSET); //1.255 comes from the machine width+track width that the radar unit is using
    double map_z = linearMap(range, 0, 1000, VERTICAL_PIXEL_OFFSET, LED_COUNT); //1.255 comes from the machine width+track width that the radar unit is using

    strip.fill(strip.Color(0, 255, 0), VERTICAL_PIXEL_OFFSET, (VERTICAL_PIXEL_COUNT * 0.333));
    if (range < 700) {
      strip.fill(strip.Color(255, 255, 0), VERTICAL_PIXEL_OFFSET + (VERTICAL_PIXEL_COUNT * 0.333), (VERTICAL_PIXEL_COUNT * 0.333));
    }
    if (range <= 100) {
      strip.fill(strip.Color(255, 0, 0), VERTICAL_PIXEL_OFFSET + (VERTICAL_PIXEL_COUNT * 0.666));
    }

    strip.setPixelColor((int)map_y, 0, 0, 255);
    strip.setPixelColor((int)map_y + 1, 0, 0, 255);
    strip.setPixelColor((int)map_y + 2, 0, 0, 255);
    strip.setPixelColor((int)map_y + 3, 0, 0, 255);
    strip.setPixelColor((int)map_y + 4, 0, 0, 255);

  }
  else
  {
    strip.clear();
  }

  strip.show();
}

void receiveCAN()
{
  unsigned char len = 0;
  unsigned char buf[8];

  if (CAN_MSGAVAIL == CAN.checkReceive())
  {
    CAN.readMsgBuf(&len, buf);

    unsigned long canId = CAN.getCanId();
    if (canId == 0x18FFB480)
    {
      modeFromMachine = buf[4];

      clearRadarTarget();
      //Currently tracking
      target.currentTarget = buf[6] != 0;
      //Target position
      target.x = ((uint8_t)buf[1] << 8) | ((uint8_t)buf[0] & 0xFF);
      target.y = ((uint8_t)buf[3] << 8) | ((uint8_t)buf[2] & 0xFF);
      buzzerEnabled = buf[5] != 0;
    }
  }
}

void sendSerial() {
  sprintf(serialOutData, "mode=%1d", modeFromMachine);
  Serial.println(serialOutData);

  sprintf(serialOutData, "x=%4d", target.x);
  Serial.println(serialOutData);

  sprintf(serialOutData, "y=%4d", target.y);
  Serial.println(serialOutData);
}

void sendCAN() {
  // send data:  id = 0x00, standrad frame, data len = 8, stmp: data buf
  unsigned char stmp[8] = {0, 0, 0, 0, 0, 0, 0, 0};

  //Debug
  stmp[0] = settings.mode;
  stmp[1] = 0x1;
  stmp[2] = (unsigned char)(settings.distance & 0x00FF);
  stmp[3] = (unsigned char)(settings.distance >> 8);
  stmp[4] = 0x1;
  stmp[5] = (unsigned char)(controllerClock & 0x00FF);
  stmp[6] = (unsigned char)(controllerClock >> 8);
  stmp[7] = count;

  //Send current mode
  stmp[4] = (byte)settings.mode;
  CAN.sendMsgBuf(0x18FFB563, 1, 8, stmp);
}

//Clears radar target data
void clearRadarTarget() {
  target.x = target.y = 0;
  target.currentTarget = false;
}

double linearMap(double x, double in_min, double in_max, double out_min, double out_max) {

  if (x < in_min) {
    return out_min;
  }
  else if (x > in_max) {
    return out_max;
  }

  if (in_max == in_min) {
    return out_min;
  }

  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min;
}

/**
   Read incoming serial data
*/
void readSerial() {

  //Return if no serial data available
  if (!Serial.available()) {
    return;
  }

  //Debug
  receivedSerialData = true;
  receivedSerialDataCounter = 0;

  //Read all serial data
  while (Serial.available()) {
    char c = Serial.read();

    if (!(serialIndex >= (MAX_SERIAL_DATA - 1))) {
      if (c == ';') { //If incoming character is delimiter ';'
        serialData[serialIndex] = 0; //Close off c-string with null character

        char* val = strchr(serialData, '='); //Find location of '='

        if (val != 0 && serialIndex != 0) { //If '=' was found and string is not length 0

          *val = 0; //Change '=' to null character
          ++val; //Set pointer to next position

          int value = atoi(val); //Parse value from c-string. This should be the number after '='

          if (value != 0) { //If the value is non-zero. atoi returns 0 if parsing failed
            changeSetting(serialData, value); //Send the "setting" string and value to change
          }

          serialData[0] = 0; //Reset serial data string
          serialIndex = 0; //Reset index counter
        }

      }
      else { //If incoming character is not delimiter
        serialData[serialIndex] = c; //Add to c-string
        serialIndex++;
      }
    }
  }

  serialData[0] = 0; //Reset serial data string
  serialIndex = 0; //Reset index counter
}

/**
   Changes specified setting to value
*/
void changeSetting(char* setting, int value) {

  if (strcmp(setting, "mode") == 0) {
    settings.mode = value;
  }
  else if (strcmp(setting, "freq") == 0) {
    settings.freq = value;
  }
  else if (strcmp(setting, "pause") == 0) {
    settings.pause = value;
  }
  else if (strcmp(setting, "distance") == 0) {
    settings.distance = value;
  }
  else if (strcmp(setting, "derate") == 0) {
    settings.derate = value;
  }
  else if (strcmp(setting, "controllerClock") == 0) {
    settings.controllerClock = value;
  }
  newData = true;
}

void processData() {

  controlBuzzer();
  outputRadarToLED();
}

void controlBuzzer() {

  if (buzzerEnabled && target.currentTarget && settings.mode != 4) {

    unsigned long currentTime = millis();

    double pauseTime = settings.pause;

    double minimumTime = pauseTime / 10.0;

    pauseTime = linearMap(target.y, 0.0, 1000.0, minimumTime, pauseTime);

    if (buzzTime == 0 || (currentTime - buzzTime) > pauseTime) {

      if (buzzOn || pauseTime == minimumTime)  {
        tone(speakerPin, (unsigned int)settings.freq);
      }
      else {
        noTone(speakerPin);
      }

      buzzOn = !buzzOn;
      buzzTime = currentTime;
    }
  }
  else {
    noTone(speakerPin);
    buzzOn = false;
    buzzTime = 0;
  }
}

void buzzerConfig() {
  //  TCCR2B = TCCR2B & B11111000 | B00000011; // for PWM frequency of 980.39 Hz
  //  TCCR2B = TCCR2B & B11111000 | B00000101; // for PWM frequency of 245.10 Hz
  //  TCCR2B = TCCR2B & B11111000 | B00000110; // for PWM frequency of 122.55 Hz
  TCCR2B = TCCR2B & B11111000 | B00000010;
  if (settings.freq >= 700) {
    TCCR2B = TCCR2B & B11111000 | B00000011; // for PWM frequency of 980.39 Hz
  }
  else if (settings.freq >= 490 && settings.freq <= 700) {
    TCCR2B = TCCR2B & B11111000 | B00000100; // for PWM frequency of
  }
  else if (settings.freq == 490) {
    TCCR2B = TCCR2B & B11111000 | B00000100; //default freq 490 on pin 11
  }
  else if (settings.freq <= 490 && settings.freq >= 200) {
    TCCR2B = TCCR2B & B11111000 | B00000101; // for PWM frequency of 245.10 Hz
  }
  else {
    TCCR2B = TCCR2B & B11111000 | B00000110; // for PWM frequency of 122.55 Hz
  }
}

void buzzerSwitch(bool state) {
  if (state) {
    // Serial.println(1);
    analogWrite(speakerPin, 250);
  }
  else {
    // Serial.println(0);
    analogWrite(speakerPin, 0);
  }
}
