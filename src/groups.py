"""Canonical organism-level model groups and reporting domains."""

MODEL_GROUPS = {
    "ecoli": {"organism": "Escherichia coli", "domain": "bacteria", "input_length": 81},
    "bsubtilis": {"organism": "Bacillus subtilis", "domain": "bacteria", "input_length": 81},
    "archaea": {"organism": "Archaea_unspecified", "domain": "archaea", "input_length": 100},
    "human": {"organism": "Homo sapiens", "domain": "eukaryota", "input_length": 251},
    "mouse": {"organism": "Mus musculus", "domain": "eukaryota", "input_length": 251},
    "arabidopsis": {"organism": "Arabidopsis thaliana", "domain": "eukaryota", "input_length": 251},
}

DOMAIN_IDS = {"bacteria": 0, "archaea": 1, "eukaryota": 2}
ORGANISM_TO_GROUP = {value["organism"]: key for key, value in MODEL_GROUPS.items()}
DOMAIN_GROUPS = {
    domain: tuple(key for key, value in MODEL_GROUPS.items() if value["domain"] == domain)
    for domain in DOMAIN_IDS
}


def model_group_for(organism: str) -> str:
    try:
        return ORGANISM_TO_GROUP[organism]
    except KeyError as exc:
        raise ValueError(f"No model group is configured for organism {organism!r}") from exc


def records_for_group(records, group: str):
    organism = MODEL_GROUPS[group]["organism"]
    return [record for record in records if record.organism == organism]
