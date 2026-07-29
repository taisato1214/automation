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
import matplotlib.pyplot as plt

# Paths
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "20260722", "Run4.txt")
FIG_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Load data
rows = []
with open(DATA_PATH, newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append({
            "Step_Count": int(r["Step_Count"]),
            "Position": float(r["Position"]),
            "Resonance_f0_GHz": float(r["Resonance_f0_GHz"]),
        })

if len(rows) == 0:
    raise RuntimeError("Run4.txt contains no data.")

def plot_columns(x_key, y_key, label_x, label_y, filename):
    plt.figure()
    x = [row[x_key] for row in rows]
    y = [row[y_key] for row in rows]
    plt.scatter(x, y, color="tab:blue")
    plt.title(f"{label_x} vs {label_y}")
    plt.xlabel(label_x)
    plt.ylabel(label_y)
    plt.grid(True, which="both", ls="--", lw=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename))
    plt.show()
    plt.close()

# Define column pairs to plot
column_pairs = [
    ("Step_Count", "Position", "Step Count", "Position", "run4_stepcount_vs_position.png"),
    ("Step_Count", "Resonance_f0_GHz", "Step Count", "Resonance (GHz)", "run4_stepcount_vs_resonance.png"),
    ("Position", "Resonance_f0_GHz", "Position", "Resonance (GHz)", "run4_position_vs_resonance.png"),
]

for x_key, y_key, label_x, label_y, fname in column_pairs:
    plot_columns(x_key, y_key, label_x, label_y, fname)

print("Column comparison plots saved in", FIG_DIR)
