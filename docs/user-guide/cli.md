# SeqDB CLI Reference

The SeqDB CLI (`seqdb`) provides command-line access to the SeqDB platform for submitting genomic data, fetching reads, and integrating with nf-core pipelines.

## Installation

```bash
pip install seqdb-cli
```

## Authentication

```bash
# Login (stores credentials in ~/.seqdb/config.toml)
seqdb login --url https://api.seqdb.nfdp.dev --email you@example.com

# Logout
seqdb logout
```

## Submitting Data

### Download a template

```bash
seqdb template ERC000011 --output my_samples.tsv
```

### Upload files to staging

```bash
seqdb upload reads/*.fastq.gz --threads 8
```

### Validate a sample sheet

```bash
seqdb validate my_samples.tsv --checklist ERC000011
```

### Submit (all-in-one)

Upload files, validate, and create entities in one command:

```bash
seqdb submit my_samples.tsv \
  --checklist ERC000011 \
  --project NFDP-PRJ-000001 \
  --files ./reads/ \
  --threads 8
```

Add `--yes` to skip the confirmation prompt.

## Fetching Data

Fetch reads from SeqDB with nf-core-compatible samplesheet output:

```bash
# Fetch by project — downloads reads + generates samplesheet
seqdb fetch NFDP-PRJ-000001 -o ./data/

# Fetch by sample
seqdb fetch NFDP-SAM-000003 -o ./data/

# Generate presigned URLs instead of downloading
seqdb fetch NFDP-PRJ-000001 --urls-only -o ./data/

# Specify nf-core pipeline format
seqdb fetch NFDP-PRJ-000001 --format rnaseq -o ./data/
seqdb fetch NFDP-PRJ-000001 --format sarek -o ./data/
```

### Using with nf-core pipelines

```bash
seqdb fetch NFDP-PRJ-000001 --format rnaseq -o ./data/
nextflow run nf-core/rnaseq --input ./data/samplesheet.csv

seqdb fetch NFDP-PRJ-000001 --format sarek -o ./data/
nextflow run nf-core/sarek --input ./data/samplesheet.csv
```

### Supported formats

| Format    | Columns                                    | Pipeline         |
|-----------|--------------------------------------------|------------------|
| `generic` | sample, fastq_1, fastq_2                   | Any              |
| `rnaseq`  | sample, fastq_1, fastq_2, strandedness     | nf-core/rnaseq   |
| `sarek`   | patient, sample, lane, fastq_1, fastq_2    | nf-core/sarek    |

## Ingesting Results

Import MultiQC results back into SeqDB:

```bash
seqdb ingest NFDP-PRJ-000001 --multiqc ./results/multiqc_data/
```

## Status & Search

```bash
# List recent projects
seqdb status

# Check a specific accession
seqdb status NFDP-PRJ-000001
seqdb status NFDP-SUB-000012

# Search
seqdb search "Bos taurus"
```

## Common Workflows

### Full submission workflow

```bash
# 1. Login
seqdb login --url https://api.seqdb.nfdp.dev --email you@example.com

# 2. Get a template
seqdb template ERC000011 -o samples.tsv

# 3. Fill in samples.tsv with your metadata

# 4. Submit with files
seqdb submit samples.tsv -c ERC000011 -p NFDP-PRJ-000001 -f ./reads/

# 5. Check status
seqdb status NFDP-PRJ-000001
```

### Fetch and analyse

```bash
# 1. Fetch reads with samplesheet
seqdb fetch NFDP-PRJ-000001 --format rnaseq -o ./analysis/

# 2. Run nf-core pipeline
nextflow run nf-core/rnaseq --input ./analysis/samplesheet.csv

# 3. Ingest QC results back
seqdb ingest NFDP-PRJ-000001 --multiqc ./analysis/results/multiqc_data/
```

## Options

All commands support `--help` for detailed usage:

```bash
seqdb --help
seqdb submit --help
seqdb fetch --help
```
