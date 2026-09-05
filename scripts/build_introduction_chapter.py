from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Detailed_Introduction_Chapter.docx"


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
    footer.add_run("Introduction | Domain-Aware Promoter Prediction")


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
    run = p.add_run("CHAPTER 1\nINTRODUCTION")
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(31, 78, 121)

    body(doc, "The rapid growth of genomic sequence data has created an unprecedented opportunity to investigate gene regulation computationally. Genome sequencing can reveal the nucleotide composition of an organism, but sequence alone does not directly identify when and where genes are transcribed. One of the essential tasks in functional genome annotation is therefore the recognition of promoters: regulatory DNA regions that direct the assembly of transcription machinery and determine the initiation of RNA synthesis. Accurate promoter identification supports the study of gene-expression control, transcriptional networks, non-coding genetic variation, evolutionary regulation, and synthetic biology. However, promoters are structurally diverse and cannot be represented by one universal consensus sequence. This biological heterogeneity makes promoter prediction a challenging pattern-recognition problem and motivates computational methods capable of learning complex sequence relationships.")

    doc.add_heading("1.1 Background of the study", level=1)
    body(doc, "Gene expression is the process through which information encoded in DNA is used to produce functional RNA and protein molecules. Transcription constitutes the first major stage of this process. During transcription initiation, RNA polymerase and associated factors recognize regulatory signals near a transcription start site (TSS), form an initiation complex, locally unwind the DNA duplex, and begin RNA synthesis. Promoters provide the sequence environment required for this recognition. Their activity influences the timing, location, strength, and condition-specific regulation of gene expression. Errors in promoter annotation can consequently propagate into gene models, regulatory-network reconstruction, interpretation of non-coding variants, and downstream experimental design.")
    body(doc, "A promoter is not simply a single short motif. It can contain several elements whose function depends on their orientation, spacing, local nucleotide context, and interaction with transcription proteins. Some promoters resemble a consensus closely, whereas others remain functional despite deviations at multiple positions. Promoter strength and specificity may also depend on DNA structural properties, local duplex stability, chromatin organization, and regulatory factors that are not completely encoded by a small set of sequence motifs. The prediction problem is therefore best understood as the identification of a distributed regulatory pattern rather than exact matching against one word.")
    body(doc, "Experimental methods such as primer extension, cap analysis of gene expression, TSS sequencing, differential RNA sequencing, reporter assays, and chromatin-based measurements can locate or validate transcription initiation. These methods provide biologically valuable evidence but may require specialized laboratory resources and are not always available for every organism, tissue, condition, or genomic region. Computational promoter prediction complements experimentation by screening large collections of sequences and prioritizing candidate regions. It cannot replace experimental validation, but it can reduce the search space and help direct limited experimental resources toward the most plausible candidates.")

    doc.add_heading("1.2 Promoter architecture across biological domains", level=1)
    doc.add_heading("1.2.1 Bacterial promoters", level=2)
    body(doc, "In bacteria, transcription initiation commonly requires an RNA polymerase holoenzyme containing a sigma factor. Housekeeping promoters often contain recognizable signals near −35 and −10 relative to the TSS, but their exact nucleotide composition and spacing vary. Extended −10 elements, upstream elements, discriminator sequences, alternative sigma-factor classes, and transcription-factor binding sites create additional diversity [1]. A sequence may retain promoter activity without containing a perfect pair of consensus elements, while short consensus-like patterns can occur by chance in non-promoter genomic DNA. This explains why simple bacterial motif searches can produce both missed promoters and false-positive predictions.")
    body(doc, "Escherichia coli and Bacillus subtilis are important bacterial models. E. coli provides a well-characterized Gram-negative regulatory system supported by RegulonDB, whereas B. subtilis represents a major Gram-positive model supported by DBTBS [2,3]. Their inclusion enables evaluation across distinct bacterial promoter contexts. Nevertheless, a classifier combining the two organisms must accommodate unequal dataset sizes and biological differences. Strong performance for one species cannot automatically be interpreted as equivalent performance for the other.")

    doc.add_heading("1.2.2 Archaeal promoters", level=2)
    body(doc, "Archaea occupy a distinctive position in transcription biology. Their genomes are prokaryotic in organization, but their basal transcription apparatus shares important homology with the eukaryotic RNA polymerase II system. Archaeal promoter recognition commonly involves TATA-binding protein, transcription factor B, and transcription factor E. Regulatory elements can include a TATA box, B-recognition element, and initiator sequence around the TSS [4,5]. These characteristics justify treating archaeal promoters as a separate modeling domain rather than merging them with bacterial promoters merely because both groups lack a nucleus.")
    body(doc, "Computational research on archaeal promoters has generally had fewer annotated sequences and less species coverage than corresponding work on major bacterial and eukaryotic organisms. Combining data from multiple archaeal species can improve statistical power, but it may obscure lineage-specific promoter patterns. A domain-level archaeal model should therefore be interpreted as a model of the represented collection rather than proof of universal generalization to all archaeal genomes.")

    doc.add_heading("1.2.3 Eukaryotic promoters", level=2)
    body(doc, "Eukaryotic promoters are especially heterogeneous. RNA polymerase II core promoters may contain TATA boxes, initiator elements, downstream promoter elements, TFIIB-recognition elements, motif ten elements, TCT motifs, or combinations of these signals. Some promoters initiate transcription at a focused position, whereas others exhibit dispersed initiation. CpG-island-associated and non-CpG promoters also differ in composition and regulatory behavior. The core promoter consequently operates as a flexible platform that integrates several kinds of regulatory information rather than following one universal architecture [6].")
    body(doc, "The present study considers human, mouse, and Arabidopsis promoters. Human and mouse provide related mammalian systems, while Arabidopsis introduces a distant plant regulatory context. Their 251-nucleotide promoter windows contain more sequence context than the bacterial or archaeal windows and may include both core and proximal information. This added context can help prediction, but it also increases the number of possible patterns and the opportunity for organism-specific composition to influence the classifier.")

    doc.add_heading("1.3 Computational promoter prediction", level=1)
    body(doc, "Computational promoter prediction has developed through several methodological stages. Early approaches relied on known motifs, position weight matrices, discriminant functions, CpG islands, nucleotide composition, DNA stability, or combinations of predefined biological signals. These methods offered relatively direct interpretation, but their dependence on expected motifs limited their ability to recognize non-canonical promoters. When applied genome-wide, even a modest false-positive rate can generate large numbers of incorrect predictions because short motif-like sequences occur frequently outside functional promoters.")
    body(doc, "Traditional machine-learning approaches expanded the representation of promoter sequences through k-mer frequencies, pseudo nucleotide composition, position-dependent scores, autocorrelation, DNA physicochemical properties, and structural descriptors. Support vector machines, Random Forests, artificial neural networks, boosting, and nearest-neighbour methods learned classification boundaries from these engineered features. MULTiPly combined local and global sequence encodings through a multi-layer framework, while iProEP integrated composition and positional-correlation information [7,8]. These approaches demonstrated that promoter identity can be represented by multiple complementary descriptors. Their limitation is that performance depends on features specified in advance and may omit patterns not anticipated by the researcher.")
    body(doc, "Deep learning enables feature representations to be learned directly from nucleotide sequences. Convolutional neural networks (CNNs) scan DNA using trainable filters that can respond to motifs and higher-order local combinations. CNNProm demonstrated the feasibility of applying convolutional models to promoters from distant prokaryotic and eukaryotic organisms [9]. Residual networks support deeper convolutional processing, while multi-scale CNNs analyze several motif widths in parallel. Recurrent neural networks such as bidirectional long short-term memory models can represent sequential dependence, and Transformer encoders use self-attention to connect distant positions. More recent graph-based approaches incorporate structural relationships in addition to the linear sequence [10].")
    body(doc, "The increasing complexity of predictive models does not eliminate the value of engineered features. Neural networks and feature-based classifiers have different inductive biases and can make different errors. Weighted ensemble methods such as iPro-WAEL combine CNN and Random Forest probabilities to integrate learned and explicit representations across species [11]. This provides a strong rationale for hybrid promoter prediction, provided that feature blocks, mixture weights, checkpoints, and thresholds are selected using development data rather than the final test set.")

    doc.add_heading("1.4 Statement of the problem", level=1)
    body(doc, "Despite continuing progress, accurate and generalizable promoter prediction remains unresolved. The first difficulty is biological heterogeneity. Promoter architecture differs among Bacteria, Archaea, and Eukaryota and also among species within each domain. A model optimized for one organism can lose accuracy when applied elsewhere. iProEP and subsequent multi-species studies have shown that cross-species transfer remains difficult because promoter composition and regulatory organization are species dependent [8,12]. A universal model may gain statistical power from pooled data but can also learn domain identity or dataset-source artifacts instead of promoter biology.")
    body(doc, "The second difficulty is dataset construction. Positive promoters are drawn from databases that differ in experimental evidence, genome assembly, window definition, and annotation history. Negative examples may be shuffled sequences, random genomic fragments, coding regions, intergenic regions, or downstream gene segments. These alternatives differ greatly in difficulty and biological realism. A classifier can obtain high apparent performance by separating database or extraction protocols rather than identifying promoter activity. Similarly, redundant or nearly identical sequences can inflate evaluation if they occur across training and test partitions.")
    body(doc, "The third difficulty is experimental evaluation. Many studies report accuracy without adequately examining sensitivity, specificity, class imbalance, probability ranking, calibration, or initialization variability. Hyperparameter tuning and threshold selection can also leak information from the test set. Exact duplicates and reverse complements require group-aware partitioning because an opposite orientation of a training sequence should not become an apparently independent test case. Without these controls, measured performance may overstate generalization.")
    body(doc, "The fourth difficulty concerns representation. Handcrafted features are interpretable and computationally efficient but may not capture complex spatial motif relationships. Deep networks learn richer representations but require sufficient data, can vary across random initializations, and may be difficult to interpret. A single feature set or architecture is unlikely to be optimal for every taxonomic group. The research problem addressed by this thesis is therefore how to construct a reproducible, leakage-aware promoter-classification framework that respects domain and organism differences while combining complementary learned and engineered sequence information.")

    doc.add_heading("1.5 Research gap", level=1)
    body(doc, "The literature contains numerous species-specific predictors, several multi-species interfaces, and a smaller number of ensemble systems. However, important gaps remain at their intersection. First, multi-domain studies often apply one representation or architecture to all organisms despite major differences in sequence length and promoter biology. Second, feature selection is commonly global even though the predictive value of k-mer orientation, position, and physicochemical information may vary by taxon. Third, model comparisons frequently use random record-level splits without explicitly grouping exact sequences and reverse complements. Fourth, single-run results do not quantify sensitivity to neural initialization.")
    body(doc, "A further gap lies between strong classification benchmarks and reproducible experimental design. Published accuracy values are difficult to compare when window length, negative sampling, class balance, and test protocol differ. Some studies classify centered sequence windows, while others locate TSSs in long genomic regions. A robust framework should therefore define its task clearly, preserve the original data, document preprocessing, freeze partitions, separate development from final evaluation, and report multiple complementary measures. It should also avoid claiming universal superiority when candidate architectures have not all been evaluated under identical multi-seed conditions.")
    body(doc, "The present study addresses these gaps by integrating data from Bacteria, Archaea, animals, and plants; reducing sequence redundancy; auditing every finalized FASTA file; grouping exact and reverse-complement records; quarantining cross-label conflicts; retaining domain-appropriate sequence lengths; implementing multiple neural architectures; selecting engineered feature blocks by organism; averaging independent neural seeds; and combining neural and Random Forest probabilities with validation-selected weights. The contribution is therefore both predictive and methodological.")

    doc.add_heading("1.6 Aim of the study", level=1)
    body(doc, "The overall aim of this research is to develop and evaluate a reproducible domain-aware computational framework for distinguishing promoter from non-promoter DNA sequences across representative bacterial, archaeal, animal, and plant datasets by combining deep sequence learning with organism-specific engineered features.")

    doc.add_heading("1.7 Research objectives", level=1)
    objectives = [
        "To construct a multi-domain promoter and non-promoter dataset containing E. coli, B. subtilis, selected Archaea, human, mouse, and Arabidopsis sequences from curated or previously published sources.",
        "To reduce sequence redundancy and audit the finalized FASTA files for sequence count, length, duplication, nucleotide validity, ambiguity, GC composition, and file integrity.",
        "To create deterministic training, validation, and test partitions that preserve organism/class distributions while preventing exact-sequence and reverse-complement leakage.",
        "To represent DNA sequences through one-hot nucleotide matrices and complementary k-mer, position-specific, and dinucleotide-stability features.",
        "To implement and assess neural architectures capable of learning local motifs, multi-scale patterns, sequential dependencies, and domain-specific representations.",
        "To determine which engineered feature blocks contribute useful organism-specific information using leakage-aware development evaluation.",
        "To reduce dependence on individual neural initialization through multi-seed probability averaging.",
        "To construct hybrid CNN–Random Forest predictors using validation-selected probability weights and decision thresholds.",
        "To evaluate finalized systems on untouched test partitions using MCC, accuracy, sensitivity, specificity, precision, F1-score, balanced accuracy, ROC-AUC, PR-AUC, Brier score, confusion matrices, and bootstrap confidence intervals.",
        "To identify the strengths, limitations, practical implications, and future requirements of multi-domain promoter prediction.",
    ]
    for item in objectives:
        bullet(doc, item, numbered=True)

    doc.add_heading("1.8 Research questions", level=1)
    questions = [
        "Can promoter and non-promoter sequences be distinguished reliably across representative bacterial, archaeal, mammalian, and plant datasets using domain-specialized sequence models?",
        "Do multi-scale convolutional and residual sequence representations provide effective promoter classification at the natural sequence lengths of different domains?",
        "Does averaging predictions from independently initialized neural networks improve robustness compared with a single trained seed?",
        "Do explicit k-mer, positional, and thermodynamic features contribute complementary information, and are the most useful feature blocks organism dependent?",
        "Does a validation-weighted CNN–Random Forest hybrid improve discrimination over the CNN ensemble alone?",
        "How do sensitivity, specificity, ranking performance, calibration, and uncertainty differ among bacterial, archaeal, and eukaryotic systems?",
        "Which methodological limitations prevent the resulting models from being interpreted as universal promoter predictors?",
    ]
    for item in questions:
        bullet(doc, item, numbered=True)

    doc.add_heading("1.9 Research hypotheses", level=1)
    body(doc, "The study was guided by the following testable expectations. First, promoter and non-promoter sequences contain learnable differences in local motif structure and global composition, so domain-specialized models should perform substantially above chance. Second, multi-scale convolution should be advantageous for shorter bacterial and archaeal windows because relevant signals occur at several motif widths. Third, multi-seed probability averaging should improve robustness by reducing initialization variance. Fourth, engineered sequence features should contribute differently across organisms because promoter architecture is taxon dependent. Fifth, a hybrid of neural and Random Forest probabilities should improve at least some discrimination measures when the component errors are complementary.")
    body(doc, "These expectations were evaluated through held-out prediction rather than formal mechanistic experiments. A positive result would demonstrate predictive association between sequence representation and promoter label; it would not prove that every influential model feature is causally involved in transcription initiation. Biological interpretation therefore remains bounded by the source annotations, negative-selection procedures, and absence of direct experimental perturbation in the present work.")

    doc.add_heading("1.10 Significance of the study", level=1)
    doc.add_heading("1.10.1 Biological significance", level=2)
    body(doc, "Promoter identification supports understanding of how genes are regulated and how transcriptional programs differ across organisms. A computational framework covering Bacteria, Archaea, mammals, and plants creates a basis for comparing sequence-level regulatory information across divergent transcription systems. Organism-specific feature selection can also generate hypotheses about the relative importance of motif directionality, oligomer composition, positional organization, and local DNA stability. These hypotheses require biological validation but can guide targeted analysis.")

    doc.add_heading("1.10.2 Computational significance", level=2)
    body(doc, "Computationally, the research combines representation learning and engineered features rather than treating them as competing alternatives. It implements a common training and evaluation pipeline while allowing architecture, input length, feature blocks, mixture weights, and thresholds to vary where biologically justified. The emphasis on deterministic splitting, group-aware leakage prevention, multi-seed evaluation, and saved prediction artifacts improves reproducibility and provides a more defensible basis for interpreting model performance.")

    doc.add_heading("1.10.3 Practical significance", level=2)
    body(doc, "Practically, a trained promoter classifier can rank candidate sequences for further investigation and reduce the number of regions requiring experimental screening. The resulting web interface accepts individual DNA sequences or FASTA files and returns promoter probabilities and class predictions. Such predictions are intended as decision support rather than experimental proof. Their most appropriate use is to prioritize candidates while preserving awareness of the training domain, sequence-length requirements, operating threshold, and possibility of false-negative or false-positive decisions.")

    doc.add_heading("1.11 Original contributions", level=1)
    contributions = [
        "A unified, audited dataset spanning representative sequences from all three domains of cellular life, including bacterial, archaeal, mammalian, and plant groups.",
        "A deterministic partitioning strategy that groups exact sequences with their reverse complements and quarantines canonical sequence groups carrying conflicting labels.",
        "Domain-appropriate processing that preserves natural bacterial, archaeal, and eukaryotic input lengths instead of forcing every sequence into one global length.",
        "Implementation of multiple neural mechanisms for local, multi-scale, recurrent, attention-based, and shared/domain-specific promoter representation.",
        "Organism-specific selection of directional or canonical k-mers, positional descriptors, and dinucleotide-stability features.",
        "A two-stage ensemble combining three-seed neural probability averaging with validation-weighted Random Forest fusion.",
        "A reproducible evaluation framework based on untouched-test predictions, validation-selected thresholds, multiple discrimination and calibration metrics, confusion matrices, and bootstrap uncertainty.",
        "A deployable prediction interface linked to the saved domain-specific hybrid artifacts.",
    ]
    for item in contributions:
        bullet(doc, item)

    doc.add_heading("1.12 Scope and delimitations", level=1)
    body(doc, "The study addresses binary classification of fixed DNA windows as promoter or non-promoter. It does not directly locate a TSS within an unrestricted chromosome, predict promoter strength, identify sigma-factor subclasses, estimate tissue-specific activity, or model enhancer–promoter interaction. The finalized dataset includes E. coli, B. subtilis, selected archaeal organisms, Homo sapiens, Mus musculus, and Arabidopsis thaliana. Other bacterial phyla, additional archaeal lineages, fungi, protists, and most plant and animal species are outside the empirical scope.")
    body(doc, "Predictions are based primarily on DNA sequence. The models do not directly incorporate gene expression, chromatin accessibility, histone modification, methylation, transcription-factor concentration, three-dimensional genome organization, or experimental condition. These factors can be essential to in-vivo promoter usage, especially in eukaryotes. The term promoter prediction in this thesis therefore refers to sequence-based discrimination under the labeling rules of the assembled datasets.")
    body(doc, "The completed confirmatory neural results correspond to selected Multi-scale CNN specialists for Bacteria and Archaea and a selected Residual CNN specialist for Eukaryota, each evaluated across three seeds. Other architectures were implemented but were not all completed under the same multi-seed confirmatory protocol. The study consequently evaluates successful finalized systems but does not claim exhaustive architectural optimization or universal state-of-the-art superiority. External species validation and wet-laboratory confirmation remain outside the current scope.")

    doc.add_heading("1.13 Key terms", level=1)
    terms = [
        ("Promoter", "A regulatory DNA region associated with recruitment of transcription machinery and initiation of RNA synthesis."),
        ("Transcription start site (TSS)", "The genomic nucleotide at which synthesis of an RNA transcript begins."),
        ("Non-promoter", "A sequence selected under the dataset protocol as not belonging to the annotated promoter class; it is not a guarantee of inactivity under every biological condition."),
        ("One-hot encoding", "A four-channel numerical representation in which A, C, G, and T are assigned distinct binary vectors."),
        ("k-mer", "A contiguous nucleotide word of length k used as a sequence feature."),
        ("CNN", "A convolutional neural network that learns local filters over ordered nucleotide positions."),
        ("Random Forest", "An ensemble of decision trees trained on sampled data and feature subsets."),
        ("Hybrid model", "A predictor that combines probabilities from neural and feature-based classifiers."),
        ("MCC", "Matthews correlation coefficient, a balanced measure derived from all four entries of the binary confusion matrix."),
        ("Information leakage", "Use of information during model development that would not be legitimately available when predicting independent data."),
    ]
    for label, definition in terms:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.first_line_indent = Inches(-0.2)
        p.paragraph_format.space_after = Pt(4)
        p.add_run(label + ": ").bold = True
        p.add_run(definition)

    doc.add_heading("1.14 Organization of the thesis", level=1)
    body(doc, "Chapter 1 introduces promoter biology, the computational problem, research gap, aim, objectives, questions, significance, contributions, and scope. Chapter 2 reviews promoter architecture, biological databases, dataset construction, conventional machine learning, deep learning, hybrid approaches, cross-species prediction, and evaluation practices. Chapter 3 describes dataset collection, redundancy reduction, auditing, leakage-aware partitioning, sequence representation, model development, training, ensembling, and evaluation. Chapter 4 presents the finalized neural, feature-ablation, and hybrid results. Chapter 5 interprets these findings, relates them to the research questions, discusses practical and biological implications, identifies limitations, and proposes future work. The final chapter provides the overall conclusion and recommendations arising from the study.")

    doc.add_heading("1.15 Chapter summary", level=1)
    body(doc, "Promoters are essential regulatory sequences whose computational identification remains challenging because their architecture is heterogeneous within and across biological domains. Experimental mapping supplies the most direct evidence but cannot always provide complete coverage, creating an important role for computational prediction. Earlier motif-based and feature-based systems established that promoter sequences contain useful signals, while deep learning enabled direct representation learning. Current research still faces species specificity, inconsistent negative construction, sequence redundancy, leakage, initialization variability, and limited interpretability. This thesis addresses these issues through a multi-domain, organism-sensitive, leakage-aware hybrid framework. The following chapter examines the literature in detail and establishes the scientific context for the selected research design.")

    doc.add_heading("References", level=1)
    refs = [
        "[1] Ruff, E. F., Record, M. T., and Artsimovitch, I. (2015). Initial events in bacterial transcription initiation. Biomolecules, 5(2), 1035–1062.",
        "[2] Gama-Castro, S., Salgado, H., Santos-Zavaleta, A., Ledezma-Tejeida, D., et al. (2016). RegulonDB version 9.0: High-level integration of gene regulation, coexpression, motif clustering and beyond. Nucleic Acids Research, 44(D1), D133–D143.",
        "[3] Ishii, T., Yoshida, K., Terai, G., Fujita, Y., and Nakai, K. (2001). DBTBS: A database of Bacillus subtilis promoters and transcription factors. Nucleic Acids Research, 29(1), 278–280.",
        "[4] Gehring, A. M., Walker, J. E., and Santangelo, T. J. (2016). Transcription regulation in Archaea. Journal of Bacteriology, 198(14), 1906–1917.",
        "[5] Blombach, F., Ausiannikava, D., Figueiredo, A. M., and Allers, T. (2021). Archaeal transcription. Emerging Topics in Life Sciences, 5(3), 343–353.",
        "[6] Roy, A. L., and Singer, D. S. (2015). Core promoters in transcription: Old problem, new insights. Trends in Biochemical Sciences, 40(3), 165–171.",
        "[7] Zhang, M., Li, F., Marquez-Lago, T. T., Leier, A., Fan, C., Kwoh, C. K., Chou, K. C., Song, J., and Jia, C. (2019). MULTiPly: A novel multi-layer predictor for discovering general and specific types of promoters. Bioinformatics, 35(17), 2957–2965.",
        "[8] Lai, H. Y., Zhang, Z. Y., Su, Z. D., Su, W., Ding, H., Chen, W., and Lin, H. (2019). iProEP: A computational predictor for predicting promoter. Molecular Therapy—Nucleic Acids, 17, 337–346.",
        "[9] Umarov, R. K., and Solovyev, V. V. (2017). Recognition of prokaryotic and eukaryotic promoters using convolutional deep learning neural networks. PLOS ONE, 12(2), e0171410.",
        "[10] Zhang, Q., Wei, Y., and Liu, L. (2024). GraphPro: An interpretable graph neural network-based model for identifying promoters in multiple species. Computers in Biology and Medicine, 180, 108974.",
        "[11] Zhang, P., Zhang, H., Wu, H., et al. (2022). iPro-WAEL: A comprehensive and robust framework for identifying promoters in multiple species. Nucleic Acids Research, 50(18), 10278–10289.",
        "[12] Wang, J., et al. (2025). iPro-MP: A BERT-based model to predict multiple prokaryotic promoters. Genome Biology. https://doi.org/10.1186/s13059-025-03819-9.",
    ]
    for ref in refs:
        p = doc.add_paragraph(ref)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(4)

    doc.core_properties.title = "Detailed Introduction Chapter"
    doc.core_properties.subject = "Domain-aware promoter prediction thesis introduction"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
