---
name: remote-ssh
description: 远端服务器 SSH 操作手册。维护 gpu5070ti/gpu3070ti 的中转入口；准备连接远端、启动训练、检查远端资源或调试端口时使用。
---

# GPU 远端操作手册

> machine-dog-nav 迁移说明：本手册从 walking 基础仓库迁入，部分历史小节仍记录旧 v9j/ELMAP 远端路径。使用前必须实连核验 `ssh -G <alias>`、远端目录和当前 task package；旧路径只能当历史线索，不能当 nav 当前状态。

> 当前手册记录 RTX 5070 Ti 与 RTX 3070 Ti 服务器。后续远端连接、训练检查优先使用中转别名 `gpu5070ti-relay` / `gpu3070ti-relay`。旧直连入口停止使用。

## Host 速查

| alias | HostName | User | 用途 | 网络 | Key |
|---|---|---|---|---|---|
| `gpu5070ti-relay` | 见 `~/.ssh/config` | `sun` | RTX 5070 Ti 主服务器 | `ubuntu-obgx` 中转，跳板本地 `127.0.0.1:2222` | `id_ed25519` |
| `gpu3070ti-relay` | 见 `~/.ssh/config` | `ubuntu` | RTX 3070 Ti 训练服务器 | `ubuntu-obgx` 中转，跳板本地 `127.0.0.1:23070` | `id_ed25519` |

当前首选连接：

```bash
ssh gpu5070ti-relay
ssh gpu3070ti-relay
```

2026-05-29 已验证 5070 Ti 信号：

```text
hostname: ubuntu
user: sun
GPU: NVIDIA GeForce RTX 5070 Ti, 16303 MiB total
host memory: 31137 MiB total
MemAvailable: 28002 MiB
GPU memory used: 179 MiB
```

2026-06-05 已验证 3070 Ti 信号：

```text
hostname: ubuntu-OMEN-by-HP-Laptop-17-ck1xxx
user: ubuntu
system: Linux 6.17.0-35-generic x86_64 GNU/Linux
GPU: NVIDIA GeForce RTX 3070 Ti Laptop GPU, 8192 MiB total
driver: 595.71.05
```

## 基础检查

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 gpu5070ti-relay 'hostname; hostname -I; whoami'
ssh -o BatchMode=yes -o ConnectTimeout=8 gpu5070ti-relay 'free -m; nvidia-smi'

ssh -o BatchMode=yes -o ConnectTimeout=8 gpu3070ti-relay 'hostname; whoami; uname -srmo'
ssh -o BatchMode=yes -o ConnectTimeout=8 gpu3070ti-relay 'free -m; nvidia-smi'
```

已验证 5070 Ti 信号：

```text
hostname: ubuntu
ssh alias: gpu5070ti-relay
GPU: NVIDIA GeForce RTX 5070 Ti
GPU memory: 179 / 16303 MiB
host memory: 31137 MiB total
MemAvailable: 28002 MiB
```

已验证 3070 Ti 信号：

```text
hostname: ubuntu-OMEN-by-HP-Laptop-17-ck1xxx
ssh alias: gpu3070ti-relay
user: ubuntu
GPU: NVIDIA GeForce RTX 3070 Ti Laptop GPU
GPU memory: 8192 MiB
driver: 595.71.05
```

## 3070 Ti Relay

3070 Ti 没有公网 IP，采用与 5070 Ti 同类的反向 SSH 中转方式。3070 Ti 主机主动连
`ubuntu-obgx`，并在跳板机本地监听 `127.0.0.1:23070`；本机通过
`ProxyJump ubuntu-obgx` 连接该端口。

本机解析应为：

```text
user ubuntu
hostname 127.0.0.1
port 23070
proxyjump ubuntu-obgx
hostkeyalias gpu3070ti-relay
```

跳板端口检查：

```bash
ssh ubuntu-obgx 'ss -ltnp | grep -E "127\\.0\\.0\\.1:23070" || true'
```

成功时应看到：

```text
127.0.0.1:23070 LISTEN
```

如果跳板端口存在但本机登录失败，先测试账号：

```bash
for u in ubuntu sun root admin; do
  ssh -o BatchMode=yes -o ConnectTimeout=6 -o PreferredAuthentications=publickey \
    -l "$u" gpu3070ti-relay 'hostname; whoami; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader'
