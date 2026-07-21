#ifndef SETUP_H
#define SETUP_H

#include <TH1.h>
#include <TH1D.h>
#include <TString.h>
#include <TMath.h>
#include <TStyle.h>
#include <map>
#include "TGaxis.h"
#include "TSystemDirectory.h"
#include "TSystemFile.h"
#include "TSystem.h"
#include "TList.h"
#include "TIterator.h"

#include "TColor.h"
using std::vector;
using std::cout;
using std::endl;

inline void Set_gStyle() {
  gStyle->SetTitleSize(0.05, "XYZ");
  gStyle->SetLabelSize(0.04, "XYZ");
  gStyle->SetPadLeftMargin(0.15);
  gStyle->SetPadRightMargin(0.15);
  gStyle->SetPadTopMargin(0.12);
  gStyle->SetPadBottomMargin(0.18);
  //gStyle->SetNdivisions(Int_t n, Option_t* axis);	//軸の目盛り数.
  //gStyle->SetTickLength(Float_t length, Option_t* axis);	//目盛の長さ.
  //gStyle->SetFrameLineWidth(2);   // TFrame の線
  //gStyle->SetLineWidth(2);
  gStyle->SetFuncWidth(2);        // TF1などの関数線
  gStyle->SetHistLineWidth(2);    // TH1などのヒストグラム線
  gStyle->SetPadGridX(1);	//X軸グリッド表示.
  gStyle->SetPadGridY(1);
  //gStyle->SetLineColor(Int_t color);
  gStyle->SetMarkerStyle(20);
  // gStyle->SetMarkerColor(Int_t color);
  // gStyle->SetMarkerSize(0.8);
  //gStyle->SetHistLineColor(Int_t color);
  // gStyle->SetOptStat(1111);
  // gStyle->SetOptFit(1112);
  gStyle->SetPalette(kRainBow);
  gStyle->SetStatX(0.85); // 右上X座標 (デフォルト0.9)
  //gStyle->SetStatX(0.26); // 右上X座標 (デフォルト0.9)
  gStyle->SetStatY(0.88); // 右上Y座標 (デフォルト0.9)
  gStyle->SetStatW(0.17); // 幅
  gStyle->SetStatH(0.1); // 高さ
  //gStyle->SetFitFormat("5.2f");
  TGaxis::SetMaxDigits(3);
}

inline TH1* RebinHistogram(TH1* h, int n) {
  if (!h) return nullptr;
  if (n <= 0) return nullptr;

  int oldNbins = h->GetNbinsX();
  int newNbins = (oldNbins + n - 1) / n; // 切り上げ

  double xmin = h->GetXaxis()->GetXmin();
  double xmax = h->GetXaxis()->GetXmax();

  TH1D* h_new = new TH1D(Form("%s_rebin", h->GetName()), h->GetTitle(), newNbins, xmin, xmax);

  for (int newBin = 1; newBin <= newNbins; ++newBin) {
    int startBin = (newBin - 1) * n + 1;
    int endBin = std::min(startBin + n - 1, oldNbins);

    double content = 0;
    double error2 = 0;
    for (int j = startBin; j <= endBin; ++j) {
      content += h->GetBinContent(j);
      double err = h->GetBinError(j);
      error2 += err * err;
    }
    h_new->SetBinContent(newBin, content);
    h_new->SetBinError(newBin, std::sqrt(error2));
  }

  return h_new;
}

// ClorMap.at(i)
static const std::map<int, int> ColorMap = {
    {0,  kRed},
    {1,  kBlue},
    {2,  kGreen+2},
    {3,  kOrange+1},
    {4,  kMagenta},
    {5, kYellow+1},
    {6,  kViolet+1},
    {7, kAzure+7},

    {8,  kRed+1},
    {9, kBlack},
    {10, kGreen+1},
    {11, kPink+1},
    {12, kCyan-7},
    {13, kOrange+4},
    {14, kViolet},
    {15,  kCyan+1},

    {16, kPink-6},
    {17, kBlue-9},
    {18, kSpring+10},
    {19, kPink-9},
    {20, kTeal-9},
    {21, kOrange},
    {22, kViolet-6},
    {23, kYellow-4},

    {24, kPink+8},
    {25, kBlue+2},
    {26, kGreen},
    {27, kRed-7},
    {28, kGreen+4},
    {29, kOrange-1},
    {30, kViolet-9},
    {31, kGray}
};

