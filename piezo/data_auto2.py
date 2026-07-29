from pyanc350.v2 import Positioner
import pyvisa, time, csv, math, datetime

# ==== 実機パラメータ ====
HZ_PER_STEP = -17.5  # Hz / step
CHANNEL = 1
MOVE_SETTLE_SEC = 0.1
TOL_HZ = 150e3
CONFIRM_TOL_HZ = TOL_HZ / 1.2
MAX_ITERS = 100
MAX_STEP_PER_ITER = 1_000_000
PEAK_MODE = 'max'
START_POS = 3667208

# ==== 中心周波数 ±200kHz を3点ふるよー ====
CENTER_FREQ = 2.565874e9
STEP = 200e3
TARGETS_HZ = [CENTER_FREQ + STEP * i for i in range(-3, 4)]  # 合計7

# ==== VNAユーティリティ ====
def vna_init():
    rm = pyvisa.ResourceManager()
    vna = rm.open_resource('TCPIP::169.254.42.144::INSTR')
    vna.timeout = 120000
    vna.write('*CLS')
    vna.write('CALC1:PAR:SDEF "S21_Trace", S21')
    vna.write('DISP:WIND1:TRAC1:FEED "S21_Trace"')
    vna.write('INIT:CONT OFF')
    vna.write('SENS1:BAND 1kHz')
    vna.write('SENS1:SWE:POIN 1601')
    return vna

def vna_sweep(vna, f_start=1.89e9, f_stop=1.905e9):　# ここも毎回変えてね 
    vna.write(f'SENS1:FREQ:STAR {f_start}')
    vna.write(f'SENS1:FREQ:STOP {f_stop}')
    vna.query('INIT:IMM; *OPC?')
    npts = int(float(vna.query('SENS1:SWE:POIN?')))
    freqs = [f_start + (f_stop - f_start) * i / (npts - 1) for i in range(npts)]
    vna.write('CALC1:PAR:SEL "S21_Trace"')
    raw = vna.query('CALC1:DATA? SDAT').strip().split(',')
    vals = [float(x) for x in raw]
    comp = [(vals[2 * i], vals[2 * i + 1]) for i in range(npts)]
    mag = [20 * math.log10(math.hypot(r, i)) for (r, i) in comp]
    return freqs, comp, mag

def find_peak_index(freqs, mag, mode='max', min_prominence=3, prominence_hz=4e6):
    points_per_hz = len(mag) / (freqs[-1] - freqs[0])
    half_window_pts = max(1, int(prominence_hz * points_per_hz / 2))
    best_idx = None
    best_val = -float('inf') if mode == 'max' else float('inf')
    for i in range(1, len(mag) - 1):
        if mode == 'max' and mag[i] > mag[i - 1] and mag[i] > mag[i + 1]:
            left_min = min(mag[max(0, i - half_window_pts):i])
            right_min = min(mag[i + 1:i + 1 + half_window_pts])
            prominence = mag[i] - max(left_min, right_min)
            if prominence >= min_prominence and mag[i] > best_val:
                best_val = mag[i]; best_idx = i
        elif mode == 'min' and mag[i] < mag[i - 1] and mag[i] < mag[i + 1]:
            left_max = max(mag[max(0, i - half_window_pts):i])
            right_max = max(mag[i + 1:i + 1 + half_window_pts])
            prominence = min(left_max, right_max) - mag[i]
            if prominence >= min_prominence and mag[i] < best_val:
                best_val = mag[i]; best_idx = i
    if best_idx is None:
        best_idx = mag.index(max(mag) if mode == 'max' else min(mag))
    return best_idx

def refine_peak_parabola(freqs, mag, idx):
    n = len(mag)
    if idx <= 0 or idx >= n - 1:
        return freqs[idx]
    y1, y2, y3 = mag[idx - 1], mag[idx], mag[idx + 1]
    f1, f2, f3 = freqs[idx - 1], freqs[idx], freqs[idx + 1]
    dx = f2 - f1
    denom = y1 - 2 * y2 + y3
    if denom == 0:
        return f2
    delta = 0.5 * (y1 - y3) / denom
    return f2 + delta * dx

def interpolate_x(x1, y1, x2, y2, y):
    if y2 == y1:
        return (x1 + x2) / 2
    return x1 + (y - y1) * (x2 - x1) / (y2 - y1)

def calc_q_value(freqs, mag, fpk, drop_db=3.0):
    idx_pk = min(range(len(freqs)), key=lambda i: abs(freqs[i] - fpk))
    pk_val = mag[idx_pk]
    threshold = pk_val - drop_db

    f_low, f_high = None, None

    for i in range(idx_pk, 0, -1):
        if (mag[i] >= threshold and mag[i - 1] <= threshold) or (mag[i] <= threshold and mag[i - 1] >= threshold):
            f_low = interpolate_x(freqs[i - 1], mag[i - 1], freqs[i], mag[i], threshold)
            break

    for i in range(idx_pk, len(mag) - 1):
        if (mag[i] >= threshold and mag[i + 1] <= threshold) or (mag[i] <= threshold and mag[i + 1] >= threshold):
            f_high = interpolate_x(freqs[i], mag[i], freqs[i + 1], mag[i + 1], threshold)
            break

    if f_low is None or f_high is None:
        return None

    bw = f_high - f_low
    if bw <= 0:
        return None

    return fpk / bw