done
```

当前正确账号是 `ubuntu`。如果 `sun@127.0.0.1: Permission denied`，检查
`~/.ssh/config` 中 `gpu3070ti-relay` 是否仍写成 `User sun`。

## IsaacLab Relay Website

`isaaclab.203203.cc` 是 5070 Ti 机器狗网页控制入口，托管在中转机
`ubuntu-obgx` 上。当前状态是 relay website + command API + 5070 Ti v9j3
Isaac runtime 已接入。网页仍是所有用户的公共入口；5070 Ti 后端通过服务端私有
隧道读取中转 API，不需要用户本机开隧道。

不要把 `Relay online` 或 `API online` 单独解释成机器狗已经可控。必须同时看到
`robotRuntime=online`、远端 `play_v9j3_relay` 进程、checkpoint load 日志，以及
`[v9j3-relay] seq=... scaled=(...)` 证据。

固定位置：

```text
domain: isaaclab.203203.cc
relay host: ubuntu-obgx
site root: /var/www/isaaclab-control
api root: /opt/isaaclab-control
api service: isaaclab-control-api.service
api listen: 127.0.0.1:8020
nginx conf: /etc/nginx/sites-available/isaaclab.203203.cc.conf
local source: artifacts/remote_admin/isaaclab_web_control_20260626/
5070 Ti private API tunnel: 127.0.0.1:18020 -> relay 127.0.0.1:8020
```

部署：

```bash
bash artifacts/remote_admin/isaaclab_web_control_20260626/deploy_to_ubuntu_obgx.sh
```

健康检查：

```bash
curl -sS http://isaaclab.203203.cc/healthz
curl -sS http://isaaclab.203203.cc/api/status
ssh ubuntu-obgx 'systemctl --no-pager --full status isaaclab-control-api.service | sed -n "1,22p"'
ssh ubuntu-obgx 'ss -ltnp | grep -E ":(8020|80) " || true'
ssh ubuntu-obgx 'nginx -t'
```

命令 API smoke：

```bash
curl -sS -H 'Content-Type: application/json' \
  -d '{"forward":1,"yaw":0,"keys":{"w":true,"a":false,"s":false,"d":false},"source":"curl"}' \
  http://isaaclab.203203.cc/api/command
curl -sS http://isaaclab.203203.cc/api/command
curl -sS -X POST http://isaaclab.203203.cc/api/stop
```

低延迟运行约定：

```text
Browser users -> isaaclab.203203.cc/api/command
relay API -> GET /api/events server-sent event stream
5070 Ti play process -> http://127.0.0.1:18020/api/events
```

不要让 Isaac 推理循环同步轮询公网 `http://isaaclab.203203.cc/api/command`。这条路
实测会出现约 0.5 秒单次读取延迟，并且普通 HTTP timeout 会卡住仿真循环。正确做法
是：

```bash
# 5070 Ti 上检查服务端私有隧道
ssh gpu5070ti-relay 'ss -ltnp | grep ":18020 " || true'

# 5070 Ti 上检查 SSE 当前 command
ssh gpu5070ti-relay 'curl -sS --max-time 2 -N http://127.0.0.1:18020/api/events || true'
```

当前 v9j3 网页控制会话：

```text
tmux tunnel: v9j3_api_tunnel_20260627_003940
tmux play:   v9j3_relay_play_sse_20260627_004621
checkpoint:  model_9999.pt
task:        Wave-C-Stairs-V9J3-OneStage-Parkour-Lite3-v0
```

按键验证：

