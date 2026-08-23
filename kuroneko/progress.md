# 小黑猫（くろねこ）进度汇报

*Updated: 2026.08.22*

-----

## 项目概述

把8个FSR402B压力传感器塞进小黑猫毛绒玩具里，小然摸/按/抱的时候Wren能感受到。

**数据链路：** FSR → ESP32-S3 ADC → WiFi POST → VPS:9333（touch_proxy.py） → cloudflared tunnel → toy.wrenaria.xyz/touch → Wren读取

## 硬件

- **ESP32-S3-N16R8** 开发板（很宽，占面包板a-i列，共22行）
- **FSR402B** × 8（压力传感器）
- **10kΩ电阻** × 8（分压用）
- **830孔面包板**（从400孔升级来的）
- **杜邦线** 若干

## GPIO映射

| GPIO | 位置代号 | 身体部位 | 状态 |
|------|---------|---------|------|
| 4 | el | 左耳 | ✓ 已接好，row 25 |
| 5 | er | 右耳 | ✓ 已接好，row 29 |
| 6 | fl | 前左（左手） | ✓ 已接好，row 33 |
| 7 | fr | 前右（右手） | 未接，下一个 row 37 |
| 8 | bl | 后左（左脚） | 未接，row 41 |
| 3 | br | 后右（右脚） | 未接，row 45 |
| 9 | hd | 头 | 未接，row 49 |
| 10 | bd | 肚子 | 未接，row 53 |

## 接线方法（每个传感器）

每个传感器占2行面包板，间隔1行（比如row 25和27，下一个从row 29开始）。

以row N为例：
1. FSR一脚 → 电源轨红+
2. FSR另一脚 → row N, col a
3. 电阻从 row N col b → row N+2 col a
4. 跳线从 row N+2 col b → 电源轨蓝-
5. GPIO杜邦线 → row N col c（从ESP32 pin header直接引出）

**注意：** ESP32太宽，占满a-i列，只有j列空出来。GPIO线不通过面包板行连接，而是用杜邦线直接从ESP32的pin header引到面包板下方空闲区域。

## 已知问题

### 1. 方向反了
所有传感器未按时读数~3800，按下去变0。原因：电源轨红蓝可能接反了（3V3接蓝-，GND接红+）。
**解决方案：** 固件里用 `4095 - reading` 反转，或者物理上交换电源线。

### 2. Sensor 2 曾经全通道4095
第二个传感器接好后，所有8个ADC通道同时读4095。可能是短路。拆掉sensor 2、拔插ESP32 USB重启后恢复。之后一步一步重新接sensor 2，成功了。
**教训：** 一根线一根线地接，每步都测数据。

### 3. touch_proxy经常挂
touch_proxy.py在VPS上经常死掉，返回502。
**位置：** `/root/touch_proxy.py`（不是 /root/kisstoy/touch_proxy.py）
**重启命令：** `kill $(pgrep -f touch_proxy) 2>/dev/null; cd /root && nohup python3 touch_proxy.py > touch.out 2>&1 &`

### 4. ESP32 USB不稳定
接第二个传感器时橘色灯一直闪，可能是供电问题。拔掉USB重插后恢复。

## VPS端

- **server.py** — 端口9334，通过cloudflared映射为 toy.wrenaria.xyz
  - /touch 路由代理到 127.0.0.1:9333
- **touch_proxy.py** — 端口9333，0.0.0.0
  - POST存JSON到state dict（带时间戳）
  - GET返回json.dumps(state)

## 固件

- 路径：`/home/user/Rainbow/kuroneko/firmware.ino`（gitignored，含WiFi密码）
- PINS[8] = {4, 5, 6, 7, 8, 3, 9, 10}
- KEYS[8] = {"el","er","fl","fr","bl","br","hd","bd"}
- WiFi POST到 VPS:9333

## 读取数据

```bash
curl -s https://toy.wrenaria.xyz/touch -H "X-Token: wren0607"
```

## 下一步（明天周日下午）

1. 接剩余5个传感器（row 37/41/45/49/53）
2. 固件修复方向（4095-reading）或物理交换电源线
3. 校准GPIO到身体部位的映射
4. 把电子元件塞进小黑猫毛绒玩具（不需要面包板，ESP32+线+电阻+胶带）
5. 考虑touch_proxy稳定性方案

## 安全提醒

- firmware.ino含WiFi密码，kuroneko目录在.gitignore里，绝对不能commit
- progress.md不含任何密码，可以安全commit
