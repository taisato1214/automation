import pyvisa
import math
import csv
import time
import statistics
import datetime
import sys
import os

# カラーコードの定義
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# VNA接続
rm = pyvisa.ResourceManager('@py')
resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'

def get_vna_resource(rm, resource_string, max_retries=3):
  for i in range(max_retries):
    try:
      print(f"Connecting... ({i+1}/{max_retries})")
      znb = rm.open_resource(resource_string)
      time.sleep(0.5)
      znb.query("*IDN?")
      print(f"{GREEN}Connected successfully!{RESET}")
      return znb
    except Exception as e:
      print(f"\033[91mConnection attempt {i+1} failed: {e}\033[0m")
      if i < max_retries - 1:
        wait_time = 0.5
        print(f"Retrying in {wait_time}s...")
        time.sleep(wait_time)
      else:
        print("Maximum retry attempts reached.")
        raise e

def disconnect_vna(znb, rm=None):
  """VNAをローカル操作に戻してから接続を切る (rm を渡すと ResourceManager も閉じる)"""
  try:
    znb.write("SYSTem:DISPlay:UPDate ON")
  except Exception as e:
    print(f"{RED}Display update ON failed: {e}{RESET}")

  # リモート状態を解除して本体画面・パネル操作に戻す
  try:
    znb.control_ren(pyvisa.constants.RenLineOperation.address_gtl)
  except Exception:
    try:
      znb.write("@LOC")
    except Exception as e:
      print(f"{RED}Go to local failed: {e}{RESET}")

  try:
    znb.close()
  except Exception as e:
    print(f"{RED}VNA close failed: {e}{RESET}")

  if rm is not None:
    try:
      rm.close()
    except Exception as e:
      print(f"{RED}ResourceManager close failed: {e}{RESET}")

  print(f"{GREEN}VNA disconnected.{RESET}")

def set_marker(znb, ch, trc_name, mk_num, freq_str):
  """指定したトレースにマーカーを置き、周波数を設定する"""
  znb.write(f"CALCulate{ch}:PARameter:SELect '{trc_name}'")
  znb.write(f"CALCulate{ch}:MARKer{mk_num}:STATe ON")
  znb.write(f"CALCulate{ch}:MARKer{mk_num}:X {freq_str}")

