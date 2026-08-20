"""SCAN planner and TCP bridge only; Isaac owns sensors and physical motion."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    scan_share = get_package_share_directory("scan_planner")
    bridge_share = get_package_share_directory("lite3_sim_bridge")
    planner_config_default = os.path.join(
        scan_share, "config", "foxy_isaac_planner.yaml"
    )
    controller_config_default = os.path.join(
        scan_share, "config", "foxy_isaac_controller.yaml"
    )
    bridge_config_default = os.path.join(bridge_share, "config", "foxy_bridge.yaml")

    telemetry_host = LaunchConfiguration("telemetry_host")
    telemetry_port = LaunchConfiguration("telemetry_port")
    command_host = LaunchConfiguration("command_host")
    command_port = LaunchConfiguration("command_port")
    bridge_max_vx = LaunchConfiguration("bridge_max_vx")
    bridge_config = LaunchConfiguration("bridge_config")
    require_dual_cloud = LaunchConfiguration("require_dual_cloud_sensor_frame")
    scan_audit_path = LaunchConfiguration("scan_audit_path")
    planner_config = LaunchConfiguration("planner_config")
    controller_config = LaunchConfiguration("controller_config")
    enable_monitor = LaunchConfiguration("enable_monitor")
    monitor_event_log = LaunchConfiguration("monitor_event_log")
    monitor_summary = LaunchConfiguration("monitor_summary")

    return LaunchDescription(
        [
            DeclareLaunchArgument("telemetry_host", default_value="127.0.0.1"),
            DeclareLaunchArgument("telemetry_port", default_value="46000"),
            DeclareLaunchArgument("command_host", default_value="127.0.0.1"),
            DeclareLaunchArgument("command_port", default_value="46001"),
            DeclareLaunchArgument("bridge_max_vx", default_value="0.75"),
            DeclareLaunchArgument("bridge_config", default_value=bridge_config_default),
            DeclareLaunchArgument(
                "require_dual_cloud_sensor_frame", default_value="false"
            ),
            DeclareLaunchArgument("scan_audit_path", default_value=""),
            DeclareLaunchArgument(
                "planner_config", default_value=planner_config_default
            ),
            DeclareLaunchArgument(
                "controller_config", default_value=controller_config_default
            ),
            DeclareLaunchArgument("enable_monitor", default_value="false"),
            DeclareLaunchArgument(
                "monitor_event_log",
                default_value="/tmp/lite3_acceptance_ros.jsonl",
            ),
            DeclareLaunchArgument(
                "monitor_summary",
                default_value="/tmp/lite3_acceptance_ros_summary.json",
            ),
            Node(
                package="lite3_sim_bridge",
                executable="foxy_bridge_node",
                name="lite3_sim_bridge",
                output="screen",
                parameters=[
                    bridge_config,
                    {
                        "telemetry_host": telemetry_host,
                        "telemetry_port": ParameterValue(
                            telemetry_port, value_type=int
                        ),
                        "command_host": command_host,
                        "command_port": ParameterValue(command_port, value_type=int),
                        "max_vx": ParameterValue(bridge_max_vx, value_type=float),
                        "require_dual_cloud_sensor_frame": ParameterValue(
                            require_dual_cloud, value_type=bool
                        ),
                        "scan_audit_path": scan_audit_path,
                    },
                ],
            ),
            Node(
                package="scan_planner",
                executable="scan_planner_node",
                name="scan_planner_node",
                output="screen",
                parameters=[planner_config],
                remappings=[
                    ("body_pose", "/quad_0/body_pose"),
                    ("sensor_pose", "/quad_0/lidar_pose"),
                    ("cloud", "/quad_0/cloud"),
                ],
            ),
            Node(
                package="scan_planner",
                executable="closed_loop_controller",
                name="closed_loop_controller",
                output="screen",
                parameters=[controller_config],
                remappings=[
                    ("body_pose", "/quad_0/body_pose"),
                    ("cmd_vel", "/quad_0/cmd_vel"),
                ],
            ),
            Node(
                package="lite3_sim_bridge",
                executable="acceptance_monitor_node",
                name="lite3_acceptance_monitor",
                output="screen",
                condition=IfCondition(enable_monitor),
                parameters=[
                    {
                        "event_log_path": monitor_event_log,
                        "summary_path": monitor_summary,
                    }
                ],
            ),
        ]
    )
