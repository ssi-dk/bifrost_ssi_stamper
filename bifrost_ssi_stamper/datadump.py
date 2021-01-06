from bifrostlib import common
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import Component
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from bifrostlib.datahandling import Category
from bifrostlib.datahandling import Test
from typing import Dict
import os
import datetime


def has_reads_files(stamper, sample):
    paired_reads = sample.get_category("paired_reads")
    test = Test(name="has_reads_files", display_name="No reads", effect="core facility", status="undefined")
    if paired_reads is None:
        test["status"] = "fail"
        test["reason"] = "paired_reads category not set"
    else:
        test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def has_min_reads(stamper, sample):
    size_check = sample.get_category("size_check")
    test = Test(name="has_min_reads", display_name="Less than min reads", effect="core facility", status="undefined")
    if size_check is None:
        test["status"] = "fail"
        test["reason"] = "size_check category not set"
    else:
        test["value"] = size_check["summary"].get("has_min_num_of_reads", False)
        if test['value'] != True:
            test["status"] = "fail"
            test["reason"] = "Less than min reads"
        else:
            test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def main_species_level_ok(stamper, sample, component):
    species_detection = sample.get_category("species_detection")
    test = Test(name="main_species_level_ok", display_name="Multiple species detected", effect="supplying lab", status="undefined")
    if species_detection is None:
        test["status"] = "fail"
        test["reason"] = "species_detection category not set"
    else:
        test["value"] = species_detection["summary"].get("percent_classified_species_1", 0) + species_detection["summary"].get("percent_unclassified", 0)
        if test["value"] < component["options"]["min_species"]:
            test["status"] = "fail"
            test["reason"] = f"Value {round(test['value'],2)} is below threshold ({component['options']['min_species']})"
        else:
            test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def unclassified_level_ok(stamper, sample, component):
    species_detection = sample.get_category("species_detection")
    test = Test(name="unclassified_level_ok", display_name="High unclassified", effect="supplying lab", status="undefined")
    if species_detection is None:
        test["status"] = "fail"
        test["reason"] = "species_detection category not set"
    else:
        test["value"] = species_detection["summary"].get("percent_unclassified", 0)
        if test["value"] >= component["options"]["max_unclassified"]:
            test["status"] = "fail"
            test["reason"] = f"Value {round(test['value'],2)} is below threshold ({component['options']['max_unclassified']})"
        else:
            test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def species_in_db(stamper, sample, component):
    species_detection = sample.get_category("species_detection")
    test = Test(name="species_in_db", display_name="No species submitted - using default values", effect="supplying lab", status="undefined")
    if species_detection is None:
        test["status"] = "fail"
        test["reason"] = "species_detection category not set"
    else:
        test["value"] = species_detection["summary"].get("species", None)
        if test["value"] not in component["options"]["species_qc_value_mapping"]:
            test["status"] = "fail"
            test["reason"] = f"Detected species ({test['value']}) not in bifrost db. Can't estimate proper QC values."
        else:
            test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def species_provided_is_detected(stamper, sample):
    species_detection = sample.get_category("species_detection")
    test = Test(name="species_provided_is_detected", display_name="Detected species mismatch", effect="supplying lab", status="undefined")
    if species_detection is None:
        test["status"] = "fail"
        test["reason"] = "species_detection category not set"
    else:
        test["value"] = species_detection["summary"].get("species", None)
        if test["value"] is None:
            test["status"] = "pass"
            test["reason"] = "No submitted species"
        elif test["value"] != species_detection["summary"].get("detected_species", None):
            test["status"] = "fail"
            test["reason"] = f"Detected species ({species_detection['summary'].get('species', None)} different than expected ({test['value']}))"
        else:
            test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def genome_size_at_x1_ok(stamper, sample, component):
    denovo_assembly = sample.get_category("denovo_assembly")
    species_detection = sample.get_category("species_detection")
    test = Test(name="genome_size_at_x1_ok", display_name="Atypical genome size (x1)", effect="supplying lab", status="undefined")
    if denovo_assembly is None:
        test["status"] = "fail"
        test["reason"] = "denovo_assembly category not set"
    elif species_detection is None:
        test["status"] = "fail"
        test["reason"] = "species_detection category not set"
    else:
        test["value"] = denovo_assembly["summary"].get('length', 0)
        species = species_detection["summary"].get("species", None)
        if species not in component["options"]["species_qc_value_mapping"]:
            species = "default"
        if (test['value'] > component["options"]["species_qc_value_mapping"][species]["min_length"] and 
            test['value'] < component["options"]["species_qc_value_mapping"][species]["max_length"]):
            test['status'] = "pass"
        else:
            test['status'] = 'fail'
            test['reason'] = f"Value ({test['value']}) below or above expected ({component['options']['species_qc_value_mapping'][species]['min_length']}, {component['options']['species_qc_value_mapping'][species]['min_length']})"
    stamper["summary"]["tests"].append(test.json)