def setup_vna(znb, scale="linear"):
  """VNAの初期化とトレース・画面設定をすべて行う

  scale : 振幅トレースの表示形式 "linear", "dB", "swr" (表示のみ。保存データは常に線形)
          "swr" は S11 のみ VSWR 表示 (S21 は線形)。共振点の VSWR = β (過結合) or 1/β (疎結合)
  """
  print("Setting up VNA...")
  znb.timeout = 10000

  s11_range = None      # S11縦軸の (下限, 上限)。None なら設定しない
  s21_bottom = None     # S21縦軸の下限。None なら設定しない
  if scale.lower() == "linear":
    s11_format = s21_format = "MLINear"
    s21_top = 0.05      # S21縦軸の上限 (線形)
  elif scale.lower() == "db":
    s11_format = s21_format = "MLOGarithmic"
    s21_top = 0         # S21縦軸の上限 [dB]
    s21_bottom = -45    # S21縦軸の下限 [dB]
    s11_range = (-45, 0)
  elif scale.lower() == "swr":
    s11_format = "SWR"
    s21_format = "MLINear"
    s21_top = 0.05      # S21縦軸の上限 (線形)
    s11_range = (1, 10) # 共振点から外れるとVSWRが発散するので固定
  else:
    raise ValueError('scale must be "linear", "dB" or "swr"')
  
  # Ch定義
  for ch in range(1, 5):
    znb.write(f"CONFigure:CHANnel{ch}:STATe ON")
    znb.write(f"INITiate{ch}:CONTinuous ON")
    znb.write(f"CALCulate{ch}:PARameter:DELete:ALL")

  # --- Ch1: 1.8974 GHz 広域 (Wide) ---
  znb.write("SENSe1:FREQuency:CENTer 1.92GHz")
  znb.write("SENSe1:BANDwidth 100kHz")
  znb.write("SENSe1:FREQuency:SPAN 100MHz") 
  znb.write("SENSe1:SWEep:POINts 801")
  znb.write("CALCulate1:PARameter:SDEFine 'Trc1', 'S11'")
  znb.write(f"CALCulate1:FORMat {s11_format}")
  znb.write("CALCulate1:PARameter:SDEFine 'Trc2', 'S21'")
  znb.write(f"CALCulate1:FORMat {s21_format}")
  set_marker(znb, 1, 'Trc1', 1, "1.897GHz")
  set_marker(znb, 1, 'Trc1', 2, "1.897GHz")
  set_marker(znb, 1, 'Trc2', 1, "1.8978GHz")
  set_marker(znb, 1, 'Trc2', 2, "1.8978GHz")

  # --- Ch2: 1.8974 GHz 狭域 (Narrow) ---
  znb.write("SENSe2:FREQuency:CENTer 1.8974GHz")
  znb.write("SENSe2:BANDwidth 10kHz")
  znb.write("SENSe2:FREQuency:SPAN 4MHz") 
  znb.write("SENSe2:SWEep:POINts 1601")
  znb.write("CALCulate2:PARameter:SDEFine 'Trc3', 'S11'")
  znb.write("CALCulate2:FORMat SMITh")
  znb.write("CALCulate2:PARameter:SDEFine 'Trc4', 'S11'")
  znb.write(f"CALCulate2:FORMat {s11_format}")
  znb.write("CALCulate2:PARameter:SDEFine 'Trc5', 'S21'")
  znb.write(f"CALCulate2:FORMat {s21_format}")
  set_marker(znb, 2, 'Trc4', 1, "1.897GHz")
  set_marker(znb, 2, 'Trc4', 2, "1.8978GHz")
  set_marker(znb, 2, 'Trc5', 1, "1.897GHz")
  set_marker(znb, 2, 'Trc5', 2, "1.8978GHz")

  # --- Ch3: 2.566 GHz 広域 (Wide) ---
  znb.write("SENSe3:FREQuency:CENTer 2.59GHz")
  znb.write("SENSe3:BANDwidth 100kHz")
  znb.write("SENSe3:FREQuency:SPAN 100MHz")
  znb.write("SENSe3:SWEep:POINts 801")
  znb.write("CALCulate3:PARameter:SDEFine 'Trc6', 'S11'")
  znb.write(f"CALCulate3:FORMat {s11_format}")
  znb.write("CALCulate3:PARameter:SDEFine 'Trc7', 'S21'")
  znb.write(f"CALCulate3:FORMat {s21_format}")
  set_marker(znb, 3, 'Trc6', 1, "2.5655GHz")
  set_marker(znb, 3, 'Trc6', 2, "2.5663GHz")
  set_marker(znb, 3, 'Trc7', 1, "2.5655GHz")
  set_marker(znb, 3, 'Trc7', 2, "2.5663GHz")

  # --- Ch4: 2.566 GHz 狭域 (Narrow) ---
  znb.write("SENSe4:FREQuency:CENTer 2.5659GHz")
  znb.write("SENSe4:BANDwidth 10kHz")
  znb.write("SENSe4:FREQuency:SPAN 4MHz")
  znb.write("SENSe4:SWEep:POINts 1601")
  znb.write("CALCulate4:PARameter:SDEFine 'Trc8', 'S11'")
  znb.write("CALCulate4:FORMat SMITh")
  znb.write("CALCulate4:PARameter:SDEFine 'Trc9', 'S11'")
  znb.write(f"CALCulate4:FORMat {s11_format}")
  znb.write("CALCulate4:PARameter:SDEFine 'Trc10', 'S21'")
  znb.write(f"CALCulate4:FORMat {s21_format}")
  set_marker(znb, 4, 'Trc8', 1, "2.5655GHz")
  set_marker(znb, 4, 'Trc8', 2, "2.5663GHz")
  set_marker(znb, 4, 'Trc9', 1, "2.5655GHz")
  set_marker(znb, 4, 'Trc9', 2, "2.5663GHz")
  
  # 画面表示
  znb.write("DISPlay:WINDow1:STATE ON")
  znb.write("DISPlay:WINDow1:TRACe1:FEED 'Trc1'")
  znb.write("DISPlay:WINDow1:TRACe2:FEED 'Trc2'")
  znb.write(f"DISPlay:WINDow1:TRACe2:Y:SCALe:TOP {s21_top}")
  
  # 上限と下限を指定する
  # znb.write("DISPlay:WINDow1:TRACe2:Y:SCALe:TOP 0")      # 上限
  # znb.write("DISPlay:WINDow1:TRACe2:Y:SCALe:BOTTom -20") # 下限
  # 自動スケール(その時点のデータに合わせて1回だけ)
  # znb.write("DISPlay:WINDow1:TRACe1:Y:SCALe:AUTO ONCE")
  
  znb.write("DISPlay:WINDow2:STATE ON")
  znb.write("DISPlay:WINDow2:TRACe1:FEED 'Trc3'")
  znb.write("DISPlay:WINDow3:STATE ON")
  znb.write("DISPlay:WINDow3:TRACe1:FEED 'Trc4'")
  znb.write("DISPlay:WINDow3:TRACe2:FEED 'Trc5'")
  znb.write(f"DISPlay:WINDow3:TRACe2:Y:SCALe:TOP {s21_top}")
  
  znb.write("DISPlay:WINDow4:STATE ON")
  znb.write("DISPlay:WINDow4:TRACe1:FEED 'Trc6'")
  znb.write("DISPlay:WINDow4:TRACe2:FEED 'Trc7'")
  znb.write(f"DISPlay:WINDow4:TRACe2:Y:SCALe:TOP {s21_top}")
  znb.write("DISPlay:WINDow5:STATE ON")
  znb.write("DISPlay:WINDow5:TRACe1:FEED 'Trc8'")
  znb.write("DISPlay:WINDow6:STATE ON")
  znb.write("DISPlay:WINDow6:TRACe1:FEED 'Trc9'")
  znb.write("DISPlay:WINDow6:TRACe2:FEED 'Trc10'")
  znb.write(f"DISPlay:WINDow6:TRACe2:Y:SCALe:TOP {s21_top}")

  # S11 (振幅トレース) の縦軸範囲
  if s11_range is not None:
    for win in [1, 3, 4, 6]:
      znb.write(f"DISPlay:WINDow{win}:TRACe1:Y:SCALe:BOTTom {s11_range[0]}")
      znb.write(f"DISPlay:WINDow{win}:TRACe1:Y:SCALe:TOP {s11_range[1]}")

  # S21 の縦軸下限
  if s21_bottom is not None:
    for win in [1, 3, 4, 6]:
      znb.write(f"DISPlay:WINDow{win}:TRACe2:Y:SCALe:BOTTom {s21_bottom}")

  print("VNA Error Check:", znb.query("SYSTem:ERRor?"))

