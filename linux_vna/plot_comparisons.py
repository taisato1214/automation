#!/usr/bin/env python3
"""Plot comparisons of rows in Run4.txt.

This script reads the Run4.txt CSV file located at
`data/20260722/Run4.txt` and creates three scatter plots comparing:
1. Step_Count vs Position
2. Step_Count vs Resonance_f0_GHz
3. Position vs Resonance_f0_GHz

Each plot shows Position (x‑axis) vs Resonance_f0_GHz (y‑axis) for the two rows.
The figures are saved as PNG files in the `figures/` directory.
"""

import csv
import os
import sys
import matplotlib.pyplot as plt

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# 引数があればそのファイル、なければデフォルトのRun4.txt
if len(sys.argv) > 1:
    DATA_PATH = os.path.abspath(sys.argv[1])
else:
    DATA_PATH = os.path.join(BASE_DIR, "data", "20261005", "Run1.txt")

FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Load data
rows = []
with open(DATA_PATH, newline="", encoding="utf-8") as f:
    # '#' で始まるコメント行をスキップしてDictReaderに渡す
    lines = [line for line in f if not line.strip().startswith("#")]
    reader = csv.DictReader(lines)
    for r in reader:
        # Step_Count
        step_count = int(r["Step_Count"])
        # Sstep (新形式にあれば取得、なければ 1)
        sstep = int(r["Sstep"]) if "Sstep" in r and r["Sstep"] else 1
        total_steps = step_count * sstep

        # Position (新形式: Position1_Mean、旧形式: Position)
        if "Position1_Mean" in r:
            pos = float(r["Position1_Mean"])
            pos_err = float(r["Position1_Err"]) if "Position1_Err" in r else 0.0
        elif "Position" in r:
            pos = float(r["Position"])
            pos_err = 0.0
        else:
            pos = 0.0
            pos_err = 0.0

        # Resonance_f0_GHz
        f0 = float(r["Resonance_f0_GHz"])

        # Direction (F: Forward, B: Backward, 旧形式なら "F")
        direction = r.get("Direction", "F").strip()

        rows.append({
            "Step_Count": step_count,
            "Sstep": sstep,
            "Total_Steps": total_steps,
            "Position": pos,
            "Position_Err": pos_err,
            "Resonance_f0_GHz": f0,
            "Direction": direction,
        })

if len(rows) == 0:
    raise RuntimeError(f"{DATA_PATH} contains no data.")

has_direction = any(r["Direction"] in ("F", "B") for r in rows) and len(set(r["Direction"] for r in rows)) > 1

def plot_columns(x_key, y_key, label_x, label_y, filename):
    plt.figure(figsize=(7, 5))
    if has_direction:
        f_rows = [r for r in rows if r["Direction"] == "F"]
        b_rows = [r for r in rows if r["Direction"] == "B"]
        if f_rows:
            plt.scatter([r[x_key] for r in f_rows], [r[y_key] for r in f_rows], color="tab:blue", label="Forward (F)", alpha=0.8)
        if b_rows:
            plt.scatter([r[x_key] for r in b_rows], [r[y_key] for r in b_rows], color="tab:orange", marker="s", label="Backward (B)", alpha=0.8)
        plt.legend()
    else:
        x = [row[x_key] for row in rows]
        y = [row[y_key] for row in rows]
        plt.scatter(x, y, color="tab:blue", alpha=0.8)

    plt.title(f"{label_x} vs {label_y}")
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.grid(True, which="both", ls="--", lw=0.5)
    plt.tight_layout()
    save_path = os.path.join(FIG_DIR, filename)
    plt.savefig(save_path)
    plt.show()

# Define column pairs to plot (Step Count横軸はsstepを掛けたTotal_Steps)
column_pairs = [
    ("Total_Steps", "Position", "Total Steps (Step_Count * sstep)", "Position (V or m)", "stepcount_vs_position.png"),
    ("Total_Steps", "Resonance_f0_GHz", "Total Steps (Step_Count * sstep)", "Resonance (GHz)", "stepcount_vs_resonance.png"),
    ("Position", "Resonance_f0_GHz", "Position (V or m)", "Resonance (GHz)", "position_vs_resonance.png"),
]

for x_key, y_key, label_x, label_y, fname in column_pairs:
    plot_columns(x_key, y_key, label_x, label_y, fname)

print("Column comparison plots saved in", FIG_DIR)

