from app.eutils.parser import parse_query
from app.eutils.search import build_query_filter, FIELD_MAP, DB_CONFIG


def test_simple_text():
    tokens = parse_query("camel WGS")
    assert len(tokens) == 1
    assert tokens[0].text == "camel WGS"
    assert tokens[0].field is None
    assert tokens[0].operator is None


def test_field_qualified_single():
    tokens = parse_query("Camelus dromedarius[ORGN]")
    assert len(tokens) == 1
    assert tokens[0].text == "Camelus dromedarius"
    assert tokens[0].field == "ORGN"


def test_boolean_and():
    tokens = parse_query("Camelus[ORGN] AND WGS[TITL]")
    assert len(tokens) == 3
    assert tokens[0].text == "Camelus"
    assert tokens[0].field == "ORGN"
    assert tokens[1].operator == "AND"
    assert tokens[2].text == "WGS"
    assert tokens[2].field == "TITL"


def test_boolean_or():
    tokens = parse_query("camel[ORGN] OR horse[ORGN]")
    assert len(tokens) == 3
    assert tokens[1].operator == "OR"


def test_boolean_not():
    tokens = parse_query("Camelus[ORGN] NOT dromedarius[TITL]")
    assert len(tokens) == 3
    assert tokens[1].operator == "NOT"


def test_accession_lookup():
    tokens = parse_query("NFDP-PRJ-000001")
    assert len(tokens) == 1
    assert tokens[0].text == "NFDP-PRJ-000001"
    assert tokens[0].field is None


def test_date_range():
    tokens = parse_query("2026/01/01:2026/12/31[PDAT]")
    assert len(tokens) == 1
    assert tokens[0].field == "PDAT"
    assert tokens[0].date_from == "2026/01/01"
    assert tokens[0].date_to == "2026/12/31"


def test_complex_query():
    tokens = parse_query("Camelus[ORGN] AND 2026/01/01:2026/06/30[PDAT]")
    assert len(tokens) == 3
    assert tokens[0].field == "ORGN"
    assert tokens[1].operator == "AND"
    assert tokens[2].field == "PDAT"
    assert tokens[2].date_from == "2026/01/01"


def test_empty_query():
    tokens = parse_query("")
    assert tokens == []


# --- Search engine tests ---


def test_field_map_has_standard_fields():
    assert "ORGN" in FIELD_MAP
    assert "TITL" in FIELD_MAP
    assert "PDAT" in FIELD_MAP
    assert "ACCN" in FIELD_MAP


def test_db_config_bioproject():
    assert "bioproject" in DB_CONFIG
    cfg = DB_CONFIG["bioproject"]
    assert cfg["model"].__tablename__ == "projects"


def test_db_config_biosample():
    assert "biosample" in DB_CONFIG
    cfg = DB_CONFIG["biosample"]
    assert cfg["model"].__tablename__ == "samples"


def test_db_config_sra():
    assert "sra" in DB_CONFIG
    cfg = DB_CONFIG["sra"]
    assert cfg["model"].__tablename__ == "experiments"


def test_build_filter_simple_text():
    tokens = parse_query("camel")
    filter_clause = build_query_filter(tokens, "bioproject")
    assert filter_clause is not None


def test_build_filter_field_qualified():
    tokens = parse_query("Camelus[ORGN]")
    filter_clause = build_query_filter(tokens, "biosample")
    assert filter_clause is not None
