# fhir-ingest-htp
Included inside this repository are the scripts used to load INCLUDE/HTP data into KF dev FHIR server.

There are two components to the process: Transformation and Loading (Extraction takes place during the initial transformation script). 

## Transformation
The purpose here is to extract the relevant data from the HTP CSV files and format the resulting output to suit the requirements of the CMG FHIR Ingest library that was previously written. These CSV input files were transformed using an R script written by Robert Carroll, primarily to roll the wide condition columns into long format. As a result, the scripts will not map directly to the official CSVs. 

## Loading into FHIR
The CMG ingest plugin is written for the [KF Ingest library](https://github.com/kids-first/kf-lib-data-ingest). While that code was originally written to suite the needs for loading CMG data into FHIR, there is sufficient overlap in requirements to permit it's use for other group's data as well. As such, the plugin has been expanded to include functionality that isn't specific to CMG. 

To accomodate the use of this plugin, the only real requirement is that the output of the transformation step must meet the expectations for the relevant components required for ingestion. 

## Requirements
The primary requirement is the CMG FHIR plugin, which is a part of the [CMG Ingest suite](https://github.com/anvilproject/cmg-data-ingest). 

Additional requirements include (Are also required by the ingest suite above): 
[NCPI FHIR Client](https://github.com/NIH-NCPI/ncpi-fhir-client) A library used to simplify authentication against various types of FHIR servers. 

[NCPI FHIR Utility](https://github.com/NIH-NCPI/ncpi-fhir-utility) A library used by the client above to interact with the FHIR REST API.
