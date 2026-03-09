from app.workers.qc import determine_qc_tool, check_thresholds
from app.models.enums import Platform


def test_determine_qc_tool_illumina():
    assert determine_qc_tool(Platform.ILLUMINA) == "fastqc"


def test_determine_qc_tool_nanopore():
    assert determine_qc_tool(Platform.OXFORD_NANOPORE) == "nanoplot"


def test_determine_qc_tool_pacbio():
    assert determine_qc_tool(Platform.PACBIO_SMRT) == "nanoplot"


def test_determine_qc_tool_snpchip():
    assert determine_qc_tool(Platform.SNP_CHIP) == "snpchip_qc"


def test_determine_qc_tool_hic():
    assert determine_qc_tool(Platform.HI_C) == "fastqc"


def test_check_thresholds_pass():
    result = check_thresholds("fastqc", {
        "q30_percent": 92.3,
        "adapter_percent": 1.2,
        "duplication_rate": 8.5,
    })
    assert result == "pass"


def test_check_thresholds_fail_low_q30():
    result = check_thresholds("fastqc", {
        "q30_percent": 50.0,
        "adapter_percent": 1.2,
        "duplication_rate": 8.5,
    })
    assert result == "fail"


def test_check_thresholds_fail_high_adapter():
    result = check_thresholds("fastqc", {
        "q30_percent": 92.0,
        "adapter_percent": 10.0,
        "duplication_rate": 8.5,
    })
    assert result == "fail"


def test_check_thresholds_snpchip_pass():
    result = check_thresholds("snpchip_qc", {
        "call_rate": 0.98,
        "missing_rate": 0.02,
    })
    assert result == "pass"


def test_check_thresholds_snpchip_fail():
    result = check_thresholds("snpchip_qc", {
        "call_rate": 0.90,
        "missing_rate": 0.10,
    })
    assert result == "fail"


def test_check_thresholds_nanoplot_pass():
    result = check_thresholds("nanoplot", {
        "mean_read_length": 5000,
        "mean_quality": 15.0,
    })
    assert result == "pass"
