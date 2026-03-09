from app.models.enums import Platform

QC_THRESHOLDS = {
    "fastqc": {
        "q30_percent": {"min": 80.0, "warn": 80.0},
        "adapter_percent": {"max": 5.0, "warn": 4.0},
        "duplication_rate": {"max": 30.0, "warn": 25.0},
    },
    "nanoplot": {
        "mean_read_length": {"min": 1000},
        "mean_quality": {"min": 10.0},
    },
    "snpchip_qc": {
        "call_rate": {"min": 0.95},
        "missing_rate": {"max": 0.05},
    },
}


def determine_qc_tool(platform: Platform) -> str:
    mapping = {
        Platform.ILLUMINA: "fastqc",
        Platform.OXFORD_NANOPORE: "nanoplot",
        Platform.PACBIO_SMRT: "nanoplot",
        Platform.SNP_CHIP: "snpchip_qc",
        Platform.HI_C: "fastqc",
    }
    return mapping[platform]


def check_thresholds(tool: str, metrics: dict) -> str:
    thresholds = QC_THRESHOLDS.get(tool, {})
    status = "pass"
    for metric, limits in thresholds.items():
        value = metrics.get(metric)
        if value is None:
            continue
        if "min" in limits and value < limits["min"]:
            return "fail"
        if "max" in limits and value > limits["max"]:
            return "fail"
        if "warn" in limits:
            if "min" in limits and value <= limits["warn"]:
                status = "warn"
            elif "max" in limits and value >= limits["warn"]:
                status = "warn"
    return status