def save_csv(path, freqs, comp, mag):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['freq_Hz', 'real', 'imag', 'mag_dB'])
        for fr, (re, im), m in zip(freqs, comp, mag):
            w.writerow([f'{fr:.3f}', f'{re:.9e}', f'{im:.9e}', f'{m:.6f}'])

def confirm_peak_avg(vna, n_confirm=3):
    peaks = []
    for _ in range(n_confirm):
        freqs, comp, mag = vna_sweep(vna)
        idx = find_peak_index(freqs, mag, PEAK_MODE)
        f_ref = refine_peak_parabola(freqs, mag, idx)
        peaks.append(f_ref)
    avg = sum(peaks) / len(peaks)
    std = (sum((p - avg) ** 2 for p in peaks) / len(peaks)) ** 0.5
    return avg, std

def pick_gain(abs_err_hz: float) -> float:
    if abs_err_hz > 2e6: return 1.0
    if abs_err_hz > 5e5: return 0.5
    if abs_err_hz > 1e5: return 0.2
    return 0.08

# ==== メイン制御ループ ====
def main():
    anc = Positioner()
    vna = None
    try:
        anc.setOutput(CHANNEL, True)
        print(f"✅ Piezo channel {CHANNEL} output ON")
        anc.moveAbsolute(CHANNEL, int(START_POS))
        time.sleep(MOVE_SETTLE_SEC)
        print(f"➡️ Moved to start position {START_POS}")
        vna = vna_init()

        for tgt in TARGETS_HZ:
            print(f'\n=== Target {tgt/1e9:.6f} GHz ===')
            freqs, comp, mag = vna_sweep(vna)
            idx = find_peak_index(freqs, mag, PEAK_MODE)
            fpk = refine_peak_parabola(freqs, mag, idx)
            pk_val = mag[idx]
            print(f' initial peak ~ {fpk/1e9:.6f} GHz, {pk_val:.2f} dB (err {(tgt - fpk)/1e3:.1f} kHz)')

            for it in range(1, MAX_ITERS + 1):
                err_hz = tgt - fpk
                abs_err = abs(err_hz)
                if abs_err <= TOL_HZ:
                    avg, std = confirm_peak_avg(vna, 3)
                    if abs(tgt - avg) <= CONFIRM_TOL_HZ:
                        fpk = avg
                        print(f' ✅ converged after confirm: |error|={(tgt - avg)/1e3:.1f} kHz')
                        break
                    else:
                        print(' confirm failed — micro-adjust')
                        err_hz = tgt - avg
                        move_steps = int(round((err_hz / HZ_PER_STEP) * 0.03))
                        move_steps = int(math.copysign(min(abs(move_steps), 1000), move_steps))
                        if move_steps == 0:
                            move_steps = 1 if err_hz > 0 else -1
                        pos_before = anc.getPosition(CHANNEL)
                        anc.moveRelative(CHANNEL, move_steps)
                        time.sleep(MOVE_SETTLE_SEC)
                        pos_after = anc.getPosition(CHANNEL)
                        freqs, comp, mag = vna_sweep(vna)
                        idx = find_peak_index(freqs, mag, PEAK_MODE)
                        fpk = refine_peak_parabola(freqs, mag, idx)
                        print(f' micro move {move_steps:+d} steps pos {pos_before}->{pos_after} fpk {fpk/1e9:.6f} GHz')
                        continue

                gain = pick_gain(abs_err)
                move_steps = int(round((err_hz / HZ_PER_STEP) * gain))
                if move_steps == 0:
                    move_steps = 1 if err_hz > 0 else -1
                if abs(move_steps) > MAX_STEP_PER_ITER:
                    move_steps = int(math.copysign(MAX_STEP_PER_ITER, move_steps))
                pos_before = anc.getPosition(CHANNEL)
                anc.moveRelative(CHANNEL, move_steps)
                time.sleep(MOVE_SETTLE_SEC)
                pos_after = anc.getPosition(CHANNEL)
                freqs, comp, mag = vna_sweep(vna)
                idx = find_peak_index(freqs, mag, PEAK_MODE)
                fpk = refine_peak_parabola(freqs, mag, idx)
                print(f' iter {it}: fpk {fpk/1e9:.6f} GHz err {err_hz/1e3:+.1f} kHz move {move_steps:+d} steps pos {pos_before}->{pos_after}')

            avg_final, std_final = confirm_peak_avg(vna, 5)
            final_err = tgt - avg_final
            print(f' final peak {avg_final/1e9:.6f} GHz std {std_final/1e3:.3f} kHz (error {final_err/1e3:+.1f} kHz)')
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            freqs, comp, mag = vna_sweep(vna)
            save_csv(f'vna_lock_{tgt/1e9:.3f}GHz_{ts}.csv', freqs, comp, mag)
            print(f' saved: vna_lock_{tgt/1e9:.3f}GHz_{ts}.csv')

            q_val = calc_q_value(freqs, mag, avg_final, drop_db=3.0)
            if q_val:
                print(f" Q-value (peak-3 dB 幅) = {q_val:.1f}")
            else:
                print(" ⚠️ Q値が計算できませんでした")

    finally:
        if vna:
            vna.close()
        try:
            anc.setOutput(CHANNEL, False)
            print(f"🛑 Piezo channel {CHANNEL} output OFF")
        except:
            pass
        try:
            anc.close()
        except:
            pass
        print('\nAll targets done.')

if __name__ == '__main__':
    main()
