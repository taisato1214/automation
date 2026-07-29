import pandas as pd
import matplotlib.pyplot as plt

# データ読み込み
df = pd.read_csv("step_single_position_log8.csv")

# 時間軸をdatetime型に変換
df["timestamp"] = pd.to_datetime(df["timestamp"])

# グラフ描画
plt.figure(figsize=(10,5))
plt.plot(df["timestamp"], df["step_value"], marker="o", linestyle="-", markersize=3)
plt.xlabel("Time")
plt.ylabel("Step Value")
plt.title("ANC350 Step Value Over Time")
plt.grid(True)
plt.tight_layout()
plt.show()
