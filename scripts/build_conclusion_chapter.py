from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Detailed_Conclusion_Chapter.docx"


def configure(doc):
    section = doc.sections[0]
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.paragraph_format.line_spacing = 1.5
    for name, size in (("Title", 18), ("Heading 1", 15), ("Heading 2", 13)):
        style = doc.styles[name]
        style.font.name = "Times New Roman"
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor(31, 78, 121)
        style.paragraph_format.keep_with_next = True
        style.paragraph_format.space_before = Pt(10)
        style.paragraph_format.space_after = Pt(5)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("Conclusion and Recommendations | Domain-Aware Promoter Prediction")


def body(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Inches(0.3)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(6)
    return p


def bullet(doc, text, numbered=False):
    p = doc.add_paragraph(style="List Number" if numbered else "List Bullet")
    p.add_run(text)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(4)
    return p


def build():
    doc = Document()
    configure(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("CHAPTER 6\nCONCLUSION AND RECOMMENDATIONS")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor(31, 78, 121)

    body(doc, "This thesis investigated the computational identification of promoter DNA sequences across representative bacterial, archaeal, animal, and plant datasets. The work was motivated by the biological diversity of promoter organization and by methodological weaknesses that can lead to optimistic computational evaluation, including sequence redundancy, reverse-complement leakage, inconsistent negative construction, single-run reporting, and test-informed model selection. To address these issues, a domain-aware and leakage-controlled framework was developed that combines audited sequence data, deterministic group-aware partitioning, deep sequence learning, organism-specific engineered features, multi-seed probability averaging, and validation-weighted hybrid prediction.")

    doc.add_heading("6.1 Summary of the research", level=1)
    body(doc, "A multi-domain dataset was assembled from curated and previously published promoter resources. It included E. coli and B. subtilis from Bacteria; a combined group containing H. volcanii, S. solfataricus, and T. kodakarensis from Archaea; and human, mouse, and Arabidopsis from Eukaryota. Following redundancy reduction at 90% sequence identity, the finalized collection contained 99,321 sequences: 49,094 promoters and 50,227 non-promoters. The finalized files were audited for sequence count, length, duplication, invalid symbols, ambiguous nucleotides, GC composition, and file integrity.")
    body(doc, "A deterministic 70:15:15 training, validation, and test protocol was then applied. Exact sequences and reverse complements were assigned a common canonical group identifier so that equivalent records could not cross data partitions. Six archaeal canonical groups containing contradictory promoter and non-promoter labels were quarantined, removing twelve records from model development and evaluation. The resulting analysis partitions contained 69,523 training sequences, 14,897 validation sequences, and 14,889 test sequences. This procedure provided a stronger basis for generalization assessment than unrestricted record-level random splitting.")
    body(doc, "The modeling framework used one-hot nucleotide representations for neural learning and complementary directional or canonical k-mers, position-specific descriptors, and dinucleotide-stability features for Random Forest classification. Multiple neural architectures were implemented, including Residual CNN, Multi-scale CNN, CNN–BiLSTM, CNN–Transformer, and a domain-aware network. The completed confirmatory systems used Multi-scale CNNs for Bacteria and Archaea and a Residual CNN for Eukaryota. Each selected network was trained using seeds 2025, 2026, and 2027, after which probabilities were averaged. Final hybrid models combined the neural ensemble with a domain-specific Random Forest through validation-selected mixture weights and thresholds.")

    doc.add_heading("6.2 Conclusions in relation to the research objectives", level=1)
    body(doc, "The first objective, construction and verification of a multi-domain promoter dataset, was achieved. The final collection provided broad representation across the three cellular domains while retaining separate organism identities where supported by the data. All FASTA files had consistent within-group lengths, and the exact dataset composition was documented. The use of curated positive sources and genomic or previously published negatives produced a biologically meaningful classification task, although negative labels remain operational rather than absolute.")
    body(doc, "The second objective, prevention of avoidable information leakage, was achieved through redundancy reduction, canonical exact/reverse-complement grouping, conflict quarantine, deterministic stratification, and preservation of a final untouched test partition. This is an important contribution because high predictive performance is scientifically valuable only when evaluation records are independent of the information used during training and selection.")
    body(doc, "The third objective, development of domain-appropriate neural representations, was also achieved. The finalized Multi-scale CNNs learned promoter signals from the shorter bacterial and archaeal windows, while the Residual CNN learned from the larger 251-nucleotide eukaryotic windows. All three neural ensembles achieved meaningful discrimination. The results support the use of specialized models rather than assuming that one architecture, sequence length, or threshold is automatically suitable across all domains.")
    body(doc, "The fourth objective concerned organism-specific engineered features. Grouped out-of-fold ablation demonstrated that useful feature blocks varied among taxa. E. coli and Archaea retained directional 1–4-mers; B. subtilis retained canonical 1–6-mers; human selected directional 1–6-mers; mouse selected canonical k-mers with position-specific information; and Arabidopsis selected canonical k-mers, positional descriptors, and dinucleotide stability. This variation confirms that a universal handcrafted feature set would have ignored meaningful taxonomic differences.")
    body(doc, "The fifth objective was to improve robustness through ensembling and hybridization. Multi-seed probability averaging improved MCC and PR-AUC over the original single-seed model in every domain. Hybridization subsequently increased MCC and both ranking measures relative to the CNN-only ensembles. The outcome confirms that independently initialized neural models and explicit feature-based classifiers provide complementary predictive information, although the magnitude and error trade-offs differ by domain.")

    doc.add_heading("6.3 Answers to the research questions", level=1)
    bullet(doc, "Promoter and non-promoter sequences were distinguished reliably in all three domains. The final hybrid MCC values were 0.624 for Bacteria, 0.844 for Archaea, and 0.723 for Eukaryota, demonstrating substantial predictive association rather than majority-class behavior.", numbered=True)
    bullet(doc, "Multi-scale convolution was effective for the shorter bacterial and archaeal windows, while residual convolution was effective for the longer and larger eukaryotic dataset. These findings support domain-appropriate architecture selection, although they do not prove global superiority over every implemented candidate.", numbered=True)
    bullet(doc, "Three-seed probability averaging improved robustness. Neural MCC increased from the original seed-2025 values of 0.561, 0.810, and 0.696 to 0.617, 0.842, and 0.708 for Bacteria, Archaea, and Eukaryota, respectively.", numbered=True)
    bullet(doc, "Engineered sequence features contributed complementary and organism-dependent information. The selected combinations differed across all six biological groups, supporting taxon-specific feature selection.", numbered=True)
    bullet(doc, "CNN–Random Forest hybridization improved MCC, ROC-AUC, and PR-AUC in each domain. The largest MCC improvement occurred in Eukaryota, while bacterial and archaeal hybrids primarily improved sensitivity and ranking at the cost of some specificity.", numbered=True)
    bullet(doc, "Error profiles differed substantially among domains. Archaea achieved the strongest and most balanced performance. Bacterial prediction remained the most difficult, while the eukaryotic system combined high specificity and precision with lower sensitivity.", numbered=True)
    bullet(doc, "The models cannot yet be considered universal promoter predictors because species coverage was limited, negative protocols differed, the archaeal group was aggregated, external validation was not performed, and all candidate neural architectures were not completed under one identical multi-seed confirmatory comparison.", numbered=True)

    doc.add_heading("6.4 Principal findings", level=1)
    body(doc, "The final bacterial hybrid used 90% CNN and 10% Random Forest probability. It achieved accuracy of 0.813, sensitivity of 0.723, specificity of 0.888, MCC of 0.624, ROC-AUC of 0.879, and PR-AUC of 0.869. The large CNN weight indicates that learned spatial features provided the main bacterial signal, while the engineered component contributed a modest improvement and recovered additional promoters.")
    body(doc, "The final archaeal hybrid used 45% CNN and 55% Random Forest probability. It achieved accuracy of 0.930, sensitivity of 0.904, specificity of 0.943, MCC of 0.844, ROC-AUC of 0.977, and PR-AUC of 0.965. This was the strongest final system. Hybridization markedly improved promoter sensitivity and ranking, although some specificity and probability calibration were exchanged. The result demonstrates that accuracy alone would not have captured the change in operating behavior.")
    body(doc, "The final eukaryotic hybrid also used 45% CNN and 55% Random Forest probability. It achieved accuracy of 0.855, sensitivity of 0.770, specificity of 0.945, MCC of 0.723, ROC-AUC of 0.918, and PR-AUC of 0.939. It showed the clearest overall benefit from hybridization because both sensitivity and specificity improved. The combination of neural and engineered representations therefore provided complementary information across the heterogeneous human, mouse, and Arabidopsis collection.")
    body(doc, "Across the three domains, the selected thresholds differed considerably. This confirms that a fixed threshold of 0.50 would not have represented the preferred MCC-based trade-off for every model. Validation-specific thresholding was therefore not merely a technical detail; it was necessary to translate probability rankings into defensible class decisions without inspecting test labels.")

    doc.add_heading("6.5 Contributions of the study", level=1)
    contributions = [
        "Construction and complete auditing of a 99,321-sequence promoter/non-promoter dataset spanning representative bacterial, archaeal, mammalian, and plant groups.",
        "Implementation of deterministic exact- and reverse-complement-aware partitioning with explicit quarantine of cross-label conflicts.",
        "Preservation of natural domain sequence lengths and mask-aware nucleotide representations.",
        "Implementation of a common framework containing residual, multi-scale, recurrent, Transformer, and domain-aware neural candidates.",
        "Organism-specific selection of engineered sequence features through grouped development evaluation.",
        "Two-stage ensemble construction using multi-seed neural averaging followed by validation-weighted CNN–Random Forest fusion.",
        "Comprehensive test evaluation using threshold-dependent, ranking, calibration, confusion-matrix, and bootstrap-uncertainty measures.",
        "Preservation of manifests, hashes, configuration files, model artifacts, probabilities, and training histories for reproducibility.",
        "Development of a web-based interface for applying the finalized domain-specific prediction artifacts to individual sequences or FASTA files.",
    ]
    for item in contributions:
        bullet(doc, item)

    doc.add_heading("6.6 Limitations", level=1)
    body(doc, "The conclusions must be interpreted within the boundaries of the assembled datasets. Only two bacterial species, three explicitly identified archaeal species in an aggregated file, two mammals, and one plant were represented. Fungi, protists, most bacterial and archaeal lineages, and the great majority of animal and plant diversity were absent. Within-domain results are therefore evidence for the represented datasets rather than universal taxonomic coverage.")
    body(doc, "Positive and negative records originated from different databases and construction protocols. Genome-derived negatives may include unannotated or condition-specific promoters, while systematic compositional differences between selected genomic regions can become predictive. The missing correctly labelled intermediate archaeal CD-HIT artifact also limits complete reconstruction of that one raw-to-finalized preprocessing transition, despite the finalized archaeal files being audited and consistently used.")
    body(doc, "The completed confirmatory neural evaluation covered selected specialist architectures rather than an exhaustive, identically controlled comparison of every implemented model. The CNN–BiLSTM, CNN–Transformer, and proposed unified domain-aware model require full multi-seed evaluation before conclusions can be drawn about their relative performance. Likewise, organism-specific feature ablation was performed on development predictions and should not be treated as an independent external confirmation of biological mechanism.")
    body(doc, "Finally, predictions were based on local DNA sequence and derived sequence features. They did not directly model chromatin state, expression, transcription-factor concentration, methylation, cellular condition, or long-range regulatory interactions. The models identify sequence patterns associated with the dataset labels; they do not experimentally demonstrate promoter activity or causal regulatory function.")

    doc.add_heading("6.7 Recommendations", level=1)
    recommendations = [
        "Validate the finalized models on independently collected promoter datasets that were not used in dataset construction, model selection, or threshold determination.",
        "Expand taxonomic coverage to additional bacterial phyla, archaeal lineages, fungi, non-model plants, invertebrates, and vertebrates.",
        "Conduct leave-one-species-out experiments to measure genuine cross-species transfer and distinguish multi-species coverage from unseen-species generalization.",
        "Complete the same multi-seed evaluation for Residual CNN, Multi-scale CNN, CNN–BiLSTM, CNN–Transformer, and the proposed domain-aware architecture under identical partitions and selection rules.",
        "Use paired prediction-level statistical tests when comparing architectures or ensembles evaluated on the same test sequences.",
        "Construct multiple matched negative sets, including coding, intergenic, downstream, GC-matched, and hard near-promoter negatives, and report performance separately for each category.",
        "Recover or regenerate the correctly labelled archaeal CD-HIT intermediate and record complete software versions and command parameters for raw-to-finalized reproducibility.",
        "Extend interpretation through in-silico mutagenesis, attribution analysis, convolutional-filter motif extraction, positional enrichment, and comparison with experimentally established promoter elements.",
        "Evaluate probability calibration and provide application-specific high-sensitivity and high-precision thresholds rather than relying on one operating point for all use cases.",
        "Experimentally validate high-confidence novel promoter predictions using appropriate reporter assays or TSS-mapping techniques.",
    ]
    for item in recommendations:
        bullet(doc, item, numbered=True)

    doc.add_heading("6.8 Final conclusion", level=1)
    body(doc, "This research demonstrates that promoter recognition across diverse biological domains benefits from a combination of specialization and integration. Specialization is required because sequence length, promoter architecture, useful engineered features, probability distribution, and decision threshold differ among taxa. Integration is valuable because multi-scale or residual neural representations, explicit sequence descriptors, and independent random initializations provide complementary information. The resulting framework achieved meaningful discrimination in every domain and produced its strongest performance in Archaea, while the largest hybrid improvement occurred in Eukaryota.")
    body(doc, "Equally important, the study demonstrates that promoter-prediction performance must be supported by defensible data design. Redundancy control, exact/reverse-complement grouping, conflict quarantine, fixed partitions, validation-only selection, multi-seed assessment, untouched-test evaluation, and transparent artifact preservation are central scientific requirements rather than optional implementation details. They determine whether reported metrics represent genuine predictive generalization or accidental reuse of information.")
    body(doc, "Within its stated scope, the thesis provides a reproducible domain-aware hybrid framework for sequence-based promoter classification. The models should be regarded as computational prioritization tools for the represented organisms, not replacements for experimental evidence or universal predictors for all species. With broader external validation, standardized negative controls, complete architecture comparison, improved interpretation, and experimental confirmation, the framework can provide a strong foundation for more general and biologically informative promoter-discovery systems.")

    doc.core_properties.title = "Detailed Conclusion and Recommendations Chapter"
    doc.core_properties.subject = "Conclusion of domain-aware promoter prediction thesis"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
