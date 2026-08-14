# Foxy Container Environment

The 5070 Ti host is Ubuntu 24.04 and must not receive a native Foxy install.
The accepted planner runtime is built as a rootless Podman image from:

- Canonical Ubuntu Minimal 20.04.6 rootfs release `20250625`;
- rootfs SHA-256
  `36fa27807168a1f34150cc93fac82595a2e92c4a1e3ed659ed736e30955bbd7b`;
- OSRF's `snapshots.ros.org/foxy/final/ubuntu` repository;
- pinned ROS meta-package version pattern `0.9.2-1*` used by the OSRF Foxy
  final Dockerfiles.

The imported base image identity on the 5070 Ti is:

```text
localhost/ubuntu:focal-minimal-20250625
image id: 1c1d5483b8b43a862b1256bad052199679e3b1ff8170531934b9cc8e3adf9892
manifest digest: sha256:be57841484c0b1635751e517c2470683949260cc43e05c7a936d4329150b0105
```

The Docker Hub pull of `ros:foxy-ros-base-focal` failed at the registry TLS
handshake. No untrusted mirror was substituted. The task instead reconstructs
the official environment from Canonical and OSRF primary sources.

The final task image is `localhost/machine-dog-nav/foxy-scan:20260813`:

```text
image id: e4aa715467b93f20a9d9cdbb6a1dbd0d3c8c1e033e7792f2d889cba03db227d8
manifest digest: sha256:290cc0390d022775a549b7b98b7abbfcaf62546965718e22fc6e50eeb92b2282
```

The accepted runtime inventory records Ubuntu 20.04.6, x86_64, ROS 2 Foxy,
GCC 9.4.0, CMake 3.16.3, Python 3.8.10, PCL 1.10.0, and Eigen 3.3.7. Exact
package versions, image inspection, rootless Podman state, and evidence hashes
are stored beside this file in `runtime_inventory.txt`, `dpkg_packages.tsv`,
`final_image_inspect.json`, `podman_info.json`, and `evidence_sha256.txt`.