```bash
curl -sS -H 'Content-Type: application/json' \
  -d '{"forward":1,"yaw":-1,"keys":{"w":true,"a":true,"s":false,"d":false},"source":"curl"}' \
  http://isaaclab.203203.cc/api/command

ssh gpu5070ti-relay 'grep -E "\\[v9j3-relay\\] seq=" \
  /home/sun/wave_c_lite3_stairs/artifacts/2026-06-25_v9j3_onestage_parkour_mainline/relay_play/v9j3_relay_play_sse_20260627_004621/stdout.log | tail'
```

期望看到：

```text
[v9j3-relay] seq=<n> stale=False raw=(1.00,-1.00) scaled=(1.500,0.000,-1.200)
```

多人同时控制时当前仍是 last-writer-wins；所有人都能通过网页发指令，但没有
controller lease。公开分享前如果要避免抢控制，需要给 API 和前端增加 active
controller / spectator 模式。

## Isaac Sim WebRTC

### 连接原则

中转切换后，Mac 原生 Isaac Sim WebRTC Streaming Client 的服务器地址尚未重新
验收。当前训练和推理验收优先使用 headless `play.py --video` 生成 mp4，再拉回
本地检查。需要实时 WebRTC 画面时，必须先为中转模式重新建立并记录
relay-compatible endpoint、TCP signaling、UDP media 和 HTTP service 的映射。

当前文档中的 WebRTC 命令只保留远端 viewer 启动、远端 listener 检查和日志检查。
本地客户端连接地址在重新验收前不写固定值。

优先使用 Isaac Sim WebRTC Streaming Client 的官方默认端口：

```text
TCP signaling: 49100
UDP media:     47998
HTTP services: 8011  # 本项目脚本约定，用于 Isaac/Kit HTTP 服务隔离
```

NVIDIA Isaac Sim 5.1 文档要求 WebRTC 主机开放 `TCP 49100` 和 `UDP 47998`。
中转模式下本地客户端地址暂未登记；不要沿用旧直连地址或历史页面参数。

### 客户端选择

按优先级使用：

```text
1. Mac 原生 Isaac Sim WebRTC Streaming Client
   用途：默认端口 49100/47998 的稳定实时查看；当前只按默认端口使用。

2. 本地 stock renderer: http://127.0.0.1:8765/
   用途：默认端口调试。打开前必须确认当前 bundle 的 streamConfig；
   历史 URL query 中的 signalingport/mediaport 不可靠。

3. 本地 patched pass-through renderer
   用途：49200/49300 等非默认端口的隔离 viewer。
   需要先生成端口匹配的页面，再打开对应 URL。
```

`/tmp/isaac_webrtc_renderer` 是临时本地 renderer 目录，页面名和 bundle 都可能
被生成脚本覆盖。任何证据采集前必须确认三件事：

```text
1. 打开的 HTML 页面名对应当前任务。
2. HTML script tag 指向预期 bundle。
3. bundle 内的 signalingPort/mediaPort 与远端 listener 一致。
```

不要凭页面名判断端口。`go1-pass-through-49200.html` 只能说明页面名，不保证
当前 bundle 仍连接 `49200/47999`。

### 正确打开方式

默认端口实时查看：

```bash
ssh gpu5070ti-relay 'ss -antup | grep -E ":(49100|47998|8011)" || true'
```

期望：

```text
tcp LISTEN 0.0.0.0:49100
udp UNCONN 0.0.0.0:47998
tcp LISTEN 0.0.0.0:8011
```

Mac 原生 Isaac Sim WebRTC Streaming Client 的 Server 字段等待中转模式重新验收后补充。

如果使用 Codex in-app browser 看默认端口，先确认 stock bundle 当前指向默认
端口，再打开：

```text
http://127.0.0.1:8765/
```

如果使用非默认端口，例如 `49300/48000/8013`，必须同时满足远端和本地两边
端口一致。

远端 viewer kit args 示例：

