import os
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    arm_velocity_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
                "arm_velocity_controller", 
                "--controller-manager", 
                "/controller_manager",
                "--controller-manager-timeout", 
                "30",
        ],
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "gripper_controller",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    return LaunchDescription([
        joint_state_broadcaster_spawner,
        arm_velocity_controller_spawner,
        gripper_controller_spawner,
    ])