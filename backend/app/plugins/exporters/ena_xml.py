import xml.etree.ElementTree as ET


def generate_study_xml(study: dict) -> str:
    root = ET.Element("STUDY_SET")
    s = ET.SubElement(root, "STUDY", alias=study["accession"])
    desc = ET.SubElement(s, "DESCRIPTOR")
    ET.SubElement(desc, "STUDY_TITLE").text = study["title"]
    abstract = ET.SubElement(desc, "STUDY_ABSTRACT")
    abstract.text = study.get("description", "")
    ET.SubElement(desc, "STUDY_TYPE", existing_study_type="Other")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def generate_sample_xml(sample: dict) -> str:
    root = ET.Element("SAMPLE_SET")
    s = ET.SubElement(root, "SAMPLE", alias=sample["accession"])
    ET.SubElement(s, "TITLE").text = sample.get("organism", "")
    name = ET.SubElement(s, "SAMPLE_NAME")
    ET.SubElement(name, "TAXON_ID").text = str(sample["tax_id"])
    ET.SubElement(name, "SCIENTIFIC_NAME").text = sample.get("organism", "")
    attrs = ET.SubElement(s, "SAMPLE_ATTRIBUTES")
    attr = ET.SubElement(attrs, "SAMPLE_ATTRIBUTE")
    ET.SubElement(attr, "TAG").text = "ENA-CHECKLIST"
    ET.SubElement(attr, "VALUE").text = sample.get("checklist_id", "")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def generate_experiment_xml(experiment: dict) -> str:
    root = ET.Element("EXPERIMENT_SET")
    e = ET.SubElement(root, "EXPERIMENT", alias=experiment["accession"])
    ET.SubElement(e, "TITLE").text = f"Experiment {experiment['accession']}"
    study_ref = ET.SubElement(e, "STUDY_REF")
    study_ref.set("refname", experiment.get("project_accession", ""))
    design = ET.SubElement(e, "DESIGN")
    ET.SubElement(design, "DESIGN_DESCRIPTION")
    sample_desc = ET.SubElement(design, "SAMPLE_DESCRIPTOR")
    sample_desc.set("refname", experiment.get("sample_accession", ""))
    lib = ET.SubElement(design, "LIBRARY_DESCRIPTOR")
    ET.SubElement(lib, "LIBRARY_STRATEGY").text = experiment.get("library_strategy", "")
    ET.SubElement(lib, "LIBRARY_SOURCE").text = experiment.get("library_source", "")
    ET.SubElement(lib, "LIBRARY_LAYOUT").text = experiment.get("library_layout", "")
    platform = ET.SubElement(e, "PLATFORM")
    plat_elem = ET.SubElement(platform, experiment.get("platform", "ILLUMINA"))
    ET.SubElement(plat_elem, "INSTRUMENT_MODEL").text = experiment.get("instrument_model", "")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def generate_run_xml(run: dict) -> str:
    root = ET.Element("RUN_SET")
    r = ET.SubElement(root, "RUN", alias=run["accession"])
    exp_ref = ET.SubElement(r, "EXPERIMENT_REF")
    exp_ref.set("refname", run.get("experiment_accession", ""))
    data_block = ET.SubElement(r, "DATA_BLOCK")
    files = ET.SubElement(data_block, "FILES")
    f = ET.SubElement(files, "FILE")
    f.set("filename", run.get("filename", ""))
    f.set("filetype", run.get("file_type", "fastq").lower())
    f.set("checksum_method", "MD5")
    f.set("checksum", run.get("checksum_md5", ""))
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def generate_submission_xml(alias: str, actions: list[dict] | None = None) -> str:
    root = ET.Element("SUBMISSION_SET")
    s = ET.SubElement(root, "SUBMISSION", alias=alias)
    acts = ET.SubElement(s, "ACTIONS")
    if actions:
        for action in actions:
            act = ET.SubElement(acts, "ACTION")
            ET.SubElement(act, action.get("type", "ADD"))
    else:
        act = ET.SubElement(acts, "ACTION")
        ET.SubElement(act, "ADD")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
