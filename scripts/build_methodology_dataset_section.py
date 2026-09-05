from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Methodology_and_Dataset_Section.docx"


def shade(cell, fill="D9EAF2"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_repeat_table_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    tr_pr.append(repeat)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = True
    set_repeat_table_header(table.rows[0])
    for i, value in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = value
        shade(cell, "1F4E78")
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for run in cell.paragraphs[0].runs:
            run.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(8.5)
    for row_i, row in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if row_i % 2:
                shade(cells[i], "EAF2F8")
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for run in p.runs:
                    run.font.size = Pt(8.2)
    return table


def add_body(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Inches(0.3)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(6)
    return p


def add_equation(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    r = p.add_run(text)
    r.italic = True


def add_bullet(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(text)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(3)


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

    for name, size in (("Title", 18), ("Heading 1", 15), ("Heading 2", 13), ("Heading 3", 11.5)):
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
    footer.add_run("Methodology and Dataset")


def build():
    doc = Document()
    configure(doc)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("CHAPTER 3\nMETHODOLOGY")
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(31, 78, 121)

    add_body(doc, "This chapter describes the materials, dataset-construction procedure, quality-control strategy, computational representation, model-development pipeline, training protocol, and evaluation framework used to develop a domain-aware promoter-prediction system. The study was formulated as supervised binary classification: for an input DNA sequence x, the model estimates the probability P(y = 1 | x), where y = 1 denotes a promoter and y = 0 denotes a non-promoter. The central methodological requirement was to learn biologically meaningful promoter signals across Bacteria, Archaea, and Eukaryota while preventing information leakage between development and final evaluation data. Accordingly, the workflow combined curated positive examples, genome-derived negative examples, redundancy reduction, sequence-level auditing, reverse-complement-aware partitioning, domain-appropriate sequence representations, organism-specific predictive models, and validation-only model and threshold selection.")

    doc.add_heading("3.1 Research design and computational workflow", level=1)
    add_body(doc, "The research followed a quantitative computational-experimental design. No new wet-laboratory samples were produced; instead, experimentally supported promoter annotations and reference-genome regions were integrated from established biological databases and previously published datasets. The unit of analysis was an individual nucleotide sequence. Each record contained an original FASTA header, a nucleotide string, a biological domain, an organism label, and a binary class label. Six organism-level modeling groups were defined: Escherichia coli, Bacillus subtilis, an aggregated archaeal group, Homo sapiens, Mus musculus, and Arabidopsis thaliana. Organism-specific models were used because promoter grammar, motif spacing, nucleotide composition, and sequence-window length vary across taxa. Bacterial and eukaryotic domain-level results were therefore descriptive summaries of organism-level predictions rather than substitutes for organism-level evaluation.")
    add_body(doc, "The complete workflow consisted of the following stages: (1) collection of promoter and non-promoter sequences; (2) standardization to FASTA format and fixed, biologically defined windows; (3) independent redundancy reduction of each organism/class dataset using CD-HIT-EST; (4) a read-only audit of the finalized files; (5) construction of deterministic train, validation, and test partitions while grouping exact sequences and reverse complements; (6) nucleotide encoding and feature extraction; (7) training of candidate convolutional and sequence-context models; (8) construction of Random Forest and hybrid neural–feature ensembles; and (9) validation-based model selection followed by one untouched-test evaluation. Random seeds, file hashes, split membership, training histories, prediction probabilities, thresholds, and metrics were saved to support reproducibility.")

    doc.add_heading("3.2 Dataset collection and description", level=1)
    doc.add_heading("3.2.1 Taxonomic coverage and rationale", level=2)
    add_body(doc, "A multi-species dataset was assembled to represent promoter recognition across the three major domains of cellular life. The bacterial subset included the Gram-negative model organism E. coli and the Gram-positive model organism B. subtilis. The eukaryotic subset included two mammals, human and mouse, and the model plant A. thaliana. The archaeal subset comprised promoter data from Haloferax volcanii, Sulfolobus solfataricus, and Thermococcus kodakarensis and was analyzed as one aggregated archaeal group. This coverage was selected to expose the learning system to materially different transcriptional architectures. Bacterial promoters commonly contain compact upstream core elements, archaeal transcription combines bacterial-like genomic compactness with components homologous to the eukaryotic basal transcription machinery, and eukaryotic promoters occupy longer and more heterogeneous sequence contexts. The dataset was therefore designed for broad taxonomic representation, not to imply that the selected species exhaust the diversity of any domain.")

    doc.add_heading("3.2.2 Positive promoter datasets", level=2)
    add_body(doc, "Experimentally supported E. coli promoters were obtained from RegulonDB, a curated resource for transcriptional regulation in E. coli [1]. Each bacterial sequence covered positions −60 to +20 relative to the transcription start site (TSS), producing an 81-nucleotide window when both endpoints are included. B. subtilis promoters were collected from the DBTBS resource described by Ishii et al. [2]. These records represented an approximately 70-bp upstream promoter region and were stored as standardized 80-nucleotide sequences in the finalized dataset. Using curated promoter repositories reduced label uncertainty compared with identifying positives solely through motif scanning or unverified computational prediction.")
    add_body(doc, "Human, mouse, and A. thaliana promoter regions were obtained from EPDnew and, for mouse where applicable, DBTSS [3,4]. The eukaryotic windows extended from −200 to +50 relative to the TSS, giving a total length of 251 nucleotides. This interval retains proximal upstream regulatory information together with the immediate downstream context and is long enough to represent both localized core elements and broader compositional patterns. Archaeal promoters were obtained from the Prokaryotic Promoter Database (PPD). The archaeal window covered −80 to +20 relative to the TSS and consisted of 100 nucleotides in the finalized files. The promoter FASTA files were maintained separately by biological group so that redundancy filtering, auditing, splitting, training, and reporting could be performed without accidental cross-organism mixing.")

    doc.add_heading("3.2.3 Construction of non-promoter datasets", level=2)
    add_body(doc, "Negative-example design is critical in promoter prediction because an arbitrarily generated negative sequence can make classification unrealistically easy. For E. coli and B. subtilis, non-promoter examples were generated from the corresponding reference genomes. Random fragments were selected from protein-coding regions, and sequence was extracted from the opposite, non-coding strand. This strategy placed negative examples within authentic genomic DNA while reducing the probability that they represented the annotated promoter orientation. For the eukaryotic datasets, random 251-nucleotide fragments were extracted from gene regions downstream of the first exon. These regions were selected because they lie away from the principal upstream promoter interval and annotated TSS while retaining organism-specific genomic composition.")
    add_body(doc, "The archaeal non-promoter sequences were taken from the negative dataset previously used by Zhang et al. [5]. Repository provenance notes indicate that the archaeal negative filename corresponds to genomic +21 to +121 regions. They were consequently treated as genome-derived downstream negative regions and not described as shuffled promoters. Because unannotated or alternative transcription initiation can exist within genomes, no genome-derived negative-selection method can guarantee that every negative is biologically inactive under every condition. The negative label should therefore be interpreted operationally as ‘not annotated or selected as a promoter under the source protocol.’ This limitation is intrinsic to large-scale computational promoter datasets and was mitigated through curated positives, genomic rather than synthetic negatives, and strict separation of evaluation data.")

    doc.add_heading("3.2.4 Redundancy reduction using CD-HIT-EST", level=2)
    add_body(doc, "Highly similar sequences can inflate measured performance because near-duplicates may carry almost identical motifs into different data partitions. To increase sequence diversity and reduce this bias, promoter and non-promoter files were processed independently with CD-HIT-EST at a sequence-identity threshold of 0.90. Sequences meeting the clustering criterion were placed into similarity clusters, and one representative sequence from each cluster was retained. Independent processing preserved the biological class boundaries and prevented the clustering operation from selecting a representative across promoter and non-promoter labels. The finalized files, rather than the raw files, were used for all subsequent analyses and were not modified or reclustered by the modeling pipeline.")
    add_body(doc, "For B. subtilis, the provenance audit verified 766 raw promoter records and 766 raw non-promoter records; redundancy reduction retained 675 promoters and all 766 non-promoters. The finalized B. subtilis FASTA files matched the correctly located CD-HIT outputs byte-for-byte. For the archaeal promoter class, the repository contains 3,955 raw records and 3,624 finalized records, but the correctly labelled intermediate CD-HIT clustering artifact was unavailable. The finalized archaeal file was included because its content and size could be audited, but the raw-to-finalized archaeal clustering step cannot be claimed as fully reproducible until the original clustering output or command log is recovered. Reporting this limitation avoids overstating provenance completeness.")

    doc.add_heading("3.2.5 Final dataset composition", level=2)
    add_body(doc, "After redundancy reduction, the finalized dataset contained 99,321 DNA sequences: 49,094 promoter sequences (49.43%) and 50,227 non-promoter sequences (50.57%). Thus, the complete collection was nearly class-balanced, although the organism-level distributions varied. Every record within an organism group had the intended fixed length. The shorter bacterial and archaeal windows were retained rather than padded to the 251-nucleotide eukaryotic size during organism-specific modeling. Table 3.1 presents the exact finalized composition verified by counting FASTA headers and checking sequence lengths.")

    p = doc.add_paragraph("Table 3.1. Final promoter and non-promoter dataset composition after redundancy reduction")
    p.runs[0].bold = True
    add_table(doc,
              ["Domain", "Organism/group", "Source", "TSS-relative region", "Length (nt)", "Promoter", "Non-promoter", "Total"],
              [
                  ["Bacteria", "E. coli", "RegulonDB", "−60 to +20", "81", "3,204", "3,369", "6,573"],
                  ["Bacteria", "B. subtilis", "DBTBS", "≈70 bp upstream", "80", "675", "766", "1,441"],
                  ["Eukaryota", "H. sapiens", "EPDnew", "−200 to +50", "251", "19,596", "12,943", "32,539"],
                  ["Eukaryota", "M. musculus", "EPDnew/DBTSS", "−200 to +50", "251", "16,110", "23,291", "39,401"],
                  ["Eukaryota", "A. thaliana", "EPDnew", "−200 to +50", "251", "5,885", "2,866", "8,751"],
                  ["Archaea", "H. volcanii; S. solfataricus; T. kodakarensis", "PPD/published negatives", "−80 to +20", "100", "3,624", "6,992", "10,616"],
                  ["All", "Combined", "—", "—", "80–251", "49,094", "50,227", "99,321"],
              ])

    doc.add_heading("3.2.6 FASTA parsing and quality audit", level=2)
    add_body(doc, "The finalized directory was scanned recursively for standard FASTA extensions. Blank lines were ignored, multiline nucleotide records were concatenated, and all symbols were converted to uppercase. A sequence appearing before its FASTA header or a file containing no records generated an error. Biological domain, organism, and class were inferred from controlled directory and filename conventions. For each file, the audit recorded the number of sequences, unique sequences, unique headers, duplicate headers, exact duplicate sequences, minimum, maximum, mean and median length, complete length distribution, invalid symbols, sequences containing N, empty records, GC-content mean and standard deviation, and a SHA-256 file checksum. All twelve finalized files contained fixed-length records: 80 nt for B. subtilis, 81 nt for E. coli, 100 nt for Archaea, and 251 nt for each eukaryotic organism.")
    add_body(doc, "Each record received a stable internal identifier derived from the source path, record index, original header, and nucleotide sequence. Original FASTA headers and source filenames were retained in the manifest and prediction outputs to preserve traceability. Canonical nucleotides A, C, G, and T were accepted directly. The ambiguous symbol N was retained rather than replaced with a randomly selected nucleotide. Any other nucleotide character was treated as invalid. This distinction ensured that uncertainty in the source sequence did not introduce fabricated base information.")

    doc.add_heading("3.3 Leakage-aware partitioning", level=1)
    add_body(doc, "A deterministic 70:15:15 train–validation–test split was generated using seed 2025 and stratification by domain, organism, and class. Simple record-level random splitting was not considered sufficient because the same DNA fragment can occur in duplicate form or as its reverse complement. For each sequence s, the reverse complement RC(s) was computed, and a canonical representation was defined as the lexicographically smaller of s and RC(s). A truncated SHA-256 digest of this canonical string served as a group identifier. All members of the same exact/reverse-complement group were assigned to a single partition, thereby preventing a model from seeing one orientation in training and being evaluated on the opposite orientation.")
    add_equation(doc, "g(s) = SHA-256[min(s, RC(s))]")
    add_body(doc, "Groups were formed within organism-and-class strata, deterministically shuffled, and allocated toward cumulative 70%, 85%, and 100% targets. Because whole groups rather than individual records were assigned, counts can differ slightly from exact fractional targets. Cross-label conflicts were identified before splitting: if the same canonical sequence occurred as both promoter and non-promoter within a domain, the entire conflicting group was excluded from model development. Six reverse-complement conflict groups, comprising six archaeal promoters and six archaeal non-promoters, were quarantined. The resulting analysis set contained 99,309 records: 69,523 training records, 14,897 validation records, and 14,889 untouched test records. Validation data were used for checkpoint, feature, blend-weight, and decision-threshold selection; test data were reserved for final performance estimation.")

    p = doc.add_paragraph("Table 3.2. Exact leakage-aware partition counts")
    p.runs[0].bold = True
    add_table(doc,
              ["Organism/group", "Class", "Training", "Validation", "Test", "Quarantined"],
              [
                  ["E. coli", "Promoter", "2,243", "481", "480", "0"],
                  ["E. coli", "Non-promoter", "2,359", "505", "505", "0"],
                  ["B. subtilis", "Promoter", "473", "101", "101", "0"],
                  ["B. subtilis", "Non-promoter", "537", "115", "114", "0"],
                  ["Archaea", "Promoter", "2,533", "543", "542", "6"],
                  ["Archaea", "Non-promoter", "4,891", "1,048", "1,047", "6"],
                  ["H. sapiens", "Promoter", "13,718", "2,939", "2,939", "0"],
                  ["H. sapiens", "Non-promoter", "9,061", "1,941", "1,941", "0"],
                  ["M. musculus", "Promoter", "11,277", "2,417", "2,416", "0"],
                  ["M. musculus", "Non-promoter", "16,304", "3,494", "3,493", "0"],
                  ["A. thaliana", "Promoter", "4,120", "883", "882", "0"],
                  ["A. thaliana", "Non-promoter", "2,007", "430", "429", "0"],
                  ["Combined", "Both classes", "69,523", "14,897", "14,889", "12"],
              ])

    doc.add_heading("3.4 Sequence representation and engineered features", level=1)
    doc.add_heading("3.4.1 One-hot nucleotide encoding and masks", level=2)
    add_body(doc, "For neural-network input, each sequence was transformed into an L × 4 matrix, where L is the domain-appropriate maximum sequence length. Adenine, cytosine, guanine, and thymine were represented as [1,0,0,0], [0,1,0,0], [0,0,1,0], and [0,0,0,1], respectively. N was encoded as [0,0,0,0]. A nucleotide-validity mask distinguished canonical bases from N, whereas a position mask distinguished biological sequence positions from right-padding. Although finalized organism-specific records were fixed length, retaining separate masks made the implementation robust to valid shorter inputs and prevented zeros introduced by ambiguity or padding from being interpreted as biological evidence. Recurrent packing, Transformer attention, and global pooling used the position mask.")

    doc.add_heading("3.4.2 Statistical sequence features", level=2)
    add_body(doc, "A complementary classical representation was developed because promoter recognition can benefit from both learned spatial motifs and explicit compositional descriptors. Normalized k-mer frequencies were calculated so that features were comparable across records. Candidate vocabularies included strand-aware directional 1–4-mers and 1–6-mers, as well as reverse-complement-collapsed canonical 1–6-mers. In canonical encoding, a k-mer and its reverse complement mapped to one feature, reducing redundant dimensions. Position-specific features summarized motif and nucleotide behavior within promoter-relevant sequence windows. Dinucleotide thermodynamic-stability descriptors were calculated using nearest-neighbour DNA duplex free-energy values at 37 °C. Feature blocks were evaluated using grouped out-of-fold development predictions; a block was retained only when it improved MCC by at least 0.002. Selection was organism-specific because the usefulness of directionality, position, and stability differs among promoter systems.")

    doc.add_heading("3.5 Model development", level=1)
    doc.add_heading("3.5.1 Candidate neural architectures", level=2)
    add_body(doc, "Five neural architectures were implemented within a common PyTorch framework. The Residual CNN used one-dimensional convolutional projections followed by residual blocks containing convolution, batch normalization, GELU activation, dropout, and skip connections. Masked global mean and maximum pooling summarized distributed composition and the strongest motif activation. The Multi-scale CNN processed each sequence through parallel kernels of 3, 5, 7, and 11 nucleotides, allowing short core motifs and wider contextual patterns to be learned simultaneously before feature fusion and masked pooling.")
    add_body(doc, "The CNN–BiLSTM combined a convolutional motif extractor with a bidirectional long short-term memory network. Packed sequences ensured that padding did not affect recurrent states. The CNN–Transformer used a convolutional front end, sinusoidal positional encodings, and a pre-normalized Transformer encoder to represent long-range interactions; invalid padded positions were excluded through the attention mask. Finally, a domain-aware architecture used separate bacterial, archaeal, and eukaryotic input encoders, multi-scale convolution, a learned domain embedding, a shared Transformer, a shared promoter head, domain-specialist promoter heads, and an auxiliary domain-classification head. These models provided complementary mechanisms for local motif detection, motif-scale diversity, sequential dependence, global context, and shared-versus-specialized biological representation.")

    doc.add_heading("3.5.2 Random Forest and hybrid ensemble", level=2)
    add_body(doc, "For each organism group, a Random Forest classifier was trained on the feature blocks selected during development. The final forest used 500 decision trees, square-root feature subsampling at each split, a minimum of two samples per leaf, balanced-subsample class weighting, parallel CPU execution, and random seed 2025. In parallel, the selected CNN configuration was trained with seeds 2025, 2026, and 2027, and the three promoter probabilities were averaged. The CNN ensemble and Random Forest probabilities were then combined by a convex weighted average.")
    add_equation(doc, "p_hybrid = w × p_CNN + (1 − w) × p_RF,   0 ≤ w ≤ 1")
    add_body(doc, "The CNN weight w was searched from 0 to 1 in increments of 0.05 using validation predictions only. For every weight, the associated classification threshold was selected by validation MCC. Candidates were ranked first by MCC and then by precision–recall area under the curve (PR-AUC). Once selected, the Random Forest, feature list, CNN weight, and decision threshold were frozen and applied to the untouched test set. This late-fusion design allowed a sequence-level neural representation and interpretable compositional features to contribute without using test labels to determine their relative importance.")

    doc.add_heading("3.6 Training and optimization protocol", level=1)
    add_body(doc, "Neural models were trained with AdamW optimization. The standard learning rate was 3 × 10⁻⁴, weight decay was 1 × 10⁻⁴, and the gradient norm was clipped at 1.0. Dropout and batch normalization regularized convolutional representations. Binary cross-entropy with logits served as the primary objective. Where weighted loss was enabled, the positive-class weight was computed from training data only as Nnegative/Npositive. The training framework also supported inverse-frequency sampling over organism/class strata; sampling was confined to training and did not alter the natural validation or test distributions. For the multi-output domain-aware network, shared and specialist promoter losses were supplemented by a lower-weight auxiliary domain-classification loss.")
    add_body(doc, "Validation MCC controlled model development. A ReduceLROnPlateau scheduler reduced the learning rate after stalled validation progress, and early stopping terminated training when MCC did not improve for the configured patience. The current model, optimizer, scheduler, epoch, early-stopping counter, configuration hash, and training history were saved after every epoch. Separate checkpoints preserved the best validation MCC and best validation PR-AUC. Interrupted runs could therefore resume without resetting their optimization state. Random, NumPy, and PyTorch generators were seeded, deterministic PyTorch operations were requested where supported, and CPU thread counts were controlled. These procedures limited avoidable run-to-run variation and provided an auditable record of each experiment.")
    add_body(doc, "Architecture selection was conducted independently for the organism-level groups. The selection hierarchy was mean validation MCC, followed by PR-AUC, balanced accuracy, sensitivity–specificity balance, stability across seeds, and model simplicity. Test metrics were prohibited from model selection. The completed specialist configuration used Multi-scale CNNs for E. coli, B. subtilis, and Archaea and Residual CNNs for human, mouse, and A. thaliana. Each selected configuration was trained under three random seeds and combined by mean probability before hybridization with its organism-specific Random Forest.")

    doc.add_heading("3.7 Performance evaluation", level=1)
    add_body(doc, "The decision threshold was optimized on validation probabilities rather than assumed to be 0.50. Probabilities were sorted, all distinct candidate cut points were evaluated efficiently through cumulative confusion-matrix counts, and the threshold maximizing validation MCC was retained. If several thresholds achieved the same MCC, the threshold nearest 0.50 was selected. This frozen threshold was subsequently used for test classification. The primary metric was MCC because it uses true positives (TP), true negatives (TN), false positives (FP), and false negatives (FN) and remains informative when class proportions differ.")
    add_equation(doc, "MCC = (TP × TN − FP × FN) / √[(TP+FP)(TP+FN)(TN+FP)(TN+FN)]")
    add_body(doc, "Additional measures included accuracy, sensitivity (recall), specificity, precision, F1-score, balanced accuracy, false-positive rate, false-negative rate, receiver-operating-characteristic area under the curve (ROC-AUC), PR-AUC, and Brier score. ROC-AUC summarized ranking performance across thresholds, whereas PR-AUC emphasized positive-class retrieval and was particularly informative for imbalanced organism subsets. Balanced accuracy averaged sensitivity and specificity. The Brier score evaluated probability calibration by measuring mean squared error between predicted probabilities and observed binary outcomes. Confusion matrices were retained so that metric values could be traced to classification counts.")
    add_equation(doc, "Sensitivity = TP/(TP+FN);   Specificity = TN/(TN+FP);   Precision = TP/(TP+FP)")
    add_equation(doc, "F1 = 2 × (Precision × Recall)/(Precision + Recall)")
    add_body(doc, "Uncertainty for MCC, ROC-AUC, and PR-AUC was estimated using 1,000 nonparametric bootstrap resamples of the test predictions with seed 2025; the 2.5th and 97.5th percentiles formed a 95% interval. Organism-level test results were the primary outcomes. Where a domain summary combined multiple organisms, each metric was weighted by the number of test records for that organism. Such summaries were descriptive and were not used to choose architectures, thresholds, or ensemble weights.")

    doc.add_heading("3.8 Reproducibility, ethical considerations, and methodological limitations", level=1)
    add_body(doc, "Reproducibility was supported at both data and model levels. Original FASTA files were read without modification; SHA-256 hashes documented finalized inputs; a row-level manifest preserved source headers, class labels, canonical group identifiers, and partitions; and configuration files recorded architecture and optimizer settings. Saved prediction files contained internal identifiers, original headers, source files, true labels, probabilities, predicted labels, thresholds, model names, seeds, and partitions. The same split definitions were reused throughout feature ablation, neural training, Random Forest construction, and ensemble evaluation.")
    add_body(doc, "The study used publicly available or previously published genomic sequence resources and did not involve recruitment, intervention, or collection of personally identifiable human-subject information. Nevertheless, database licenses and citation requirements should be observed in any distribution of derived files. Human sequences were treated solely as genomic reference intervals for computational classification. The principal methodological limitations were possible residual label noise in genome-derived negatives, unequal numbers of records among organisms, aggregation of several archaeal organisms, and incomplete provenance for the intermediate archaeal CD-HIT output. Furthermore, fixed windows represent only local promoter context, and performance on the selected organisms does not by itself establish universal cross-species generalization. These constraints should be considered when interpreting results and when extending the system to additional taxa or experimental conditions.")

    doc.add_heading("3.9 Chapter summary", level=1)
    add_body(doc, "In summary, the methodology integrated 99,321 finalized promoter and non-promoter sequences from bacterial, archaeal, animal, and plant sources. Redundancy was reduced at 90% sequence identity; all files were audited for count, length, symbols, duplication, composition, and integrity; and twelve archaeal cross-label conflicts were quarantined. Exact sequences and reverse complements were grouped before deterministic stratified splitting. Neural networks learned positional motif representations from one-hot sequences, while Random Forests used organism-selected k-mer, positional, and stability features. Validation data controlled model, feature, blend-weight, checkpoint, and threshold decisions, and the untouched test set was used only after those decisions were frozen. This combination of biological diversity, leakage control, domain-aware modeling, and reproducible evaluation provides the methodological basis for the results presented in the following chapter.")

    doc.add_heading("References", level=1)
    refs = [
        "[1] Gama-Castro, S., Salgado, H., Santos-Zavaleta, A., Ledezma-Tejeida, D., et al. (2016). RegulonDB version 9.0: High-level integration of gene regulation, coexpression, motif clustering and beyond. Nucleic Acids Research, 44(D1), D133–D143.",
        "[2] Ishii, T., Yoshida, K., Terai, G., Fujita, Y., and Nakai, K. (2001). DBTBS: A database of Bacillus subtilis promoters and transcription factors. Nucleic Acids Research, 29(1), 278–280.",
        "[3] Dreos, R., Ambrosini, G., Périer, R., and Bucher, P. (2013). EPD and EPDnew, high-quality promoter resources in the next-generation sequencing era. Nucleic Acids Research, 41(Database issue), D157–D164.",
        "[4] Suzuki, A., Wakaguri, H., Yamashita, R., Kawano, S., Tsuchihara, K., Sugano, S., Suzuki, Y., and Nakai, K. (2015). DBTSS as an integrative platform for transcriptome, epigenome and genome sequence variation data. Nucleic Acids Research, 43(D1), D1–D5.",
        "[5] Zhang, M., et al. (2019). MULTiPly: A novel multi-layer predictor for discovering general and specific types of promoters. Bioinformatics, 35(17), 2957–2965.",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(4)

    doc.core_properties.title = "Methodology and Dataset Section"
    doc.core_properties.subject = "Domain-aware promoter prediction thesis methodology"
    doc.core_properties.author = "Research thesis draft"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
