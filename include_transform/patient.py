
"""Help format the patient data to be ready to load into fhir

We are also capturing the condition strings in conditions_present and 
conditions_absent arrays in order to populate the input for the basic
condition objects
"""

from ncpi_fhir_plugin.common import CONCEPT, constants, GENDERFICATION
from cmg_transform import Transform

import sys
import pdb

class Patient:
    def __init__(self, row):
        self.id = Transform.CleanSubjectId(Transform.ExtractVar(row, 'participantid'))
        self.family_id = Transform.ExtractVar(row, 'familyid')
        self.sex = Transform.ExtractVar(row, 'sex', constants.GENDER)
        self.cohort_type = Transform.ExtractVar(row, 'cohort_type')
        self.race = Transform.ExtractVar(row, 'race', None)
        #pdb.set_trace()
        self.eth = Transform.ExtractVar(row, 'ethnicity', constants.ETHNICITY)
        self.abstraction_status = Transform.ExtractVar(row, 'mrabstractionstatus')
        self.phenotype_description = Transform.ExtractVar(row, 'cohort_type')

        self.conditions_present = []
        self.conditions_absent = []
        self.age_of_onset = None

    def load_ds_condition(self, row):
        "SNOMED:734840008 - body structure for Karyotype"
        "LOINC:LP28493-2 Karyotype"
        self.karyoptype = Transform.ExtractVar(row, 'karyotype')
        self.diagnosis = Transform.ExtractVar(row, 'ds_diagnosis')
        self.official_diag = Transform.ExtractVar(row, 'officialdsdiagnosis')

    # We'll just cache the present/absent bits accordingly
    def load_condition(self, row):
        if row['condition_status'] == "TRUE":
            self.conditions_present.append(row['condition_code'])
        elif row['condition_status'] == 'FALSE':
            self.conditions_absent.append(row['condition_code'])

    @classmethod
    def write_subject_header(self, writer):
        writer.writerow([
            CONCEPT.STUDY.NAME,
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.PARTICIPANT.GENDER,
            CONCEPT.PARTICIPANT.RACE,
            CONCEPT.PARTICIPANT.ETHNICITY
        ])

    def write_subject_data(self, study, writer):

        writer.writerow([
            study, 
            self.family_id,
            self.id,
            self.sex,
            self.race,
            self.eth 
        ])

    @classmethod
    def write_disease_header(cls, writer):
        writer.writerow([
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.DIAGNOSIS.DISEASE_ID,
            CONCEPT.DIAGNOSIS.DISEASE_CODE,
            CONCEPT.DIAGNOSIS.DESCRIPTION,
            CONCEPT.DIAGNOSIS.SYSTEM,
            CONCEPT.DIAGNOSIS.NAME,
            CONCEPT.DIAGNOSIS.AGE_ONSET,
            CONCEPT.PHENOTYPE.OBSERVED,
            CONCEPT.PHENOTYPE.DESCRIPTION,
            CONCEPT.DIAGNOSIS.AFFECTED_STATUS
            ])

    def write_disease(self, study_name, writer):
        ds_value = ""

        print(f"Cohort: {self.cohort_type}")
        #pdb.set_trace()
        if self.cohort_type == 'Control':
            ds_value = 'Absent'
        elif self.cohort_type == 'Down syndrome':
            ds_value = 'Present'

        if ds_value != "":
            self.write_condition_row(
                study_name, 
                writer, 
                "OMIM:190685",
                "OMIM:190685", 
                "TRISOMY 21", 
                "https://www.omim.org/", 
                "Down Syndrome", 
                ds_value)

    @classmethod
    def write_observation_header(cls, writer):
        writer.writerow([
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.OBSERVATION.ID,
            CONCEPT.PARTICIPANT.OBSERVATION.NAME,
            CONCEPT.PARTICIPANT.OBSERVATION.SYSTEM,
            CONCEPT.PARTICIPANT.OBSERVATION.DESCRIPTION,
            CONCEPT.PARTICIPANT.OBSERVATION.VALUE
        ])

    def write_observations(self, study_name, writer):
        writer.writerow([
            self.id,            
            study_name, 
            self.family_id,
            "MRAbstractionStatus",
            "MRAbstractionStatus",
            None, 
            None,
            self.abstraction_status
        ])

        # "SNOMED:734840008 - body structure for Karyotype"
        """writer.writerow([
            self.id,            
            study_name, 
            self.family_id,
            "734840008",
            "body structure for Karyotype",
            "http://snomed.info/sct",
            "body structure for Karyotype",
            self.karyoptype
        ])"""
        writer.writerow([
            self.id,            
            study_name, 
            self.family_id,
            "LP28493-2",
            "Karyotype",
            "http://loinc.org",
            "Karyotype",
            self.karyoptype
        ])
        """if self.official_diag.lower() != "na":
            # Kind of guessing how to handle these...so, using an observation
            writer.writerow([
                self.id,            
                study_name, 
                self.family_id,
                "315115008",
                "Downs screening test",
                "http://snomed.info/sct",
                "Official DS Diagnosis",
                self.official_diag
            ])"""
        if self.official_diag.lower() != "na":
            # Kind of guessing how to handle these...so, using an observation
            writer.writerow([
                self.id,            
                study_name, 
                self.family_id,
                "73779-1",
                "Down syndrome karyotype status [US Standard Certificate of Live Birth]",
                "http://loinc.org",
                "Official DS Diagnosis",
                self.official_diag
            ])
    @classmethod
    def write_condition_header(cls, writer):
        writer.writerow([
            CONCEPT.FAMILY.ID,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.STUDY.NAME,
            CONCEPT.PHENOTYPE.ID,
            CONCEPT.DIAGNOSIS.DISEASE_CODE,
            CONCEPT.DIAGNOSIS.DESCRIPTION,
            CONCEPT.DIAGNOSIS.SYSTEM,
            CONCEPT.DIAGNOSIS.NAME,
            CONCEPT.DIAGNOSIS.AGE_ONSET,
            CONCEPT.PHENOTYPE.OBSERVED,
            CONCEPT.PHENOTYPE.DESCRIPTION,
            CONCEPT.DIAGNOSIS.AFFECTED_STATUS
            ])

    def write_conditions(self, study_name, writer, cde_conversions):
        for condition_desc in self.conditions_present:
            aff_status = constants.PHENOTYPE.OBSERVED.PRESENT
            codes_written = 0
            condition_id = None
            for code in cde_conversions.get_matches(condition_desc):
                condition_system, condition_name, condition_code = code
                if condition_code is not None and condition_code.strip() != "":
                    if codes_written == 0:
                        condition_id = condition_code
                    self.write_condition_row(study_name, writer, condition_id, condition_code, condition_desc, condition_system, condition_name, aff_status)
                    codes_written += 1
            if codes_written == 0:
                self.write_condition_row(study_name, writer, None, None, condition_desc, None, condition_desc, aff_status)

        for condition_desc in self.conditions_absent:
            aff_status = constants.PHENOTYPE.OBSERVED.ABSENT
            codes_written = 0
            condition_id = None
            for code in cde_conversions.get_matches(condition_desc):
                condition_system, condition_name, condition_code = code
                if condition_code is not None and condition_code.strip() != "":
                    if codes_written == 0:
                        condition_id = condition_code
                    self.write_condition_row(study_name, writer, condition_id, condition_code, condition_desc, condition_system, condition_name, aff_status)
                    codes_written += 1
            if codes_written == 0:
                self.write_condition_row(study_name, writer, None, None, condition_desc, None, condition_desc, aff_status)

    def write_condition_row(self, study_name, writer, disease_id, disease_code, disease_description, disease_system, disease_name, affected_status):
        writer.writerow([
            self.family_id,
            self.id,
            study_name,
            disease_id,
            disease_code,
            disease_description,
            disease_system,
            disease_name,
            self.age_of_onset,
            affected_status,
            disease_description,
            self.phenotype_description
        ])