def genome_size_at_x10_ok(stamper, sample, component):
    mapping_qc = sample.get_category("mapping_qc")
    species_detection = sample.get_category("species_detection")
    test = Test(name="genome_size_at_x10_ok", display_name="Atypical genome size (x10)", effect="supplying lab", status="undefined")
    if mapping_qc is None:
        test["status"] = "fail"
        test["reason"] = "mapping_qc category not set"
    elif species_detection is None:
        test["status"] = "fail"
        test["reason"] = "species_detection category not set"
    else:
        test["value"] = mapping_qc["summary"].get('values_at_floor_of_depth', 0).get('x10', 0).get('length', 0)
        species = species_detection["summary"].get("species", None)
        if species not in component["options"]["species_qc_value_mapping"]:
            species = "default"
        if (test['value'] > component["options"]["species_qc_value_mapping"][species]["min_length"] and
                test['value'] < component["options"]["species_qc_value_mapping"][species]["max_length"]):
            test['status'] = "pass"
        else:
            test['status'] = 'fail'
            test['reason'] = f"Value ({test['value']}) below or above expected ({component['options']['species_qc_value_mapping'][species]['min_length']}, {component['options']['species_qc_value_mapping'][species]['min_length']})"
    stamper["summary"]["tests"].append(test.json)

def genome_size_difference_x1_x10_ok(stamper, sample, component):
    denovo_assembly = sample.get_category("denovo_assembly")
    mapping_qc = sample.get_category("mapping_qc")
    test = Test(name="genome_size_difference_x1_x10_ok", display_name="Atypical genome size (x1 - x10)", effect="supplying lab", status="undefined")
    if denovo_assembly is None:
        test["status"] = "fail"
        test["reason"] = "denovo_assembly category not set"
    elif mapping_qc is None:
        test["status"] = "fail"
        test["reason"] = "mapping_qc category not set"
    else:
        test["value"] = denovo_assembly["summary"].get('length', 0) - mapping_qc["summary"].get('values_at_floor_of_depth', 0).get('x10', 0).get('length', 0)
        if test["value"] < component["options"]["max_size_difference_for_x1_and_x10"]:
            test["status"] = "pass"
        else:
            test["status"] = "fail"
            test["reason"] = f"Value ({test['value']}) above expected ({component['options']['max_size_difference_for_x1_and_x10']})"
    stamper["summary"]["tests"].append(test.json)

def genome_average_depth_ok(stamper, sample, component):
    denovo_assembly = sample.get_category("denovo_assembly")
    mapping_qc = sample.get_category("mapping_qc")
    test = Test(name="genome_average_depth_ok", display_name="Atypical genome coverage", effect="supplying lab", status="undefined")
    if denovo_assembly is None:
        test["status"] = "fail"
        test["reason"] = "denovo_assembly category not set"
    elif mapping_qc is None:
        test["status"] = "fail"
        test["reason"] = "mapping_qc category not set"
    else:
        test['value'] = denovo_assembly['summary'].get('depth', 0)
        if test['value'] < component['options']['average_coverage_fail']:
            test["status"] = "fail"
            test["reason"] = f"Lack of reads ({test['value']} < {component['options']['average_coverage_fail']})"
            test["effect"] = "core_facility"
        elif test['value'] < component['options']['average_coverage_low']:
            test["status"] = "fail"
            test["reason"] = f"Not enough reads ({test['value']} < {component['options']['average_coverage_low']})"
            test["effect"] = "core_facility"
        elif test['value'] < component['options']['average_coverage_warn']:
            test["status"] = "fail"
            test["reason"] = f"Low reads ({test['value']} < {component['options']['average_coverage_warn']})"
        else:
            test["status"] = "pass"
    stamper["summary"]["tests"].append(test.json)

