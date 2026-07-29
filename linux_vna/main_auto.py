import sys

import Switchcontrol
import vna_tools
import find_resonance


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
    csv_path = vna_tools.run_measurement(mode)

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


