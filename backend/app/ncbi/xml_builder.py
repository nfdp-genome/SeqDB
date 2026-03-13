"""Generate NCBI-compliant XML for BioProject, BioSample, and SRA submissions."""

from xml.etree.ElementTree import Element, SubElement, tostring

from app.schemas.domains.mapper import export_ncbi


def build_submission_xml(
    action: str,
    target_db: str,
    center_name: str,
    submitter_email: str = "",
) -> str:
    """Build the outer Submission XML envelope."""
    submission = Element("Submission")
    desc = SubElement(submission, "Description")
    SubElement(desc, "Comment").text = f"SeqDB automated submission to {target_db}"
    if submitter_email:
        contact = SubElement(desc, "Organization", type="center", role="owner")
        SubElement(contact, "Name").text = center_name
        c = SubElement(contact, "Contact", email=submitter_email)
        SubElement(c, "Name")

    action_elem = SubElement(submission, "Action", name=action)
    SubElement(action_elem, "AddData", target_db=target_db)

    return _to_xml_string(submission)


def build_bioproject_xml(project: dict, center_name: str) -> str:
    """Build BioProject XML from a project dict."""
    root = Element("Project")

    # Project descriptor
    descr = SubElement(root, "ProjectDescr")
    SubElement(descr, "Title").text = project["title"]
    SubElement(descr, "Description").text = project.get("description", "")

    # Project type
    project_type = SubElement(root, "ProjectType")
    sub_type = SubElement(project_type, "ProjectTypeSubmission")
    SubElement(sub_type, "ProjectDataTypeSort").text = "eSequenceData"
    SubElement(sub_type, "IntendedDataTypeSet")

    # Identifier (SPUID)
    identifiers = SubElement(root, "ProjectID")
    spuid = SubElement(identifiers, "SPUID", spuid_namespace=center_name)
    spuid.text = project["internal_accession"]

    return _to_xml_string(root)


def build_biosample_xml(
    samples: list[dict],
    domain_id: str,
    center_name: str,
) -> str:
    """Build BioSample XML from a list of sample dicts.

    Uses export_ncbi() to translate SeqDB field names to NCBI names.
    """
    root = Element("BioSampleSet")

    for sample in samples:
        bs = SubElement(root, "BioSample", schema_version="2.0")

        # Sample ID
        sample_id = SubElement(bs, "SampleId")
        spuid = SubElement(sample_id, "SPUID", spuid_namespace=center_name)
        spuid.text = sample.get("internal_accession", "")

        # Descriptor
        descriptor = SubElement(bs, "Descriptor")
        SubElement(descriptor, "Title").text = (
            f"{sample.get('organism', '')} sample"
        )

        # Organism
        org = SubElement(bs, "Organism")
        SubElement(org, "OrganismName").text = sample.get("organism", "")
        if sample.get("tax_id"):
            org.set("taxonomy_id", str(sample["tax_id"]))

        # Attributes — use domain mapper for NCBI field names
        ncbi_fields = export_ncbi(sample, domain_id)
        attributes = SubElement(bs, "Attributes")
        # Skip organism and tax_id since they're in the Organism element
        skip = {"organism", "tax_id"}
        for ncbi_name, value in ncbi_fields.items():
            if ncbi_name in skip:
                continue
            attr = SubElement(attributes, "Attribute", attribute_name=ncbi_name)
            attr.text = str(value)

    return _to_xml_string(root)


def build_sra_xml(
    experiments: list[dict],
    runs: list[dict],
    center_name: str,
) -> str:
    """Build SRA XML for experiments and runs."""
    root = Element("SRASubmission")

    for exp in experiments:
        exp_elem = SubElement(root, "Experiment")

        # Identifiers
        ids = SubElement(exp_elem, "IDENTIFIERS")
        spuid = SubElement(ids, "SPUID", spuid_namespace=center_name)
        spuid.text = exp.get("internal_accession", "")

        # Design
        design = SubElement(exp_elem, "DESIGN")
        SubElement(design, "DESIGN_DESCRIPTION").text = ""
        lib = SubElement(design, "LIBRARY_DESCRIPTOR")
        SubElement(lib, "LIBRARY_STRATEGY").text = exp.get("library_strategy", "")
        SubElement(lib, "LIBRARY_SOURCE").text = exp.get("library_source", "")
        SubElement(lib, "LIBRARY_LAYOUT").text = exp.get("library_layout", "")

        # Platform
        platform = SubElement(exp_elem, "PLATFORM")
        p = exp.get("platform", "ILLUMINA")
        plat_elem = SubElement(platform, p)
        SubElement(plat_elem, "INSTRUMENT_MODEL").text = exp.get("instrument_model", "")

        # Sample reference
        sample_ref = SubElement(exp_elem, "SAMPLE_DESCRIPTOR")
        ref_id = SubElement(sample_ref, "IDENTIFIERS")
        ref_spuid = SubElement(ref_id, "SPUID", spuid_namespace=center_name)
        ref_spuid.text = exp.get("sample_accession", "")

    # Runs
    for run in runs:
        run_elem = SubElement(root, "Run")

        ids = SubElement(run_elem, "IDENTIFIERS")
        spuid = SubElement(ids, "SPUID", spuid_namespace=center_name)
        spuid.text = run.get("internal_accession", "")

        # File reference
        files = SubElement(run_elem, "DataBlock")
        f = SubElement(files, "Files")
        SubElement(
            f, "File",
            filename=run.get("filename", ""),
            filetype=run.get("file_type", "fastq"),
            checksum_method="MD5",
            checksum=run.get("checksum_md5", ""),
        )

        # Experiment reference
        exp_ref = SubElement(run_elem, "EXPERIMENT_REF")
        ref_id = SubElement(exp_ref, "IDENTIFIERS")
        ref_spuid = SubElement(ref_id, "SPUID", spuid_namespace=center_name)
        ref_spuid.text = run.get("experiment_accession", "")

    return _to_xml_string(root)


def _to_xml_string(element: Element) -> str:
    """Convert an Element to a formatted XML string."""
    return tostring(element, encoding="unicode", xml_declaration=False)
