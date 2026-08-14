"""Record ROS-side rates and synchronized closed-loop evidence."""

import json
from pathlib import Path
import threading
import time

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from scan_planner_msgs.msg import Bspline
from sensor_msgs.msg import PointCloud2

from .monitor_core import AcceptanceAccumulator


def _stamp_ns(message) -> int:
    return int(message.header.stamp.sec) * 1_000_000_000 + int(
        message.header.stamp.nanosec
    )


class AcceptanceMonitorNode(Node):
    """Subscribe with matching QoS and persist a compact ROS-side trace."""

    def __init__(self) -> None:
        super().__init__("lite3_acceptance_monitor")
        event_path = Path(
            self.declare_parameter("event_log_path", "/tmp/lite3_acceptance_ros.jsonl").value
        )
        summary_path = Path(
            self.declare_parameter(
                "summary_path", "/tmp/lite3_acceptance_ros_summary.json"
            ).value
        )
        event_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        self._event_path = event_path
        self._summary_path = summary_path
        self._events = event_path.open("w", encoding="utf-8")
        self._lock = threading.Lock()
        self._accumulator = AcceptanceAccumulator()
        self._closed = False
        self._started_ns = time.monotonic_ns()

        self.create_subscription(
            Odometry, "/quad_0/body_pose", self._body_pose, qos_profile_sensor_data
        )
        self.create_subscription(
            Odometry, "/quad_0/lidar_pose", self._sensor_pose, qos_profile_sensor_data
        )
        self.create_subscription(
            PointCloud2, "/quad_0/cloud", self._cloud, qos_profile_sensor_data
        )
        self.create_subscription(Twist, "/quad_0/cmd_vel", self._command, 50)
        self.create_subscription(Bspline, "/planning/bspline", self._bspline, 20)
        self.get_logger().info(
            f"Acceptance monitor writing {event_path} and {summary_path}"
        )

    def _write(self, value) -> None:
        self._events.write(json.dumps(value, sort_keys=True) + "\n")
        self._events.flush()

    def _body_pose(self, message: Odometry) -> None:
        receipt = time.monotonic_ns()
        stamp = _stamp_ns(message)
        position = message.pose.pose.position
        values = (position.x, position.y, position.z)
        with self._lock:
            self._accumulator.observe_body_pose(receipt, stamp, values)
            self._write(
                {
                    "kind": "body_pose",
                    "receipt_monotonic_ns": receipt,
                    "stamp_ns": stamp,
                    "position": values,
                }
            )

    def _sensor_pose(self, message: Odometry) -> None:
        receipt = time.monotonic_ns()
        stamp = _stamp_ns(message)
        with self._lock:
            self._accumulator.observe_sensor_pose(receipt, stamp)
            self._write(
                {
                    "kind": "sensor_pose",
                    "receipt_monotonic_ns": receipt,
                    "stamp_ns": stamp,
                }
            )

    def _cloud(self, message: PointCloud2) -> None:
        receipt = time.monotonic_ns()
        stamp = _stamp_ns(message)
        count = int(message.width) * int(message.height)
        with self._lock:
            self._accumulator.observe_cloud(receipt, stamp, count)
            self._write(
                {
                    "kind": "cloud",
                    "receipt_monotonic_ns": receipt,
                    "stamp_ns": stamp,
                    "point_count": count,
                    "is_bigendian": bool(message.is_bigendian),
                }
            )

    def _command(self, message: Twist) -> None:
        receipt = time.monotonic_ns()
        command = (message.linear.x, message.linear.y, message.angular.z)
        with self._lock:
            self._accumulator.observe_command(receipt, command)
            self._write(
                {
                    "kind": "cmd_vel",
                    "receipt_monotonic_ns": receipt,
                    "command": command,
                }
            )

    def _bspline(self, message: Bspline) -> None:
        receipt = time.monotonic_ns()
        with self._lock:
            self._accumulator.observe_bspline(receipt, message.traj_id)
            self._write(
                {
                    "kind": "bspline",
                    "receipt_monotonic_ns": receipt,
                    "trajectory_id": int(message.traj_id),
                    "control_point_count": len(message.pos_pts),
                }
            )

    def finalize(self) -> None:
        with self._lock:
            if self._closed:
                return
            summary = self._accumulator.summary()
            summary["monitor_duration_seconds"] = (
                time.monotonic_ns() - self._started_ns
            ) / 1.0e9
            self._summary_path.write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            self._events.close()
            self._closed = True

    def destroy_node(self):
        self.finalize()
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = AcceptanceMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
