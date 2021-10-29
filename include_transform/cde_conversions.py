"""
Build a system to convert phenotypes into the codes where we have the right information

This is being worked on by google documents: 
    Merge : https://docs.google.com/spreadsheets/d/1HvT68h3C29Kb6g59EDoorTsifIEJ86PPMZEbgmkGOiU
    MCD DD : https://docs.google.com/spreadsheets/d/1gUiFUAke5vz-JId4mExoYxwx3X0pr2TdbTlMvtZtTdo

I did strip some extraneous header information for the exported files I'm using. However,
the colnames were not changed

MCD DD ties a common var to HPO, Mondo and ICD where possible
Merge links a specific var from a given dataset (such as HTP) and the varname in the MCD
"""

from collections import defaultdict
import csv
import pdb

class NoCodeFound:
    def __init__(self, source, label):
        super.__init__(f"No Code Found for {source}:{label}")
        self.source = source 
        self.label = label

class DictEntry:
    all_codes = defaultdict(dict)
    cs_urls = {
        "HPO": "http://purl.obolibrary.org/obo/hp.owl",
        "Mondo": "http://purl.obolibrary.org/obo/mondo.owl",
        "OMIM": "https://omim.org/"
    }
    def __init__(self, row, label, varname):
        if label != "ICD":
            #pdb.set_trace()
            self.code = row[f"{label} ID"].replace("_", ":")
            self.label = row[f"{label} Label"]
            assert(self.code not in DictEntry.all_codes)
            if self.code is None or self.code.strip() == "" or self.code in ['N/A']:
                raise NoCodeFound(label, varname)
            DictEntry.all_codes[label][self.code] = self
        else:
            # We have a header with 10 (I guess) identically named columns. 
            # Can't use csv dict reader for that, since it seems to overwrite
            # the one place for each of these.
            # If we want ICD, we'll need to use a standard list and id the 
            # difference col indexes required for each of those codes and labels
            self.code = row["ICD code"]

    @classmethod
    def dump_fsh_entries(cls, writer):
        for term in cls.all_codes:
            writer.write(f"/* {term} */\n")
            for code_value in list(cls.all_codes[term]):  
                if code_value in cls.all_codes[term]:
                    code = cls.all_codes[term][code_value]
                    #pdb.set_trace()
                    writer.write(f"* #{code.code} \"{code.label}\"\n")
            writer.write("\n\n")

class CdeVar:
    def get_matches(self, code):
        matches = []

        if code in self.hpo:
            #pdb.set_trace()
            matches.append([
                DictEntry.cs_urls["HPO"],
                self.hpo[code].label, 
                self.hpo[code].code
            ])
        if code in self.mondo:
            matches.append([
                DictEntry.cs_urls["Mondo"],
                self.mondo[code].label,
                self.mondo[code].code
            ])
        

        if len(matches) == 0:
            print(f"No match for code {code}")
            #pdb.set_trace()
        return matches

    def __init__(self, merge, mcd_dd, merge_col):
        # All of these will point pheno=>relevant code if there is a valid match
        self.cde = dict()
        self.hpo = dict()
        self.mondo = dict()
        self.icd = dict()

        #pdb.set_trace()
        # Get the vars we are interested in 
        with open(merge, 'rt') as f:
            reader = csv.DictReader(f, delimiter=',', quotechar='"')

            for row in reader:
                target_var = row[merge_col]
                if target_var is not None:
                    cde_var = row['CDE Variable']
                    assert(cde_var is not None)

                    self.cde[cde_var] = target_var
        #pdb.set_trace()
        # Now we'll find their mappings
        with open(mcd_dd, 'rt') as f:
            reader = csv.DictReader(f, delimiter=',', quotechar='"')

            for row in reader:
                cde_var = row['Variable / Field Name']
                if cde_var in self.cde:
                    #pdb.set_trace()
                    ds_var = self.cde[cde_var]
                    if ds_var and ds_var.strip() is not "":
                        try:
                            #pdb.set_trace()
                            
                            self.hpo[ds_var] = DictEntry(row, 'HPO', cde_var)
                        except:
                            if row['HPO ID'] != "N/A":
                                pdb.set_trace()
                                pass
                            
                        try:
                            self.mondo[ds_var] = DictEntry(row, 'Mondo', cde_var)
                        except:
                            print(sorted(row.keys()))
                            if row['Mondo ID'] != 'N/A':
                                pdb.set_trace()
                                pass
                else:
                    print(f"Skipping code {cde_var}")
        #pdb.set_trace()

    def write_cde_to_terms(self, filename):
        with open(filename, 'wt') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"')
            writer.writerow(['CDE', 'CDE2', 'HPO', 'Mondo'])
            #pdb.set_trace()
            for var in self.cde.keys():
                target_var = self.cde[var]
                data = [var, target_var, '', '']
                if target_var in self.hpo:
                    data[2] = self.hpo[target_var].code
                if target_var in self.mondo:
                    data[3] = self.mondo[target_var].code
                writer.writerow(data)

    def write_fsh_fragments(self, filename):
        with open(filename, 'wt') as f:
            DictEntry.dump_fsh_entries(f)



