# 60 秒视频交付踩坑

## 历史 bridge 路径被重新注入

native RViz driver 在 conda 激活后把 `PYTHONPATH` 重设为历史 `RUN_ROOT`
下的 bridge，导致同步的新 bridge 没有被 continuity postprocessor 使用。
统一改为 `BRIDGE_ROOT`，并增加静态回归测试，禁止历史表达式重新出现。

## 附着 SSH 不适合长链包装

`dryrun01` 的仿真和主要采集已完成，但用户继续交互后附着通道关闭，外层
driver 在终点验证和视频包装前被终止。以后此类慢墙钟长链使用脱离会话执行，
状态以独立 PID、日志和 exit 文件读取；失败 run 原样保留。

## 10 MB 预算要同时约束体积和画质

60 秒 1920x540 两遍编码虽只有 9,155,709 bytes，但 SSIM 0.939357，不能因
体积达标就交付。保留该 FAIL，使用新文件名生成 1280x360 版本；后者
9,176,726 bytes、SSIM 0.964990，并通过完整解码、帧/时长和人工抽检。
