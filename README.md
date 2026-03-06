# Sequence_archive
Sequence deposition archive system following ENA xml submission system

**Overview**
------------

This guide outlines the process of creating a sequence deposit archive similar
to the European Nucleotide Archive (ENA) for NFDP genome and data science. We follow the ENA style for 
data and API design and metadata. 


**Requirements**
---------------

* Programming languages: Python, R, and Bash
* Database management system: MySQL or PostgreSQL
* Cloud storage: Amazon S3 or Google Cloud Storage (optional)



**Step 1: Set up the Archive**
-----------------------------

1. Create a new database to store sequence data.
2. Install required libraries and tools, for QC of reads.
3. Follow ENA/SRA design for studies, project, samples with NFDP style and accessiohn.

**Step 2: Develop the Sequence Deposition System**
----------------------------------------------

1. Design a user-friendly web interface for depositing sequences using HTML, CSS, and JavaScript, or use React with DGA design guide.
2. Implement a Python or R script to parse sequence files (FASTA, GenBank, etc.) and validate data.
3. Create a database schema to store deposited sequences, including metadata.
4. Desing metadata standards for Snpchip data.
5. Build a ENA submission workflow.


**Step 3: Integrate BLAST and Sequence Retrieval**
---------------------------------------------

1. Install BLAST+ and integrate it with the sequence deposition system.
2. Develop a script to perform BLAST searches against the deposited sequences.
3. Use nextflow for pipeline runs. 


**Step 4: Set up Data Import and Export**
--------------------------------------

1. Create scripts to import data from various sources (e.g., primers, gene models).
2. Implement data export features for downstream analysis or publishing.

**Step 5: Test and Refine**
------------------------

1. Perform thorough testing of the sequence deposition system.
2. Gather feedback from users and refine the system accordingly.
3. 



**Additional Considerations**
---------------------------

* Data privacy and security: @Sameer to implement robust access controls and encryption.
* Data archiving and backup: schedule regular backups and maintain a long-term archive strategy.
* Data mamangement plan and index: Design integration to DMP system later to be discussed. 
* Integration with LIMS: @Osama @abdulaziz to work to integrate the deposition with LIMS.


**Next Steps**
--------------

* Develop a project plan and timeline with key milestones.
* Establish a governance model for the sequence deposit archive.
