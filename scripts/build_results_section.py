from __future__ import annotations

import json
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RESULTS_JSON = ROOT / "results" / "main_tables" / "multiseed_ensemble.json"
FIGURES = ROOT / "results" / "main_figures"
OUTPUT = REPORTS / "Results.docx"

DOMAINS = ("bacteria", "archaea", "eukaryota")
LABELS = {"bacteria": "Bacteria", "archaea": "Archaea", "eukaryota": "Eukaryota"}
RUNS = {
    "bacteria": ("multiscale_cnn", "screening"),
    "archaea": ("multiscale_cnn", "screening"),
    "eukaryota": ("residual_cnn", "eukaryota_multiscale"),
}
INITIAL = {
    "bacteria": ROOT / "results/checkpoints/bacteria/multiscale_cnn/seed_2025/test_metrics.json",
    "archaea": ROOT / "results/checkpoints/archaea/multiscale_cnn/seed_2025/test_metrics.json",
    "eukaryota": ROOT / "results/checkpoints/eukaryota/residual_cnn/seed_2025/test_metrics.json",
}


def shade(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), fill)
    props.append(node)


def add_table(document, headers, rows, font_size=8.5):
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for index, header in enumerate(headers):
        cell = table.rows[0].cells[index]
        cell.text = header
        shade(cell, "24435C")
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(font_size)
    for row_index, row in enumerate(rows):
        cells = table.add_row().cells
        for index, value in enumerate(row):
            cells[index].text = str(value)
            if row_index % 2:
                shade(cells[index], "EAF0F4")
            for run in cells[index].paragraphs[0].runs:
                run.font.size = Pt(font_size)
    table.autofit = True
    return table


def fmt(value):
    return f"{value:.3f}"


def architecture_label(name):
    return "Multi-scale CNN" if name == "multiscale_cnn" else "Residual CNN"


def load_results():
    ensemble = json.loads(RESULTS_JSON.read_text())
    per_seed = {}
    initial = {}
    for domain in DOMAINS:
        model, config = RUNS[domain]
        per_seed[domain] = {}
        for seed in (2025, 2026, 2027):
            root = ROOT / "results" / "checkpoints" / domain / model / config / f"seed_{seed}"
            per_seed[domain][seed] = {
                "validation": json.loads((root / "validation_metrics.json").read_text()),
                "test": json.loads((root / "test_metrics.json").read_text()),
                "run": json.loads((root / "run.json").read_text()),
            }
        initial[domain] = json.loads(INITIAL[domain].read_text())
    return ensemble, per_seed, initial


def add_figure(document, path, width, caption):
    document.add_picture(str(path), width=Inches(width))
    document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph = document.add_paragraph(caption)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.runs[0].italic = True


def build_organism_results(payload):
    """Build the final report for organism-specific models and weighted domain summaries."""
    document = Document()
    document.styles["Normal"].font.name = "Times New Roman"
    document.styles["Normal"].font.size = Pt(11)
    document.add_heading("Results", 0)
    document.add_paragraph(
        "Promoter classifiers were trained and thresholded independently for E. coli, "
        "B. subtilis, Archaea, Human, Mouse, and Arabidopsis. This separation avoids forcing "
        "organisms with different promoter composition—including the opposing Arabidopsis "
        "GC-content signal—into one decision boundary."
    )
    document.add_heading("Organism-level test performance", level=1)
    rows=[]
    for group, item in payload["organism_models"].items():
        score=item["test"]
        rows.append([item["organism"], item["domain"].title(), architecture_label(item["model"]),
                     item["test_count"], fmt(item["threshold"]), fmt(score["accuracy"]),
                     fmt(score["mcc"]), fmt(score["roc_auc"]), fmt(score["pr_auc"])])
    add_table(document,["Organism","Reporting domain","Model","Test n","Threshold","Accuracy","MCC","ROC-AUC","PR-AUC"],rows,8)
    document.add_paragraph(
        "Each threshold was selected exclusively from that organism's validation predictions. "
        "Test predictions from different organisms were not pooled to choose a common threshold."
    )
    document.add_heading("Weighted domain-level performance", level=1)
    rows=[]
    for domain,item in payload["domain_weighted_average"].items():
        score=item["test"]
        rows.append([domain.title(), ", ".join(item["groups"]), item["test_count"],
                     fmt(score["accuracy"]),fmt(score["mcc"]),fmt(score["roc_auc"]),fmt(score["pr_auc"])])
    add_table(document,["Domain","Contributing models","Test n","Accuracy","MCC","ROC-AUC","PR-AUC"],rows,8)
    document.add_paragraph(
        "Domain-level values are descriptive test-count-weighted averages of the corresponding "
        "organism-level metrics. Organism-level results remain the primary inferential results, "
        "because a weighted average of nonlinear metrics such as MCC is not equivalent to an MCC "
        "computed from a pooled confusion matrix."
    )
    REPORTS.mkdir(parents=True,exist_ok=True); document.save(OUTPUT); print(OUTPUT)