def evaluate_tests_and_stamp(stamper, sample):
    core_facility = False
    supplying_lab = False
    for test in stamper['summary']['tests']:
        if test["status"] == "fail":
            if test["effect"] == "supplying lab":
                supplying_lab = True
            elif test["effect"] == "core facility":
                core_facility = True

    #Custom check
    checks = [False, False, False, False]
    for test in stamper['summary']['tests']:
        if test["name"] == 'genome_size_difference_x1_x10_ok' and test['status'] == 'pass':
            checks[0] = True
        if test["name"] == 'genome_average_depth_ok' and test['status'] == 'fail' and test['effect'] == "supplying lab":
            checks[1] = True
        if test["name"] == 'species_provided_is_detected' and test['status'] == 'pass':
            checks[2] = True
        if test["name"] == 'genome_size_at_x1_ok' and test['status'] == 'fail':
            checks[3] = True
    
    species_detection = sample.get_category("species_detection")
    if species_detection is not None:
        if species_detection["summary"]["species"] == species_detection["summary"]["detected_species"]:
            if all(checks) == True:
                core_facility = True

    action = "OK"
    status = "pass"
    if supplying_lab:
        status = "fail"
        action = "supplying lab"
    if core_facility:
        status = "fail"
        action = "core facility"
    stamper["stamp"] = {
        "display_name": "ssi_stamper",
        "name": "ssi_stamper",
        "status": status,
        "value": action,
        "date": common.date_now(),
        "reason": ""
    }

def generate_report(stamper):
    data = []
    for test in stamper['summary']['tests']:
        data.append({"test": f"{test.get('display_name','')}: {test.get('status','')}: {test.get('value','')}: {test.get('reason','')}"})

    stamper['report']['columns']['items'] = {"id": "test", "name": "test"}
    stamper['report']['data'] = data

def datadump(samplecomponent_ref_json: Dict):
    samplecomponent_ref = SampleComponentReference(value=samplecomponent_ref_json)
    samplecomponent = SampleComponent.load(samplecomponent_ref)
    sample = Sample.load(samplecomponent.sample)
    component = Component.load(samplecomponent.component)
    stamper = samplecomponent.get_category("stamper")
    if stamper is None:
        stamper = Category(value={
            "name": "stamper",
            "component": {"id": samplecomponent["component"]["_id"], "name": samplecomponent["component"]["name"]},
            "summary": { "tests": [] },
            "report": { "columns": {}, "data": {}}
        })
    has_reads_files(stamper, sample)
    has_min_reads(stamper, sample)
    main_species_level_ok(stamper, sample, component)
    unclassified_level_ok(stamper, sample, component)
    species_in_db(stamper, sample, component)
    species_provided_is_detected(stamper, sample)
    genome_size_at_x1_ok(stamper, sample, component)
    genome_size_at_x10_ok(stamper, sample, component)
    genome_size_difference_x1_x10_ok(stamper, sample, component)
    genome_average_depth_ok(stamper, sample, component)
    evaluate_tests_and_stamp(stamper, sample)
    generate_report(stamper)
    samplecomponent.set_category(stamper)
    sample.set_category(stamper)
    samplecomponent.save_files()
    common.set_status_and_save(sample, samplecomponent, "Success")
    with open(os.path.join(samplecomponent["component"]["name"], "datadump_complete"), "w+") as fh:
        fh.write("done")

datadump(
    snakemake.params.samplecomponent_ref_json,
)
