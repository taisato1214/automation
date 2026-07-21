#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdlib> // strtodのため
#include "TGraphErrors.h"
#include "TCanvas.h"
#include "TH1D.h"
#include "TF1.h"
#include "TStyle.h"
#include "TROOT.h"
#include "../Setup.h"

void VNA_data_fit(const char* filename = "../data/202604231743_110_Narrow_test110.csv") {
  Set_gStyle();
  int mode = 110;
  // filename = "../data/202604231525_210_Narrow_test.csv";
  // filename = "../data/202604231525_210_Wide_test.csv";
  // filename = "../data/202604231525_210_Narrow_test.csv";
  // filename = "../data/202604231743_110_Wide_test110.csv";
  filename = "../data/202604231743_110_Narrow_test110.csv";
  filename = "../data/202604241359_110_Narrow_data.csv";
  
  int Nbin = 50;
  double f_center = (mode == 110) ? 1.898e6 : 2.565e6; // kHz
  
  // --- スタイル設定 ---
  gStyle->SetOptFit(1111);
  gStyle->SetOptStat(1111);

  // --- データ格納用配列 (名前を実態に合わせて修正) ---
  std::vector<double> x_freq;     // 周波数
  std::vector<double> x_freq_err; // 周波数の誤差(0.0)
  std::vector<double> y_s11_amp;  // S11 振幅
  std::vector<double> y_s11_err;  // S11 振幅の誤差
  std::vector<double> y_s21_amp;  // S21 振幅
  std::vector<double> y_s21_err;  // S21 振幅の誤差

  std::ifstream file(filename);
  if (!file.is_open()) {
    std::cerr << "Error: Could not open file " << filename << std::endl;
    return;
  }

  std::string line;
  int line_count = 0;
  int success_count = 0;

  // ヘッダー行を読み飛ばす
  for(int i = 0; i < 1; i++){
    if(std::getline(file, line)) {
      line_count++;
      std::cout << "Header skipped: " << line << std::endl;
    }
  }

  while (std::getline(file, line)) {
    line_count++;
    if (line.empty()) continue;

    std::stringstream ss(line);
    std::string token;
    int col_idx = 0;
    
    // 一時変数群
    double freq = 0;
    double s11_amp = 0, s11_err = 0, s11_phase = 0, s11_phase_err = 0;
    double s21_amp = 0, s21_err = 0, s21_phase = 0, s21_phase_err = 0;
    
    bool freq_ok = false;
    bool s11_amp_ok = false, s11_err_ok = false, s11_phase_ok = false, s11_phase_err_ok = false;
    bool s21_amp_ok = false, s21_err_ok = false, s21_phase_ok = false, s21_phase_err_ok = false;

    while (std::getline(ss, token, ',')) {
      col_idx++;
      
      // TryParse関数で変換を試みる
      if (col_idx == 1) {
        if (TryParse(token, freq)) freq_ok = true;
      } else if (col_idx == 2) {
        if (TryParse(token, s11_amp)) s11_amp_ok = true;
      } else if (col_idx == 3) {
        if (TryParse(token, s11_err)) s11_err_ok = true;
      } else if (col_idx == 4) {
        if (TryParse(token, s11_phase)) s11_phase_ok = true;
      } else if (col_idx == 5) {
        if (TryParse(token, s11_phase_err)) s11_phase_err_ok = true;
      } else if (col_idx == 6) {
        if (TryParse(token, s21_amp)) s21_amp_ok = true;
      } else if (col_idx == 7) {
        if (TryParse(token, s21_err)) s21_err_ok = true;
      } else if (col_idx == 8) {
        if (TryParse(token, s21_phase)) s21_phase_ok = true;
      } else if (col_idx == 9) {
        if (TryParse(token, s21_phase_err)) s21_phase_err_ok = true;
      }
    }

    // 周波数とS11が読めた行だけ採用
    if (freq_ok && s11_amp_ok) {
      x_freq.push_back(freq * 1e-3); // Hz -> kHz に変換
      x_freq_err.push_back(0.0);     // 周波数の誤差は0
      
      y_s11_amp.push_back(s11_amp);
      y_s11_err.push_back(s11_err_ok ? s11_err : 0.0);
      
      if (s21_amp_ok) {
        y_s21_amp.push_back(s21_amp);
        y_s21_err.push_back(s21_err_ok ? s21_err : 0.0);
      } 
      success_count++;
    } else {
      if (line_count < 10) { 
        std::cout << "Skip Line " << line_count << " (Not a number)" << std::endl; 
      }
    }
  }
  file.close();

  std::cout << "Loaded " << success_count << " valid data points." << std::endl;

  if (x_freq.empty()) {
    std::cout << "Error: No valid data found. Check column numbers." << std::endl;
    return;
  }

  // --- グラフ作成 (TGraphErrorsに統一) ---
  TGraphErrors *gr_s11 = new TGraphErrors(x_freq.size(), &x_freq[0], &y_s11_amp[0], &x_freq_err[0], &y_s11_err[0]);
  gr_s11->SetTitle("S11 Data;Frequency [kHz];Amp Mean");
  gr_s11->SetMarkerStyle(20);
  gr_s11->SetMarkerSize(0.5);
  gr_s11->SetMarkerColor(kBlue);

  TGraphErrors *gr_s21 = new TGraphErrors(x_freq.size(), &x_freq[0], &y_s21_amp[0], &x_freq_err[0], &y_s21_err[0]);
  gr_s21->SetTitle("S21 Data;Frequency [kHz];Amp Mean");
  gr_s21->SetMarkerStyle(20);
  gr_s21->SetMarkerSize(0.5);
  gr_s21->SetMarkerColor(kBlue);

  // --- 2. ヒストグラム & フィット ---
  double min_v = *std::min_element(y_s11_amp.begin(), y_s11_amp.end());
  double max_v = *std::max_element(y_s11_amp.begin(), y_s11_amp.end());
  double margin = (max_v - min_v) * 0.1;
  if (margin == 0) margin = 1.0;

  TH1D *h1 = new TH1D("h1", "Distribution;Value;Counts", Nbin, min_v - margin, max_v + margin);
  for (double v : y_s11_amp) h1->Fill(v);
  
  // フィット範囲 (kHz)
  double f_min = min_v - margin; 
  double f_max = max_v + margin;
  // double fx_min = *std::min_element(x_freq.begin(), x_freq.end());
  // double fx_max = *std::max_element(x_freq.begin(), x_freq.end());
  double offset = 3e3;
  double fx_min = f_center + offset;
  double fx_max = f_center - offset;


  // パラメータ定義
  TF1 *f_lor_s11 = new TF1("f_lor_s11", "[0]/TMath::Pi()* (([2]/2) / ((x-[1])*(x-[1])+[2]*[2]/4)) + [3] + [4]*(x-[1])", fx_min, fx_max);
  TF1 *f_lor_s21 = new TF1("f_lor_s21", "[0]/TMath::Pi()* (([2]/2) / ((x-[1])*(x-[1])+[2]*[2]/4)) + [3] + [4]*(x-[1])", fx_min, fx_max);
  TF1 *f_lor_s21 = new TF1("f_lor_s21", "[0] * TMath::Power([2]/2, 2) / (TMath::Power(x-[1], 2) + TMath::Power([2]/2, 2)) + [3] + [4]*(x-[1])", fx_min, fx_max);

  TF1 *f_lor2 = new TF1("f_lor2", "[0]/TMath::Pi()* (([2]/2) / ((x-[1])*(x-[1])+[2]*[2]/4)) + [3] + [4]*(x-[1]) + [5]*(x-[1])*(x-[1])", fx_min, fx_max);

  TF1 *f_double_lor_s11 = new TF1("f_double_lor_s11", "[0]/TMath::Pi()* (([2]/2) / ((x-[1])*(x-[1])+[2]*[2]/4)) + [3]/TMath::Pi()* (([5]/2) / ((x-[4])*(x-[4])+[5]*[5]/4)) + [6]", fx_min, fx_max);
  TF1 *f_double_lor_s21 = new TF1("f_double_lor_s21", "[0]/TMath::Pi()* (([2]/2) / ((x-[1])*(x-[1])+[2]*[2]/4)) + [3]/TMath::Pi()* (([5]/2) / ((x-[4])*(x-[4])+[5]*[5]/4)) + [6]", fx_min, fx_max);

  // --- 初期値のセット ---
  f_double_lor_s11->SetParNames("Amp1", "Mean1", "FWHM1", "Amp2", "Mean2", "FWHM2", "BG");
  f_double_lor_s21->SetParNames("Amp1", "Mean1", "FWHM1", "Amp2", "Mean2", "FWHM2", "BG");
  f_double_lor_s11->SetParameters(1, f_center, 1e-4, -1e-3, 30, 20, 1);
  f_double_lor_s11->SetParLimits(0, 0.8, 1.2);
  f_double_lor_s11->SetParLimits(2, 0, 1);
  f_double_lor_s11->SetParLimits(3, -1, 0);
  f_double_lor_s11->SetParLimits(5, 0, 1);
  f_double_lor_s11->SetLineColor(6);
  // f_double_lor_s11->Draw("same");

  // ローレンチアン1個 S11
  f_lor_s11->SetParNames("Amp1", "Mean", "FWHM", "Const", "Slope");
  f_lor_s11->SetParameters(-2e2, f_center, 5e2, 1., -1e-8);
  f_lor_s11->SetParLimits(0, -1e3, 0.);
  f_lor_s11->SetParLimits(2, 0, 1e3);
  f_lor_s11->SetLineColor(2);
  f_lor_s11->SetNpx(1000);
  gr_s11->Fit(f_lor_s11, "REMS");

  // S21
  f_lor_s21->SetParNames("Amp1", "Mean", "FWHM", "Const", "Slope");
  f_lor_s21->SetParameters(50, f_center, 5e2, 0., -1e-9);
  f_lor_s21->SetParLimits(0, 0, 1e1);
  f_lor_s21->SetParLimits(2, 0, 7e2);
  f_lor_s21->SetLineColor(2);
  f_lor_s21->SetNpx(1000);
  f_lor_s21->FixParameter(0, 12);
  f_lor_s21->FixParameter(1, 1.8976e6);
  f_lor_s21->FixParameter(2, 500);
  gr_s21->Fit(f_lor_s21, "REMS");

  // --- 描画 ---
  TCanvas *c1 = new TCanvas("c1", "Stability Monitor (S11)", 800, 600);
  gr_s11->Draw("AP");
  // f_lor_s11->Draw("same");

  TCanvas *c2 = new TCanvas("c2", "c2 (S21)", 800, 600);
  gr_s21->Draw("AP");
  // f_lor_s21->Draw("same");

  TCanvas *c3 = new TCanvas("c3", "Fit Result", 800, 600);
  h1->Draw();
  
  double amp = h1->GetMaximum();
  double mean = h1->GetMean();
  double rms = h1->GetRMS();
  
  // --- 結果表示 ---
  double m1 = f_lor_s11->GetParameter(1);
  double m1e = f_lor_s11->GetParError(1);
  double s1 = f_lor_s11->GetParameter(2);
  double s1e = f_lor_s11->GetParError(2);

  double m2 = f_lor_s21->GetParameter(1);
  double m2e = f_lor_s21->GetParError(1);
  double s2 = f_lor_s21->GetParameter(2);
  double s2e = f_lor_s21->GetParError(2);

  std::cout << "[Fit Results: S11 Peak]" << std::endl;
  std::cout << " Mean (Center)   : " << m1 << " +/- " << m1e << std::endl;
  std::cout << " FHWM            : " << s1 << " +/- " << s1e << std::endl;
  std::cout << " Q1 (Mean / FHWM): " << (s1 != 0 ? (m1/s1) : 0) << std::endl;

  std::cout << "\n[Fit Results: S21 Peak]" << std::endl;
  std::cout << " Mean (Center)   : " << m2 << " +/- " << m2e << std::endl;
  std::cout << " FHWM            : " << s2 << " +/- " << s2e << std::endl;
  std::cout << " Q2 (Mean / FHWM): " << (s2 != 0 ? (m2/s2) : 0) << std::endl;

  c1->Show();
  c2->Show();
}