#!/usr/bin/env python3
"""Plot Run#.txt data with Forward/Backward separation and error bars."""

import csv
import os
import sys

import matplotlib.pyplot as plt
import numpy as np


BASE_DIR = os.path.abspath(os.path.dirname(__file__))

if len(sys.argv) > 1:
    DATA_PATH = os.path.abspath(sys.argv[1])
else:
    DATA_PATH = os.path.join(BASE_DIR, "data", "20261005", "Run1.txt")

FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


def load_rows(path):
    rows = []

    with open(path, newline="", encoding="utf-8-sig") as file:
        lines = [line for line in file if line.strip() and not line.lstrip().startswith("#")]
        reader = csv.DictReader(lines)

        required = {"Step_Count", "Resonance_f0_GHz"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise RuntimeError(f"Missing columns: {', '.join(sorted(missing))}")

        for row in reader:
            step_count = int(row["Step_Count"])
            sstep = float(row["Sstep"]) if row.get("Sstep") else 1.0

            if row.get("Position1_Mean"):
                position = float(row["Position1_Mean"])
                position_error = float(row.get("Position1_Err") or 0.0)
            elif row.get("Position"):
                position = float(row["Position"])
                position_error = 0.0
            else:
                raise RuntimeError("Position1_Mean or Position column is missing")

            rows.append(
                {
                    "Step_Count": step_count,
                    "Sstep": sstep,
                    "Total_Steps": step_count * sstep,
                    "Position": position,
                    "Position_Err": position_error,
                    "Resonance_f0_GHz": float(row["Resonance_f0_GHz"]),
                    "Direction": (row.get("Direction") or "F").strip().upper(),
                }
            )

    if not rows:
        raise RuntimeError(f"{path} contains no data.")
    return rows


rows = load_rows(DATA_PATH)
has_direction = {row["Direction"] for row in rows} >= {"F", "B"}


def plot_columns(x_key, y_key, label_x, label_y, filename,
                 x_error_key=None, y_error_key=None):
    fig, ax = plt.subplots(figsize=(7, 5))

    groups = [("F", "tab:blue", "o", "Forward (F)"),
              ("B", "tab:orange", "s", "Backward (B)")]

    if has_direction:
        plot_groups = groups
    else:
        plot_groups = [(None, "tab:blue", "o", "Data")]

    for direction, color, marker, label in plot_groups:
        selected = (
            [row for row in rows if row["Direction"] == direction]
            if direction is not None else rows
        )
        if not selected:
            continue

        x = np.asarray([row[x_key] for row in selected], dtype=float)
        y = np.asarray([row[y_key] for row in selected], dtype=float)

        xerr = None
        yerr = None
        if x_error_key is not None:
            xerr = np.asarray([row[x_error_key] for row in selected], dtype=float)
        if y_error_key is not None:
            yerr = np.asarray([row[y_error_key] for row in selected], dtype=float)

        ax.errorbar(
            x,
            y,
            xerr=xerr,
            yerr=yerr,
            fmt=marker,
            color=color,
            ecolor=color,
            elinewidth=1,
            capsize=3,
            markersize=5,
            alpha=0.85,
            label=label,
        )

    ax.set_title(f"{label_x} vs {label_y}")
    ax.set_xlabel(label_x)
    ax.set_ylabel(label_y)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    ax.legend()
    fig.tight_layout()

    save_path = os.path.join(FIG_DIR, filename)
    fig.savefig(save_path, dpi=150)
    return fig


# Position1_Err をY方向のエラーとして表示
plot_columns(
    "Total_Steps",
    "Position",
    "Total Steps [Step Number]",
    "Position [V]",
    "stepcount_vs_position.png",
    y_error_key="Position_Err",
)

# 共振周波数のエラー列がないため、エラーバーなし
plot_columns(
    "Total_Steps",
    "Resonance_f0_GHz",
    "Total Steps [Step Number]",
    "Resonance [GHz]",
    "stepcount_vs_resonance.png",
)

# Position1_Err をX方向のエラーとして表示
plot_columns(
    "Position",
    "Resonance_f0_GHz",
    "Position [V]",
    "Resonance [GHz]",
    "position_vs_resonance.png",
    x_error_key="Position_Err",
)

print(f"Column comparison plots saved in {FIG_DIR}")
print("Close the plot windows to finish.")
plt.show()