def build():
    payload=json.loads(RESULTS_JSON.read_text())
    if "organism_models" in payload:
        return build_organism_results(payload)
    ensemble, per_seed, initial = load_results()
    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.7)
    section.bottom_margin = Inches(0.7)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    document.styles["Normal"].font.name = "Times New Roman"
    document.styles["Normal"].font.size = Pt(11)
    for name, size in (("Title", 20), ("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 11.5)):
        document.styles[name].font.name = "Times New Roman"
        document.styles[name].font.size = Pt(size)
        document.styles[name].font.color.rgb = RGBColor(26, 55, 76)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("Results")
    run.bold = True
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(26, 55, 76)
    subtitle = document.add_paragraph("Domain-specialized promoter prediction and finalized ensemble performance")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.runs[0].italic = True

    document.add_heading("1. Overview of completed experiments", level=1)
    document.add_paragraph(
        "The completed experiments evaluated fixed-configuration domain-specialized promoter classifiers for Bacteria, Archaea, and Eukaryota. Multi-scale CNNs were used for the bacterial and archaeal domains, while a compact Residual CNN was used for the larger eukaryotic dataset. "
        "Each specialist architecture was trained independently with random seeds 2025, 2026, and 2027. Individual checkpoints were selected using validation Matthews correlation coefficient (MCC), after which validation probabilities were averaged to determine a single ensemble threshold. "
        "The frozen ensemble and threshold were then applied once to the untouched test set."
    )
    document.add_paragraph(
        "The results presented in this chapter therefore include individual seed-level validation and test performance, finalized three-seed ensemble performance, confusion-matrix analysis, and bootstrap confidence intervals. "
        "These are the finalized results for the selected fixed configurations. They do not constitute a complete comparison of all five implemented architectures."
    )

    document.add_heading("2. Individual seed-level results", level=1)
    rows = []
    for domain in DOMAINS:
        model, _ = RUNS[domain]
        for seed in (2025, 2026, 2027):
            validation = per_seed[domain][seed]["validation"]
            test = per_seed[domain][seed]["test"]
            rows.append([
                LABELS[domain], architecture_label(model), seed,
                fmt(validation["mcc"]), fmt(validation["pr_auc"]),
                fmt(test["mcc"]), fmt(test["pr_auc"]), fmt(test["roc_auc"]),
            ])
    document.add_paragraph("Table 1. Validation and test performance of individual seed models").runs[0].bold = True
    add_table(document, ["Domain", "Architecture", "Seed", "Val. MCC", "Val. PR-AUC", "Test MCC", "Test PR-AUC", "Test ROC-AUC"], rows, 8)
    document.add_paragraph(
        "The bacterial seed models produced test MCC values of "
        f"{fmt(per_seed['bacteria'][2025]['test']['mcc'])}, {fmt(per_seed['bacteria'][2026]['test']['mcc'])}, and {fmt(per_seed['bacteria'][2027]['test']['mcc'])}. "
        "This domain displayed the greatest sensitivity to random initialization, with seed 2027 producing the strongest individual result. "
        "The archaeal seed models were consistently stronger than the bacterial models, while the eukaryotic models showed comparatively narrow variation across seeds because of the substantially larger dataset."
    )

    document.add_heading("3. Finalized ensemble performance", level=1)
    final_rows = []
    for domain in DOMAINS:
        item = ensemble[domain]
        metric = item["test"]
        final_rows.append([
            LABELS[domain], architecture_label(item["model"]), fmt(item["threshold"]),
            fmt(metric["accuracy"]), fmt(metric["sensitivity"]), fmt(metric["specificity"]),
            fmt(metric["precision"]), fmt(metric["f1"]), fmt(metric["mcc"]),
            fmt(metric["balanced_accuracy"]), fmt(metric["roc_auc"]), fmt(metric["pr_auc"]),
        ])
    document.add_paragraph("Table 2. Final test performance of three-seed probability ensembles").runs[0].bold = True
    add_table(document, ["Domain", "Model", "Threshold", "Accuracy", "Sensitivity", "Specificity", "Precision", "F1", "MCC", "Bal. Acc.", "ROC-AUC", "PR-AUC"], final_rows, 7.2)
    add_figure(document, FIGURES / "ensemble_performance.png", 7.0, "Figure 1. Principal test metrics for the finalized three-seed ensembles.")

    document.add_heading("3.1 Bacterial ensemble", level=2)
    b = ensemble["bacteria"]["test"]
    document.add_paragraph(
        f"The finalized bacterial Multi-scale CNN ensemble achieved an MCC of {fmt(b['mcc'])}, PR-AUC of {fmt(b['pr_auc'])}, ROC-AUC of {fmt(b['roc_auc'])}, and balanced accuracy of {fmt(b['balanced_accuracy'])}. "
        f"Its sensitivity was {fmt(b['sensitivity'])}, whereas specificity reached {fmt(b['specificity'])}. The difference between these values indicates that the selected validation threshold favored conservative promoter prediction: non-promoters were rejected more reliably than promoters were detected. "
        f"Precision was {fmt(b['precision'])}, demonstrating that most sequences predicted as promoters were correct, although the false-negative rate of {fmt(b['false_negative_rate'])} shows that a meaningful fraction of promoters remained undetected."
    )

    document.add_heading("3.2 Archaeal ensemble", level=2)
    a = ensemble["archaea"]["test"]
    document.add_paragraph(
        f"The archaeal Multi-scale CNN ensemble produced the strongest overall result. It achieved an MCC of {fmt(a['mcc'])}, PR-AUC of {fmt(a['pr_auc'])}, ROC-AUC of {fmt(a['roc_auc'])}, and balanced accuracy of {fmt(a['balanced_accuracy'])}. "
        f"Sensitivity and specificity were {fmt(a['sensitivity'])} and {fmt(a['specificity'])}, respectively, indicating strong performance for both promoter detection and non-promoter rejection. "
        f"The precision of {fmt(a['precision'])} further shows that positive archaeal predictions were highly reliable. The high ranking metrics demonstrate that promoter and non-promoter probabilities remained well separated across a wide range of thresholds."
    )

    document.add_heading("3.3 Eukaryotic ensemble", level=2)
    e = ensemble["eukaryota"]["test"]
    document.add_paragraph(
        f"The finalized eukaryotic Residual CNN ensemble achieved an MCC of {fmt(e['mcc'])}, PR-AUC of {fmt(e['pr_auc'])}, ROC-AUC of {fmt(e['roc_auc'])}, and balanced accuracy of {fmt(e['balanced_accuracy'])}. "
        f"The model obtained high specificity ({fmt(e['specificity'])}) and precision ({fmt(e['precision'])}), whereas sensitivity was lower at {fmt(e['sensitivity'])}. "
        "The eukaryotic classifier therefore produced few false promoter calls but missed a larger proportion of true promoters. This behavior is consistent with a conservative validation-selected operating threshold and the biological heterogeneity of promoters pooled across human, mouse, and Arabidopsis."
    )

    document.add_heading("4. Confusion-matrix analysis", level=1)
    add_figure(document, FIGURES / "ensemble_confusion_matrices.png", 7.1, "Figure 2. Test-set confusion matrices at the validation-selected ensemble thresholds.")
    confusion_rows = []
    for domain in DOMAINS:
        matrix = ensemble[domain]["test"]["confusion_matrix"]
        tn, fp = matrix[0]
        fn, tp = matrix[1]
        confusion_rows.append([LABELS[domain], f"{tn:,}", f"{fp:,}", f"{fn:,}", f"{tp:,}"])
    document.add_paragraph("Table 3. Confusion-matrix counts for the finalized test predictions").runs[0].bold = True
    add_table(document, ["Domain", "TN", "FP", "FN", "TP"], confusion_rows)
    document.add_paragraph(
        "The bacterial ensemble correctly classified 574 non-promoters and 370 promoters, with 60 false positives and 165 false negatives. The archaeal ensemble produced 1,005 true negatives and 472 true positives, while limiting errors to 42 false positives and 70 false negatives. "
        "The eukaryotic ensemble correctly rejected 5,504 non-promoters and detected 4,748 promoters; however, it generated 1,489 false negatives compared with 359 false positives. These counts reinforce the observation that the eukaryotic operating point prioritized specificity and precision over maximum sensitivity."
    )

    document.add_heading("5. Bootstrap uncertainty", level=1)
    ci_rows = []
    for domain in DOMAINS:
        ci = ensemble[domain]["test_bootstrap_95_ci"]
        ci_rows.append([
            LABELS[domain],
            f"{fmt(ci['mcc'][0])}-{fmt(ci['mcc'][1])}",
            f"{fmt(ci['roc_auc'][0])}-{fmt(ci['roc_auc'][1])}",
            f"{fmt(ci['pr_auc'][0])}-{fmt(ci['pr_auc'][1])}",
        ])
    document.add_paragraph("Table 4. Bootstrap 95% confidence intervals from 1,000 test resamples").runs[0].bold = True
    add_table(document, ["Domain", "MCC 95% CI", "ROC-AUC 95% CI", "PR-AUC 95% CI"], ci_rows)
    document.add_paragraph(
        "The bacterial MCC interval was the widest relative to its point estimate, reflecting its smaller test set and greater seed-level variability. The archaeal interval remained clearly above the bacterial interval, supporting the conclusion that the archaeal system achieved stronger classification performance under the current experimental conditions. "
        "The eukaryotic intervals were narrow because of the large test partition, indicating that its reported metrics were estimated with comparatively high precision. These confidence intervals quantify sampling uncertainty but do not replace paired significance testing between alternative architectures."
    )

    document.add_heading("6. Improvement produced by multi-seed ensembling", level=1)
    improvement_rows = []
    for domain in DOMAINS:
        old = initial[domain]
        new = ensemble[domain]["test"]
        improvement_rows.append([
            LABELS[domain], fmt(old["mcc"]), fmt(new["mcc"]), f"{new['mcc']-old['mcc']:+.3f}",
            fmt(old["pr_auc"]), fmt(new["pr_auc"]), f"{new['pr_auc']-old['pr_auc']:+.3f}",
        ])
    document.add_paragraph("Table 5. Change from the original single-seed model to the finalized ensemble").runs[0].bold = True
    add_table(document, ["Domain", "Initial MCC", "Ensemble MCC", "Δ MCC", "Initial PR-AUC", "Ensemble PR-AUC", "Δ PR-AUC"], improvement_rows, 8)
    document.add_paragraph(
        "Probability averaging improved MCC in all three domains. The largest gain was observed for Bacteria, where MCC increased from 0.561 to 0.617. Archaea improved from 0.810 to 0.842, while Eukaryota improved from 0.696 to 0.708. "
        "PR-AUC also increased in every domain. The consistent improvement suggests that independent initializations learned complementary decision boundaries and that probability averaging reduced model variance. Nevertheless, statistical significance of these gains would require paired comparison of ensemble and individual predictions."
    )

    document.add_heading("7. Comparative interpretation", level=1)
    document.add_paragraph(
        "Across domains, the archaeal ensemble delivered the strongest classification and ranking performance. The eukaryotic ensemble ranked second by MCC and produced the highest positive-prediction reliability after Archaea, but its lower sensitivity indicates that promoter diversity remained challenging. "
        "The bacterial ensemble had the lowest MCC, PR-AUC, and balanced accuracy. This result may reflect the smaller bacterial dataset, differences between Gram-negative and Gram-positive promoter structures, and residual organism-specific heterogeneity after balanced sampling."
    )
    document.add_paragraph(
        "The selected thresholds differed substantially among domains: 0.876 for Bacteria, 0.598 for Archaea, and 0.560 for Eukaryota. These differences demonstrate why a universal threshold of 0.50 was inappropriate. "
        "The high bacterial threshold increased precision and specificity but also contributed to reduced sensitivity. Thresholds were selected only from validation predictions, so these operating characteristics were not adjusted in response to test-set errors."
    )

    document.add_heading("8. Finalized results summary", level=1)
    document.add_paragraph(
        "The finalized fixed-configuration systems were a three-seed Multi-scale CNN ensemble for Bacteria, a three-seed Multi-scale CNN ensemble for Archaea, and a three-seed Residual CNN ensemble for Eukaryota. "
        "Their final test MCC values were 0.617, 0.842, and 0.708, respectively. Corresponding PR-AUC values were 0.860, 0.954, and 0.932. The ensembles improved MCC and PR-AUC over the original single-seed models in every domain and produced reproducible test predictions with bootstrap confidence intervals."
    )

    document.add_heading("9. Scope and limitations of the reported results", level=1)
    document.add_paragraph(
        "The reported results are finalized for the selected fixed architectures and three-seed probability ensembles. They were obtained using leakage-controlled partitions, validation-only checkpoint and threshold selection, and untouched test evaluation. "
        "However, these findings should not be interpreted as evidence that the selected specialists are globally optimal among all five implemented architectures. A complete publication-level architecture comparison would additionally require training every candidate architecture across each domain, group-aware cross-validation, evaluation of the proposed unified model, biological controls, interpretability experiments, ablations, and paired statistical comparisons."
    )
    document.add_paragraph(
        "Accordingly, the present results provide a defensible and reproducible evaluation of the completed specialist ensembles, while broader claims concerning architectural superiority or universal cross-domain generalization should be reserved until the remaining experiments have been completed."
    )

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Results | Domain-Specialized Promoter Prediction")
    REPORTS.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
