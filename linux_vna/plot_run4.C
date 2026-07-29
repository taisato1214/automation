// plot_run4.C
// ROOT macro to plot comparisons of rows in Run4.txt
// Rows: 1 vs 2, 2 vs 3, 1 vs 3
// Each point: Position (x) vs Resonance_f0_GHz (y)

void plot_run4() {
  gROOT->SetBatch(kFALSE); // ensure interactive mode
  // Path to data file (relative to macro location)
  const char *dataFile = "data/20260722/Run4.txt";
  std::ifstream in(dataFile);
  if (!in.is_open()) {
    std::cerr << "Cannot open " << dataFile << std::endl;
    return;
  }
  std::string line;
  // Skip header
  std::getline(in, line);
  std::vector<double> step, pos, freq;
  while (std::getline(in, line)) {
    if (line.empty())
      continue;
    std::stringstream ss(line);
    std::string token;
    std::vector<std::string> cols;
    while (std::getline(ss, token, ',')) {
      cols.push_back(token);
    }
    if (cols.size() < 3)
      continue;
    step.push_back(std::stod(cols[0]));
    pos.push_back(std::stod(cols[1]));
    freq.push_back(std::stod(cols[2]));
  }
  in.close();
  if (step.size() < 3) {
    std::cerr << "Not enough rows in Run4.txt" << std::endl;
    return;
  }
  // Helper function to plot column pairs with linear fit
  auto plotColumns = [&](const std::vector<double> &x,
                         const std::vector<double> &y, const char *xLabel,
                         const char *yLabel, const char *name) {
    TCanvas *c = new TCanvas(name, name, 800, 600);
    c->SetLeftMargin(0.15);   // 左余白を広げて軸ラベルを見やすく
    c->SetBottomMargin(0.15); // 下余白を広げて軸ラベルを見やすく
    c->SetRightMargin(0.05);  // 右余白は最小限に
    c->SetTopMargin(0.08);    // 上余白も少し確保

    TGraph *g = new TGraph(x.size());
    for (size_t i = 0; i < x.size(); ++i) {
      g->SetPoint(i, x[i], y[i]);
    }
    g->SetMarkerStyle(20);
    g->SetMarkerSize(1.5);
    g->SetTitle(Form("%s;%s;%s", name, xLabel, yLabel));
    g->SetMarkerColor(kRed);
    g->Draw("AP");

    // --- Linear fit ---
    TF1 *fitFunc = new TF1(Form("fit_%s", name), "pol1",
                           *std::min_element(x.begin(), x.end()),
                           *std::max_element(x.begin(), x.end()));
    fitFunc->SetLineColor(kBlue);
    fitFunc->SetLineWidth(2);
    g->Fit(fitFunc, "Q"); // "Q" = quiet mode (no printout)

    double slope     = fitFunc->GetParameter(1);
    double intercept = fitFunc->GetParameter(0);
    double slopeErr  = fitFunc->GetParError(1);
    double intErr    = fitFunc->GetParError(0);

    // Compute R² = 1 - SS_res / SS_tot
    double yMean = 0;
    for (double v : y) yMean += v;
    yMean /= y.size();
    double ssTot = 0, ssRes = 0;
    for (size_t i = 0; i < x.size(); ++i) {
      double diff = y[i] - yMean;
      ssTot += diff * diff;
      double res = y[i] - fitFunc->Eval(x[i]);
      ssRes += res * res;
    }
    double r2 = (ssTot > 0) ? 1.0 - ssRes / ssTot : 0.0;

    // --- Display fit results on canvas ---
    // Position: NDC coordinates (top-left area, avoiding axes)
    TPaveText *pt = new TPaveText(0.18, 0.68, 0.58, 0.90, "NDC");
    pt->SetFillColor(0);
    pt->SetFillStyle(1001);
    pt->SetBorderSize(1);
    pt->SetTextAlign(12);
    pt->SetTextFont(42);
    pt->SetTextSize(0.035);
    pt->AddText("Linear Fit:  y = a + b #times x");
    pt->AddText(Form("a (intercept) = %.4g #pm %.4g", intercept, intErr));
    pt->AddText(Form("b (slope)     = %.4g #pm %.4g", slope, slopeErr));
    pt->AddText(Form("R^{2}          = %.5f", r2));
    pt->Draw();

    c->Update();
    c->SaveAs(Form("figures/%s.png", name));
    c->Draw(); // display on screen
               // keep canvas alive for interactive viewing (no delete)
  };
  // Ensure figures directory exists (ROOT can call system mkdir)
  gSystem->Exec("mkdir -p figures");
  // Plot column pairs
  plotColumns(step, pos, "Step Count", "Position", "step_vs_position");
  plotColumns(step, freq, "Step Count", "Resonance (GHz)", "step_vs_resonance");
  plotColumns(pos, freq, "Position", "Resonance (GHz)",
              "position_vs_resonance");
  std::cout << "Column comparison plots saved in figures/" << std::endl;
}
