#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdlib>
#include <complex>
#include <cstdio> // printf用
#include "TGraph.h"
#include "TCanvas.h"
#include "TF1.h"
#include "TStyle.h"
#include "TROOT.h"
#include "TMinuit.h"
#include "TMath.h"
#include "TEllipse.h"
#include "TMarker.h"
#include "TH2D.h"     // 追加：フレーム描画用
#include "../Setup.h"

// --- グローバル変数 ---
std::vector<double> g_s11_freq;
std::vector<double> g_s11_re;
std::vector<double> g_s11_err;
std::vector<double> g_s11_im;
std::vector<double> g_s21_freq;
std::vector<double> g_s21_re;
std::vector<double> g_s21_err;
std::vector<double> g_s21_im;
double g_fit_f_min = 0.0;
double g_fit_f_max = 1e12; // 初期値は十分大きく

// --- 同時フィット用の目的関数 (Chi2) ---
void fcn(int &npar, double *gin, double &f, double *par, int iflag) {
  double f0 = par[0];
  double Q  = par[1];
  
  double a1_re = par[2], a1_im = par[3];
  double b1_re = par[4], b1_im = par[5];
  double d1    = par[6];
  double s1_re = par[7], s1_im = par[8];

  double a2_re = par[9],  a2_im = par[10];
  double b2_re = par[11], b2_im = par[12];
  double d2    = par[13];
  double s2_re = par[14], s2_im = par[15];

  double chi2 = 0;

  // fit範囲の設定
  // if ( mode==210 && (freq > 2.567e6 || freq < 2.564e6) ) continue;
  // double fit_range_half = 1000.0; // Hz
  // double f_min = f0 - fit_range_half;
  // double f_max = f0 + fit_range_half;
  // fit範囲の設定 (グローバル変数を使用)
  double f_min = g_fit_f_min;
  double f_max = g_fit_f_max;

  double err_s11 = 0.001;
  double err_s21 = 0.0001;

  // 1. S11 の Chi2
  for (size_t i = 0; i < g_s11_freq.size(); i++) {
    if (g_s11_freq[i] < f_min || g_s11_freq[i] > f_max) continue;
    double df = g_s11_freq[i] - f0;
    double bg_re = b1_re + s1_re * df;
    double bg_im = b1_im + s1_im * df;
    
    double dx = 2.0 * Q * df / f0;
    double den = 1.0 + dx * dx; 
    double core_re = (a1_re + a1_im * dx) / den + bg_re;
    double core_im = (a1_im - a1_re * dx) / den + bg_im;

    double theta = d1 * df;
    double model_re = core_re * cos(theta) - core_im * sin(theta);
    double model_im = core_re * sin(theta) + core_im * cos(theta);

    double diff_re = g_s11_re[i] - model_re;
    double diff_im = g_s11_im[i] - model_im;
    // データから取得した誤差を使用
    double sigma = g_s11_err[i];
    chi2 += (diff_re * diff_re + diff_im * diff_im) / (sigma * sigma);
    // chi2 += (diff_re * diff_re + diff_im * diff_im) / (err_s11 * err_s11);
  }

  // 2. S21 の Chi2
  for (size_t i = 0; i < g_s21_freq.size(); i++) {
    if (g_s21_freq[i] < f_min || g_s21_freq[i] > f_max) continue;
    double df = g_s21_freq[i] - f0;
    double bg_re = b2_re + s2_re * df;
    double bg_im = b2_im + s2_im * df;
    
    double dx = 2.0 * Q * df / f0;
    double den = 1.0 + dx * dx; 
    double core_re = (a2_re + a2_im * dx) / den + bg_re;
    double core_im = (a2_im - a2_re * dx) / den + bg_im;

    double theta = d2 * df;
    double model_re = core_re * cos(theta) - core_im * sin(theta);
    double model_im = core_re * sin(theta) + core_im * cos(theta);

    double diff_re = g_s21_re[i] - model_re;
    double diff_im = g_s21_im[i] - model_im;
    // データから取得した誤差を使用
    double sigma = g_s21_err[i];
    chi2 += (diff_re * diff_re + diff_im * diff_im) / (sigma * sigma);
    // chi2 += (diff_re * diff_re + diff_im * diff_im) / (err_s21 * err_s21); 
  }

  f = chi2;
}