static const int kLightRed   = TColor::GetColor(1.0f, 0.7f, 0.7f);
static const int kLightBlue  = TColor::GetColor(0.7f, 0.7f, 1.0f);
static const int kLightGreen = TColor::GetColor(0.7f, 1.0f, 0.7f);
static const int kLightGray  = TColor::GetColor(0.85f, 0.85f, 0.85f);
static const int kLightOrange = TColor::GetColor(1.0f, 0.85f, 0.6f);
static const int kPaleRed     = TColor::GetColor(1.0f, 0.85f, 0.85f);  
static const int kPaleBlue    = TColor::GetColor(0.85f, 0.85f, 1.0f);
static const int kPaleGreen   = TColor::GetColor(0.85f, 1.0f, 0.85f);
static const int kPaleGray    = TColor::GetColor(0.92f, 0.92f, 0.92f);
static const int kPaleOrange  = TColor::GetColor(1.0f, 0.92f, 0.75f);
static const int kSoftPink    = TColor::GetColor(1.0f, 0.8f, 0.85f);
static const int kSoftCyan    = TColor::GetColor(0.7f, 0.9f, 1.0f);
static const int kSoftGreen   = TColor::GetColor(0.7f, 1.0f, 0.7f);
static const int kOrangeRed  = TColor::GetColor(1.0f, 0.6f, 0.6f);
static const int kCyanGreen  = TColor::GetColor(0.6f, 1.0f, 0.8f);
static const int kYellowRed  = TColor::GetColor(1.0f, 0.75f, 0.6f);
static const int kAquaGreen  = TColor::GetColor(0.6f, 1.0f, 0.9f);
static const int kLightLime = TColor::GetColor(0.8f, 1.0f, 0.7f);

class OpenRootFile {
public:
  // 指定ディレクトリdirpath内で、ファイル名がprefixで始まり、suffixで終わるファイルを探して最初に開く
  // 見つかればTFile*を返す。失敗ならnullptr
  static TFile* FindandOpenRootFile(const TString& dirpath, const TString& prefix, const TString& suffix, const TString& label = "") {
    TSystemDirectory dir("dir", dirpath);
    TList* files = dir.GetListOfFiles();
    if (!files) {
      std::cerr << "ディレクトリが見つかりません: " << dirpath.Data() << std::endl;
      return nullptr;
    }

    TSystemFile* file;
    TIter next(files);
    while ((file = (TSystemFile*)next())) {
      TString fname = file->GetName();
      if (!file->IsDirectory() && fname.BeginsWith(prefix) && fname.EndsWith(suffix)) {
        TString fullpath = dirpath + "/" + fname;
        TFile* f = TFile::Open(fullpath);
        if (f && !f->IsZombie()) {
          if (!label.IsNull()) std::cout << " (" << label << ") = ";
            std::cout << f->GetName() << std::endl;
            return f;
        } else {
          std::cerr << "ファイルが壊れています: " << fullpath.Data() << std::endl;
          if (f) f->Close();
          return nullptr;
        }
      }
    }

    std::cerr << "該当ファイルが見つかりません: " << dirpath.Data() << "  prefix: " << prefix.Data() << "  suffix: " << suffix.Data() << std::endl;
    return nullptr;
  }
};

