from pathlib import Path
import re

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Detailed_Literature_Review_Chapter.docx"


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
    footer.add_run("Literature Review | Computational Promoter Prediction")


def body(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.first_line_indent = Inches(0.3)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(6)
    return p


def shade(cell, fill):
    props = cell._tc.get_or_add_tcPr()
    node = OxmlElement("w:shd")
    node.set(qn("w:fill"), fill)
    props.append(node)


def table(doc, headers, rows, size=7.8):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    header_props = t.rows[0]._tr.get_or_add_trPr()
    repeat = OxmlElement("w:tblHeader")
    repeat.set(qn("w:val"), "true")
    header_props.append(repeat)
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = h
        shade(c, "1F4E78")
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        for r in c.paragraphs[0].runs:
            r.bold = True
            r.font.color.rgb = RGBColor(255, 255, 255)
            r.font.size = Pt(size)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if ri % 2:
                shade(cells[i], "EAF2F8")
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(0)
                for r in p.runs:
                    r.font.size = Pt(size)
    return t


def caption(doc, text):
    p = doc.add_paragraph(text)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.runs[0].bold = True


def build():
    doc = Document()
    configure(doc)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("CHAPTER 2\nLITERATURE REVIEW")
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(18)
    r.font.color.rgb = RGBColor(31, 78, 121)

    body(doc, "Promoters are central cis-regulatory regions that direct the initiation of transcription and influence when, where, and at what level genes are expressed. Their computational identification is therefore important for genome annotation, regulatory-network analysis, interpretation of non-coding variation, and the design of synthetic regulatory sequences. Despite decades of research, promoter prediction remains difficult because promoter sequences are heterogeneous, many promoters lack a single universally conserved motif, and genomic non-promoter regions can resemble individual promoter elements. The problem becomes more challenging when a predictor is expected to operate across evolutionarily distant organisms whose transcriptional machinery and promoter architecture differ. This chapter reviews the biological foundations of promoter recognition, the principal promoter databases and dataset-design practices, conventional and deep-learning methods, evaluation concerns, and the unresolved research gap motivating a domain-aware hybrid approach.")

    doc.add_heading("2.1 Biological foundations of transcription initiation", level=1)
    body(doc, "Transcription begins when RNA polymerase and associated initiation factors recognize regulatory information surrounding a transcription start site (TSS), assemble an initiation complex, unwind the DNA duplex, and begin RNA synthesis. A promoter is consequently not defined by one motif alone; it is a functional sequence context whose elements act in combination with transcription machinery. The relative position, orientation, spacing, nucleotide composition, DNA stability, and accessibility of these elements can all influence promoter activity. Sequence-based prediction attempts to infer this functional potential from the nucleotide string, although the full in-vivo process may also depend on transcription-factor abundance, chromatin state, DNA methylation, nucleosome occupancy, and cellular condition [1–3].")
    body(doc, "The term core promoter usually denotes the region immediately surrounding the TSS that is sufficient to direct accurate initiation by the basal machinery. Additional proximal and distal regulatory elements can modulate the frequency and specificity of transcription. For computational studies, promoters are normally represented as fixed windows relative to a mapped TSS. This representation makes supervised learning possible but creates an important dependency on window choice. A short interval emphasizes core motifs and spacing, whereas a longer interval can include broader compositional information and proximal regulatory signals. Different studies therefore address related but non-identical prediction tasks when they use different coordinate ranges.")

    doc.add_heading("2.2 Diversity of promoter architecture across domains", level=1)
    doc.add_heading("2.2.1 Bacterial promoters", level=2)
    body(doc, "Bacterial transcription initiation is commonly mediated by RNA polymerase associated with a sigma factor. Promoters recognized by the housekeeping sigma factor often contain elements centered near −35 and −10 relative to the TSS, with spacing between these elements affecting recognition. Extended −10 elements, upstream elements, discriminator sequences, alternative sigma-factor motifs, and transcription-factor binding sites create substantial diversity [1,2]. A promoter may deviate from the consensus at multiple positions while remaining active because the contribution of one element can compensate for another. Consequently, exact motif matching produces false negatives, while scanning for short consensus-like words throughout a genome produces false positives.")
    body(doc, "E. coli and B. subtilis are widely used model organisms, but they represent different bacterial lineages and regulatory systems. E. coli is Gram-negative and has extensive curated regulatory information in RegulonDB, whereas B. subtilis is a Gram-positive model supported by DBTBS [4,5]. Even within one species, promoter classes associated with different sigma factors can follow different sequence rules. A predictor trained on one bacterial promoter collection may therefore perform poorly on another organism or promoter subclass unless the model captures both shared sequence organization and species-specific variation.")

    doc.add_heading("2.2.2 Archaeal promoters", level=2)
    body(doc, "Archaea possess compact genomes but use a transcription-initiation apparatus that is evolutionarily and structurally related to the eukaryotic RNA polymerase II system. Archaeal initiation typically involves TATA-binding protein, transcription factor B, and transcription factor E homologues. Common promoter elements include a TATA box, the upstream B-recognition element, and an initiator signal around the TSS [3,6]. This mixture of prokaryotic genome organization and eukaryote-related basal machinery makes Archaea a distinct prediction problem rather than a simple extension of bacterial modeling.")
    body(doc, "Archaeal promoter datasets have historically been smaller and taxonomically narrower than major bacterial and human resources. Aggregating several archaeal species can provide sufficient data for machine learning, but it can also conceal organism-specific differences in GC content, optimal growth conditions, regulatory proteins, and promoter consensus. Literature on multi-species prediction therefore supports explicit reporting of the represented organisms and cautions against using a strong result on selected archaeal species as evidence of universal archaeal generalization.")

    doc.add_heading("2.2.3 Eukaryotic promoters", level=2)
    body(doc, "Eukaryotic RNA polymerase II promoters are highly heterogeneous. Recognized core elements include the TATA box, initiator, downstream promoter element, motif ten element, TFIIB-recognition elements, and TCT motif, but these occur in different combinations rather than as a universal template [7]. Promoters may be focused around a narrow initiation site or dispersed over a broader region. CpG-island-associated and non-CpG promoters also have different compositional characteristics. The core promoter acts as both an assembly platform and an active participant in regulatory integration, which helps explain why fixed consensus models have limited genome-wide performance [7].")
    body(doc, "Human and mouse share mammalian regulatory properties, whereas Arabidopsis represents a distant plant lineage. A model spanning these organisms must therefore accommodate differences in base composition, motif prevalence, chromatin organization, and TSS distribution. High-throughput TSS mapping, including CAGE and TSS-seq, has greatly expanded eukaryotic promoter collections. EPDnew integrates experimentally supported promoter annotations with promoter-specific high-throughput evidence, while DBTSS provides precise TSS information and associated transcriptomic or epigenomic context [8,9]. These resources support larger learning datasets but do not eliminate biological or technical variation among tissues, assays, genome assemblies, and database releases.")

    doc.add_heading("2.3 Promoter databases and benchmark datasets", level=1)
    body(doc, "Reliable computational prediction begins with reliable labels. RegulonDB organizes experimentally supported and computationally inferred information on E. coli transcriptional regulation, operons, promoters, and regulatory sites [4]. DBTBS was established to consolidate B. subtilis promoters, transcription factors, and known cis-elements and to support analysis of its regulatory network [5]. For eukaryotes, EPD and EPDnew provide non-redundant collections centered on experimentally mapped TSSs, whereas DBTSS integrates extensive TSS tag data across tissues and cell types [8,9]. These databases have enabled machine-learning studies by converting dispersed experimental evidence into structured sequence collections.")
    body(doc, "Database origin alone does not guarantee that benchmark datasets are directly comparable. Studies differ in evidence thresholds, promoter-window coordinates, inclusion of alternative TSSs, sequence redundancy, class balance, and negative construction. Some predictors classify short, centered windows, while others scan long genomic sequences and must control an enormous number of potential false-positive positions. DeeReCT-PromID emphasized this distinction: strong classification of pre-extracted windows does not automatically imply accurate genome-wide promoter localization [10]. Literature comparisons must therefore consider the prediction task and dataset protocol, not only the reported accuracy.")
    body(doc, "Sequence redundancy is another important concern. If highly similar promoter records occur in both training and evaluation sets, measured performance can reflect recognition of near-duplicate sequences. CD-HIT and CD-HIT-EST use short-word filtering and greedy incremental clustering to efficiently create non-redundant protein or nucleotide datasets [11]. Redundancy thresholds such as 80%, 90%, or 95% represent different levels of stringency, and their effect depends on sequence length and alignment coverage. A sound study should report the selected threshold, whether classes were clustered separately, and whether the split procedure additionally grouped identical or reverse-complement sequences.")

    doc.add_heading("2.4 The problem of negative-sequence construction", level=1)
    body(doc, "Negative examples are one of the most consequential and least standardized components of promoter prediction. Shuffled promoters can preserve nucleotide or dinucleotide composition while destroying motif order, but they may be much easier to separate than authentic genomic regions. Random genome fragments are more realistic, yet they can include unannotated promoters. Coding-region fragments, intragenic downstream regions, intergenic sequences, and regions surrounding false TSS candidates each define a different learning problem. DeeReCT-PromID specifically introduced challenging genomic negatives to reduce false-positive predictions during long-sequence scanning [10]. Comparative studies likewise warn that performance is strongly affected by how negative data are generated [12,13].")
    body(doc, "A model can exploit differences between positive and negative collection procedures rather than promoter biology. For example, negatives taken from a genomic compartment with systematically different GC content can make composition alone highly predictive. Conversely, overly similar hard negatives may contain true but unannotated promoter activity and introduce label noise. The best negative design depends on the intended application. Genome-wide scanning requires representative genomic background; promoter-versus-shuffle discrimination tests motif organization under controlled composition; and annotation near genes may benefit from matched upstream and downstream controls. Transparent reporting and evaluation across more than one negative type are therefore preferable.")

    doc.add_heading("2.5 Early computational promoter-prediction approaches", level=1)
    body(doc, "Early promoter predictors were largely signal based, content based, or hybrid. Signal-based systems searched for known elements such as TATA boxes, bacterial −10/−35 motifs, initiators, CpG islands, or transcription-factor binding sites. Content-based systems summarized oligonucleotide frequencies, compositional bias, DNA bendability, or local stability. Statistical techniques included position weight matrices, linear discriminant functions, hidden Markov models, nearest-neighbour rules, and early artificial neural networks. Representative programs combined motif scores with triplet or hexamer preferences and potential binding-site information [10,14].")
    body(doc, "These approaches offered interpretability because their decisions could be related to predefined signals. However, their feature definitions limited the patterns that could be discovered. Individual promoters often lack canonical elements or use them in non-standard combinations. A motif detector can therefore have good sensitivity for one subclass but poor generality. Genome-wide application also magnifies false positives because motif-like words occur frequently by chance. Reviews of promoter-recognition tools have consequently found that scoring-function methods are generally less competitive than modern machine-learning and deep-learning approaches, although their simplicity and biological transparency remain valuable [12,14].")

    doc.add_heading("2.6 Feature-based machine learning", level=1)
    body(doc, "Traditional machine learning expanded promoter prediction by combining many descriptors into a learned decision boundary. Common encodings include mono- and oligonucleotide composition, k-spaced nucleotide pairs, pseudo k-tuple nucleotide composition, position-specific propensities, autocorrelation, physicochemical indices, DNA stability, entropy, and predicted structural properties. Support vector machines, Random Forests, logistic regression, boosting, k-nearest-neighbour classifiers, and shallow neural networks have all been applied. Feature selection is commonly used to reduce dimensionality and retain descriptors that contribute complementary information.")
    body(doc, "MULTiPly is an influential example of multi-layer feature integration. It combined local information such as k-tuple nucleotide composition and dinucleotide-based autocovariance with global encodings based on bi-profile Bayes and k-nearest-neighbour representations. Feature selection and successive integration were used to identify general and specific promoter classes [15]. iProEP combined pseudo nucleotide composition with positional-correlation scoring and reported that cross-species performance deteriorated when models were transferred between organisms, highlighting promoter species specificity [16].")
    body(doc, "Random Forests are attractive for promoter prediction because they can model nonlinear interactions, tolerate mixed feature scales, and provide measures of feature importance. Their effectiveness nevertheless depends on the quality of the representation supplied to them. A forest trained on k-mer frequencies may capture composition but lose exact positional relationships; adding position-specific or thermodynamic features can restore part of that information. Feature-based models therefore remain competitive, especially when datasets are moderate in size or interpretability is important, but manual representations can omit sequence patterns not anticipated by the investigator.")

    doc.add_heading("2.7 Deep learning for promoter recognition", level=1)
    doc.add_heading("2.7.1 Convolutional neural networks", level=2)
    body(doc, "Deep learning shifted the focus from manually designed descriptors toward representation learning from nucleotide sequences. DNA is typically one-hot encoded, after which one-dimensional convolutional filters scan for recurring local patterns. Early layers can behave like motif detectors, while deeper layers combine motifs into higher-order representations. Pooling provides partial positional tolerance, and dense layers convert the learned representation into a promoter probability. CNNProm demonstrated that a related convolutional architecture could be trained on promoters from distant organisms including human, mouse, Arabidopsis, E. coli, and B. subtilis [17].")
    body(doc, "The appeal of CNNs lies in their ability to learn motifs without requiring an explicit catalogue. Kernel width determines the local context viewed by a filter, so multi-scale convolution can represent motifs and motif combinations of different sizes. Residual connections support deeper feature extraction by improving gradient flow. However, standard CNNs can struggle with long-range dependencies unless receptive fields are expanded through depth, dilation, or large kernels. Their learned filters are also not automatically biologically interpretable; post-hoc analysis is required to determine whether influential activations correspond to recognized regulatory elements.")

    doc.add_heading("2.7.2 Recurrent and attention-based models", level=2)
    body(doc, "Recurrent neural networks, particularly long short-term memory networks, model sequences as ordered dependencies. Bidirectional LSTMs can integrate upstream-to-downstream and downstream-to-upstream context, making them suitable for promoter elements whose interpretation depends on surrounding sequence. CNN–LSTM hybrids use convolution to extract local motifs and recurrence to integrate their order. Comparative work across eukaryotic species has evaluated CNN, LSTM, Random Forest, one-hot encoding, and frequency-based tokenization, illustrating how both representation and classifier affect performance [13]. Recurrent models can be computationally slower than CNNs and may be unnecessary for short fixed windows, but they remain a useful candidate when sequential order is central.")
    body(doc, "Transformer architectures replace recurrence with self-attention, allowing every position to interact directly with other positions. This mechanism can represent long-range motif relationships and has been adapted to DNA through k-mer tokenization and pretrained genomic language models. Recent prokaryotic work has used DNABERT-based frameworks across many species and reported that cross-species experiments continue to support species-specific modeling [18]. Attention models require careful regularization and adequate data, and their attention weights should not be equated automatically with causal biological explanation.")

    doc.add_heading("2.7.3 Graph and multimodal representations", level=2)
    body(doc, "More recent studies have explored representations beyond a linear nucleotide string. GraphPro combined CNN-derived sequence information with graph representations motivated by DNA secondary structure and used graph convolution or graph attention to support multi-species promoter identification and interpretation [19]. Other multimodal approaches integrate sequence, k-mer composition, predicted DNA shape, physicochemical properties, or epigenomic signals. These systems recognize that promoter activity emerges from more than a single motif scale. Their potential advantage is richer biological representation; their disadvantages include greater complexity, increased opportunity for overfitting, dependence on additional preprocessing, and difficulty establishing which modality is responsible for a reported gain.")

    doc.add_heading("2.8 Ensemble and hybrid learning", level=1)
    body(doc, "Ensemble learning combines predictions from multiple models to reduce variance or exploit complementary errors. Models with the same architecture but different random initializations can be averaged, while heterogeneous ensembles combine different algorithms or feature spaces. In promoter prediction, iPro-WAEL integrated a CNN and Random Forest through weighted probability averaging and evaluated the framework across seven species [20]. The CNN learned features from sequence representations, whereas the forest used explicit descriptors. This design is closely aligned with the broader principle that learned spatial motifs and engineered compositional features need not be mutually exclusive.")
    body(doc, "Weighted averaging is simple, transparent, and comparatively resistant to overfitting when the number of candidate weights is controlled. Its validity depends on selecting mixture weights and thresholds without using test labels. If test performance guides the weight, the result becomes optimistically biased. Ensemble studies should also compare the hybrid against each component, report whether gains occur in threshold-dependent and ranking metrics, and examine calibration. An ensemble can improve ROC-AUC while worsening probability calibration or exchanging specificity for sensitivity.")

    doc.add_heading("2.9 Multi-species and cross-species prediction", level=1)
    body(doc, "A recurring theme in the literature is the difference between multi-species coverage and genuine cross-species generalization. A system may contain separate species-specific models behind one interface, train one pooled model on multiple species, or train on one species and test on an unseen species. These are distinct claims. iProEP reported marked loss of accuracy when models were transferred among species, attributing the result to species-specific promoter properties [16]. iPro-WAEL addressed multi-species identification through an ensemble framework, while GraphPro and recent transformer work have explicitly investigated broader transfer [18–20].")
    body(doc, "Species-specific models can achieve strong within-species performance but require routing information and cannot directly predict an unrepresented organism. A pooled model has more training data but may learn species identity or dataset-source signals rather than promoter biology. Domain-aware or multi-task models offer a compromise by combining shared representations with specialist components. Their evaluation should include leave-one-species-out testing, per-species metrics, and controls showing that domain classification is not functioning as a shortcut for the promoter label.")

    doc.add_heading("2.10 Evaluation practices and common sources of bias", level=1)
    body(doc, "The literature uses accuracy, sensitivity, specificity, precision, F1-score, MCC, ROC-AUC, and PR-AUC, but no single metric fully characterizes promoter prediction. Accuracy can be misleading under imbalance. Sensitivity measures recovered promoters, specificity measures rejected non-promoters, and precision describes the reliability of positive predictions. MCC incorporates all four confusion-matrix cells and is informative when class distributions differ. ROC-AUC summarizes ranking across thresholds, whereas PR-AUC concentrates on positive retrieval and is often more revealing when promoters are rare. Genome-wide scanning additionally requires measures of false positives per sequence length or per correctly localized TSS [10,12].")
    body(doc, "Evaluation bias can arise from duplicate sequences, reverse complements, related windows from the same locus, hyperparameter tuning on test results, and threshold selection after examining test probabilities. Random splitting alone does not prevent these problems. Sequence similarity should be controlled before or during partitioning, and all equivalent groups should remain within one split. Validation data should be used for architecture, checkpoint, feature, ensemble-weight, and threshold decisions; the test set should be evaluated only after these choices are frozen. Confidence intervals and multi-seed analysis help quantify uncertainty, but they do not repair leakage in the data design.")
    body(doc, "Published performance values are particularly difficult to compare when datasets differ. A high accuracy on balanced, shuffled negatives is not directly comparable with a lower value from genome-wide scanning against realistic background. Critical assessments of promoter predictors emphasize that results change when models are evaluated on new datasets and that tool availability, task definition, and benchmark composition must be considered alongside reported metrics [12]. Therefore, literature review should identify methodological trends and limitations rather than construct an unqualified league table from incompatible studies.")

    doc.add_heading("2.11 Interpretability and biological validation", level=1)
    body(doc, "Interpretability is important because promoter prediction is often intended to produce biological insight rather than only a label. Feature-based models can rank k-mers or physicochemical descriptors, while neural models can be examined through convolutional-filter visualization, saliency maps, integrated gradients, attention analysis, and in-silico mutagenesis. iPro-WAEL investigated influential transcription-factor binding motifs, and GraphPro connected learned decisions with motif-like sequence patterns [19,20]. Such analyses can generate hypotheses about regulatory elements.")
    body(doc, "However, model attribution is not equivalent to causal validation. A feature can be predictive because of database construction, genomic composition, or correlation with another element. Robust interpretation should be stable across random seeds, localized relative to the TSS, enriched in promoters compared with matched negatives, and consistent with known motifs where appropriate. The strongest evidence comes from experimental perturbation, such as promoter-reporter assays or systematic nucleotide substitution. Computational interpretation is therefore best presented as hypothesis generation unless experimental support is available.")

    doc.add_heading("2.12 Synthesis of representative computational approaches", level=1)
    caption(doc, "Table 2.1. Representative developments in computational promoter prediction")
    table(doc,
          ["Approach", "Representative work", "Main representation/model", "Contribution", "Important limitation"],
          [
              ["Signal/scoring", "TSSW, FPROM, Promoter 2.0", "Motif and content scores; discriminant or shallow ANN", "Biologically interpretable promoter signals", "Limited coverage of heterogeneous promoters; many genomic false positives"],
              ["Feature integration", "MULTiPly (2019)", "k-tuple composition, autocovariance, Bayes and nearest-neighbour features", "General and specific promoter prediction", "Manually defined features and benchmark dependence"],
              ["Species-specific ML", "iProEP (2019)", "Pseudo nucleotide composition and positional correlation with SVM", "Demonstrated cross-species deterioration", "Requires species-specific training/routing"],
              ["CNN", "CNNProm (2017)", "One-hot DNA and convolutional filters", "Representation learning across distant organisms", "Short-window classification does not equal genome-wide localization"],
              ["Genome scanning", "DeeReCT-PromID (2019)", "Deep CNN with challenging genomic negatives", "Reduced false positives in long human sequences", "Human-centered task and specific scanning protocol"],
              ["Hybrid ensemble", "iPro-WAEL (2022)", "Weighted Random Forest and CNN", "Complementary feature and neural evidence across species", "Weights and performance depend on validation and dataset design"],
              ["Graph learning", "GraphPro (2024)", "CNN plus graph representation", "Multi-species prediction and interpretability", "Greater model and preprocessing complexity"],
              ["DNA language model", "iPro-MP (2025)", "DNABERT-based prokaryotic model", "Broader multi-prokaryote and cross-species analysis", "Data and compute demands; transfer remains species sensitive"],
          ], 7.3)

    doc.add_heading("2.13 Research gaps", level=1)
    body(doc, "The reviewed literature reveals substantial progress but leaves several connected gaps. First, many systems are restricted to one organism, a small group of species, or one biological domain. Models advertised as multi-species may still require a separately tuned classifier for every species. Second, promoter datasets use inconsistent window lengths and negative-construction procedures, limiting direct comparison. Third, redundancy control does not always prevent exact or reverse-complement leakage after partitioning. Fourth, many studies report one model run or rely primarily on accuracy, providing limited evidence about initialization variability, class-specific errors, calibration, or uncertainty.")
    body(doc, "A fifth gap concerns representation. Classical models offer explicit features but may miss unanticipated spatial patterns; deep networks learn representations but can overlook useful global descriptors or become difficult to interpret. Hybrid approaches address this complementarity, yet mixture weights and feature blocks are often treated as universal rather than taxon dependent. Sixth, strong benchmark performance does not guarantee transfer to new species or realistic genome-wide background. Finally, incomplete provenance and unavailable processing artifacts can undermine reproducibility even when model code is shared.")
    body(doc, "These gaps motivate a framework that combines curated multi-domain data, transparent redundancy reduction, a comprehensive sequence audit, exact/reverse-complement-aware splitting, organism-specific feature selection, domain-appropriate neural architectures, multi-seed averaging, validation-selected hybridization, and untouched-test evaluation. Such a design does not remove the biological differences among domains; it treats those differences as explicit modeling information while preserving common principles of reproducible evaluation.")

    doc.add_heading("2.14 Positioning of the present study", level=1)
    body(doc, "The present research is positioned between species-specific promoter classifiers and a universal pooled predictor. It includes E. coli and B. subtilis as bacterial representatives; selected archaeal organisms; human and mouse as mammalian representatives; and Arabidopsis as a plant representative. Rather than assuming a single window length or feature set, it retains domain-appropriate sequence lengths and performs organism-specific feature selection. Its neural candidates include residual, multi-scale, recurrent, Transformer, and domain-aware architectures, while the finalized pipeline combines multi-seed CNN probabilities with Random Forest evidence.")
    body(doc, "Methodologically, the study places particular emphasis on leakage prevention and test-set isolation. Redundant sequences were reduced before modeling, exact sequences and reverse complements were grouped during splitting, cross-label conflicts were quarantined, and development choices were restricted to training and validation data. MCC served as the principal selection measure, while PR-AUC, ROC-AUC, balanced accuracy, confusion matrices, Brier score, and bootstrap intervals provided complementary evidence. This combination responds directly to the literature’s concerns regarding benchmark dependence, species specificity, negative design, representation choice, and incomplete evaluation.")
    body(doc, "The intended contribution is therefore not a claim that one architecture solves promoter recognition universally. Rather, it is a reproducible domain-aware framework in which shared computational principles coexist with organism-sensitive features and operating thresholds. The literature indicates that this balance is necessary: promoter biology contains recurring local and contextual sequence signals, but their expression and predictive value vary among taxa. The subsequent methodology and results chapters evaluate whether this integrated strategy produces reliable promoter classification on the finalized multi-domain dataset.")

    doc.add_heading("2.15 Chapter summary", level=1)
    body(doc, "Promoter prediction has evolved from consensus-motif scoring and manually defined signals to feature-based machine learning, convolutional and recurrent networks, Transformers, graph models, and heterogeneous ensembles. Curated resources such as RegulonDB, DBTBS, EPDnew, and DBTSS provide essential training data, but benchmark construction, redundancy, negative sampling, and species composition strongly influence reported performance. Biological differences among bacterial, archaeal, and eukaryotic transcription argue against assuming one universal promoter grammar. Current literature supports learned sequence representations and hybrid modeling while continuing to identify cross-species transfer, interpretability, realistic negatives, leakage control, calibration, and reproducibility as unresolved challenges. These findings provide the conceptual basis for the domain-aware, leakage-controlled, multi-seed hybrid framework developed in this thesis.")

    doc.add_heading("References", level=1)
    references = [
        "[1] Ruff, E. F., Record, M. T., and Artsimovitch, I. (2015). Initial events in bacterial transcription initiation. Biomolecules, 5(2), 1035–1062.",
        "[2] Blombach, F., and Grohmann, D. (2017). Same same but different: The evolution of TBP and TFB in archaea and their role in transcription initiation. Frontiers in Microbiology, 8, 1352.",
        "[3] Gehring, A. M., Walker, J. E., and Santangelo, T. J. (2016). Transcription regulation in Archaea. Journal of Bacteriology, 198(14), 1906–1917.",
        "[4] Gama-Castro, S., Salgado, H., Santos-Zavaleta, A., Ledezma-Tejeida, D., et al. (2016). RegulonDB version 9.0: High-level integration of gene regulation, coexpression, motif clustering and beyond. Nucleic Acids Research, 44(D1), D133–D143.",
        "[5] Ishii, T., Yoshida, K., Terai, G., Fujita, Y., and Nakai, K. (2001). DBTBS: A database of Bacillus subtilis promoters and transcription factors. Nucleic Acids Research, 29(1), 278–280.",
        "[6] Blombach, F., Ausiannikava, D., Figueiredo, A. M., and Allers, T. (2021). Archaeal transcription. Methods, mechanisms and regulation. Emerging Topics in Life Sciences, 5(3), 343–353.",
        "[7] Roy, A. L., and Singer, D. S. (2015). Core promoters in transcription: Old problem, new insights. Trends in Biochemical Sciences, 40(3), 165–171.",
        "[8] Dreos, R., Ambrosini, G., Périer, R. C., and Bucher, P. (2013). EPD and EPDnew, high-quality promoter resources in the next-generation sequencing era. Nucleic Acids Research, 41(D1), D157–D164.",
        "[9] Suzuki, A., Wakaguri, H., Yamashita, R., Kawano, S., Tsuchihara, K., Sugano, S., Suzuki, Y., and Nakai, K. (2015). DBTSS as an integrative platform for transcriptome, epigenome and genome sequence variation data. Nucleic Acids Research, 43(D1), D87–D91.",
        "[10] Umarov, R., Kuwahara, H., Li, Y., Gao, X., and Solovyev, V. (2019). Promoter analysis and prediction in the human genome using sequence-based deep learning models. Bioinformatics, 35(16), 2730–2737.",
        "[11] Li, W., and Godzik, A. (2006). Cd-hit: A fast program for clustering and comparing large sets of protein or nucleotide sequences. Bioinformatics, 22(13), 1658–1659.",
        "[12] Liu, B., et al. (2022). Critical assessment of computational tools for prokaryotic and eukaryotic promoter prediction. Briefings in Bioinformatics, 23(2), bbab551.",
        "[13] Bhandari, N., Khare, S., Walambe, R., and Kotecha, K. (2021). Comparison of machine learning and deep learning techniques in promoter prediction across diverse species. PeerJ Computer Science, 7, e365.",
        "[14] Abeel, T., Saeys, Y., Bonnet, E., Rouzé, P., and Van de Peer, Y. (2008). Generic eukaryotic core promoter prediction using structural features of DNA. Genome Research, 18(2), 310–323.",
        "[15] Zhang, M., Li, F., Marquez-Lago, T. T., Leier, A., Fan, C., Kwoh, C. K., Chou, K. C., Song, J., and Jia, C. (2019). MULTiPly: A novel multi-layer predictor for discovering general and specific types of promoters. Bioinformatics, 35(17), 2957–2965.",
        "[16] Lai, H. Y., Zhang, Z. Y., Su, Z. D., Su, W., Ding, H., Chen, W., and Lin, H. (2019). iProEP: A computational predictor for predicting promoter. Molecular Therapy—Nucleic Acids, 17, 337–346.",
        "[17] Umarov, R. K., and Solovyev, V. V. (2017). Recognition of prokaryotic and eukaryotic promoters using convolutional deep learning neural networks. PLOS ONE, 12(2), e0171410.",
        "[18] Wang, J., et al. (2025). iPro-MP: A BERT-based model to predict multiple prokaryotic promoters. Genome Biology. https://doi.org/10.1186/s13059-025-03819-9.",
        "[19] Zhang, Q., Wei, Y., and Liu, L. (2024). GraphPro: An interpretable graph neural network-based model for identifying promoters in multiple species. Computers in Biology and Medicine, 180, 108974.",
        "[20] Zhang, P., Zhang, H., Wu, H., et al. (2022). iPro-WAEL: A comprehensive and robust framework for identifying promoters in multiple species. Nucleic Acids Research, 50(18), 10278–10289.",
    ]
    for ref in references:
        p = doc.add_paragraph(ref)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.first_line_indent = Inches(-0.3)
        p.paragraph_format.space_after = Pt(4)

    doc.core_properties.title = "Detailed Literature Review Chapter"
    doc.core_properties.subject = "Computational promoter prediction literature review"
    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    build()
