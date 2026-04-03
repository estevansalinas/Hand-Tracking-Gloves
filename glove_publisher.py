#!/usr/bin/env python3

# This node acts as the bridge between the Arduino glove and the Kinova Gen3 arm in ROS2.
# It reads serial data from the Arduino, converts it into ROS2 messages, and publishes
# them to the cartesian_motion_controller and Robotiq 2f-85 gripper controller.

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
FLEX_MIN = 200   # Value when finger is fully open
FLEX_MAX = 800   # Value when finger is fully closed

# Robotiq 2f-85 gripper range in meters (0.0 = closed, 0.085 = fully open)
GRIPPER_MIN = 0.0
GRIPPER_MAX = 0.085

# Cartesian workspace bounds for the Kinova arm (meters)
# These define how far the end effector can move in each direction.
# Tune these to match your sim workspace to avoid hitting joint limits.
X_FIXED = 0.4          # We hold X fixed for now, only using orientation + Y/Z
Y_RANGE = 0.3          # End effector moves +/- 0.3m in Y
Z_CENTER = 0.3         # Center height of workspace
Z_RANGE  = 0.2         # End effector moves +/- 0.2m in Z


class GlovePublisher(Node):

    def __init__(self):
        super().__init__('glove_publisher')

        # -------------------- PUBLISHERS --------------------
        # Publishes the target pose for the cartesian_motion_controller.
        # The controller reads this topic and moves the end effector to match.
        self.pose_pub = self.create_publisher(
            PoseStamped,
            '/target_frame',   # Default topic name expected by FZI cartesian_motion_controller
            10
        )

        # Publishes the gripper open/close command.
        # GripperCommand uses a position value in meters for the Robotiq 2f-85.
        self.gripper_pub = self.create_publisher(
            GripperCommand,
            '/robotiq_gripper_controller/gripper_cmd',
            10
        )

        # -------------------- SERIAL SETUP --------------------
        # Open the serial port to the Arduino.
        # timeout=1 means readline() will wait up to 1 second for a full line
        # before giving up, preventing the node from hanging indefinitely.
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            self.get_logger().info(f'Opened serial port {SERIAL_PORT} at {BAUD_RATE} baud')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port: {e}')
            raise

        # -------------------- WAIT FOR READY SIGNAL --------------------
        # Block here until the Arduino sends "READY", which it does at the end
        # of setup() after calibration is complete. This prevents the node from
        # trying to parse garbage or incomplete lines during Arduino startup.
        self.get_logger().info('Waiting for Arduino READY signal...')
        while True:
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            if line == 'READY':
                self.get_logger().info('Arduino is ready, starting data stream')
                break

        # -------------------- TIMER --------------------
        # Creates a repeating timer that calls read_and_publish() at 50Hz.
        # This matches the Arduino output rate so we process every line as it arrives.
        self.create_timer(1.0 / PUBLISH_HZ, self.read_and_publish)


    def read_and_publish(self):
        # -------------------- READ SERIAL LINE --------------------
        try:
            raw = self.ser.readline().decode('utf-8', errors='ignore').strip()
        except serial.SerialException as e:
            self.get_logger().warn(f'Serial read error: {e}')
            return

        # Skip empty lines (can happen if Arduino isn't ready or line timed out)
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
            # Line contained non-numeric data (e.g. a leftover debug print)
            self.get_logger().warn(f'Could not parse line: {raw}')
            return

        # Unpack all 14 values by index
        gx, gy, gz         = values[0], values[1], values[2]   # Gyro (deg/s)
        lax, lay, laz      = values[3], values[4], values[5]   # Linear accel (g)
        roll, pitch, yaw   = values[6], values[7], values[8]   # Orientation (degrees)
        pinky  = int(values[9])                                 # Flex sensors (0-1023)
        ring   = int(values[10])
        middle = int(values[11])
        index  = int(values[12])
        thumb  = int(values[13])

        # -------------------- PUBLISH POSE --------------------
        self.publish_pose(roll, pitch, yaw, lay, laz)

        # -------------------- PUBLISH GRIPPER --------------------
        # Use index finger flex as the primary gripper control.
        # You can change this to average multiple fingers if preferred.
        self.publish_gripper(index)


    def publish_pose(self, roll, pitch, yaw, lay, laz):
        msg = PoseStamped()

        # Stamp and frame are required by cartesian_motion_controller.
        # base_link is the root frame of the Kinova arm in ros2_kortex.
        msg.header.stamp    = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'

        # -------------------- POSITION --------------------
        # X is held fixed — we're not tracking forward/back hand movement yet.
        # Y and Z are derived from linear acceleration as a simple proxy for
        # hand position offset. Tune Y_RANGE and Z_RANGE to your workspace.
        msg.pose.position.x = X_FIXED
        msg.pose.position.y = self.clamp(lay * Y_RANGE, -Y_RANGE, Y_RANGE)
        msg.pose.position.z = Z_CENTER + self.clamp(laz * Z_RANGE, -Z_RANGE, Z_RANGE)

        # -------------------- ORIENTATION --------------------
        # Convert roll/pitch/yaw (degrees) from the Arduino into a quaternion.
        # scipy expects angles in the order [roll, pitch, yaw] with 'xyz' convention.
        # The quaternion is what ROS2 uses internally to represent orientation.
        q = Rotation.from_euler('xyz', [roll, pitch, yaw], degrees=True).as_quat()
        # scipy returns quaternion as [x, y, z, w]
        msg.pose.orientation.x = q[0]
        msg.pose.orientation.y = q[1]
        msg.pose.orientation.z = q[2]
        msg.pose.orientation.w = q[3]

        self.pose_pub.publish(msg)


    def publish_gripper(self, flex_value):
        # -------------------- MAP FLEX TO GRIPPER WIDTH --------------------
        # Normalize the raw ADC flex value (FLEX_MIN to FLEX_MAX) to
        # the Robotiq 2f-85 gripper range (0.0m closed to 0.085m open).
        # clamp() prevents out-of-range values from crashing the controller.
        normalized = (flex_value - FLEX_MIN) / (FLEX_MAX - FLEX_MIN)
        normalized = self.clamp(normalized, 0.0, 1.0)

        # Invert so that a bent (closed) finger = closed gripper
        gripper_pos = GRIPPER_MAX - (normalized * (GRIPPER_MAX - GRIPPER_MIN))

        msg = GripperCommand()
        msg.position = gripper_pos
        msg.max_effort = 10.0   # Newtons — keep low during sim testing

        self.gripper_pub.publish(msg)


    def clamp(self, value, min_val, max_val):
        # Utility to keep a value within [min_val, max_val].
        # Used to prevent out-of-bounds poses or gripper commands.
        return max(min_val, min(max_val, value))


def main(args=None):
    rclpy.init(args=args)
    node = GlovePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        # Clean up serial port and shut down ROS2 gracefully
        node.ser.close()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
