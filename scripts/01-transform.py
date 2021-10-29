#!/usr/bin/env python

import csv

from os import getenv

from yaml import safe_load
from argparse import ArgumentParser, FileType
from pathlib import Path
from collections import defaultdict
import cmg_transform.tools
from cmg_transform.tools.term_lookup import pull_details, write_cache, remote_calls

from ncpi_fhir_plugin.common import CONCEPT, constants

from cmg_transform.tools.variant_details import Variant

from cmg_transform import Transform, InvalidID
from include_transform.patient import Patient
from include_transform.encounter import Encounter
from include_transform.cde_conversions import CdeVar
from cmg_transform.consent import ConsentGroup

from cmg_transform.change_logger import ChangeLog

import pdb


def Run(output, study_name, dataset, cde, delim=None):
    if "delim" not in dataset:
        delim = "\t"
    else:
        delim = dataset['delim']

    study_title = dataset['study_title']
    study_id = dataset['study_id']

    consent_name = None
    if len(dataset['consent-groups']) == 1:
        consent_name = study_id
    study_group = ConsentGroup(study_name, study_title=study_title, study_id=study_id, group_name=study_title, consent_name=consent_name)

    # We'll dump consents for each group as they are parsed then the entire study
    fconsent = open(output /"consent_groups.tsv", 'wt')
    wconsent = csv.writer(fconsent, delimiter='\t', quotechar='"')
    ConsentGroup.write_default_header(wconsent)

    #pdb.set_trace()

    with open(output / "participant.tsv", 'wt') as partf, \
            open(output / "conditions.tsv", 'wt') as condf, \
            open(output / "diseases.tsv", 'wt') as disf, \
            open(output / "encounters.tsv", 'wt') as encf, \
            open(output / "observations.tsv", 'wt') as obsf:

        # We need to be able find them later to add conditions and whatnot
        subjects = {}

        wparticipant = csv.writer(partf, delimiter='\t', quotechar='"')
        Patient.write_subject_header(wparticipant)

        wcondition = csv.writer(condf, delimiter='\t', quotechar='"')
        Patient.write_condition_header(wcondition)   

        wdisease = csv.writer(disf, delimiter='\t', quotechar='"')
        Patient.write_disease_header(wdisease)   

        wenc = csv.writer(encf, delimiter='\t', quotechar='"')
        Encounter.write_measurements_header(wenc)

        wobservation = csv.writer(obsf, delimiter='\t', quotechar='"') 
        Patient.write_observation_header(wobservation)   

        for consent_name in dataset['consent-groups'].keys():
            consent = dataset['consent-groups'][consent_name]
            # We need a way to point back to the family when we parse our specimen file
            family_lkup = {}

            seq_center = consent['seq_center']
            # There is currently no reference to the proband from parent rows, so we 
            # need to define that. 
            proband_relationships = defaultdict(dict)           # parent_id => "relationship" => proband_id 

            if 'field_map' in consent:
                Transform.LoadFieldMap(consent['field_map'])
                print(Transform._field_map)

            if 'data_map' in consent:
                Transform.LoadDataMap(consent['data_map'])
                print(Transform._data_map)
                print(Transform._data_transform)
                #pdb.set_trace()

            if 'invalid-ids' in consent:
                Transform.LoadInvalidIDs(consent['invalid-ids'])
                print(Transform._invalid_ids)

            consent_group = None
            if len(dataset['consent-groups']) > 1:
                consent_group = ConsentGroup(study_name, study_title=study_title, study_id=study_id, group_name=consent_name, consent_name=consent_name)

            drs_ids = {}
            if 'drs' in consent:
                with open(consent['drs'], 'rt') as file:
                    reader = csv.DictReader(file, delimiter='\t', quotechar='"')

                    for row in reader:
                        locals = dict(zip(row['filenames'].split(","), row['object_id'].split(",")))
                        for fn in locals.keys():
                            drs_ids[fn] = locals[fn]

            with open(consent['participant'], 'rt', encoding='utf-8-sig') as file:
                reader = Transform.GetReader(file, delimiter=delim)

                print(f"The Patient: {consent['participant']}")

                for line in reader:
                    Transform._linenumber += 1
                    #print(f"-- {line}")
                    p = Patient(line)
                    subjects[p.id] = p

                for p in  sorted(subjects.keys()):
                    subjects[p].write_subject_data(study_name, wparticipant)
                    study_group.add_patient(p, seq_center)
                    if consent_group:
                        consent_group.add_patient(p, seq_center)

            # For conditions, we'll read in both condition and ds_condition and then 
            # write those to a single file
            with open(consent['condition'], 'rt', encoding='utf-8-sig') as file:
                reader = Transform.GetReader(file, delimiter=delim)

                print(f"The condition file: {consent['condition']}")
                for line in reader:
                    print(line.keys())
                    subjects[line['participantid']].load_condition(line)
                    Transform._linenumber += 1
                
            with open(consent['ds_condition'], 'rt', encoding='utf-8-sig') as file:
                reader = Transform.GetReader(file, delimiter=delim)

                print(f"DS Condition File: {consent['ds_condition']}")

                print(subjects.keys())
                for line in reader:
                    subjects[line['participantid']].load_ds_condition(line)
                    Transform._linenumber += 1

            for p in  sorted(subjects.keys()):
                subjects[p].write_conditions(study_name, wcondition, cde)
                subjects[p].write_disease(study_name, wdisease)

            # Finally, encounters are a bit different and should be self contained
            with open(consent['encounter'], 'rt', encoding='utf-8-sig') as file:
                reader = Transform.GetReader(file, delimiter=delim)

                print(f"Encounter File: {consent['encounter']}")    
                for line in reader:
                    enc = Encounter(line)
                    enc.write_measurements(study_name, wenc)

            with open(output / "observations.tsv", 'wt') as outf:
                writer = csv.writer(outf, delimiter='\t', quotechar='"')
                Patient.write_observation_header(writer) 

                for p in  sorted(subjects.keys()):
                    subjects[p].write_observations(study_name, writer)
            if consent_group is not None:
                consent_group.write_data(wconsent)
    study_group.write_data(wconsent)
    fconsent.close()

if __name__ == "__main__":
    # Some files may end up going in a directory corresponding to the environment
    hostsfile = Path(getenv("FHIRHOSTS", 'fhir_hosts'))
    config = safe_load(hostsfile.open("rt"))
    #env_options = config.list_environments()

    parser = ArgumentParser()
    parser.add_argument("-d", 
                "--dataset", 
                type=FileType('rt'),
                help=f"Dataset config to be used",
                required=True,
                action='append')
    parser.add_argument("-o", "--out", default='output')
    args = parser.parse_args()

    for dsfile in sorted(args.dataset):
        study = safe_load(dsfile)
        study_name = study['study_name'].replace(' ', '_')
        dirname = Path(f"{args.out}/{study_name}/transformed")
        dirname.mkdir(parents=True, exist_ok=True)
        ChangeLog.InitDB(args.out, study_name, purge_priors=True)
        cde = CdeVar(study['dict_merge'], study['mcd'], study['merge_col'])
        cde.write_cde_to_terms(f"{args.out}/{study_name}/cde_map.csv")

        Run(dirname, study_name, study, cde)
        cde.write_fsh_fragments(f"{args.out}/{study_name}/pheno.fsh")

    # Write the term cache to file since the API can sometimes be unresponsive
    write_cache()

    print(f"Total calls to remote api {remote_calls}")

    # Make sure the cache is saved
    Variant.cache.commit()
    ChangeLog.Close()


