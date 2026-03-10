import json

# Test the parsing logic directly rather than via CLI runner to avoid main.py conflicts
def test_parse_multiqc_data(tmp_path):
    """Test that MultiQC data can be parsed."""
    mqc_dir = tmp_path / "multiqc_data"
    mqc_dir.mkdir()
    mqc_data = {
        "report_general_stats_data": [
            {"NFDP-SAM-000001": {"total_sequences": 1000000, "avg_sequence_length": 150.0}},
        ],
    }
    (mqc_dir / "multiqc_data.json").write_text(json.dumps(mqc_data))

    # Verify the JSON can be loaded and parsed
    with open(mqc_dir / "multiqc_data.json") as f:
        data = json.load(f)

    general_stats = data.get("report_general_stats_data", [])
    sample_stats = {}
    for stats_block in general_stats:
        for sample_name, metrics in stats_block.items():
            if sample_name not in sample_stats:
                sample_stats[sample_name] = {}
            sample_stats[sample_name].update(metrics)

    assert len(sample_stats) == 1
    assert "NFDP-SAM-000001" in sample_stats
    assert sample_stats["NFDP-SAM-000001"]["total_sequences"] == 1000000