// ヒストを描画しつつ、0だけ白マスクをかける
inline void DrawHistZeroWhite(TH2* hist, Option_t* opt="COLZ") {
    if (!hist) return;
    gStyle->SetPalette(kRainBow);
    gStyle->SetNumberContours(255);
    hist->Draw(opt);

    // マスク作成
    TH2D* hmask = (TH2D*)hist->Clone(Form("%s_mask", hist->GetName()));
    hmask->Reset();

    for (int ix=1; ix<=hist->GetNbinsX(); ix++) {
        for (int iy=1; iy<=hist->GetNbinsY(); iy++) {
            if (hist->GetBinContent(ix,iy) == 0) {
                hmask->SetBinContent(ix,iy, 1); // ダミー値
            }
        }
    }

    hmask->SetMarkerColor(kWhite);
    hmask->SetMarkerSize(1.2);
    hmask->Draw("SAME BOX");  // 白四角で塗る
}

TH1D* Hist_XOffset(TH1D* h_old, double x_offset) {
  int Nbinx = h_old->GetNbinsX();
  double x_min_old = h_old->GetXaxis()->GetXmin();
  double x_max_old = h_old->GetXaxis()->GetXmax();
  // X軸だけオフセットを加える（内容はそのまま）.
  TH1D* h_new = new TH1D(Form("%s_new", h_old->GetName()), h_old->GetTitle(), Nbinx, x_min_old - x_offset, x_max_old - x_offset);
  h_new->GetXaxis()->SetTitle(h_old->GetXaxis()->GetTitle());
  h_new->GetYaxis()->SetTitle(h_old->GetYaxis()->GetTitle());
  h_new->GetZaxis()->SetTitle(h_old->GetZaxis()->GetTitle());

  // 元ヒストのビンを新ヒストにマッピングしてコピー.
  for(int i=1; i<=Nbinx; i++){
    double content = h_old->GetBinContent(i);
    double error   = h_old->GetBinError(i);

    h_new->SetBinContent(i, content);
    h_new->SetBinError(i, error);
  }
  h_new->SetLineColor(h_old->GetLineColor());
  // h_new->SetFillColor(h_old->GetFillColor());
  h_new->SetMarkerColor(h_old->GetMarkerColor());
  // h_new->SetMarkerStyle(h_old->GetMarkerStyle());

  return h_new;
}

TH1D* Hist_XUnitScale(TH1D* h_old, double x_scale) {
  int Nbinx = h_old->GetNbinsX();
  double x_min_old = h_old->GetXaxis()->GetXmin();
  double x_max_old = h_old->GetXaxis()->GetXmax();
  // X軸だけスケールを変える（内容はそのまま単位変換したいとき）.
  TH1D* h_new = new TH1D(Form("%s_scaled", h_old->GetName()), h_old->GetTitle(), Nbinx, x_min_old*x_scale, x_max_old*x_scale);
  h_new->GetXaxis()->SetTitle(h_old->GetXaxis()->GetTitle());
  h_new->GetYaxis()->SetTitle(h_old->GetYaxis()->GetTitle());
  h_new->GetZaxis()->SetTitle(h_old->GetZaxis()->GetTitle());

  for(int i=1; i<=Nbinx; i++){
    double content = h_old->GetBinContent(i);
    double error   = h_old->GetBinError(i);

    h_new->SetBinContent(i, content);
    h_new->SetBinError(i, error);
  }
  h_new->SetLineColor(h_old->GetLineColor());
  h_new->SetMarkerColor(h_old->GetMarkerColor());

  return h_new;
}

// --- 数字変換の安全装置 (絶対に落ちない) ---
// 成功したら true を返し、val に数値を入れる。失敗したら false を返す。
bool TryParse(std::string token, double &val) {
  // 1. ゴミ文字の徹底削除
  token.erase(std::remove(token.begin(), token.end(), '\r'), token.end());
  token.erase(std::remove(token.begin(), token.end(), '\n'), token.end());
  token.erase(std::remove(token.begin(), token.end(), ' '), token.end());
  token.erase(std::remove(token.begin(), token.end(), '\t'), token.end());

  if (token.empty()) return false;

  // 2. C言語由来の strtod を使用 (これはエラーで落ちない)
  char* endPtr;
  val = std::strtod(token.c_str(), &endPtr);

  // 変換できなかった場合、endPtr は文字列の先頭を指したままになる
  if (endPtr == token.c_str()) {
      return false;
  }
  return true;
}

#endif