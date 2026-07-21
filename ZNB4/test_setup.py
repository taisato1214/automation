import pyvisa
import time

# カラーコードの定義
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

def get_vna_resource(rm, resource_string, max_retries=3):
  """接続をn回試行し、成功したらリソースを返す関数"""
  for i in range(max_retries):
    try:
      print(f"Connecting... ({i+1}/{max_retries})")
      znb = rm.open_resource(resource_string)
      time.sleep(0.5)
      znb.query("*IDN?")
      print(f"{GREEN}Connected successfully!{RESET}")
      return znb
    except Exception as e:
      # エラーメッセージ \033[91m が赤色開始、\033[0m が色リセット
      print(f"{RED}Connection attempt {i+1} failed: {e}{RESET}")
      if i < max_retries - 1:
        wait_time = 0.5
        print(f"Retrying in {wait_time}s...")
        time.sleep(wait_time)
      else:
        print("Maximum retry attempts reached.")
        raise e

def set_marker(znb, ch, trc_name, mk_num, freq_str):
  """指定したトレースにマーカーを置き、周波数を設定する"""
  # 1. トレースをアクティブにする
  znb.write(f"CALCulate{ch}:PARameter:SELect '{trc_name}'")
  # 2. マーカーをONにする
  znb.write(f"CALCulate{ch}:MARKer{mk_num}:STATe ON")
  # 3. 周波数を設定する (例: "1.8974GHz")
  znb.write(f"CALCulate{ch}:MARKer{mk_num}:X {freq_str}")
  
  # 確認用：マーカーの値を読み取る (必要あれば)
  # val = znb.query(f"CALCulate{ch}:MARKer{mk_num}:Y?")
  # print(f"Marker {mk_num} at {freq_str}: {val}")