void VNA_data_complex_fit_e(const char* filename = "./csv/VNA/202602_TM210.csv", double fit_ini = -1, double fit_end = -1) {
  int mode =110;
  int beamtime =1;
  // filename = Form("./csv/VNA/202501_TM%d.csv", mode);
  // filename = Form("./csv/VNA/202511_TM%d.csv", mode);
  // filename = Form("./csv/VNA/202511_TM%d_2.csv", mode);
  // filename = Form("./csv/VNA/202602_TM%d.csv", mode);
  filename = Form("./csv/VNA/202602_TM%d_1897400.csv", mode);
  // filename = Form("./csv/VNA/202602_TM%d_2565860.csv", mode);
  // filename = Form("./csv/VNA/202602_TM%d_2565260.csv", mode);
  // filename = Form("./csv/VNA/202602_TM%d_2566460.csv", mode);
  // filename = "../data/202604241359_110_Narrow_data.csv";
  filename = "../data/202604241636_110_Narrow_normal_110.csv";
  // filename = "../data/202604241636_110_Wide_normal_110.csv";
  // filename = "../data/202604241635_210_Narrow_normal_210.csv";
  // filename = "../data/202604241635_210_Wide_normal_210.csv";
  filename = "../data/beamtime/202511062131-1897400-Ch2.csv";

  TH1D *h_err_s11 = new TH1D("h_err_s11", "S11 Error Magnitude;Standard Deviation;Counts", 50, 0, 0.005);
  TH1D *h_err_s21 = new TH1D("h_err_s21", "S21 Error Magnitude;Standard Deviation;Counts", 50, 0, 0.005);

  Set_gStyle();
  // --- フィット範囲の決定 ---
  // 2. 三項演算子で、引数が -1 の場合に mode ごとの値をセット
  // fit_ini が 0以上ならその値を、-1 なら mode を見て初期値を決定
  g_fit_f_min = (fit_ini >= 0) ? fit_ini : (mode == 110 ? 1.894e6 : 2.564e6);
  g_fit_f_max = (fit_end >= 0) ? fit_end : (mode == 110 ? 1.900e6 : 2.568e6);
  gStyle->SetOptFit(1111);
  // gStyle->SetOptTitle(0);

  g_s11_freq.clear(); g_s11_re.clear(); g_s11_im.clear();
  g_s21_freq.clear(); g_s21_re.clear(); g_s21_im.clear();

  std::ifstream file(filename);
  if (!file.is_open()) {
    std::cerr << "Error: Could not open file" << std::endl;
    return;
  }

  std::string line;
  int success_count_s11 = 0;
  int success_count_s21 = 0;

  for(int i = 0; i < 3; i++) std::getline(file, line);

  while (std::getline(file, line)) {
    if (line.empty()) continue;
    std::stringstream ss(line);
    std::string token;
    int col_idx = 0;
    
    double val_f = 0, s11_a = 0, s11_ae = 0, s11_p = 0, s21_a = 0, s21_ae = 0, s21_p;
    bool f_ok = false, s11a_ok = false, s11ae_ok = false, s11p_ok = false, s21a_ok = false, s21ae_ok = false, s21p_ok = false;
    if (beamtime==0){
      while (std::getline(ss, token, ',')) {
        col_idx++;
        if      (col_idx == 1) f_ok    = TryParse(token, val_f);
        else if (col_idx == 2) s11a_ok = TryParse(token, s11_a);
        else if (col_idx == 3) s11ae_ok= TryParse(token, s11_ae); // S11 Amp Err
        else if (col_idx == 4) s11p_ok = TryParse(token, s11_p);
        else if (col_idx == 6) s21a_ok = TryParse(token, s21_a);
        else if (col_idx == 7) s21ae_ok= TryParse(token, s21_ae); // S21 Amp Err
        else if (col_idx == 8) s21p_ok = TryParse(token, s21_p);
      }
    } else {
      while (std::getline(ss, token, ',')) {
        col_idx++;
        if      (col_idx == 1) f_ok    = TryParse(token, val_f);
        else if (col_idx == 2) s11a_ok = TryParse(token, s11_a);
        else if (col_idx == 3) s11p_ok = TryParse(token, s11_p);
        else if (col_idx == 4) s21a_ok = TryParse(token, s21_a);
        else if (col_idx == 5) s21p_ok = TryParse(token, s21_p);
      }
    }

    double freq = val_f * 1e-3; // kHz変換
    // if ( mode==110 && (freq > 1.898e6 || freq < 1.894e6) ) continue;
    // if ( mode==210 && (freq > 2.567e6 || freq < 1.894e6) ) continue;
    // if ( mode==210 && (freq > 2.567e6 || freq < 2.564e6) ) continue;

    if (f_ok && s11a_ok && s11p_ok) {
      double phase_rad = s11_p * TMath::Pi() / 180.0;
      g_s11_freq.push_back(freq);
      g_s11_re.push_back(s11_a * cos(phase_rad));
      g_s11_im.push_back(s11_a * sin(phase_rad));
      g_s11_err.push_back(s11_ae > 1e-10 ? s11_ae : 1e-5);
      h_err_s11->Fill(s11_ae);
      success_count_s11++;
    }

    if (f_ok && s21a_ok && s21p_ok) {
      double phase_rad = s21_p * TMath::Pi() / 180.0;
      g_s21_freq.push_back(freq);
      g_s21_re.push_back(s21_a * cos(phase_rad));
      g_s21_im.push_back(s21_a * sin(phase_rad));
      g_s21_err.push_back(s21_ae > 1e-10 ? s21_ae : 1e-6);
      h_err_s21->Fill(s21_ae);
      success_count_s21++;
    }
  }
  file.close();

  // データの有無をチェック
  std::cout << "Loaded S11: " << success_count_s11 << ", S21: " << success_count_s21 << std::endl;
  if (g_s11_freq.empty()) {
    std::cerr << "Error: No S11 data found in the file." << std::endl;
    return;
  }
  bool has_s21 = !g_s21_freq.empty();

  // --- フィット範囲の確定 (データ読み込み後) ---
  if (g_s11_freq.empty()) return;
  double data_f_min = *std::min_element(g_s11_freq.begin(), g_s11_freq.end());
  double data_f_max = *std::max_element(g_s11_freq.begin(), g_s11_freq.end());

  if (g_fit_f_min < 0) g_fit_f_min = data_f_min;
  if (g_fit_f_max < 0) g_fit_f_max = data_f_max;

  // --- TMinuit による同時フィット ---
  TMinuit *minuit = new TMinuit(16); 
  minuit->SetFCN(fcn);
  
  minuit->SetPrintLevel(-1);

  double arglist[10]; int ierflg = 0;
  arglist[0] = 1; // 1sigma エラー定義
  minuit->mnexcm("SET ERR", arglist, 1, ierflg);

  bool fix_QL = false;             // QLを固定する場合は true
  double fixed_QL_val = 3800.0;  // ここに固定したいQLの目標値を入力

  double f0_init = 1.896e6; 
  if (mode==210) f0_init = 2.5659e6; 
  double Q_init = fix_QL ? fixed_QL_val : 1000;
  minuit->mnparm(0, "f0", f0_init, 50, 0, 0, ierflg);
  minuit->mnparm(1, "QL", Q_init,  10,  1e2, 1e5, ierflg);

  // QLを固定する処理
  if (fix_QL) {
    minuit->FixParameter(1); // パラメータ1(QL)を固定
    std::cout << "=> Notice: Parameter 1 (QL) is FIXED to " << fixed_QL_val << std::endl;
  }

  minuit->mnparm(2, "S11_AmpRe", -0.8, 0.01, 0, 0, ierflg);
  minuit->mnparm(3, "S11_AmpIm",  0.0, 0.01, 0, 0, ierflg);
  minuit->mnparm(4, "S11_BGRe",   0.8, 0.01, 0, 0, ierflg);
  minuit->mnparm(5, "S11_BGIm",   0.0, 0.01, 0, 0, ierflg);
  minuit->mnparm(6, "S11_Delay",  0.0, 1e-6, 0, 0, ierflg);
  minuit->mnparm(7, "S11_SlpRe",  0.0, 1e-8, 0, 0, ierflg);
  minuit->mnparm(8, "S11_SlpIm",  0.0, 1e-8, 0, 0, ierflg);

  minuit->mnparm(9,  "S21_AmpRe",  -0.002, 0.0001, 0, 0, ierflg);
  minuit->mnparm(10, "S21_AmpIm",  -0.002, 0.0001, 0, 0, ierflg);
  minuit->mnparm(11, "S21_BGRe",   0.007, 0.0001, 0, 0, ierflg);
  minuit->mnparm(12, "S21_BGIm",  -0.004, 0.0001, 0, 0, ierflg);
  minuit->mnparm(13, "S21_Delay",  0.0,   1e-6,   0, 0, ierflg);
  minuit->mnparm(14, "S21_SlpRe",  0.0,   1e-8,   0, 0, ierflg);
  minuit->mnparm(15, "S21_SlpIm",  0.0,   1e-8,   0, 0, ierflg);

  // S21のデータが無い場合、S21のパラメータを固定してエラーを防ぐ
  if (!has_s21) {
    for (int i = 9; i <= 15; i++) {
      minuit->FixParameter(i);
    }
  }

  arglist[0] = 20000; // イタレーション上限
  arglist[1] = 1.;   
  minuit->mnexcm("MIGRAD", arglist, 2, ierflg);

  // 全16パラメータと誤差の取得
  double f0_fit, f0_err, Q_fit, Q_err;
  double a1_r, e_a1r, a1_i, e_a1i, b1_r, e_b1r, b1_i, e_b1i, d1_fit, e_d1, s1_r, e_s1r, s1_i, e_s1i;
  double a2_r, e_a2r, a2_i, e_a2i, b2_r, e_b2r, b2_i, e_b2i, d2_fit, e_d2, s2_r, e_s2r, s2_i, e_s2i;

  minuit->GetParameter(0, f0_fit, f0_err); minuit->GetParameter(1, Q_fit, Q_err);
  minuit->GetParameter(2, a1_r, e_a1r);    minuit->GetParameter(3, a1_i, e_a1i);
  minuit->GetParameter(4, b1_r, e_b1r);    minuit->GetParameter(5, b1_i, e_b1i);
  minuit->GetParameter(6, d1_fit, e_d1);   minuit->GetParameter(7, s1_r, e_s1r); minuit->GetParameter(8, s1_i, e_s1i);
  minuit->GetParameter(9, a2_r, e_a2r);    minuit->GetParameter(10, a2_i, e_a2i);
  minuit->GetParameter(11, b2_r, e_b2r);   minuit->GetParameter(12, b2_i, e_b2i);
  minuit->GetParameter(13, d2_fit, e_d2);  minuit->GetParameter(14, s2_r, e_s2r); minuit->GetParameter(15, s2_i, e_s2i);

  // --- カイ二乗とNDFの取得 (MIGRAD直後に行う) ---
  double chi2_min, edm, errdef;
  int nvpar, nparx, icstat;
  minuit->mnstat(chi2_min, edm, errdef, nvpar, nparx, icstat);

  // f0_fit を基準に、実際にフィットに使ったデータ点数を数え直す
  double fit_range_half = 3000.0;
  double f_min = f0_fit - fit_range_half;
  double f_max = f0_fit + fit_range_half;

  // 実際にフィットに使ったデータ点数をカウント
  int n_data_points = 0;
  for (size_t i = 0; i < g_s11_freq.size(); i++) {
    if (g_s11_freq[i] >= g_fit_f_min && g_s11_freq[i] <= g_fit_f_max) n_data_points += 2;
  }
  if (has_s21) {
    for (size_t i = 0; i < g_s21_freq.size(); i++) {
      if (g_s21_freq[i] >= g_fit_f_min && g_s21_freq[i] <= g_fit_f_max) n_data_points += 2;
    }
  }
  int ndf = n_data_points - nvpar;
  double reduced_chi2 = (ndf > 0) ? chi2_min / ndf : 0;

  /// --- 物理パラメータの算出 ---
  double D1 = TMath::Sqrt(a1_r*a1_r + a1_i*a1_i);
  double B1 = TMath::Sqrt(b1_r*b1_r + b1_i*b1_i);
  double d1 = D1 / B1; 
  
  double D21 = 0.0;
  double d2_star = 0.0;
  double beta2 = 0.0;
  
  // S21がある時だけ計算
  if (has_s21) {
    D21 = TMath::Sqrt(a2_r*a2_r + a2_i*a2_i);
    d2_star = (D21 * D21) / d1; 
  }
  
  double beta_sum = (d1 + d2_star) / (2.0 - d1 - d2_star);
  double beta1 = (d1 / 2.0) * (1.0 + beta_sum);
  if (has_s21) {
    beta2 = (d2_star / 2.0) * (1.0 + beta_sum);
  }
  double Q0 = Q_fit * (1.0 + beta_sum);

  // --- カスタム出力フォーマット (綺麗に整列) ---
  std::cout << "\n==================================================" << std::endl;
  std::cout << "              GLOBAL FIT RESULTS                  " << std::endl;
  std::cout << "==================================================" << std::endl;

  std::cout << "\n[S11 Parameters]" << std::endl;
  printf(" Amp Re        : %12.5f +/- %9.5f\n", a1_r, e_a1r);
  printf(" Amp Im        : %12.5f +/- %9.5f\n", a1_i, e_a1i);
  printf(" BG Re         : %12.5f +/- %9.5f\n", b1_r, e_b1r);
  printf(" BG Im         : %12.5f +/- %9.5f\n", b1_i, e_b1i);
  printf(" Delay         : %12.5e +/- %9.5e\n", d1_fit, e_d1);
  printf(" Slope Re      : %12.5e +/- %9.5e\n", s1_r, e_s1r);
  printf(" Slope Im      : %12.5e +/- %9.5e\n", s1_i, e_s1i);

  if (has_s21) {
    std::cout << "\n[S21 Parameters]" << std::endl;
    printf(" Amp Re        : %12.5f +/- %9.5f\n", a2_r, e_a2r);
    printf(" Amp Im        : %12.5f +/- %9.5f\n", a2_i, e_a2i);
    printf(" BG Re         : %12.5f +/- %9.5f\n", b2_r, e_b2r);
    printf(" BG Im         : %12.5f +/- %9.5f\n", b2_i, e_b2i);
    printf(" Delay         : %12.5e +/- %9.5e\n", d2_fit, e_d2);
    printf(" Slope Re      : %12.5e +/- %9.5e\n", s2_r, e_s2r);
    printf(" Slope Im      : %12.5e +/- %9.5e\n", s2_i, e_s2i);
  }

  std::cout << "\n[Physical Parameters]" << std::endl;
  printf(" Chi2 / NDF    : %12.2f / %d = %.3f\n", chi2_min, ndf, reduced_chi2);
  printf(" f0 (Center)   : %12.5f +/- %9.5f kHz\n", f0_fit, f0_err);
  printf(" Loaded Q (QL) : %12.2f +/- %9.2f\n", Q_fit, Q_err);
  printf(" Unloaded Q0   : %12.2f\n", Q0);
  printf(" Coupling b1   : %12.5f\n", beta1);
  if (has_s21) printf(" Coupling b2   : %12.5f\n", beta2);
  std::cout << "==================================================\n" << std::endl;

  // --- 描画データ作成 ---
  int n_fit = 1000;
  TGraph *gr_s11_nyq = new TGraph(g_s11_freq.size(), &g_s11_re[0], &g_s11_im[0]);
  TGraph *gr_s11_mag = new TGraph(g_s11_freq.size());
  TGraph *gr_fit_s11_nyq = new TGraph(n_fit);
  TGraph *gr_fit_s11_mag = new TGraph(n_fit);

  for(size_t i=0; i<g_s11_freq.size(); i++) gr_s11_mag->SetPoint(i, g_s11_freq[i], TMath::Sqrt(g_s11_re[i]*g_s11_re[i] + g_s11_im[i]*g_s11_im[i]));

  // --- S11のフィット曲線計算 ---
  // double f_min_s11 = *std::min_element(g_s11_freq.begin(), g_s11_freq.end());
  // double f_max_s11 = *std::max_element(g_s11_freq.begin(), g_s11_freq.end());
  // フィット範囲のみ描画
  double f_min_s11 = g_fit_f_min;
  double f_max_s11 = g_fit_f_max;
  for (int i = 0; i < n_fit; i++) {
    double f = f_min_s11 + (f_max_s11 - f_min_s11) * i / (n_fit - 1.0);
    double df = f - f0_fit;
    double bg_re = b1_r + s1_r * df, bg_im = b1_i + s1_i * df;
    double dx = 2.0 * Q_fit * df / f0_fit;
    double den = 1.0 + dx * dx;
    double core_re = (a1_r + a1_i * dx) / den + bg_re;
    double core_im = (a1_i - a1_r * dx) / den + bg_im;
    double theta = d1_fit * df;
    double re_fit = core_re * cos(theta) - core_im * sin(theta);
    double im_fit = core_re * sin(theta) + core_im * cos(theta);
    gr_fit_s11_nyq->SetPoint(i, re_fit, im_fit);
    gr_fit_s11_mag->SetPoint(i, f, TMath::Sqrt(re_fit*re_fit + im_fit*im_fit));
  }

  // グラフのスタイル設定 (S11)
  gr_s11_nyq->SetMarkerStyle(20); gr_s11_nyq->SetMarkerSize(0.6); gr_s11_nyq->SetMarkerColor(kBlue);
  gr_s11_mag->SetTitle("S11 Magnitude;Frequency [kHz];Magnitude"); gr_s11_mag->SetMarkerStyle(20); gr_s11_mag->SetMarkerSize(0.6);
  gr_s11_mag->SetMarkerColor(4);
  gr_fit_s11_nyq->SetLineColor(kRed); gr_fit_s11_nyq->SetLineWidth(2);
  gr_fit_s11_mag->SetLineColor(kRed); gr_fit_s11_mag->SetLineWidth(2);

  // --- 描画 (S21がある場合はキャンバスを分割、無い場合は単一) ---
  int canvas_width = has_s21 ? 1400 : 700;
  
  TCanvas *c_nyq = new TCanvas("c_nyq", "Nyquist Plots", canvas_width, 700);
  if (has_s21) c_nyq->Divide(2, 1);
  c_nyq->cd(1); gPad->SetGrid(); 
  
  // 【追加】S11 Nyquist 用の固定フレーム (縦横比1:1を維持するため)
  TH2D *frame_s11 = new TH2D("frame_s11", "S11 Nyquist Plot;Real;Imag", 100, -0.6, 1., 100, -0.8, 0.8);
  frame_s11->SetStats(0);
  frame_s11->Draw();
  gr_s11_nyq->Draw("P SAME"); 
  gr_fit_s11_nyq->Draw("L SAME");

  // r=1の円 (中心(0.5, 0)、半径0.5) を点線で描画
  TEllipse *circle_r1 = new TEllipse(0.5, 0.0, 0.5, 0.5);
  circle_r1->SetFillStyle(0);      // 塗りつぶしなし
  circle_r1->SetLineColor(kGray+2);
  circle_r1->SetLineStyle(2);      // 点線
  circle_r1->Draw("SAME");

  // 中心周波数(f0)のプロット点をマゼンタの星形で描画
  double f0_re = a1_r + b1_r;
  double f0_im = a1_i + b1_i;
  TMarker *marker_f0 = new TMarker(f0_re, f0_im, 29); // 29は星型マーカー
  marker_f0->SetMarkerColor(kMagenta);
  marker_f0->SetMarkerSize(2.0);
  marker_f0->Draw("SAME");

  TCanvas *c_mag = new TCanvas("c_mag", "Magnitude Plots", canvas_width, 500);
  if (has_s21) c_mag->Divide(2, 1);
  c_mag->cd(1); gPad->SetGrid(); 
  
  // 【追加】S11 Magnitude のY軸を固定
  gr_s11_mag->Draw("AP"); 
  gr_s11_mag->SetMinimum(0.0);
  gr_s11_mag->SetMaximum(1.1);
  gr_fit_s11_mag->Draw("L SAME");

  // S21のデータがある場合のみ、S21の曲線計算と描画を行う
  if (has_s21) {
    TGraph *gr_s21_nyq = new TGraph(g_s21_freq.size(), &g_s21_re[0], &g_s21_im[0]);
    TGraph *gr_s21_mag = new TGraph(g_s21_freq.size());
    TGraph *gr_fit_s21_nyq = new TGraph(n_fit);
    TGraph *gr_fit_s21_mag = new TGraph(n_fit);

    double max_s21 = 0; // 【追加】S21の最大振幅を取得してフレームサイズを決定
    for(size_t i=0; i<g_s21_freq.size(); i++) {
      double val = TMath::Sqrt(g_s21_re[i]*g_s21_re[i] + g_s21_im[i]*g_s21_im[i]);
      gr_s21_mag->SetPoint(i, g_s21_freq[i], val);
      if(val > max_s21) max_s21 = val;
    }

    // --- S21のフィット曲線計算 ---
    // double f_min_s21 = *std::min_element(g_s21_freq.begin(), g_s21_freq.end());
    // double f_max_s21 = *std::max_element(g_s21_freq.begin(), g_s21_freq.end());
    // フィット範囲のみ描画
    double f_min_s21 = g_fit_f_min;
    double f_max_s21 = g_fit_f_max;

    for (int i = 0; i < n_fit; i++) {
      double f = f_min_s21 + (f_max_s21 - f_min_s21) * i / (n_fit - 1.0);
      double df = f - f0_fit;
      double bg_re = b2_r + s2_r * df, bg_im = b2_i + s2_i * df;
      double dx = 2.0 * Q_fit * df / f0_fit;
      double den = 1.0 + dx * dx;
      double core_re = (a2_r + a2_i * dx) / den + bg_re;
      double core_im = (a2_i - a2_r * dx) / den + bg_im;
      double theta = d2_fit * df;
      double re_fit = core_re * cos(theta) - core_im * sin(theta);
      double im_fit = core_re * sin(theta) + core_im * cos(theta);
      gr_fit_s21_nyq->SetPoint(i, re_fit, im_fit);
      gr_fit_s21_mag->SetPoint(i, f, TMath::Sqrt(re_fit*re_fit + im_fit*im_fit));
    }

    gr_s21_nyq->SetMarkerStyle(20); gr_s21_nyq->SetMarkerSize(0.6); gr_s21_nyq->SetMarkerColor(kGreen+2);
    gr_s21_mag->SetTitle("S21 Magnitude;Frequency [kHz];Magnitude"); gr_s21_mag->SetMarkerStyle(20); gr_s21_mag->SetMarkerSize(0.6);
    gr_s21_mag->SetMarkerColor(418);
    gr_fit_s21_nyq->SetLineColor(kRed); gr_fit_s21_nyq->SetLineWidth(2);
    gr_fit_s21_mag->SetLineColor(kRed); gr_fit_s21_mag->SetLineWidth(2);

    c_nyq->cd(2); gPad->SetGrid(); 
    
    // 【追加】S21 Nyquist 用の固定フレーム (最大値に合わせて正方形を維持)
    double lim_s21 = max_s21 * 1.2;
    if(lim_s21 == 0) lim_s21 = 1.0;
    TH2D *frame_s21 = new TH2D("frame_s21", "S21 Nyquist Plot;Real;Imag", 100, -lim_s21, lim_s21, 100, -lim_s21, lim_s21);
    frame_s21->SetStats(0);
    frame_s21->Draw();
    gr_s21_nyq->Draw("P SAME"); 
    gr_fit_s21_nyq->Draw("L SAME");
    
    c_mag->cd(2); 
    gr_s21_mag->Draw("AP"); 
    gr_s21_mag->SetMinimum(0.0);
    gr_fit_s21_mag->Draw("L SAME");
  }
  
  // 1. 残差プロット (vs Frequency)
  TCanvas *c_resid = new TCanvas("c_resid", "Magnitude Residuals", canvas_width, 500);
  if (has_s21) c_resid->Divide(2, 1);

  // 2. 残差ヒストグラム
  TCanvas *c_hist = new TCanvas("c_hist", "Residual Distribution", canvas_width, 500);
  if (has_s21) c_hist->Divide(2, 1);

  // --- S11 残差計算 ---
  c_resid->cd(1); gPad->SetGrid();
  TGraph *gr_s11_res = new TGraph();
  TH1D *h_s11_res = new TH1D("h_s11_res", "S11 Residual Dist.;Data - Fit;Counts", 50, -0.003, 0.003);

  for (size_t i = 0; i < g_s11_freq.size(); i++) {
    double f = g_s11_freq[i];
    if (f < g_fit_f_min || f > g_fit_f_max) continue;
    double df = f - f0_fit;
    double bg_re = b1_r + s1_r * df, bg_im = b1_i + s1_i * df;
    double dx = 2.0 * Q_fit * df / f0_fit;
    double den = 1.0 + dx * dx;
    double core_re = (a1_r + a1_i * dx) / den + bg_re;
    double core_im = (a1_i - a1_r * dx) / den + bg_im;
    double theta = d1_fit * df;
    double re_fit = core_re * cos(theta) - core_im * sin(theta);
    double im_fit = core_re * sin(theta) + core_im * cos(theta);
    
    double mag_data = TMath::Sqrt(g_s11_re[i]*g_s11_re[i] + g_s11_im[i]*g_s11_im[i]);
    double mag_fit  = TMath::Sqrt(re_fit*re_fit + im_fit*im_fit);
    double res = mag_data - mag_fit;
    gr_s11_res->SetPoint(gr_s11_res->GetN(), f, res);
    h_s11_res->Fill(res);
  }
  gr_s11_res->SetTitle("S11 Magnitude Residual;Frequency [kHz];Data - Fit");
  gr_s11_res->SetMarkerStyle(20); gr_s11_res->SetMarkerSize(0.6); gr_s11_res->SetMarkerColor(kBlue);
  gr_s11_res->Draw("AP");
  TLine *l1 = new TLine(gPad->GetUxmin(), 0, gPad->GetUxmax(), 0); l1->SetLineStyle(2); l1->Draw();

  c_hist->cd(1);
  h_s11_res->SetFillColor(kBlue-10);
  h_s11_res->Draw();
  h_s11_res->Fit("gaus", "Q"); // ガウス分布でフィット

  // --- S21 残差計算 ---
  if (has_s21) {
    c_resid->cd(2); gPad->SetGrid();
    TGraph *gr_s21_res = new TGraph();
    TH1D *h_s21_res = new TH1D("h_s21_res", "S21 Residual Dist.;Data - Fit;Counts", 50, -0.003, 0.003);

    for (size_t i = 0; i < g_s21_freq.size(); i++) {
      double f = g_s21_freq[i];
      if (f < g_fit_f_min || f > g_fit_f_max) continue;
      double df = f - f0_fit;
      double bg_re = b2_r + s2_r * df, bg_im = b2_i + s2_i * df;
      double dx = 2.0 * Q_fit * df / f0_fit;
      double den = 1.0 + dx * dx;
      double core_re = (a2_r + a2_i * dx) / den + bg_re;
      double core_im = (a2_i - a2_r * dx) / den + bg_im;
      double theta = d2_fit * df;
      double re_fit = core_re * cos(theta) - core_im * sin(theta);
      double im_fit = core_re * sin(theta) + core_im * cos(theta);
      
      double mag_data = TMath::Sqrt(g_s21_re[i]*g_s21_re[i] + g_s21_im[i]*g_s21_im[i]);
      double mag_fit  = TMath::Sqrt(re_fit*re_fit + im_fit*im_fit);
      double res = mag_data - mag_fit;
      gr_s21_res->SetPoint(gr_s21_res->GetN(), f, res);
      h_s21_res->Fill(res);
    }
    gr_s21_res->SetTitle("S21 Magnitude Residual;Frequency [kHz];Data - Fit");
    gr_s21_res->SetMarkerStyle(20); gr_s21_res->SetMarkerSize(0.6); gr_s21_res->SetMarkerColor(kGreen+2);
    gr_s21_res->Draw("AP");
    TLine *l2 = new TLine(gPad->GetUxmin(), 0, gPad->GetUxmax(), 0); l2->SetLineStyle(2); l2->Draw();

    c_hist->cd(2);
    h_s21_res->SetFillColor(kGreen-10);
    h_s21_res->Draw();
    h_s21_res->Fit("gaus", "Q");
  }

  TCanvas *c_err_comp = new TCanvas("c_err_comp", "Error Comparison", 1400, 500);
  c_err_comp->Divide(2, 1);

  c_err_comp->cd(1);
  h_err_s11->SetFillColor(kBlue-10);
  h_err_s11->SetLineColor(kBlue);
  h_err_s11->Draw();
  // gPad->SetLogy(); // エラーの分布が見にくい場合はログスケールに

  c_err_comp->cd(2);
  h_err_s21->SetFillColor(kGreen-10);
  h_err_s21->SetLineColor(kGreen+2);
  h_err_s21->Draw();
  // gPad->SetLogy();

  printf("\n--- Residual Analysis ---\n");
  printf("Target Sigma (err_s11): %.5f\n", 0.002/3);
  if (h_s11_res->GetFunction("gaus")) {
    printf("S11 Measured Sigma   : %.5f\n", h_s11_res->GetFunction("gaus")->GetParameter(2));
  }
}
