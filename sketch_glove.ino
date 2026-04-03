#include <Arduino_LSM6DS3.h>   // Library for the onboard gyroscope/accelerometer

/*This code combines the finger tracking, gyroscope, and accelerometer together.
Expected output should hold 14 comma separated values per line
 
ORDER OF VALUES IN SERIAL MONITOR: 
1. Gyro X (deg/s)
2. Gyro Y (deg/s)
3. Gyro Z (deg/s)
4. Linear Accel X (g's)
5. Linear Accel Y (g's)
6. Linear Accel Z (g's)
7. Roll  (degrees)
8. Pitch (degrees)
9. Yaw   (degrees) -- gyro-integrated, drifts over time
10. Pinky bend (0-1023)
11. Ring bend (0-1023)
12. Middle bend (0-1023)
13. Index bend (0-1023)
14. Thumb bend (0-1023)
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
float biasX = 0, biasY = 0, biasZ = 0;
float gravityX = 0, gravityY = 0, gravityZ = 1.0;

// -------------------- YAW INTEGRATION --------------------
// Yaw cannot be derived from the accelerometer alone (it only sees gravity, which
// doesn't change when you rotate around the vertical axis). Instead we integrate
// the gyro Z rate over time to accumulate a yaw angle.
float yaw = 0.0;            // Accumulated yaw angle in degrees
unsigned long lastTime = 0; // Tracks the timestamp of the previous loop iteration
                            // so we can compute an accurate dt each cycle

// -------------------- FLEX SENSOR SMOOTHING --------------------
// Averages 4 analogRead samples to reduce ADC noise on flex sensors.
// More samples = smoother signal but slightly more latency.
int smoothRead(int pin) {
  int sum = 0;
  for (int i = 0; i < 4; i++) sum += analogRead(pin);
  return sum / 4;
}

void setup() {
  Serial.begin(115200);
  while (!Serial);
  
  if (!IMU.begin()) {
    while (1);
  }
  
  pinMode(finger1, INPUT);
  pinMode(finger2, INPUT);
  pinMode(finger3, INPUT);
  pinMode(finger4, INPUT);
  pinMode(finger5, INPUT);

  // Capture the start time so the first dt calculation isn't garbage
  lastTime = millis();

  // Signal to the ROS2 node that the Arduino is live and ready to stream data.
  // The Python node should wait for this string before entering its read loop
  // to avoid parsing garbage or incomplete lines during startup.
  Serial.println("READY");
}

void loop() {
  // -------------------- READ IMU DATA --------------------
  float gx, gy, gz;
  float ax, ay, az;
  
  if (!IMU.gyroscopeAvailable() || !IMU.accelerationAvailable()) return;
  
  IMU.readGyroscope(gx, gy, gz);
  IMU.readAcceleration(ax, ay, az);
  
  // Apply gyro calibration
  float gxCal = gx - biasX;
  float gyCal = gy - biasY;
  float gzCal = gz - biasZ;
  
  // Linear acceleration (gravity removed)
  float linAx = ax - gravityX;
  float linAy = ay - gravityY;
  float linAz = az - gravityZ;

  // -------------------- ROLL & PITCH FROM ACCEL --------------------
  // atan2 gives a stable angle from two components without singularities.
  // Roll:  rotation around the X-axis (hand tilting left/right)
  // Pitch: rotation around the Y-axis (hand tilting forward/back)
  // These are computed from raw accel (ax, ay, az), NOT linear accel,
  // because gravity is exactly what we're measuring the tilt against.
  float roll  = atan2(ay, az) * 180.0 / PI;   // Convert radians to degrees
  float pitch = atan2(-ax, sqrt(ay * ay + az * az)) * 180.0 / PI;

  // -------------------- YAW FROM GYRO INTEGRATION --------------------
  // dt = time elapsed since last loop in seconds
  // Multiplying gyro Z rate (deg/s) by dt (s) gives degrees rotated this cycle
  // Accumulating these increments over time gives the total yaw angle
  unsigned long now = millis();
  float dt = (now - lastTime) / 1000.0;  // Convert ms to seconds
  lastTime = now;                         // Update for next iteration
  yaw += gzCal * dt;

  // Keep yaw wrapped within [-180, 180] to avoid unbounded growth
  if (yaw > 180.0)  yaw -= 360.0;
  if (yaw < -180.0) yaw += 360.0;

  // -------------------- READ FLEX SENSORS --------------------
  // Using smoothRead() instead of analogRead() to average out ADC noise
  int bendValue1 = smoothRead(finger1);  // Pinky
  int bendValue2 = smoothRead(finger2);  // Ring
  int bendValue3 = smoothRead(finger3);  // Middle
  int bendValue4 = smoothRead(finger4);  // Index
  int bendValue5 = smoothRead(finger5);  // Thumb
  
  // -------------------- OUTPUT ALL DATA --------------------
  // IMU raw (6 values)
  Serial.print(gxCal, 3); Serial.print(",");
  Serial.print(gyCal, 3); Serial.print(",");
  Serial.print(gzCal, 3); Serial.print(",");
  Serial.print(linAx, 3); Serial.print(",");
  Serial.print(linAy, 3); Serial.print(",");
  Serial.print(linAz, 3); Serial.print(",");

  // Orientation angles (3 values) -- these are what the ROS2 node uses
  // to compute the quaternion for the cartesian_motion_controller
  Serial.print(roll,  3); Serial.print(",");
  Serial.print(pitch, 3); Serial.print(",");
  Serial.print(yaw,   3); Serial.print(",");

  // Flex sensors (5 values)
  Serial.print(bendValue1); Serial.print(",");
  Serial.print(bendValue2); Serial.print(",");
  Serial.print(bendValue3); Serial.print(",");
  Serial.print(bendValue4); Serial.print(",");
  Serial.println(bendValue5);  // println ends the line — ROS2 node reads until \n
  
  delay(LOOP_DELAY_MS);
}
