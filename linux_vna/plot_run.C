// plot_run_errorbar.C
// Run#.txt を読み込み、エラーバー付きで3種類のグラフを作成するROOTマクロ
//
// 実行例:
//   root -l -q 'plot_run_errorbar.C("./data/20261005/Run1.txt")'
//
// 対応列:
//   Direction, Step_Count, Sstep,
//   Position1_Mean, Position1_Err, Resonance_f0_GHz

#include <TROOT.h>
#include <TSystem.h>
#include <TCanvas.h>
#include <TGraphErrors.h>
#include <TF1.h>
#include <TPaveText.h>
#include <TLegend.h>

#include <algorithm>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Row {
  double step = 0.0;
  double position = 0.0;
  double positionError = 0.0;
  double frequency = 0.0;
  std::string direction = "F";
};

std::string trim(const std::string& input) {
  const std::size_t first = input.find_first_not_of(" \t\r\n");
  if (first == std::string::npos) return "";
  const std::size_t last = input.find_last_not_of(" \t\r\n");
  return input.substr(first, last - first + 1);
}

std::vector<std::string> splitCSV(const std::string& line) {
  std::vector<std::string> fields;
  std::stringstream stream(line);
  std::string field;
  while (std::getline(stream, field, ',')) {
    fields.push_back(trim(field));
  }
  return fields;
}

int columnIndex(const std::vector<std::string>& headers,
                const std::string& name) {
  for (std::size_t i = 0; i < headers.size(); ++i) {
    if (headers[i] == name) return static_cast<int>(i);
  }
  return -1;
}

std::vector<Row> readRows(const char* filename) {
  std::ifstream input(filename);
  if (!input.is_open()) {
    throw std::runtime_error(std::string("Cannot open ") + filename);
  }

  std::string line;
  std::vector<std::string> headers;

  // # で始まるメタデータ行を読み飛ばし、CSVヘッダーを取得
  while (std::getline(input, line)) {
    line = trim(line);
    if (!line.empty() && line[0] != '#') {
      headers = splitCSV(line);
      break;
    }
  }

  if (headers.empty()) {
    throw std::runtime_error("CSV header was not found");
  }

  int stepIndex = columnIndex(headers, "Step_Count");
  int sstepIndex = columnIndex(headers, "Sstep");
  int positionIndex = columnIndex(headers, "Position1_Mean");
  int positionErrorIndex = columnIndex(headers, "Position1_Err");
  int frequencyIndex = columnIndex(headers, "Resonance_f0_GHz");
  int directionIndex = columnIndex(headers, "Direction");

  // 旧形式にも対応
  if (positionIndex < 0) {
    positionIndex = columnIndex(headers, "Position");
  }
  if (stepIndex < 0) stepIndex = 0;
  if (positionIndex < 0 && headers.size() > 1) positionIndex = 1;
  if (frequencyIndex < 0 && headers.size() > 2) {
    frequencyIndex = static_cast<int>(headers.size()) - 1;
  }

  if (positionIndex < 0 || frequencyIndex < 0) {
    throw std::runtime_error("Required columns were not found");
  }

  std::vector<Row> rows;

  while (std::getline(input, line)) {
    line = trim(line);
    if (line.empty() || line[0] == '#') continue;

    const std::vector<std::string> fields = splitCSV(line);
    const int maxIndex = std::max(stepIndex, std::max(positionIndex, frequencyIndex));
    if (static_cast<int>(fields.size()) <= maxIndex) continue;

    try {
      Row row;
      const double stepCount = std::stod(fields[stepIndex]);
      const double sstep =
          (sstepIndex >= 0 && sstepIndex < static_cast<int>(fields.size()))
              ? std::stod(fields[sstepIndex])
              : 1.0;

      row.step = stepCount * sstep;
      row.position = std::stod(fields[positionIndex]);
      row.frequency = std::stod(fields[frequencyIndex]);

      if (positionErrorIndex >= 0 &&
          positionErrorIndex < static_cast<int>(fields.size())) {
        row.positionError = std::stod(fields[positionErrorIndex]);
      }

      if (directionIndex >= 0 &&
          directionIndex < static_cast<int>(fields.size())) {
        row.direction = trim(fields[directionIndex]);
      }

      rows.push_back(row);
    } catch (...) {
      std::cerr << "Skipping invalid row: " << line << std::endl;
    }
  }

  return rows;
}

