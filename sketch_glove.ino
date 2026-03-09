#include <Arduino_LSM6DS3.h>   // Library for the onboard gyroscope/accelerometer

/*This code combines the finger tracking, gyroscope, and accelerometer together.
Expected output should hold 11 comma separated values per line
 
ORDER OF VALUES IN SERIAL MONITOR: 
1. Gyro X (deg/s)
2. Gyro Y (deg/s)
3. Gyro Z (deg/s)
4. Linear Accel X (g's)
5. Linear Accel Y (g's)
6. Linear Accel Z (g's)
7. Pinky bend (0-1023)
8. Ring bend (0-1023)
9. Middle bend (0-1023)
10. Index bend (0-1023)
11. Thumb bend (0-1023)
*/


// -------------------- FLEX SENSOR PINS --------------------
const int finger1 = A1;  // Pinky
const int finger2 = A2;  // Ring
const int finger3 = A3;  // Middle
const int finger4 = A6;  // Index
const int finger5 = A7;  // Thumb
// NOTE: A4 and A5 are reserved for I2C (IMU communication)

// -------------------- TUNABLE PARAMETERS --------------------
const unsigned long LOOP_DELAY_MS = 20;      // 50 Hz update rate

// -------------------- CALIBRATION VALUES --------------------
// Gyroscope bias values 
float biasX = 0, biasY = 0, biasZ = 0;
// Gravity vector (default assumes Z-axis points down when at rest)
float gravityX = 0, gravityY = 0, gravityZ = 1.0;

void setup() {
  Serial.begin(115200);  // Using higher baud rate
  while (!Serial);
  
  // Initialize IMU
  if (!IMU.begin()) {
    while (1);  // Freeze if IMU fails
  }
  
  // Initialize flex sensor pins
  pinMode(finger1, INPUT);  // Pinky
  pinMode(finger2, INPUT);  // Ring
  pinMode(finger3, INPUT);  // Middle
  pinMode(finger4, INPUT);  // Index
  pinMode(finger5, INPUT);  // Thumb
}

void loop() {
  // -------------------- READ IMU DATA --------------------
  float gx, gy, gz;
  float ax, ay, az;
  
  // Check if new IMU data is available
  if (!IMU.gyroscopeAvailable() || !IMU.accelerationAvailable()) return;
  
  // Read raw gyro values (degrees per second)
  IMU.readGyroscope(gx, gy, gz);
  
  // Read raw accelerometer values (in g's)
  IMU.readAcceleration(ax, ay, az);
  
  // Apply gyro calibration
  float gxCal = gx - biasX;
  float gyCal = gy - biasY;
  float gzCal = gz - biasZ;
  
  // Calculate LINEAR acceleration (motion-induced acceleration with gravity removed)
  float linAx = ax - gravityX;
  float linAy = ay - gravityY;
  float linAz = az - gravityZ;
  
  // -------------------- READ FLEX SENSORS --------------------
  int bendValue1 = analogRead(finger1);  // Pinky (0-1023)
  int bendValue2 = analogRead(finger2);  // Ring
  int bendValue3 = analogRead(finger3);  // Middle
  int bendValue4 = analogRead(finger4);  // Index
  int bendValue5 = analogRead(finger5);  // Thumb
  
  // -------------------- OUTPUT ALL DATA --------------------
  // Format: gyroX, gyroY, gyroZ, accelX, accelY, accelZ, pinky, ring, middle, index, thumb
  
  // IMU data (6 values)
  Serial.print(gxCal, 3); Serial.print(",");
  Serial.print(gyCal, 3); Serial.print(",");
  Serial.print(gzCal, 3); Serial.print(",");
  Serial.print(linAx, 3); Serial.print(",");
  Serial.print(linAy, 3); Serial.print(",");
  Serial.print(linAz, 3); Serial.print(",");
  
  // Flex sensor data (5 values)
  Serial.print(bendValue1); Serial.print(",");
  Serial.print(bendValue2); Serial.print(",");
  Serial.print(bendValue3); Serial.print(",");
  Serial.print(bendValue4); Serial.print(",");
  Serial.println(bendValue5);  // Last value ends the line
  
  delay(LOOP_DELAY_MS);
}