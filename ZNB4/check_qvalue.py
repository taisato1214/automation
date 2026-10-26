import pyvisa
import sys
import math
import vna_tools

# Q値を計算する狭域チャンネル: (ch, S11振幅トレース名, 表示名)
Q_CONFIG = [
  (2, 'Trc4', "110_Narrow"),
  (4, 'Trc9', "210_Narrow"),
]

def fetch_s11(znb, ch, trc_name):
  """周波数軸と S11 の線形振幅を取得する"""
  raw_freq = znb.query(f"CALCulate{ch}:DATA:STIMulus?")
  freqs = [float(x) for x in raw_freq.strip().split(',')]
  raw_data = znb.query(f"CALCulate{ch}:DATA:TRACe? '{trc_name}', SDATa")
  vals = [float(x) for x in raw_data.strip().split(',')]
  amps = [math.hypot(vals[i*2], vals[i*2+1]) for i in range(len(vals)//2)]
  return freqs, amps

def crossing(freqs, pow2, i_from, step, level):
  """i_from から step 方向に |S11|^2 が level を超える点を線形補間で探す"""
  i = i_from
  while 0 <= i + step < len(freqs):
    j = i + step
    if pow2[j] >= level:
      # i (<level) と j (>=level) の間を線形補間
      t = (level - pow2[i]) / (pow2[j] - pow2[i])
      return freqs[i] + t * (freqs[j] - freqs[i])
    i = j
  return None

def calc_qvalue(znb, ch, trc_name, threshold=0.5):
  """find_min_freq で共振点を求め、反射法 (S11) で Q値を計算する

  負荷Q  : Q_L = f0 / Δf
           Δf は |S11|^2 = (1 + |S11(f0)|^2) / 2 となる2点間の幅 (半値幅)
  結合度 : β = (1 - Γ0) / (1 + Γ0) (疎結合), (1 + Γ0) / (1 - Γ0) (過結合)
  無負荷Q: Q_0 = Q_L * (1 + β)
  """
  f0, gamma0 = vna_tools.find_min_freq(znb, ch, trc_name, threshold)
  if f0 is None:
    return None

  freqs, amps = fetch_s11(znb, ch, trc_name)
  pow2 = [a**2 for a in amps]
  i0 = freqs.index(f0)
  level = (1 + gamma0**2) / 2

  f_low = crossing(freqs, pow2, i0, -1, level)
  f_high = crossing(freqs, pow2, i0, +1, level)
  if f_low is None or f_high is None:
    print(f"{vna_tools.RED}Ch{ch} '{trc_name}': 半値幅が掃引範囲内に収まっていません。{vna_tools.RESET}")
    return None

  bw = f_high - f_low
  q_l = f0 / bw
  beta_under = (1 - gamma0) / (1 + gamma0)
  beta_over = (1 + gamma0) / (1 - gamma0)
  return {
    'f0': f0, 'gamma0': gamma0, 'bw': bw, 'q_l': q_l,
    'beta_under': beta_under, 'q0_under': q_l * (1 + beta_under),
    'beta_over': beta_over, 'q0_over': q_l * (1 + beta_over),
  }

def main():
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'

  # 1. 接続
  try:
    znb = vna_tools.get_vna_resource(rm, resource_string)
  except Exception as e:
    print("Connection Failed:", e)
    return

  # 2. セットアップ実行
  vna_tools.setup_vna(znb)

  # 探索する振幅の上限 (省略時 0.5)
  threshold = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5

  # 3. 1回掃引してからデータを読む
  znb.timeout = 60000
  for ch, _, _ in Q_CONFIG:
    znb.write(f"INITiate{ch}:CONTinuous OFF")
  znb.write("FORMat:DATA ASCii")
  for ch, _, _ in Q_CONFIG:
    znb.write(f"INITiate{ch}:IMMediate")
  znb.query("*OPC?")

  # 4. Q値計算
  for ch, trc_name, name in Q_CONFIG:
    r = calc_qvalue(znb, ch, trc_name, threshold)
    if r is None:
      continue
    print(f"--- {name} (Ch{ch}, {trc_name}) ---")
    print(f"  f0       = {r['f0']/1e9:.6f} GHz")
    print(f"  |S11(f0)| = {r['gamma0']:.4f}")
    print(f"  Δf       = {r['bw']/1e3:.2f} kHz")
    print(f"  Q_L      = {r['q_l']:.1f}")
    print(f"  疎結合: β = {r['beta_under']:.3f}, Q_0 = {r['q0_under']:.1f}")
    print(f"  過結合: β = {r['beta_over']:.3f}, Q_0 = {r['q0_over']:.1f}")

  for ch, _, _ in Q_CONFIG:
    znb.write(f"INITiate{ch}:CONTinuous ON")

  # 5. 終了処理
  vna_tools.disconnect_vna(znb, rm)

if __name__ == "__main__":
  main()
