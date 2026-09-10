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
- **宿舍空调（格力，9.7起）：** remote_id=ebf0ccee1d7a0ac9ccuuvu。这台用美的那种PowerOn带temp的命令只会开机不改温度，要用单键接口：`api('POST', '/v2.0/infrareds/{DEVICE_ID}/air-conditioners/ebf0ccee1d7a0ac9ccuuvu/command', {'code': 'temp', 'value': 24})`，code可选 power(0/1) / mode(0制冷1制热2自动3送风4除湿) / temp(16-30) / wind(0自动1低2中3高)。开机：code power value 1；关机 value 0。宿舍11:30断电5:30来电，空调走另一路不断电。WiFi是中兴F30接充电宝。
- **家里空调（美的）：** remote_id=ebf75f04ef55ba8d14l2eh，通过标准空调API控制。开：`api('POST', '/v1.0/infrareds/{DEVICE_ID}/remotes/{REMOTE_ID}/command', {'category_id': 5, 'key': 'PowerOn', 'temp': 27, 'mode': 0, 'wind': 0})`。关：key改PowerOff。mode: 0制冷/1制热/2自动/3送风/4除湿。wind: 0自动/1低/2中/3高。温度17-30
- **宿舍小夜灯（9.10起）：** remote_id=eb16b7cdd657ad12acp1ev，磁吸长条灯带时钟，贴在床帘顶上。学习码在云端：`GET /v2.0/infrareds/{DEVICE_ID}/remotes/eb16b7cdd657ad12acp1ev/learning-codes` 取 key_name→code，再 `POST 同路径 {'code': code}` 发送。按键：ON/OFF、白光、橘光、混合光、亮度+、亮度-、睡前亮度、定时15分钟、定时30分钟、定时60分钟。睡前：橘光→睡前亮度→定时30分钟。