```text
--/app/livestream/publicEndpointAddress=<relay-compatible-endpoint-after-revalidation>
--/app/livestream/port=49300
--/app/livestream/fixedHostPort=48000
--/app/livestream/minHostPort=48000
--/app/livestream/maxHostPort=48000
--/exts/omni.services.transport.server.http/port=8013
```

Isaac Lab 训练或 viewer 里需要看动态 articulation 时，保留 Fabric scene
delegate：

```text
--/app/useFabricSceneDelegate=true
```

不要把动态训练画面的 kit args 固定成 `--/app/useFabricSceneDelegate=false`。
该设置可能让 WebRTC viewport 里的 Go1 停在初始 USD 姿态；日志和 tensor 在变，
但肉眼看不到狗本体动作。验收必须同时看两类信号：浏览器画面里狗的腿/机身姿
态变化，以及远端诊断里 `root_pos_w`、`joint_pos` 或 `body_pos_w` 随 step 变化。
整张截图差分只能说明画面变化，不能证明狗本体在动。

本地 patched renderer 生成示例：

```bash
python3 2_experiment/isaaclab_quadruped_baseline/scripts/prepare_isolated_go1_webrtc_viewer.py \
  --host <relay-compatible-endpoint-after-revalidation> \
  --signaling-port 49300 \
  --media-port 48000 \
  --page-name elmap-pass-through-49300.html
```

打开：

```text
http://127.0.0.1:8765/elmap-pass-through-49300.html?viewer=elmap-pass-through-49300
```

验证本地 bundle：

```bash
strings /tmp/isaac_webrtc_renderer/assets/renderer-CTjqlyFI-iso-pass-through.js \
  | rg -o 'streamConfig:.{0,220}' \
  | rg 'signalingPort:49300|mediaPort:48000'
```

如果 `renderer-CTjqlyFI-iso-pass-through.js` 被其他任务复用过，重新生成页面并
使用任务专属页面名，例如 `elmap-pass-through-49300.html`。证据台账需要记录
页面名、bundle 文件名、host、signaling port、media port 和远端 tmux session。

### 启动后验证

远端端口验证：

```bash
ssh gpu5070ti-relay 'ss -antup | grep -E ":(49100|47998|8011|49300|48000|8013)" || true'
```

非默认端口对应替换：

```bash
ssh gpu5070ti-relay 'ss -u -a -n -p | grep -E ":(48000|47998)" || true'
```

浏览器或原生客户端连上后，远端应出现 `ESTAB`：

```bash
ssh gpu5070ti-relay 'ss -antp | grep -E ":(49100|49300)" || true'
```

日志验证：

```bash
ssh gpu5070ti-relay 'tail -n 160 /home/sun/elmap_isaaclab_256/artifacts/elmap_remote_smoke/logs/webrtc_pretrain_viewer.out 2>/dev/null || true'
ssh gpu5070ti-relay 'tail -n 160 /home/sun/elmap_isaaclab_256/artifacts/elmap_remote_smoke/logs/webrtc_pretrain_viewer.err 2>/dev/null || true'
```

期望看到：

```text
[elmap] WebRTC camera configured ...
[elmap] wrote WebRTC review candidate: ...
[elmap] WebRTC viewer running ... kit_args=...
```

### WebRTC 相机与滚轮缩放

如果浏览器里滚轮放大后马上又回到远景，优先检查远端 viewer 的
`--camera-update-every`。`real_env_webrtc_viewer.py` 默认值是 `12`，表示脚本
会周期性把相机刷新到设定视角。人工看画面、拖拽、滚轮缩放时，这会表现为刚放
大又被拉回。

人工验收画面时，保留原有端口、环境数量、terrain、action mode 和 kit args，
只把相机刷新参数设为：

```text
--camera-update-every 0
```

远端进程确认：

```bash
ssh gpu5070ti-relay 'ps -eo pid,pcpu,pmem,cmd | awk "/real_env_webrtc_viewer/ && !/awk/ {print}"'
```

