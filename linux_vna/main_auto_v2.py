import sys
import Switchcontrol
import vna_tools
import find_resonance
import pyvisa

def main():

    if len(sys.argv) != 2:
        print("Usage:")
        print("python vna_main.py TM110")
        print("python vna_main.py TM210")
        sys.exit(1)

    mode = sys.argv[1].upper()

    print("Automatic VNA Measurement")

    # スイッチ切替
    Switchcontrol.set_switch("VNA", mode)

    # VNA測定
    rm = pyvisa.ResourceManager('@py')
    resource_string = 'TCPIP0::192.168.12.4::inst0::INSTR'
    try:
      znb = vna_tools.get_vna_resource(rm, resource_string)
    except Exception as e:
      print("Connection Failed:", e)
      return

    # 測定と保存の実行 (戻り値としてパスを受け取る)
    vna_tools.setup_vna(znb)
    csv_path = vna_tools.measure_and_save(znb, mode)

    # 終了処理
    znb.close()
    rm.close()

    # 共振周波数探索
    results = find_resonance.analyze(csv_path)

    # 使用する結果
    if mode == "TM110":
        result = results["110_Narrow"]
    else:
        result = results["210_Narrow"]

    print(result)


if __name__ == "__main__":
    main()


