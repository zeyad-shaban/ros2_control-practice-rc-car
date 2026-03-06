import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, SetEnvironmentVariable
from launch.actions import IncludeLaunchDescription
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    bringup_pkg_path = get_package_share_directory('my_robot_bringup')
    desc_pkg_path = get_package_share_directory('my_robot_description')
    
    urdf_path = os.path.join(desc_pkg_path, 'urdf', 'my_robot.urdf.xacro')
    rviz_config_path = os.path.join(bringup_pkg_path, 'config', 'rviz_config.rviz')
    world_sdf_path = os.path.join(bringup_pkg_path, 'worlds', 'my_world.sdf')
    robot_controllers = os.path.join(get_package_share_directory('my_robot_bringup'), 'config', 'my_robot_controllers.yaml')
    
    ld = LaunchDescription()
    
    ld.add_action(
        SetEnvironmentVariable(
            name='GZ_SIM_SYSTEM_PLUGIN_PATH',
            value='/opt/ros/jazzy/lib'
        )
    )

    # launch_robot_description
    ld.add_action(
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': Command([ FindExecutable(name='xacro'), ' ', urdf_path])}]
        )
    )
    
    # gz_sim_launch
    ld.add_action(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                [PathJoinSubstitution([FindPackageShare('ros_gz_sim'),
                                       'launch',
                                       'gz_sim.launch.py'])]),
            launch_arguments=[('gz_args', [f' -r -v 1 {world_sdf_path}'])]),
    )
    
    gz_spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=['-topic', 'robot_description', '-name',
                   'diff_drive', '-allow_renaming', 'true'],
    )
    
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', 'diff_drive_controller'],
    )
    
    diff_drive_base_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'riff_drive_controller',
            '--param-file',
            robot_controllers,
        ],
    )
    
    ld.add_action(
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=gz_spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        )
    )
    
    ld.add_action(
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[diff_drive_base_controller_spawner],
            )
        ),
    )
    
    # Bridge
    ld.add_action(
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            output='screen',
        )
    )
    
    ld.add_action(gz_spawn_entity)
    
    
    # launch_rviz2
    ld.add_action(
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config_path],
        )
    )
    
    return ld