期望命令中出现：

```text
--camera-update-every 0
```

浏览器验证时，滚轮必须落在 `video` 区域内，空白页或页面容器上的滚轮不会进入
WebRTC 画面。连接成功后应看到：

```text
Session started successfully
fbc-video-0 play succeeded
```

再在视频区域滚轮放大，等待数秒后画面仍保持放大状态，才算相机刷新问题已经排
除。若画面继续回到远景，继续查远端进程是否仍是旧 viewer，或是否另一个客户端
占用了旧连接。

### “无法播放媒体”排查顺序

先查端口是否真的活着：

```bash
ssh gpu5070ti-relay 'ss -antup | grep -E ":(49300|48000|8013)" || true'
```

如果 `49300` 或 `8013` 没有 listener，原因是远端当前没有对应 viewer。
处理方式是按已批准命令重新启动对应端口 viewer，或者改用当前真正监听的默认
端口。

再查本地页面是否连错端口：

```bash
strings /tmp/isaac_webrtc_renderer/assets/renderer-CTjqlyFI-iso-pass-through.js \
  | rg -o 'streamConfig:.{0,220}'
```

如果页面 URL 写着 `49300`，但 bundle 里仍是其他端口，需要重新运行
`prepare_isolated_go1_webrtc_viewer.py --signaling-port 49300 --media-port 48000`
并使用新的任务专属页面名。URL query 不能作为端口证据。

如果 TCP listener、UDP listener、bundle 端口都一致但仍无法播放，不要把原因
归到 `49300` 本身。继续比较 `--livestream 1/2`、客户端类型、浏览器 console、
远端 `webrtc_pretrain_viewer.*` 日志和是否已有其他客户端连接。

如果端口和 bundle 都一致，再查 UDP：

```bash
ssh gpu5070ti-relay 'ss -u -a -n -p | grep -E ":(48000|47998)" || true'
```

TCP signaling 可连但 UDP media 没开，通常会表现为已连接但没有画面或无法播
放媒体。处理方式是重启 viewer，并确认 kit args 中同时设置
`fixedHostPort/minHostPort/maxHostPort`。

最后查客户端独占：

```bash
ssh gpu5070ti-relay 'ss -antp | grep -E ":(49100|49300)" || true'
```

Isaac Sim 文档说明每个 Isaac Sim instance 同时只支持一个 streaming client。
如果普通 Chrome 已经占着同一 stream，不要由 AI 自动操作或关闭普通 Chrome。
改用 Codex in-app browser 的隔离页面、另启已批准的隔离端口 viewer，或请 Dr
Sun 手动关闭对应客户端。

### 启动空 Isaac Sim 视口

```bash
ssh gpu5070ti-relay 'bash -s' <<'REMOTE'
set -euo pipefail
OLD_PID=$(cat /home/sun/isaac_webrtc_official.pid 2>/dev/null || true)
if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
  kill "$OLD_PID" || true
  sleep 2
  kill -9 "$OLD_PID" 2>/dev/null || true
fi
pkill -f 'isaacsim.exp.full.streaming' 2>/dev/null || true
pkill -f 'scripts/demos/quadrupeds.py' 2>/dev/null || true
LOG=/home/sun/isaac_webrtc_official.log
PIDFILE=/home/sun/isaac_webrtc_official.pid
: > "$LOG"
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
nohup isaacsim isaacsim.exp.full.streaming --no-window \
  --/app/livestream/port=49100 \
  --/app/livestream/fixedHostPort=47998 \
  --/app/livestream/minHostPort=47998 \
  --/app/livestream/maxHostPort=47998 \
  --/app/livestream/logLevel=verbose \
  --/exts/omni.services.transport.server.http/port=8011 \
  > "$LOG" 2>&1 &
echo $! > "$PIDFILE"
REMOTE
```

### 启动 quadrupeds 可视化自检

