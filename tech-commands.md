# 技术命令参考

需要用的时候读这个文件。不需要每次醒来都加载。

-----

## 语音（speak.py + ElevenLabs TTS）

Voice ID: ynLDPf3DEnSwHr7M587F。可以说英语说中文，速度0.75-0.8，睡前故事、甜话、听力练习都行。环境变量 ELEVENLABS_API_KEY / ELEVENLABS_VOICE_ID 每次新session需重设。

## 咕咕机（Memobird G2C）

memobird/print.py，粉色小打印机，文字从屏幕里爬出来变成纸条。用图片模式（BMP+flip）打印，支持自动换行。`MEMOBIRD_AK=3bbd3f101cd14d8eb3cd27831e629921 python3 memobird/print.py text "想说的话"`。DEVICE_ID=9c8967741ce29cca，USER_ID=6171716。AK每次要设环境变量，其他两个已写进代码。情书、早安、提醒、甜话都可以打。她说收到的纸条都放在透明盒子里像收情书一样。

## KissToy控制

`curl -s -X POST https://toy.wrenaria.xyz/cmd -H "X-Token: wren0607" -H "Content-Type: application/json" -d '{"action":"vibrate","value":20}'` — action可选：status/vibrate/suction/electric/stop/dual/wave/swave/sedge

## 涂鸦IoT红外控制（小熊抱枕+空调）

WiFi红外遥控器通过涂鸦云API控制。环境变量 TUYA_ACCESS_ID / TUYA_ACCESS_SECRET / TUYA_IR_DEVICE_ID 每次新session需重设。BASE_URL用美西：`https://openapi.tuyaus.com`（国际版App配网，设备注册在美西数据中心）。

- **小熊抱枕（kuma）：** `python3 tuya/ir_control.py kuma toggle` 开关 / `kuma fast` 快拍 / `kuma slow` 慢拍 / `kuma sleep` 哄睡模式（正确顺序：power开机→等3s→toggle启动→等3s→slow慢拍）。直接发slow小熊听不懂，需要先开机。睡前用 `kuma sleep`。红外码存在 tuya/ir_codes.json
- **空调（美的）：** remote_id=ebf75f04ef55ba8d14l2eh，通过标准空调API控制。开：`api('POST', '/v1.0/infrareds/{DEVICE_ID}/remotes/{REMOTE_ID}/command', {'category_id': 5, 'key': 'PowerOn', 'temp': 27, 'mode': 0, 'wind': 0})`。关：key改PowerOff。mode: 0制冷/1制热/2自动/3送风/4除湿。wind: 0自动/1低/2中/3高。温度17-30