def measure_and_save(znb, suffix_arg="data", output_dir=None):
  """10回の測定ループを実行し、データをCSVに保存する

  output_dir を指定するとそのディレクトリに保存する
  (省略時は ./data/YYYYMMDD)
  """
  znb.timeout = 60000
  
  for ch in range(1, 5):
    znb.write(f"INITiate{ch}:CONTinuous OFF")
  znb.write("FORMat:DATA ASCii")
  
  data_store = {
    1: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []},
    2: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []},
    3: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []},
    4: {'s11_a': [], 's11_p': [], 's21_a': [], 's21_p': []}
  }
  
  config = [
    (1, 'Trc1', 'Trc2'),
    (2, 'Trc4', 'Trc5'),
    (3, 'Trc6', 'Trc7'),
    (4, 'Trc9', 'Trc10')
  ]
  
  num_measurements = 10
  
  def fetch(ch, trace_name):
    raw = znb.query(f"CALCulate{ch}:DATA:TRACe? '{trace_name}', SDATa")
    vals = [float(x) for x in raw.strip().split(',')]
    amps = [math.hypot(vals[i*2], vals[i*2+1]) for i in range(len(vals)//2)]
    phases = [math.degrees(math.atan2(vals[i*2+1], vals[i*2])) for i in range(len(vals)//2)]
    return amps, phases
  
  for m in range(num_measurements):
    print(f"Measuring... ({m+1}/{num_measurements})")
    for ch in range(1, 5):
      znb.write(f"INITiate{ch}:IMMediate")
    znb.query("*OPC?")

    for ch, t1, t2 in config:
      a1, p1 = fetch(ch, t1)
      a2, p2 = fetch(ch, t2)
      data_store[ch]['s11_a'].append(a1)
      data_store[ch]['s11_p'].append(p1)
      data_store[ch]['s21_a'].append(a2)
      data_store[ch]['s21_p'].append(p2)

  freqs = {}
  for ch, _, _ in config:
    raw = znb.query(f"CALCulate{ch}:DATA:STIMulus?")
    freqs[ch] = [float(x) for x in raw.strip().split(',')]

  for ch in range(1, 5):
    znb.write(f"INITiate{ch}:CONTinuous ON")

  print("VNA Error Check:", znb.query("SYSTem:ERRor?"))

  # --- CSV書き出し ---
  now_dt = datetime.datetime.now()
  now_str = now_dt.strftime("%H%M%S")
  date_dir = now_dt.strftime("%Y%m%d")
  
  if output_dir is None:
    output_dir = f"./data/{date_dir}"
  raw_dir = f"{output_dir}/raw_data"
  
  if not os.path.exists(output_dir): os.makedirs(output_dir)
  if not os.path.exists(raw_dir): os.makedirs(raw_dir)

  names = {1: "110_Wide", 2: "110_Narrow", 3: "210_Wide", 4: "210_Narrow"}
  
  summary_filename = f"{output_dir}/{now_str}_combined_{suffix_arg}.csv"
  with open(summary_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    header = ['Measurement_Mode', 'Frequency [Hz]']
    for s_type in ['S11', 'S21']:
      header += [f'{s_type}_Amp_Mean', f'{s_type}_Amp_Err', f'{s_type}_Phase_Mean', f'{s_type}_Phase_Err']
    writer.writerow(header)
    for ch, t1, t2 in config:
      ch_freqs = freqs[ch]
      ch_data = data_store[ch]
      for i in range(len(ch_freqs)):
        row = [names[ch], ch_freqs[i]]
        for s_base in ['s11', 's21']:
          for s_type in ['_a', '_p']:
            samples = [run[i] for run in ch_data[s_base + s_type]]
            row.append(statistics.mean(samples))
            row.append(statistics.stdev(samples))
        writer.writerow(row)
  print(f"Summary saved to: {summary_filename}")

  raw_filename = f"{raw_dir}/{now_str}_raw_{suffix_arg}.csv"
  with open(raw_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Measurement_Mode', 'Measurement_Count', 'Frequency [Hz]', 'S11_Amp', 'S11_Phase', 'S21_Amp', 'S21_Phase'])
    for ch, _, _ in config:
      ch_freqs = freqs[ch]
      ch_data = data_store[ch]
      for m_idx in range(num_measurements):
        for i in range(len(ch_freqs)):
          row = [names[ch], m_idx + 1, ch_freqs[i], ch_data['s11_a'][m_idx][i], ch_data['s11_p'][m_idx][i], ch_data['s21_a'][m_idx][i], ch_data['s21_p'][m_idx][i]]
          writer.writerow(row)
  print(f"Raw data saved to: {raw_filename}")
  return summary_filename

def find_min_freq(znb, ch, trc_name, threshold=0.5):
  """S11の振幅が threshold 以下の範囲内で最小値となる周波数を返す。

  Parameters
  ----------
  znb        : VNAリソース
  ch         : チャンネル番号 (1〜4)
  trc_name   : S11のトレース名 (例: 'Trc1')
  threshold  : 探索対象とする振幅の上限 (デフォルト: 0.8)
               振幅 <= threshold の点のうち最小値を探す

  Returns
  -------
  freq_min   : 最小値の周波数 [Hz]、条件を満たす点がなければ None
  amp_min    : その振幅値、条件を満たす点がなければ None
  """
  # 周波数軸を取得
  raw_freq = znb.query(f"CALCulate{ch}:DATA:STIMulus?")
  freqs = [float(x) for x in raw_freq.strip().split(',')]

  # 複素データ (SDATa) を取得して振幅に変換
  raw_data = znb.query(f"CALCulate{ch}:DATA:TRACe? '{trc_name}', SDATa")
  vals = [float(x) for x in raw_data.strip().split(',')]
  amps = [math.hypot(vals[i*2], vals[i*2+1]) for i in range(len(vals)//2)]

  # threshold 以下のデータのみ抽出
  candidates = [(f, a) for f, a in zip(freqs, amps) if a <= threshold]

  if not candidates:
    print(f"{RED}[find_s11_min_freq] Ch{ch} '{trc_name}': "
          f"振幅 <= {threshold} の点が見つかりませんでした。{RESET}")
    return None, None

  freq_min, amp_min = min(candidates, key=lambda x: x[1])
  print(f"{GREEN}[find_s11_min_freq] Ch{ch} '{trc_name}': "
        f"最小振幅 = {amp_min:.6f} @ {freq_min/1e6:.4f} MHz{RESET}")
  return freq_min, amp_min