std::vector<Row> selectRows(const std::vector<Row>& rows,
                            const std::string& direction) {
  std::vector<Row> selected;
  for (const Row& row : rows) {
    if (row.direction == direction) selected.push_back(row);
  }
  return selected;
}

std::vector<double> zeros(std::size_t size) {
  return std::vector<double>(size, 0.0);
}

TGraphErrors* makeGraph(const std::vector<double>& x,
                        const std::vector<double>& y,
                        const std::vector<double>& xError,
                        const std::vector<double>& yError) {
  TGraphErrors* graph = new TGraphErrors(static_cast<int>(x.size()));
  for (std::size_t i = 0; i < x.size(); ++i) {
    graph->SetPoint(static_cast<int>(i), x[i], y[i]);
    graph->SetPointError(static_cast<int>(i), xError[i], yError[i]);
  }
  return graph;
}

void styleGraph(TGraphErrors* graph, int color, int marker) {
  graph->SetMarkerColor(color);
  graph->SetLineColor(color);
  graph->SetMarkerStyle(marker);
  graph->SetMarkerSize(0.8);
  graph->SetLineWidth(1);
}

void plotColumns(const std::vector<double>& xF,
                 const std::vector<double>& yF,
                 const std::vector<double>& exF,
                 const std::vector<double>& eyF,
                 const std::vector<double>& xB,
                 const std::vector<double>& yB,
                 const std::vector<double>& exB,
                 const std::vector<double>& eyB,
                 const std::vector<double>& xAll,
                 const std::vector<double>& yAll,
                 const std::vector<double>& exAll,
                 const std::vector<double>& eyAll,
                 const char* xLabel,
                 const char* yLabel,
                 const char* name) {
  TCanvas* canvas = new TCanvas(name, name, 900, 650);
  canvas->SetLeftMargin(0.15);
  canvas->SetBottomMargin(0.15);
  canvas->SetGrid();

  const bool hasBothDirections = !xF.empty() && !xB.empty();
  TGraphErrors* graphF = nullptr;
  TGraphErrors* graphB = nullptr;
  TGraphErrors* graphMain = nullptr;

  if (hasBothDirections) {
    graphF = makeGraph(xF, yF, exF, eyF);
    graphB = makeGraph(xB, yB, exB, eyB);

    styleGraph(graphF, kRed + 1, 20);
    styleGraph(graphB, kBlue + 1, 21);

    graphF->SetTitle(Form("%s;%s;%s", name, xLabel, yLabel));

    // A: 軸、P: 点、E: エラーバー
    graphF->Draw("APE");
    graphB->Draw("PE SAME");
    graphMain = graphF;

    TLegend* legend = new TLegend(0.68, 0.78, 0.93, 0.90);
    legend->AddEntry(graphF, "Forward (F)", "lep");
    legend->AddEntry(graphB, "Backward (B)", "lep");
    legend->Draw();
  } else {
    graphMain = makeGraph(xAll, yAll, exAll, eyAll);
    styleGraph(graphMain, kRed + 1, 20);
    graphMain->SetTitle(Form("%s;%s;%s", name, xLabel, yLabel));
    graphMain->Draw("APE");
  }

  // 全データに対する線形フィット
  if (xAll.size() >= 2 &&
      *std::min_element(xAll.begin(), xAll.end()) !=
          *std::max_element(xAll.begin(), xAll.end())) {
    const double xMin = *std::min_element(xAll.begin(), xAll.end());
    const double xMax = *std::max_element(xAll.begin(), xAll.end());

    TF1* fit = new TF1(Form("fit_%s", name), "pol1", xMin, xMax);
    fit->SetLineColor(kBlack);
    fit->SetLineStyle(2);
    fit->SetLineWidth(2);
    graphMain->Fit(fit, "Q+");

    double yMean = 0.0;
    for (double value : yAll) yMean += value;
    yMean /= yAll.size();

    double ssTotal = 0.0;
    double ssResidual = 0.0;
    for (std::size_t i = 0; i < xAll.size(); ++i) {
      ssTotal += (yAll[i] - yMean) * (yAll[i] - yMean);
      ssResidual += (yAll[i] - fit->Eval(xAll[i])) *
                    (yAll[i] - fit->Eval(xAll[i]));
    }
    const double r2 = ssTotal > 0.0 ? 1.0 - ssResidual / ssTotal : 0.0;

    TPaveText* box = new TPaveText(0.18, 0.70, 0.57, 0.90, "NDC");
    box->SetFillColor(0);
    box->SetTextAlign(12);
    box->AddText("Linear fit: y = a + b x");
    box->AddText(Form("a = %.5g #pm %.5g", fit->GetParameter(0), fit->GetParError(0)));
    box->AddText(Form("b = %.5g #pm %.5g", fit->GetParameter(1), fit->GetParError(1)));
    box->AddText(Form("R^{2} = %.5f", r2));
    box->Draw();
  }

  canvas->Update();
  canvas->SaveAs(Form("figures/%s.png", name));
}