```bash
ssh gpu5070ti-relay 'bash -s' <<'REMOTE'
set -euo pipefail
OLD_PID=$(cat /home/sun/isaac_webrtc_official.pid 2>/dev/null || true)
if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
  kill "$OLD_PID" || true
  sleep 3
  kill -9 "$OLD_PID" 2>/dev/null || true
fi
OLD_QPID=$(cat /home/sun/isaac_quadrupeds_webrtc.pid 2>/dev/null || true)
if [ -n "$OLD_QPID" ] && kill -0 "$OLD_QPID" 2>/dev/null; then
  kill "$OLD_QPID" || true
  sleep 2
  kill -9 "$OLD_QPID" 2>/dev/null || true
fi
pkill -f 'scripts/demos/quadrupeds.py' 2>/dev/null || true
pkill -f 'isaacsim.exp.full.streaming' 2>/dev/null || true
LOG=/home/sun/isaac_quadrupeds_webrtc.log
PIDFILE=/home/sun/isaac_quadrupeds_webrtc.pid
: > "$LOG"
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
export LIVESTREAM=2
cd /home/sun/IsaacLab
nohup ./isaaclab.sh -p scripts/demos/quadrupeds.py --headless --livestream 2 \
  --kit_args "--/app/livestream/port=49100 --/app/livestream/fixedHostPort=47998 --/app/livestream/minHostPort=47998 --/app/livestream/maxHostPort=47998 --/exts/omni.services.transport.server.http/port=8011" \
  > "$LOG" 2>&1 &
echo $! > "$PIDFILE"
REMOTE
```

连接恢复后，Mac 客户端应显示多只四足机器人和地面网格。客户端如果停在“无法播放媒体”，先确认中转模式的客户端地址已经重新验收。

### WebRTC 验证

```bash
ssh gpu5070ti-relay 'ss -antup | awk "/49100|47998|8011/ {print}"'
```

期望看到：

```text
tcp LISTEN 0.0.0.0:49100
tcp LISTEN 0.0.0.0:8011
udp UNCONN 0.0.0.0:47998
tcp ESTAB <remote-endpoint>:49100 <- Mac client
```

## 远端运行约束

非交互 SSH 不读取 `~/.bashrc`。任何会 import Isaac 的命令，都需要在同一个 shell 中先写：

```bash
source /home/sun/miniconda3/etc/profile.d/conda.sh
conda activate isaaclab
export OMNI_KIT_ACCEPT_EULA=YES
export PRIVACY_CONSENT=N
```

多步远端命令统一使用单引号 heredoc，避免 `2>&1`、`$?` 和环境变量被本地 shell 提前展开：

```bash
ssh gpu5070ti-relay 'bash -s' <<'REMOTE'
set -euo pipefail
# commands here
REMOTE
```

超过 10 分钟的远端任务使用 `tmux` 或 `nohup`。本地 SSH 退出后，普通前台子进程会收到 SIGHUP。

## 潞晨云临时服务器接入

潞晨云新服务器使用本项目的傻瓜式接入包：

```text
artifacts/remote_admin/luchen_elmap_onboarding/
```

适用任务：在临时潞晨云服务器上查看 `ETH-PBL/elmap-rl-controller`
原仓库 Isaac Gym viewer 行为。该流程只是原作者 Isaac Gym 视觉行为参考实验，
不能作为 Isaac Lab 256 环境或训练效果证据。

固定事实：

```text
repo: ETH-PBL/elmap-rl-controller
commit: 7177258
Python: 3.8.16
torch: 1.10.0+cu113
Isaac Gym: Preview 4, 需要 Dr Sun 从 NVIDIA 下载授权包
```

本地配置 SSH alias：

```bash
bash artifacts/remote_admin/luchen_elmap_onboarding/configure_luchen_ssh.sh --print-only 'ssh -p PORT USER@HOST'
bash artifacts/remote_admin/luchen_elmap_onboarding/configure_luchen_ssh.sh 'ssh -p PORT USER@HOST'
```

