from pathlib import Path

import pytest

from webapp.predictor import MAX_RECORDS, ModelRegistry, parse_fasta, parse_sequence


def test_parse_plain_sequence():
    assert parse_sequence("acgt\nNN")[0].sequence == "ACGTNN"


def test_parse_fasta_and_duplicate_ids():
    records = parse_fasta(">sample\nACGT\n>sample\nNNNN\n")
    assert [record.sequence_id for record in records] == ["sample", "sample (2)"]


def test_large_fasta_keeps_first_10000_records():
    text = "".join(f">record_{index}\nACGT\n" for index in range(MAX_RECORDS + 2))
    records = parse_fasta(text)
    assert len(records) == MAX_RECORDS
    assert records[-1].sequence_id == "record_9999"


@pytest.mark.parametrize("text", ["ACGT", ">x\nACGU", ">\nACGT"])
def test_invalid_fasta(text):
    with pytest.raises(ValueError):
        parse_fasta(text)


def test_model_registry_has_six_organism_groups():
    registry = ModelRegistry(Path(__file__).resolve().parents[1])
    descriptions = registry.describe()
    assert {row["model_group"] for row in descriptions} == {
        "ecoli", "bsubtilis", "archaea", "human", "mouse", "arabidopsis"
    }
    assert registry.input_lengths["bsubtilis"] == 81
    assert all(row["available"] for row in descriptions)
    assert all("3_seed_ensemble" in row["model"] for row in descriptions)


def test_web_page_contains_prediction_workflows_and_plotly():
    page = (Path(__file__).resolve().parents[1] / "webapp" / "static" / "index.html").read_text(encoding="utf-8")
    assert 'id="single-form"' in page
    assert 'id="fasta-form"' in page
    assert 'id="pie-chart"' in page
    assert "plotly-3.1.0.min.js" in page
    assert 'class="site-footer"' in page


def test_render_blueprint_uses_health_check_and_port():
    blueprint = (Path(__file__).resolve().parents[1] / "render.yaml").read_text(encoding="utf-8")
    assert "healthCheckPath: /api/health" in blueprint
    assert "--port $PORT" in blueprint
