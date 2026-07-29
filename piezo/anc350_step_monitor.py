# anc350_step_monitor_single_position.py
import time
import csv
import statistics
from pyanc350.v2 import Positioner

# ==== 設定 ====
CHANNEL = 1          # モニタするチャンネル
TARGET_POSITION = 4_000_000  # 測定位置
INTERVAL = 1.0       # 測定間隔 [秒]
DURATION = 60        # 測定時間 [秒]
OUTPUT_CSV = "step_single_position_log.csv"

# ==== 接続 ====
anc = Positioner()
anc.connect()
print(f"Monitoring ANC350 step drift at position {TARGET_POSITION} (channel {CHANNEL})")

# ==== CSV準備 ====
with open(OUTPUT_CSV, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["time_sec", "step_value"])

# ==== 移動 & 測定 ====
print(f"\nMoving to position {TARGET_POSITION} ...")
anc.moveAbsolute(CHANNEL, TARGET_POSITION)
time.sleep(1)  # 移動後の安定待ち

data = []
start_time = time.time()
while (time.time() - start_time) < DURATION:
    try:
        step = anc.getPosition(CHANNEL)
    except Exception as e:
        print(f"Error reading position: {e}")
        step = None
    elapsed = time.time() - start_time
    if step is not None:
        data.append(step)
        with open(OUTPUT_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([elapsed, step])
    time.sleep(INTERVAL)

anc.close()

# ==== 統計評価 ====
if data:
    mean_val = statistics.mean(data)
    stdev_val = statistics.stdev(data) if len(data) > 1 else 0
    max_val = max(data)
    min_val = min(data)
    drift_range = max_val - min_val
    print("\n===== Step Drift Evaluation =====")
    print(f"Total duration       : {DURATION} s")
    print(f"Samples acquired     : {len(data)}")
    print(f"Mean step value      : {mean_val:.2f}")
    print(f"Standard deviation   : {stdev_val:.2f}")
    print(f"Maximum step value   : {max_val:.2f}")
    print(f"Minimum step value   : {min_val:.2f}")
    print(f"Max drift (Δmax-min) : {drift_range:.2f}")
    print(f"Data saved to        : {OUTPUT_CSV}")
    print("================================\n")
else:
    print("⚠ No valid data recorded.")
