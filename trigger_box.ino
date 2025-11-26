// PINS USED //

//Use     Pin#  Port#
//BNC0      41    PG0
//BNC1      40    PG1
//BNC2      39    PG2
//BNC3       6    PH3
//BNC4       7    PH4
//BNC5       8    PH5
//LDR        9    PH6
//ledBNC0   22    PA0
//ledBNC1   23    PA1
//ledBNC2   24    PA2
//ledBNC3   25    PA3
//ledBNC4   26    PA4
//ledBNC5   27    PA5
//ledLDR    28    PA6
//ledAudio  29    PA7
//EEG0      37    PC0
//EEG1      36    PC1
//EEG2      35    PC2
//EEG3      34    PC3
//EEG4      33    PC4
//EEG5      32    PC5
//EEG6      31    PC6
//EEG7      30    PC7
//ET0       49    PL0
//ET1       48    PL1
//ET2       47    PL2
//ET3       46    PL3
//ET4       45    PL4
//ET5       44    PL5
//ET6       43    PL6
//ET7       42    PL7
//Aux       15    PJ0
//Navi      14    PJ1

#include "DFRobot_RGBLCD1602.h"
#include <EEPROM.h>

//Rotary encoder inputs
#define inputRotaryA 2       //PE4 (INT4)
#define inputRotaryB 3       //PE5 (INT5)
#define inputRotaryButton 10 //PB4

//Digital input masks
const uint8_t digitalInputs1 = (1 << PG0) | (1 << PG1) | (1 << PG2);
const uint8_t digitalInputs2 = (1 << PH3) | (1 << PH4) | (1 << PH5) | (1 << PH6);
const uint8_t BNCOutputs = (1 << PJ0) | (1 << PJ1);

//Analog sources
#define inputAudio A1  //PF1

const int EEPROM_ADDRESS = 0;

// LCD setup
const int colorR = 0;
const int colorG = 100;
const int colorB = 155;
DFRobot_RGBLCD1602 lcd(0x6B, 16, 2);

// Encoder and threshold variables
volatile int diff = 0;
volatile int threshold = 511;
const int stepSizeBig = 10;
const int stepSizeSmall = 1;
volatile int stepSize = stepSizeBig;

// Button debouncing variables
volatile boolean buttonEvent = false;
int buttonState;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Track last displayed values to avoid unnecessary updates
int lastDisplayedThreshold = -1;
int lastDisplayedStep = -1;

void setup() {
  //Set pin 6-9 (BNC0, BNC1, BNC2, BNC3) as inputs
  DDRG &= ~(digitalInputs1);
  //Set pin 10-12 (BNC4, BNC5, Photoresistor) as inputs
  DDRH &= ~(digitalInputs2);
  //Set pin 22-29 (LEDs) as output
  DDRA = 0xFF;
  //Set pin 37-30 (EEG) as output
  DDRC = 0xFF;
  //Set pin 49-42 (EyeTracker) as output
  DDRL = 0xFF;
  //Set pin 14 & 15 as output
  DDRJ |= 0x03;

  pinMode(inputRotaryA, INPUT_PULLUP);
  pinMode(inputRotaryB, INPUT_PULLUP);
  pinMode(inputRotaryButton, INPUT_PULLUP);
  pinMode(inputAudio, INPUT);

  //Initialize EEG outputs
  PORTC = 0x00;
  //Initialize EyeTracker outputs
  PORTL = 0x00;
  //Initialize BNC outputs
  PORTJ &= ~0x03;

  //Restore audio threshold from EEPROM
  EEPROM.get(EEPROM_ADDRESS, threshold);

  // Initialize LCD and set display
  lcd.init();
  lcd.setRGB(colorR, colorG, colorB);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Threshold:");
  lcd.setCursor(0, 1);
  lcd.print("Step:");
  updateLCD();

  // Setup encoder interrupts
  attachInterrupt(digitalPinToInterrupt(inputRotaryA), readEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(inputRotaryB), readEncoder, CHANGE);

  //Enable pin change interrupt on port B
  PCICR |= (1 << PCIE0); 
  PCMSK0 |= (1 << PCINT4); //enables PCINT for pin10

  Serial.begin(9600);
}

void loop() {
  static bool updateOutputs = false;
  static bool lastAudioState = 0;
  static uint8_t lastDigitalState = 0;

  //Handle audio
  int audioLevel = analogRead(inputAudio);
  bool audioState = (audioLevel > threshold);
  if (audioState != lastAudioState) {
    lastAudioState = audioState;
    updateOutputs = true;
  }

  //Handle digital inputs
  uint8_t digitalState = (PING & digitalInputs1) | (PINH & digitalInputs2);
  if (digitalState != lastDigitalState) {
    lastDigitalState = digitalState;
    updateOutputs = true;
  }

  if (updateOutputs) {
    uint8_t inputState = (audioState << 7) | digitalState;
    PORTA = inputState;   //update LEDs
    PORTC = inputState;   //write state to EEG
    PORTL = inputState;   //write state to EyeTracker
    bool AUXOut = inputState;
    bool NaviOut = (inputState & 0x07);
    PORTJ = (NaviOut << PJ1) | (AUXOut << PJ0);
    updateOutputs = false;
    //Serial.println(inputState)
  }

  // Handle encoder output
  if (diff != 0) {
    updateLCD();  // Update LCD when threshold changes
    EEPROM.put(EEPROM_ADDRESS, threshold); //store new threshold
    diff = 0;
  }

  // Handle button press with debouncing
  if (buttonEvent) {
    if (millis() - lastDebounceTime > debounceDelay) {
      int reading = digitalRead(inputRotaryButton); 
      if (reading != lastButtonState) {
        lastButtonState = reading;
        if (lastButtonState == LOW) {
          // Toggle step size
          if (stepSize == stepSizeBig) {
            stepSize = stepSizeSmall;
          } else if (stepSize == stepSizeSmall) {
            stepSize = stepSizeBig;
          }
          updateLCD();
        }
      }
      lastDebounceTime = millis();
    }
    buttonEvent = false;
  }
}

void updateLCD() {
  // Only update if values have changed (prevents flickering)
  if (threshold != lastDisplayedThreshold) {
    lcd.setCursor(11, 0);
    lcd.print("     ");  // Clear old value
    lcd.setCursor(11, 0);
    lcd.print(threshold);
    lastDisplayedThreshold = threshold;
  }

  if (stepSize != lastDisplayedStep) {
    lcd.setCursor(6, 1);
    lcd.print("          ");  // Clear old value
    lcd.setCursor(6, 1);
    lcd.print(stepSize);
    lastDisplayedStep = stepSize;
  }
}

void readEncoder() {
  static int8_t lastEncoded = 0;

  int a = digitalRead(inputRotaryA);
  int b = digitalRead(inputRotaryB);

  int encoded = (a << 1) | b;
  int sum = (lastEncoded << 2) | encoded;

  static const int8_t table[] = {
    0, -1, 1, 0,
    1, 0, 0, -1,
    -1, 0, 0, 1,
    0, 1, -1, 0
  };

  int8_t direction = table[sum];

  if (direction != 0) {
    diff = direction;
    threshold = threshold + direction * stepSize;
  }

  lastEncoded = encoded;
}

//ISR for Port B pin changes
ISR(PCINT0_vect) {
  //Works as long as only the button is connected to portB
  buttonEvent = true;
}
