"""ROS 2 Foxy adapter for the versioned Lite3 simulation transport."""

import json
from pathlib import Path
import threading
import time
from typing import Optional

import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import TransformStamped, Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState, PointCloud2, PointField
from tf2_ros import TransformBroadcaster

from .command_state import CommandLimits
from .protocol import (
    CommandV1,
    JointStateV1,
    MessageType,
    ProtocolError,
    ScanIdTracker,
    SequenceTracker,
    decode_dual_cloud_sensor_payload,
    decode_joint_state_payload,
    decode_sensor_payload,
    decode_status_payload,
    xyz_f32_be_to_le,
)
from .transport import CommandClient, FrameStreamClient


def _time_message(timestamp_ns: int) -> Time:
    if timestamp_ns < 0:
        raise ValueError("timestamp_ns must be non-negative")
    message = Time()
    message.sec = timestamp_ns // 1_000_000_000
    message.nanosec = timestamp_ns % 1_000_000_000
    return message


class FoxyBridgeNode(Node):
    """Publish Isaac telemetry to ROS and forward latest bounded Twist."""

    ZERO = CommandV1(0.0, 0.0, 0.0)

    def __init__(self) -> None:
        super().__init__("lite3_sim_bridge")
        self._telemetry_host = self.declare_parameter("telemetry_host", "127.0.0.1").value
        self._telemetry_port = int(self.declare_parameter("telemetry_port", 46000).value)
        self._command_host = self.declare_parameter("command_host", "127.0.0.1").value
        self._command_port = int(self.declare_parameter("command_port", 46001).value)
        self._connect_timeout = float(
            self.declare_parameter("connect_timeout_seconds", 5.0).value
        )
        self._telemetry_receive_timeout = float(
            self.declare_parameter("telemetry_receive_timeout_seconds", 10.0).value
        )
        self._reconnect_delay = float(
            self.declare_parameter("reconnect_delay_seconds", 0.2).value
        )
        command_rate_hz = float(self.declare_parameter("command_rate_hz", 50.0).value)
        source_timeout_seconds = float(
            self.declare_parameter("source_command_timeout_seconds", 0.25).value
        )
        if (
            command_rate_hz <= 0.0
            or source_timeout_seconds <= 0.0
            or self._connect_timeout <= 0.0
            or self._telemetry_receive_timeout <= 0.0
        ):
            raise ValueError("bridge rates and timeouts must be positive")
        self._command_period = 1.0 / command_rate_hz
        self._source_timeout_ns = int(source_timeout_seconds * 1_000_000_000)
        self._limits = CommandLimits(
            max_vx=float(self.declare_parameter("max_vx", 0.75).value),
            max_vy=float(self.declare_parameter("max_vy", 0.35).value),
            max_wz=float(self.declare_parameter("max_wz", 1.0).value),
        )
        self._world_frame = self.declare_parameter("world_frame", "world").value
        self._base_frame = self.declare_parameter("base_frame", "base").value
        self._sensor_frame = self.declare_parameter("sensor_frame", "lidar").value
        body_pose_topic = self.declare_parameter(
            "body_pose_topic", "/quad_0/body_pose"
        ).value
        sensor_pose_topic = self.declare_parameter(
            "sensor_pose_topic", "/quad_0/lidar_pose"
        ).value
        cloud_topic = self.declare_parameter("cloud_topic", "/quad_0/cloud").value
        raw_cloud_topic = self.declare_parameter(
            "raw_cloud_topic", "/quad_0/cloud_raw"
        ).value
        self._require_dual_cloud = bool(
            self.declare_parameter("require_dual_cloud_sensor_frame", False).value
        )
        scan_audit_path = self.declare_parameter("scan_audit_path", "").value
        if not cloud_topic or not raw_cloud_topic or cloud_topic == raw_cloud_topic:
            raise ValueError("raw and planning cloud topics must be distinct and non-empty")
        joint_state_topic = self.declare_parameter(
            "joint_state_topic", "/quad_0/joint_states"
        ).value
        cmd_vel_topic = self.declare_parameter(
            "cmd_vel_topic", "/quad_0/cmd_vel"
        ).value

        self._body_pose_publisher = self.create_publisher(
            Odometry, body_pose_topic, qos_profile_sensor_data
        )
        self._sensor_pose_publisher = self.create_publisher(
            Odometry, sensor_pose_topic, qos_profile_sensor_data
        )
        self._cloud_publisher = self.create_publisher(
            PointCloud2, cloud_topic, qos_profile_sensor_data
        )
        self._raw_cloud_publisher = self.create_publisher(
            PointCloud2, raw_cloud_topic, qos_profile_sensor_data
        )
        self._joint_state_publisher = self.create_publisher(
            JointState, joint_state_topic, 20
        )
        self._transform_broadcaster = TransformBroadcaster(self)
        self._command_subscription = self.create_subscription(
            Twist, cmd_vel_topic, self._on_twist, 20
        )

        self._latest_lock = threading.Lock()
        self._latest_sensor = None
        self._latest_joint_state = None  # type: Optional[tuple]
        self._latest_status = None
        self._latest_command = self.ZERO
        self._latest_command_monotonic_ns = None  # type: Optional[int]
        self._telemetry_tracker = SequenceTracker()
        self._scan_id_tracker = ScanIdTracker()
        self._telemetry_overwrites = 0
        self._scan_audit_lock = threading.Lock()
        self._scan_audit_file = None
        if scan_audit_path:
            audit_path = Path(scan_audit_path).expanduser()
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            self._scan_audit_file = audit_path.open("a", encoding="utf-8")
        self._stop_event = threading.Event()
        self._telemetry_thread = threading.Thread(
            target=self._telemetry_loop,
            name="foxy-telemetry-client",
            daemon=True,
        )
        self._command_thread = threading.Thread(
            target=self._command_loop,
            name="foxy-command-client",
            daemon=True,
        )
        self._telemetry_thread.start()
        self._command_thread.start()
        self._publish_timer = self.create_timer(0.01, self._publish_latest)
        self.get_logger().info(
            "Lite3 bridge ready: "
            f"telemetry {self._telemetry_host}:{self._telemetry_port}, "
            f"command {self._command_host}:{self._command_port}"
        )

    def _on_twist(self, message: Twist) -> None:
        try:
            checked = self._limits.clamp(
                CommandV1(message.linear.x, message.linear.y, message.angular.z)
            )
        except ProtocolError as error:
            self.get_logger().error(f"Rejecting invalid Twist: {error}")
            return
        with self._latest_lock:
            self._latest_command = checked
            self._latest_command_monotonic_ns = time.monotonic_ns()

    def _telemetry_loop(self) -> None:
        client = FrameStreamClient(
            self._telemetry_host,
            self._telemetry_port,
            self._telemetry_receive_timeout,
        )
        connected = False
        while not self._stop_event.is_set():
            if not connected:
                try:
                    client.connect()
                    connected = True
                    self.get_logger().info("Telemetry stream connected")
                except OSError:
                    self._stop_event.wait(self._reconnect_delay)
                    continue
            try:
                frame = client.receive()
                self._telemetry_tracker.observe(frame.header.sequence)
                if frame.header.message_type == MessageType.SENSOR_FRAME_V1:
                    if self._require_dual_cloud:
                        raise ProtocolError("dual-cloud sensor frame is required")
                    decoded = decode_sensor_payload(frame.payload)
                    with self._latest_lock:
                        if self._latest_sensor is not None:
                            self._telemetry_overwrites += 1
                        self._latest_sensor = (frame.header, decoded)
                elif frame.header.message_type == MessageType.SENSOR_FRAME_DUAL_CLOUD_V1:
                    decoded = decode_dual_cloud_sensor_payload(frame.payload)
                    self._scan_id_tracker.observe(decoded.scan_id)
                    with self._latest_lock:
                        if self._latest_sensor is not None:
                            self._telemetry_overwrites += 1
                            old_header, old_sensor = self._latest_sensor
                            if hasattr(old_sensor, "scan_id"):
                                self._write_scan_audit(
                                    old_header, old_sensor, "overwritten_before_publish"
                                )
                        self._latest_sensor = (frame.header, decoded)
                elif frame.header.message_type == MessageType.STATUS_V1:
                    decoded_status = decode_status_payload(frame.payload)
                    with self._latest_lock:
                        self._latest_status = (frame.header, decoded_status)
                elif frame.header.message_type == MessageType.JOINT_STATE_V1:
                    decoded_joints = decode_joint_state_payload(frame.payload)
                    with self._latest_lock:
                        self._latest_joint_state = (frame.header, decoded_joints)
                elif frame.header.message_type != MessageType.HEARTBEAT_V1:
                    raise ProtocolError("unexpected telemetry message type")
            except (EOFError, OSError, ProtocolError) as error:
                if connected:
                    self.get_logger().warning(f"Telemetry stream reset: {error}")
                connected = False
                client.close()
                self._stop_event.wait(self._reconnect_delay)
        client.close()

    def _command_loop(self) -> None:
        client = CommandClient(
            self._command_host,
            self._command_port,
            limits=self._limits,
            timeout_seconds=self._connect_timeout,
        )
        connected = False
        while not self._stop_event.is_set():
            loop_started = time.monotonic()
            if not connected:
                try:
                    client.connect()
                    connected = True
                    self.get_logger().info("Command stream connected")
                except OSError:
                    self._stop_event.wait(self._reconnect_delay)
                    continue
            now_ns = time.monotonic_ns()
            with self._latest_lock:
                command = self._latest_command
                received_ns = self._latest_command_monotonic_ns
            if received_ns is None or now_ns - received_ns > self._source_timeout_ns:
                command = self.ZERO
            try:
                client.send_command(command, timestamp_ns=now_ns)
            except (ConnectionError, OSError, ProtocolError) as error:
                if connected:
                    self.get_logger().warning(f"Command stream reset: {error}")
                connected = False
                client.close()
            elapsed = time.monotonic() - loop_started
            self._stop_event.wait(max(0.0, self._command_period - elapsed))
        client.close()

    def _publish_latest(self) -> None:
        with self._latest_lock:
            latest_sensor = self._latest_sensor
            self._latest_sensor = None
            latest_status = self._latest_status
            self._latest_status = None
            latest_joint_state = self._latest_joint_state
            self._latest_joint_state = None
        if latest_sensor is not None:
            header, sensor = latest_sensor
            stamp = _time_message(header.timestamp_ns)
            self._body_pose_publisher.publish(
                self._odometry_message(
                    stamp,
                    self._base_frame,
                    sensor.body_position,
                    sensor.body_quaternion_xyzw,
                )
            )
            sensor_odometry = self._odometry_message(
                stamp,
                self._sensor_frame,
                sensor.sensor_position,
                sensor.sensor_quaternion_xyzw,
            )
            self._sensor_pose_publisher.publish(sensor_odometry)
            self._transform_broadcaster.sendTransform(
                self._transform_message(
                    stamp,
                    self._sensor_frame,
                    sensor.sensor_position,
                    sensor.sensor_quaternion_xyzw,
                )
            )
            if hasattr(sensor, "scan_id"):
                raw_cloud = self._cloud_message(
                    stamp, sensor.raw_point_count, sensor.raw_points_xyz_f32_be
                )
                planner_cloud = self._cloud_message(
                    stamp,
                    sensor.planner_point_count,
                    sensor.planner_points_xyz_f32_be,
                )
                # Both messages come from this one decoded payload and share the
                # exact stamp/frame. ROS publication itself remains sequential.
                self._raw_cloud_publisher.publish(raw_cloud)
                self._cloud_publisher.publish(planner_cloud)
                self._write_scan_audit(header, sensor, "published_sequentially")
            else:
                self._cloud_publisher.publish(
                    self._cloud_message(
                        stamp, sensor.point_count, sensor.points_xyz_f32_be
                    )
                )
        if latest_joint_state is not None:
            header, joints = latest_joint_state
            self._joint_state_publisher.publish(
                self._joint_state_message(_time_message(header.timestamp_ns), joints)
            )
        if latest_status is not None:
            _, status = latest_status
            if status.flags:
                self.get_logger().debug(
                    "Isaac status "
                    f"flags={status.flags} contacts={status.contact_count} "
                    f"drops={status.dropped_frames} "
                    f"watchdog={status.watchdog_events}"
                )

    def _odometry_message(self, stamp, child_frame, position, quaternion):
        message = Odometry()
        message.header.stamp = stamp
        message.header.frame_id = self._world_frame
        message.child_frame_id = child_frame
        message.pose.pose.position.x = position[0]
        message.pose.pose.position.y = position[1]
        message.pose.pose.position.z = position[2]
        message.pose.pose.orientation.x = quaternion[0]
        message.pose.pose.orientation.y = quaternion[1]
        message.pose.pose.orientation.z = quaternion[2]
        message.pose.pose.orientation.w = quaternion[3]
        return message

    def _transform_message(self, stamp, child_frame, position, quaternion):
        message = TransformStamped()
        message.header.stamp = stamp
        message.header.frame_id = self._world_frame
        message.child_frame_id = child_frame
        message.transform.translation.x = position[0]
        message.transform.translation.y = position[1]
        message.transform.translation.z = position[2]
        message.transform.rotation.x = quaternion[0]
        message.transform.rotation.y = quaternion[1]
        message.transform.rotation.z = quaternion[2]
        message.transform.rotation.w = quaternion[3]
        return message

    def _cloud_message(self, stamp, point_count, point_bytes):
        message = PointCloud2()
        message.header.stamp = stamp
        message.header.frame_id = self._sensor_frame
        message.height = 1
        message.width = point_count
        message.fields = [
            PointField(name="x", offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name="y", offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name="z", offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        # The TCP payload is network-order. Publish explicit little-endian data
        # for the x86 Foxy/PCL boundary instead of relying on implicit swapping.
        message.is_bigendian = False
        message.point_step = 12
        message.row_step = point_count * 12
        message.data = xyz_f32_be_to_le(point_bytes)
        message.is_dense = True
        return message

    def _write_scan_audit(self, header, sensor, outcome) -> None:
        if self._scan_audit_file is None:
            return
        row = {
            "scan_id": sensor.scan_id,
            "timestamp_ns": header.timestamp_ns,
            "frame_id": self._sensor_frame,
            "raw_point_count": sensor.raw_point_count,
            "filtered_ground_point_count": sensor.filtered_ground_point_count,
            "planning_point_count": sensor.planner_point_count,
            "conservative_retained_point_count": sensor.conservative_retained_point_count,
            "outcome": outcome,
            "telemetry_overwrite_count": self._telemetry_overwrites,
        }
        with self._scan_audit_lock:
            self._scan_audit_file.write(json.dumps(row, sort_keys=True) + "\n")
            self._scan_audit_file.flush()

    @staticmethod
    def _joint_state_message(stamp, joints: JointStateV1) -> JointState:
        message = JointState()
        message.header.stamp = stamp
        message.name = list(joints.names)
        message.position = list(joints.positions)
        message.velocity = list(joints.velocities)
        return message

    def destroy_node(self):
        self._stop_event.set()
        self._telemetry_thread.join(timeout=2.0)
        self._command_thread.join(timeout=2.0)
        if self._scan_audit_file is not None:
            self._scan_audit_file.close()
            self._scan_audit_file = None
        return super().destroy_node()


def main(args=None) -> None:
    rclpy.init(args=args)
    node = FoxyBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