本地检查 SSH 与 GPU：

```bash
bash artifacts/remote_admin/luchen_elmap_onboarding/check_luchen_ssh.sh
```

远端初始化基础环境：

```bash
ssh luchen-elmap 'bash -s' < artifacts/remote_admin/luchen_elmap_onboarding/remote_bootstrap_luchen_base.sh
```

上传并解压 NVIDIA 授权包：

```bash
scp IsaacGym_Preview_4_Package.tar.gz luchen-elmap:/workspace/
ssh luchen-elmap 'cd /workspace && tar -xzf IsaacGym_Preview_4_Package.tar.gz'
```

安装原仓库环境：

```bash
ssh luchen-elmap 'bash -s' < artifacts/remote_admin/luchen_elmap_onboarding/remote_setup_origin_elmap_isaacgym.sh
```

启动原仓库 viewer 检查：

```bash
ssh -t luchen-elmap 'bash /workspace/elmap-origin-viewer/remote_run_origin_viewer_check.sh'
```

GUI 需要潞晨云远程桌面、X11 或同类图形会话。如果 `scripts/test.py` 仍以
headless 模式运行，需要在远端临时检查 viewer/headless 参数，例如
`headless=False`。

### 潞晨云临时 noVNC 桌面

如果潞晨云实例只有 Jupyter，没有 `DISPLAY`，原仓库 Isaac Gym GUI 可以通过
Xvfb + x11vnc + noVNC 临时查看。端口只绑定远端 `127.0.0.1`，本机通过 SSH 隧道
访问。

安装：

```bash
ssh luchen-elmap 'apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends xvfb x11vnc novnc websockify fluxbox mesa-utils xterm'
```

远端启动：

```bash
ssh luchen-elmap 'bash -s' <<'REMOTE'
set -euo pipefail
mkdir -p /workspace/elmap-origin-viewer/logs
LOGDIR=/workspace/elmap-origin-viewer/logs
rm -f /tmp/.X1-lock
nohup Xvfb :1 -screen 0 1600x900x24 +extension GLX +render -noreset > "$LOGDIR/xvfb.log" 2>&1 &
DISPLAY=:1 nohup fluxbox > "$LOGDIR/fluxbox.log" 2>&1 &
DISPLAY=:1 nohup x11vnc -display :1 -localhost -forever -shared -nopw -rfbport 5901 > "$LOGDIR/x11vnc.log" 2>&1 &
nohup websockify --web=/usr/share/novnc 127.0.0.1:6080 127.0.0.1:5901 > "$LOGDIR/novnc.log" 2>&1 &
REMOTE
```

本机隧道：

```bash
ssh -N -L 6080:127.0.0.1:6080 luchen-elmap
```

浏览器打开：

```text
http://127.0.0.1:6080/vnc.html?host=127.0.0.1&port=6080&autoconnect=1
```

远端运行图形脚本前设置：

```bash
export DISPLAY=:1
```

该桌面使用 Xvfb/llvmpipe 显示 GUI，Physics 仍可使用 CUDA。它适合原仓库 Isaac
Gym viewer 参考检查；正式 Isaac Lab 256 证据仍使用项目规定的 WebRTC 证据流程。

### 原仓库 backpack viewer 事实

`scripts/test.py` 只是普通 Go1 启动检查，函数体调用 `config_go1(Cfg)`。真正的
backpack 训练入口是：

```text
scripts/train_exteroceptive_robust_icra_proposed.py
```

该脚本调用 `config_go1_backpack(Cfg)`，默认 `Cfg.env.num_envs = 4096`。训练脚本
将地形设置为 `20 x 10` 个 cells，每块 `5m x 5m`，并设置
`Cfg.terrain.center_robots = True` 与 `Cfg.terrain.center_span = 5`。可视化应看到
多只带橙色 backpack 的 Go1 分布在离散障碍地形上，而不是集中挤在同一个小地形里。
