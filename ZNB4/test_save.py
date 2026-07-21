import pyvisa
import math
import csv
import time

def get_vna_resource(rm, resource_string, max_retries=3):
  """接続を試行し、成功したらリソースを返す関数"""
  for i in range(max_retries):
    try:
      print(f"接続試行中... ({i+1}/{max_retries}回目)")
      znb = rm.open_resource(resource_string)
      time.sleep(0.5)
      znb.query("*IDN?")
      print("接続成功！")
      return znb
    except Exception as e:
      print(f"{i+1}回目の接続に失敗しました: {e}")
      if i < max_retries - 1:
        wait_time = 0.5
        print(f"{wait_time}秒後にリトライします...")
        time.sleep(wait_time)
      else:
        print("最大リトライ回数に達しました。")
        raise e

def main():
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
  
  try:
    znb = get_vna_resource(rm, resource_string)
  except Exception as e:
    print("接続エラー:", e)
    return
    
  znb.timeout = 10000
  
  # 1. 測定モード設定
  znb.write("INITiate:CONTinuous OFF")
  
  # 2. トレース定義（全部消してから作成）
  znb.write("CALCulate1:PARameter:DELete:ALL")
  znb.write("CALCulate1:PARameter:SDEFine 'Trc1', 'S11'")
  znb.write("CALCulate1:PARameter:SDEFine 'Trc2', 'S21'")
  
  # 3. 画面表示 (Window1にTrc1, Window2にTrc2)
  znb.write("DISPlay:WINDow1:STATE ON")
  znb.write("DISPlay:WINDow1:TRACe1:FEED 'Trc1'")
  znb.write("DISPlay:WINDow2:STATE ON")
  znb.write("DISPlay:WINDow2:TRACe1:FEED 'Trc2'") # Window2の「1番目のトレース」としてTrc2を割り当て
  
  znb.write("FORMat:DATA ASCii")
  
  print("測定中...")
  znb.query("INITiate:IMMediate; *OPC?")
  
  print("データ転送中...")
  znb.write("CALCulate1:PARameter:SELect 'Trc1'")
  s11_data_str = znb.query("CALCulate1:DATA? SDATa")
  
  znb.write("CALCulate1:PARameter:SELect 'Trc2'")
  s21_data_str = znb.query("CALCulate1:DATA? SDATa")
  
  znb.close()
  rm.close()

  # --- データ処理 ---
  def parse_to_lists(data_str):
    values = [float(x) for x in data_str.strip().split(',')]
    amps = []
    phases = []
    for i in range(len(values) // 2):
      re, im = values[i*2], values[i*2+1]
      amps.append(math.hypot(re, im))
      phases.append(math.degrees(math.atan2(im, re)))
    return amps, phases

  s11_amp, s11_phase = parse_to_lists(s11_data_str)
  s21_amp, s21_phase = parse_to_lists(s21_data_str)

  csv_filename = 'vna_data.csv'
  with open(csv_filename, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Point', 'S11_Amp', 'S11_Phase', 'S21_Amp', 'S21_Phase'])
    for i in range(len(s11_amp)):
      writer.writerow([i + 1, s11_amp[i], s11_phase[i], s21_amp[i], s21_phase[i]])
      
  print(f"{csv_filename} に保存完了！")

if __name__ == "__main__":
  main()