void plot_run(const char* dataFile = "./data/20261005/Run1.txt") {
  gROOT->SetBatch(kFALSE);
  gSystem->Exec("mkdir -p figures");

  try {
    const std::vector<Row> rows = readRows(dataFile);
    if (rows.empty()) {
      throw std::runtime_error("No valid data rows found");
    }

    const std::vector<Row> rowsF = selectRows(rows, "F");
    const std::vector<Row> rowsB = selectRows(rows, "B");

    std::vector<double> stepF, posF, posErrF, freqF;
    std::vector<double> stepB, posB, posErrB, freqB;
    std::vector<double> stepAll, posAll, posErrAll, freqAll;

    for (const Row& row : rows) {
      stepAll.push_back(row.step);
      posAll.push_back(row.position);
      posErrAll.push_back(row.positionError);
      freqAll.push_back(row.frequency);
    }
    for (const Row& row : rowsF) {
      stepF.push_back(row.step);
      posF.push_back(row.position);
      posErrF.push_back(row.positionError);
      freqF.push_back(row.frequency);
    }
    for (const Row& row : rowsB) {
      stepB.push_back(row.step);
      posB.push_back(row.position);
      posErrB.push_back(row.positionError);
      freqB.push_back(row.frequency);
    }

    const char* stepLabel = "Total Steps (Step_Count #times Sstep)";

    // Step vs Position: Position1_Err をY方向のエラーにする
    plotColumns(
        stepF, posF, zeros(stepF.size()), posErrF,
        stepB, posB, zeros(stepB.size()), posErrB,
        stepAll, posAll, zeros(stepAll.size()), posErrAll,
        stepLabel, "Position 1", "step_vs_position");

    // Step vs Resonance: 周波数の誤差列がないためエラーなし
    plotColumns(
        stepF, freqF, zeros(stepF.size()), zeros(freqF.size()),
        stepB, freqB, zeros(stepB.size()), zeros(freqB.size()),
        stepAll, freqAll, zeros(stepAll.size()), zeros(freqAll.size()),
        stepLabel, "Resonance f0 (GHz)", "step_vs_resonance");

    // Position vs Resonance: Position1_Err をX方向のエラーにする
    plotColumns(
        posF, freqF, posErrF, zeros(freqF.size()),
        posB, freqB, posErrB, zeros(freqB.size()),
        posAll, freqAll, posErrAll, zeros(freqAll.size()),
        "Position 1", "Resonance f0 (GHz)", "position_vs_resonance");

    std::cout << "Plots saved in figures/" << std::endl;
  } catch (const std::exception& error) {
    std::cerr << "plot_run_errorbar.C: " << error.what() << std::endl;
  }
}
