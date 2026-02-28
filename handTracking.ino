// Chase Torre
// Arduino NANO 33 IoT
// Senior Project (Fall 2025 - Spring 2026)
// Hand Tracking Gloves Value Generator

//pin initialization 
const int finger1 = A1; 
const int finger2 = A2;
const int finger3 = A3;
const int finger4 = A6;
const int finger5 = A7;
// *note* A4 and A5 are SDA/SCL, so we aren't using them here

void setup() {
  Serial.begin(9600); //setting io and baud rate
  pinMode(finger1, INPUT);  // pinky
  pinMode(finger2, INPUT);  // ring
  pinMode(finger3, INPUT);  // middle
  pinMode(finger4, INPUT);  // index
  pinMode(finger5, INPUT);  // thumb
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// Constant Initialization 

const float VCC = 3.2; // measured voltage 

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////// Value Reading

// Pinky Readings

void loop() { //reading and printing analog voltages of each finger bend

  int bendValue1 = analogRead(finger1); // reads digital integer representation 

  float voltage1 = bendValue1 * (VCC/1023); // Converts digital integer to voltage


///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Ring Readings

  int bendValue2 = analogRead(finger2); 

  float voltage2 = bendValue2 * (VCC/1023); 




///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Middle Readings

  int bendValue3 = analogRead(finger3); 

  float voltage3 = bendValue3 * (VCC/1023); 

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Index Readings

  int bendValue4 = analogRead(finger4);

  float voltage4 = bendValue4 * (VCC/1023); 

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// Thumb Readings

  int bendValue5 = analogRead(finger5);  

  float voltage5 = bendValue5 * (VCC/1023); 

///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//Monitor/Plotter Output 

//For debug

  /*Serial.println("\nPinky value: " + String(bendValue1)); // Print Digital Integer
  Serial.println("Voltage: " + String(voltage1) + " V\n"); // Print Output Voltage

  Serial.println("Ring value: " + String(bendValue2)); 
  Serial.println("Voltage: " + String(voltage2) + " V\n"); 

  Serial.println("Middle value: " + String(bendValue3)); 
  Serial.println("Voltage: " + String(voltage3) + " V\n"); 

  Serial.println("Index value: " + String(bendValue4)); 
  Serial.println("Voltage: " + String(voltage4) + " V\n"); 
  
  Serial.println("Thumb value: " + String(bendValue5)); 
  Serial.println("Voltage: " + String(voltage5) + " V \n\n"); 
  */

//Output Plotter

  Serial.print(bendValue1); Serial.print(",");
  Serial.print(bendValue2); Serial.print(",");
  Serial.print(bendValue3); Serial.print(",");
  Serial.print(bendValue4); Serial.print(",");
  Serial.println(bendValue5); // last value ends the line

  Serial.println(" ");
  delay (50);
}
