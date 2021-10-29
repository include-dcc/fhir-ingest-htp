from cmg_transform import Transform
from ncpi_fhir_plugin.common import CONCEPT, constants
import pdb
"""For include, (at least for the HTP samples I'm using for reference) this will
cover the Specimen, Encounter and the measurements: BMI, Height and Weight
"""
invalid_values = set(["", "NA"])

class Encounter:
    def __init__(self, row):
        #pdb.set_trace()
        self.id = Transform.CleanSubjectId(Transform.ExtractVar(row, 'participantid'))
        #self.encounter_id = Transform.ExtractID(row, 'event_name')
        if row.get("event_name") is not None:
            #pdb.set_trace()
            self.encounter_id = row["event_name"].split(" ")[-1] #Transform.ExtractID(row, 'event_name')
        self.age_at_event = Transform.ExtractVar(row, 'age_at_visit')
        # "whole blood": "UBERON:0000178"
        self.sample_id = Transform.ExtractVar(row, 'labid')
        self.weight_kg = Transform.ExtractVar(row, 'weight_kg')
        self.height_cm = Transform.ExtractVar(row, 'height_cm')
        self.bmi = Transform.ExtractVar(row, 'bmi')


    @classmethod
    def write_measurements_header(cls, writer):
        writer.writerow([
            CONCEPT.STUDY.NAME,
            CONCEPT.PARTICIPANT.ID,
            CONCEPT.BIOSPECIMEN.ID,
            CONCEPT.PARTICIPANT.AGE_AT_EVENT,
            CONCEPT.PARTICIPANT.VISIT_NUMBER,
            CONCEPT.PARTICIPANT.MEASUREMENT.ID,
            CONCEPT.PARTICIPANT.MEASUREMENT.UNITS,
            CONCEPT.PARTICIPANT.MEASUREMENT.UNITS_SYSTEM,
            CONCEPT.PARTICIPANT.MEASUREMENT.CODE,
            CONCEPT.PARTICIPANT.MEASUREMENT.NAME,
            CONCEPT.PARTICIPANT.MEASUREMENT.DERIVED_FROM,
            CONCEPT.PARTICIPANT.MEASUREMENT.ALT_CODES,
            CONCEPT.PARTICIPANT.MEASUREMENT.DESC,
            CONCEPT.BIOSPECIMEN.TISSUE_TYPE,
            CONCEPT.BIOSPECIMEN.TISSUE_TYPE_NAME,
        ])

    # We'll have different rows for each subject
    def write_measurements(self, study, writer):
        global invalid_values
        # Height
        if self.height_cm is not None and self.height_cm.strip() not in invalid_values:
            writer.writerow([
                study,
                self.id,
                self.sample_id,
                self.age_at_event,
                self.encounter_id,
                self.height_cm,
                'cm',
                "http://unitsofmeasure.org",
                '8302-2',
                'Body height',
                None,
                'https://www.ohdsi.org^^3036277',
                None,
                "UBERON:0000178",
                "whole blood"
            ])

        if self.weight_kg is not None and self.weight_kg.strip() not in invalid_values:
            writer.writerow([
                study,
                self.id,
                self.sample_id,
                self.age_at_event,
                self.encounter_id,
                self.weight_kg,
                'kg',
                "http://unitsofmeasure.org",
                '29463-7',
                'Body weight',
                None,
                'https://www.ohdsi.org^^3025315',
                None,
                "UBERON:0000178",
                "whole blood"])

        if self.bmi is not None and self.bmi.strip() not in invalid_values:
            writer.writerow([
                study, 
                self.id,
                self.sample_id,
                self.age_at_event,
                self.encounter_id,
                self.bmi,
                'kg/m2',
                "http://unitsofmeasure.org",
                '39156-5',
                'Body mass index (BMI) [Ratio]',
                '8302-2|29463-7',
                'https://www.ohdsi.org^^3038553',
                None,
                "UBERON:0000178",
                "whole blood"])