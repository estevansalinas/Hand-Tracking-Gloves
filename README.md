# Hand Tracking Glove - Technical Documentation

## System Overview
The hand tracking glove combines two sensor systems:
1. **IMU (Inertial Measurement Unit)** - LSM6DS3 chip for hand position/orientation
2. **Flex Sensors** - 5 resistive bend sensors for finger tracking

### Hardware
- **Microcontroller:** Arduino Nano 33 IoT
- **IMU Sensor:** LSM6DS3 (onboard, communicates via I2C)
  - 3-axis gyroscope (measures rotation rate)
  - 3-axis accelerometer (measures linear acceleration)
- **Flex Sensors:** 5× resistive flex sensors (one per finger)

## Data Output Format

The Arduino outputs 11 comma-separated values at 50Hz via serial (115200 baud):
```
gyroX, gyroY, gyroZ, accelX, accelY, accelZ, pinky, ring, middle, index, thumb
```

### Channel Specifications

| Channel | Sensor | Unit | Range | Description |
|---------|--------|------|-------|-------------|
| 0-2 | Gyroscope (IMU) | deg/s | ±500 | Wrist rotation rate (X, Y, Z axes) |
| 3-5 | Accelerometer (IMU) | g | ±2 | Linear hand acceleration (X, Y, Z axes) |
| 6 | Flex sensor | 0-1023 | analog | Pinky finger bend |
| 7 | Flex sensor | 0-1023 | analog | Ring finger bend |
| 8 | Flex sensor | 0-1023 | analog | Middle finger bend |
| 9 | Flex sensor | 0-1023 | analog | Index finger bend |
| 10 | Flex sensor | 0-1023 | analog | Thumb bend |

### Example Output
```
12.345,-1.892,0.183,0.623,-0.483,-0.400,512,487,523,501,495
```
This represents:
- Hand rotating at 12.3 deg/s around X-axis
- Linear acceleration of 0.623g in X direction
- Pinky bent to 512 (about halfway)

## Pin Assignments

### IMU (Built-in)
- **Communication:** I2C (uses pins A4/SDA and A5/SCL internally)
- **Library:** Arduino_LSM6DS3

### Flex Sensors (Analog Input)
- **Pinky:** A1
- **Ring:** A2
- **Middle:** A3
- **Index:** A6
- **Thumb:** A7

**Note:** A4 and A5 are reserved for I2C communication with the IMU.

## Communication Settings
- **Baud Rate:** 115200
- **Update Rate:** 50 Hz (20ms loop delay)
- **Data Format:** CSV (comma-separated values)

## Dependencies
- Arduino IDE 1.8.x or later
- Arduino_LSM6DS3 library

## Authors
- Kaden Fountain
- Chase Torre
- Estevan Salinas
