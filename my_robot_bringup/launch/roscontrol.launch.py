import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import Command, FindExecutable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    
    urdf_path = os.path.join(get_package_share_directory('my_robot_description'), 'urdf', 'my_robot.urdf.xacro')
    controller_manager_config_path = os.path.join(get_package_share_directory('my_robot_bringup'), 'config', 'my_robot_controllers.yaml') 
    rviz_config_path = os.path.join(get_package_share_directory('my_robot_bringup'), 'config', 'rviz_config.rviz')
    
    ld = LaunchDescription()
    
    # Launch Arguments
    ld.add_action(
        DeclareLaunchArgument('use_teleop', default_value='false'),
    )
    
    # Robot state publisher to publish the /robot_description and /tf
    ld.add_action(
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': Command([ FindExecutable(name='xacro'), ' ', urdf_path])}]
        )
    )
    
    # controller manager node
    ld.add_action(
        Node(
            package='controller_manager',
            executable='ros2_control_node',
            parameters=[controller_manager_config_path],
        ),
    )
    
    # Spawn controllers
    ld.add_action(
        Node(
            package='controller_manager',
            executable='spawner',
            arguments=['joint_state_broadcaster', 'diff_drive_controller'],
        )
    )
        
    # rviz2
    ld.add_action(
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config_path],
        )
    )
    
    # Teleop twist for control (if wanted, idk how to get this "if" thing tho)
    ld.add_action(
        Node(
            package='teleop_twist_keyboard',
            executable='teleop_twist_keyboard',
            remappings=[('/cmd_vel', '/diff_drive_controller/cmd_vel')],
            parameters=[{'stamped': True}],
            prefix='xterm -e',
            condition=IfCondition(LaunchConfiguration('use_teleop'))
        ),
    )
    
    return ld