def main():
  rm = pyvisa.ResourceManager('@py')
  resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
  
  try:
    znb = get_vna_resource(rm, resource_string)
  except Exception as e:
    print("Connection Error:", e)
    return
    
  znb.timeout = 10000
  
  # Ch定義
  znb.write("CONFigure:CHANnel1:STATe ON")
  znb.write("CONFigure:CHANnel2:STATe ON")
  znb.write("CONFigure:CHANnel3:STATe ON")
  znb.write("CONFigure:CHANnel4:STATe ON")

  for ch in range(1, 5):
    znb.write(f"INITiate{ch}:CONTinuous ON")

  # トレース定義（全部消してから作成）
  znb.write("CALCulate1:PARameter:DELete:ALL")
  znb.write("CALCulate2:PARameter:DELete:ALL")
  znb.write("CALCulate3:PARameter:DELete:ALL")
  znb.write("CALCulate4:PARameter:DELete:ALL")

  # --- Ch1: 1.8974 GHz 広域 (Wide) ---
  znb.write("SENSe1:FREQuency:CENTer 1.92GHz")
  znb.write("SENSe1:BANDwidth 100kHz")
  znb.write("SENSe1:FREQuency:SPAN 100MHz") 
  znb.write("SENSe1:SWEep:POINts 801")
  znb.write("CALCulate1:PARameter:SDEFine 'Trc1', 'S11'")
  znb.write("CALCulate1:FORMat MLINear")
  znb.write("CALCulate1:PARameter:SDEFine 'Trc2', 'S21'")
  znb.write("CALCulate1:FORMat MLINear")
  set_marker(znb, 1, 'Trc1', 1, "1.897GHz")
  set_marker(znb, 1, 'Trc1', 2, "1.897GHz")
  set_marker(znb, 1, 'Trc2', 1, "1.8978GHz")
  set_marker(znb, 1, 'Trc2', 2, "1.8978GHz")
  # znb.write("CALCulate1:PARameter:SDEFine 'Trc3', 'S11'")
  # znb.write("CALCulate1:FORMat SMITh")

  # --- Ch2: 1.8974 GHz 狭域 (Narrow) ---
  znb.write("SENSe2:FREQuency:CENTer 1.8974GHz")
  znb.write("SENSe2:BANDwidth 10kHz")
  znb.write("SENSe2:FREQuency:SPAN 4MHz") 
  znb.write("SENSe2:SWEep:POINts 1601")
  znb.write("CALCulate2:PARameter:SDEFine 'Trc3', 'S11'")
  znb.write("CALCulate2:FORMat SMITh")
  znb.write("CALCulate2:PARameter:SDEFine 'Trc4', 'S11'")
  znb.write("CALCulate2:FORMat MLINear")
  znb.write("CALCulate2:PARameter:SDEFine 'Trc5', 'S21'")
  znb.write("CALCulate2:FORMat MLINear")
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
  znb.write("CALCulate3:FORMat MLINear")
  znb.write("CALCulate3:PARameter:SDEFine 'Trc7', 'S21'")
  znb.write("CALCulate3:FORMat MLINear")
  set_marker(znb, 3, 'Trc6', 1, "2.5655GHz")
  set_marker(znb, 3, 'Trc6', 2, "2.5663GHz")
  set_marker(znb, 3, 'Trc7', 1, "2.5655GHz")
  set_marker(znb, 3, 'Trc7', 2, "2.5663GHz")
  # znb.write("CALCulate3:PARameter:SDEFine 'Trc8', 'S11'")
  # znb.write("CALCulate3:FORMat SMITh")

  # --- Ch4: 2.566 GHz 狭域 (Narrow) ---
  znb.write("SENSe4:FREQuency:CENTer 2.5659GHz")
  znb.write("SENSe4:BANDwidth 10kHz")
  znb.write("SENSe4:FREQuency:SPAN 4MHz")
  znb.write("SENSe4:SWEep:POINts 1601")
  znb.write("CALCulate4:PARameter:SDEFine 'Trc8', 'S11'")
  znb.write("CALCulate4:FORMat SMITh")
  znb.write("CALCulate4:PARameter:SDEFine 'Trc9', 'S11'")
  znb.write("CALCulate4:FORMat MLINear")
  znb.write("CALCulate4:PARameter:SDEFine 'Trc10', 'S21'")
  znb.write("CALCulate4:FORMat MLINear")
  set_marker(znb, 4, 'Trc8', 1, "2.5655GHz")
  set_marker(znb, 4, 'Trc8', 2, "2.5663GHz")
  set_marker(znb, 4, 'Trc9', 1, "2.5655GHz")
  set_marker(znb, 4, 'Trc9', 2, "2.5663GHz")
  
  # 3. 画面表示 (8画面または重ね書きで整理)
  # 1.8974G 広域 Window1
  znb.write("DISPlay:WINDow1:STATE ON")
  znb.write("DISPlay:WINDow1:TRACe1:FEED 'Trc1'")
  znb.write("DISPlay:WINDow1:TRACe2:FEED 'Trc2'")
  znb.write("DISPlay:WINDow1:TRACe2:Y:SCALe:TOP 0.05")

  # 1.8974G 広域 Window2
  znb.write("DISPlay:WINDow2:STATE ON")
  znb.write("DISPlay:WINDow2:TRACe1:FEED 'Trc3'")

  # 1.8974G 狭域 Window3
  znb.write("DISPlay:WINDow3:STATE ON")
  znb.write("DISPlay:WINDow3:TRACe1:FEED 'Trc4'")
  znb.write("DISPlay:WINDow3:TRACe2:FEED 'Trc5'")
  znb.write("DISPlay:WINDow3:TRACe2:Y:SCALe:TOP 0.05")

  # 2.566G 広域 Window4
  znb.write("DISPlay:WINDow4:STATE ON")
  znb.write("DISPlay:WINDow4:TRACe1:FEED 'Trc6'")
  znb.write("DISPlay:WINDow4:TRACe2:FEED 'Trc7'")
  znb.write("DISPlay:WINDow4:TRACe2:Y:SCALe:TOP 0.05")

  # 2.566G 広域 Window5
  znb.write("DISPlay:WINDow5:STATE ON")
  znb.write("DISPlay:WINDow5:TRACe1:FEED 'Trc8'")

  # 2.566G Window6
  znb.write("DISPlay:WINDow6:STATE ON")
  znb.write("DISPlay:WINDow6:TRACe1:FEED 'Trc9'")
  znb.write("DISPlay:WINDow6:TRACe2:FEED 'Trc10'")
  znb.write("DISPlay:WINDow6:TRACe2:Y:SCALe:TOP 0.05")

  print("VNA Error Check:", znb.query("SYSTem:ERRor?"))
  
  znb.close()
  rm.close()

if __name__ == "__main__":
  main()