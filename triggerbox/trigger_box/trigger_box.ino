// PINS USED //

//Use     Pin#  Port#
//BNC0      41    PG0
//BNC1      40    PG1
//BNC2      39    PG2
//BNC3       6    PH3
//BNC4       7    PH4
//BNC5       8    PH5
//LDR        9    PH6
//LDR-anlg  A7
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
const uint8_t digitalInputs2 = (1 << PH3) | (1 << PH4) | (1 << PH5); //| (1 << PH6);

//Analog sources
#define inputAudio A1 
#define inputLDR   A7 

const int EEPROM_ADDRESS_AUDIO = 0;
const int EEPROM_ADDRESS_LDR = 4;   // int takes 4 bytes

// LCD setup
const int colorR = 0;
const int colorG = 100;
const int colorB = 155;
DFRobot_RGBLCD1602 lcd(0x6B, 16, 2);

// Encoder and threshold variables
volatile int diff = 0;
volatile int audioThreshold = 511;
volatile int ldrThreshold = 511;
volatile int stepSize = 1;

// Track which threshold is currently being edited (0=Audio, 1=LDR)
volatile int currentThresholdMode = 0;

// Button debouncing variables
volatile boolean buttonEvent = false;
int buttonState;
int lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50;

// Track last displayed values to avoid unnecessary updates
int lastDisplayedAudioThreshold = -1;
int lastDisplayedLDRThreshold = -1;
int lastDisplayedMode = -1;

void setup() {
  //Set pin 6-9 (BNC0, BNC1, BNC2, BNC3) as inputs
  DDRG &= ~(digitalInputs1);
  //Set pin 10-12 (BNC4, BNC5) as inputs
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

  //Initialize EEG outputs
  PORTC = 0x00;
  //Initialize EyeTracker outputs
  PORTL = 0x00;
  //Initialize BNC outputs
  PORTJ &= ~0x03;

  // Set ADC prescaler to 32 (16MHz/32 = 500kHz ADC clock)
  // This reduces analogRead time to ~27us
  ADCSRA |= (1 << ADPS2) | (1 << ADPS0);
  ADCSRA &= ~(1 << ADPS1);
  
  //Restore thresholds from EEPROM
  EEPROM.get(EEPROM_ADDRESS_AUDIO, audioThreshold);
  EEPROM.get(EEPROM_ADDRESS_LDR, ldrThreshold);

  // Initialize LCD and set display
  lcd.init();
  lcd.setRGB(colorR, colorG, colorB);
  lcd.clear();
  updateLCD();

  // Setup encoder interrupts
  attachInterrupt(digitalPinToInterrupt(inputRotaryA), readEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(inputRotaryB), readEncoder, CHANGE);

  //Enable pin change interrupt on port B (button press)
  PCICR |= (1 << PCIE0); 
  PCMSK0 |= (1 << PCINT4); //enables PCINT for pin10

  //Serial.begin(9600);
}

void loop() {

  //Handle audio (approx 27us analogRead)
  int audioLevel = analogRead(inputAudio);
  bool audioState = (audioLevel > audioThreshold);

  // Handle LDR (approx 27us analogRead)
  int ldrLevel = analogRead(inputLDR);
  bool ldrState = (ldrLevel > ldrThreshold);

  //Handle digital inputs
  uint8_t digitalState = (PING & digitalInputs1) | (PINH & digitalInputs2);

 //Combined input state
  uint8_t inputState = (audioState << 7) | (ldrState << 6) | digitalState;

  static uint8_t lastInputState = 0; 
  if (inputState != lastInputState) {
    lastInputState = inputState;
    
    PORTA = inputState;   //update LEDs
    PORTC = inputState;   //write state to EEG
    PORTL = inputState;   //write state to EyeTracker

    PORTJ = 0x00; // Reset port J
    if (inputState) { 
        PORTJ |= (1 << PJ0); // Set AUX out if any input is high
    }
    if (inputState & 0x07) { // Check if lower 3 bits (BNC 0-2) are set for Navi
        PORTJ |= (1 << PJ1);
    }
  }

  // Handle encoder output 
  if (diff != 0) {
    // START CRITICAL SECTION 
    noInterrupts(); 
    int currentDiff = diff; // Quickly copy the volatile value
    diff = 0;               // Reset the volatile flag
    interrupts();
    // END CRITICAL SECTION

    if (currentThresholdMode == 0) {
      audioThreshold = audioThreshold + currentDiff;
      EEPROM.put(EEPROM_ADDRESS_AUDIO, audioThreshold);
    } else {
      ldrThreshold = ldrThreshold + currentDiff;
      EEPROM.put(EEPROM_ADDRESS_LDR, ldrThreshold);
    }
    updateLCD();
  }

  // Handle button press with debouncing
  if (buttonEvent) {
    if (millis() - lastDebounceTime > debounceDelay) {
      int reading = digitalRead(inputRotaryButton); 
      if (reading != lastButtonState) {
        lastButtonState = reading;
        if (lastButtonState == LOW) {
          // Toggle threshold mode
          currentThresholdMode = 1 - currentThresholdMode; // Toggles between 0 and 1
          updateLCD();
        }
      }
      lastDebounceTime = millis();
    }
    buttonEvent = false;
  }
}

void updateLCD() {
  // Update Threshold values
  if (audioThreshold != lastDisplayedAudioThreshold || ldrThreshold != lastDisplayedLDRThreshold) {
    lcd.clear(); // Easier than clearing specific areas
    lcd.setCursor(0, 0);
    lcd.print("Aud T:");
    lcd.print(audioThreshold);
    lcd.setCursor(0, 1);
    lcd.print("LDR T:");
    lcd.print(ldrThreshold);

    lastDisplayedAudioThreshold = audioThreshold;
    lastDisplayedLDRThreshold = ldrThreshold;
  }
  
  // Update mode indicator (using cursor position to show active mode)
  if (currentThresholdMode != lastDisplayedMode) {
    if (currentThresholdMode == 0) {
        // Highlight Audio (maybe move cursor to start of line 0 for a moment, or use a character)
        // Simple text indicator:
        lcd.setCursor(15, 0);
        lcd.print("<");
        lcd.setCursor(15, 1);
        lcd.print(" ");
    } else {
        lcd.setCursor(15, 0);
        lcd.print(" ");
        lcd.setCursor(15, 1);
        lcd.print("<");
    }
    lastDisplayedMode = currentThresholdMode;
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
  }

  lastEncoded = encoded;
}

//ISR for Port B pin changes
ISR(PCINT0_vect) {
  //Works as long as only the button is connected to portB
  buttonEvent = true;
}
