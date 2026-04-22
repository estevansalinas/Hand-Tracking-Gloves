#!/usr/bin/env python3

# This node acts as the bridge between the Arduino glove and the Kinova Gen3 arm in ROS2.
# It reads serial data from the Arduino, converts it into ROS2 messages, and publishes
# them to the cartesian_motion_controller and gripper_control node.

import rclpy
from rclpy.node import Node
import serial
from scipy.spatial.transform import Rotation
from geometry_msgs.msg import PoseStamped
from control_msgs.msg import GripperCommand

# -------------------- TUNABLE PARAMETERS --------------------
SERIAL_PORT = '/dev/ttyUSB0'   # Change to /dev/pts/X if using socat for testing
BAUD_RATE   = 115200           # Must match Arduino sketch
PUBLISH_HZ  = 50               # Match Arduino's 50Hz output rate

# Flex sensor raw ADC range observed from your hardware (tune these after testing)
FLEX_MIN = 200   # Value when finger is fully open / unbent
FLEX_MAX = 800   # Value when finger is fully closed / bent

# Robotiq 2f-85 gripper range in meters (0.0 = closed, 0.085 = fully open)
GRIPPER_MIN = 0.0
GRIPPER_MAX = 0.085

# Cartesian workspace bounds for the Kinova arm (meters)
X_FIXED  = 0.4   # X held fixed — not tracking forward/back hand movement
Y_RANGE  = 0.3   # End effector moves +/- 0.3m in Y
Z_CENTER = 0.3   # Center height of workspace
Z_RANGE  = 0.2   # End effector moves +/- 0.2m in Z


class GlovePublisher(Node):

    def __init__(self):
        super().__init__('glove_publisher')

        # -------------------- PUBLISHERS --------------------
        # Publishes the target pose for the cartesian_motion_controller.
        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/target_frame',
            10
        )

        # Publishes gripper open/close command to the gripper_control node.
        # Updated from robotiq_gripper_controller — gripper_control is the
        # active controller in this setup.
        self.gripper_pub = self.create_publisher(
            GripperCommand,
            '/gripper_control/gripper_cmd',
            10
        )

        # -------------------- SERIAL SETUP --------------------
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.get_logger().info(f'Opened serial port {SERIAL_PORT} at {BAUD_RATE} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            raise

        # -------------------- WAIT FOR READY SIGNAL --------------------
        self.get_logger().info('Waiting for Arduino READY signal...')
        while True:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line == 'READY':
                self.get_logger().info('Arduino is ready, starting data stream')
                break

        # -------------------- TIMER --------------------
        self.create_timer(1.0 / PUBLISH_HZ, self.read_and_publish)


    def read_and_publish(self):
        # -------------------- READ SERIAL LINE --------------------
        try:
            raw = self.ser.readline().decode('utf-8', errors='ignore').strip()
        except serial.SerialException as e:
            self.get_logger().warn(f'Serial read error: {e}')
            return

        if not raw:
            return

        # -------------------- PARSE CSV --------------------
        # Expected format (14 values):
        # gxCal, gyCal, gzCal, linAx, linAy, linAz, roll, pitch, yaw,
        # pinky, ring, middle, index, thumb
        try:
            values = list(map(float, raw.split(',')))
            if len(values) != 14:
                self.get_logger().warn(f'Unexpected value count: {len(values)}, skipping line')
                return
        except ValueError:
            self.get_logger().warn(f'Could not parse line: {raw}')
            return

        # Unpack values by index
        lax, lay, laz = values[3], values[4], values[5]   # Linear accel (g)
        roll, pitch   = values[6], values[7]               # Accel-derived, stable
        # values[8] is gyro-integrated yaw — ignored due to LSM6DS3 having no
        # magnetometer. Yaw drift makes it unusable for arm control.

        pinky  = int(values[9])    # Flex sensors (0-1023)
        ring   = int(values[10])
        middle = int(values[11])
        index  = int(values[12])
        thumb  = int(values[13])

        # -------------------- YAW FROM FINGERS --------------------
        # The LSM6DS3 has no magnetometer so gyro-integrated yaw drifts
        # unboundedly. Instead we derive yaw from the pinky, ring, and middle
        # fingers which are otherwise unused.
        # Unbent (FLEX_MIN) = 180 degrees, fully bent (FLEX_MAX) = 0 degrees.
        # This gives stable, intentional yaw control with zero drift.
        yaw_flex_avg   = (pinky + ring + middle) / 3.0
        normalized_yaw = (yaw_flex_avg - FLEX_MIN) / (FLEX_MAX - FLEX_MIN)
        normalized_yaw = self.clamp(normalized_yaw, 0.0, 1.0)
        finger_yaw     = 180.0 - (normalized_yaw * 180.0)  # 180 open, 0 bent

        # -------------------- GRIPPER FROM THUMB + INDEX --------------------
        # Average thumb and index flex to drive gripper open/close.
        # Both fingers bent = gripper closed, both open = gripper open.
        gripper_flex_avg = (thumb + index) / 2.0

        self.publish_pose(roll, pitch, finger_yaw, lay, laz)
        self.publish_gripper(gripper_flex_avg)


    def publish_pose(self, roll, pitch, yaw, lay, laz):
        msg = PoseStamped()
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        # -------------------- POSITION --------------------
        msg.pose.position.x = X_FIXED
        msg.pose.position.y = self.clamp(lay * Y_RANGE, -Y_RANGE, Y_RANGE)
        msg.pose.position.z = Z_CENTER + self.clamp(laz * Z_RANGE, -Z_RANGE, Z_RANGE)

        # -------------------- ORIENTATION --------------------
        # Roll and pitch are accel-derived (stable).
        # Yaw is now finger-derived (stable, no drift).
        q = Rotation.from_euler('xyz', [roll, pitch, yaw], degrees=True).as_quat()
        msg.pose.orientation.x = q[0]
        msg.pose.orientation.y = q[1]
        msg.pose.orientation.z = q[2]
        msg.pose.orientation.w = q[3]

        self.pose_pub.publish(msg)


    def publish_gripper(self, flex_value):
        # -------------------- MAP FLEX TO GRIPPER WIDTH --------------------
        # Normalize thumb+index average (FLEX_MIN to FLEX_MAX) to
        # Robotiq 2f-85 range (0.0m closed to 0.085m open).
        normalized  = (flex_value - FLEX_MIN) / (FLEX_MAX - FLEX_MIN)
        normalized  = self.clamp(normalized, 0.0, 1.0)

        # Invert so bent fingers = closed gripper
        gripper_pos = GRIPPER_MAX - (normalized * (GRIPPER_MAX - GRIPPER_MIN))

        msg = GripperCommand()
        msg.position   = gripper_pos
        msg.max_effort = 10.0   # Newtons — keep low during sim testing

        self.gripper_pub.publish(msg)


    def clamp(self, value, min_val, max_val):
        return max(min_val, min(max_val, value))


def main(args=None):
    rclpy.init(args=args)
    node = GlovePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.ser.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
