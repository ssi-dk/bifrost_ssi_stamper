#- Templated section: start ------------------------------------------------------------------------
import os
import sys
import traceback

from bifrostlib import common
from bifrostlib.datahandling import SampleReference
from bifrostlib.datahandling import Sample
from bifrostlib.datahandling import ComponentReference
from bifrostlib.datahandling import Component
from bifrostlib.datahandling import SampleComponentReference
from bifrostlib.datahandling import SampleComponent
from snakemake.io import directory
import datetime

os.umask(0o2)

try:
    sample_ref = SampleReference(_id=config.get('sample_id', None), name=config.get('sample_name', None))
    sample: Sample = Sample.load(sample_ref)
    if sample is None:
        raise Exception("invalid sample passed")

    component_ref = ComponentReference(name=config['component_name'])
    component: Component = Component.load(reference=component_ref)
    if component is None:
        raise Exception("invalid component passed")

    samplecomponent_ref = SampleComponentReference(
        name=SampleComponentReference.name_generator(sample.to_reference(), component.to_reference())
    )
    samplecomponent = SampleComponent.load(samplecomponent_ref)

    if samplecomponent is None:
        samplecomponent = SampleComponent(
            sample_reference=sample.to_reference(),
            component_reference=component.to_reference()
        )

    common.set_status_and_save(sample, samplecomponent, "Running")

except Exception:
    print(traceback.format_exc(), file=sys.stderr)
    raise Exception("failed to set sample, component and/or samplecomponent")

if not samplecomponent.has_requirements():
   common.set_status_and_save(sample, samplecomponent, "Requirements not met")
   raise SystemExit("Requirements not met")

onerror:
    if not samplecomponent.has_requirements():
        common.set_status_and_save(sample, samplecomponent, "Requirements not met")
    if samplecomponent["status"] == "Running":
        common.set_status_and_save(sample, samplecomponent, "Failure")

# -------------------------------------------------------------------------
# MAIN + TIMING
# -------------------------------------------------------------------------

rule all:
    input:
        f"{component['name']}/datadump_complete",
        f"{component['name']}/runtime_set"
    run:
        common.set_status_and_save(sample, samplecomponent, "Success")

rule set_time_start:
    output:
        start_file = f"{component['name']}/time_start.txt"
    run:
        import time
        with open(output.start_file, "w") as fh:
            fh.write(str(time.time()))

rule setup:
    input:
        rules.set_time_start.output.start_file
    output:
        init_file = touch(f"{component['name']}/initialized")
    run:
        samplecomponent["path"] = os.path.join(os.getcwd(), component["name"])
        samplecomponent.save()

# -------------------------------------------------------------------------
# MAIN WORK (ssi_stamper only runs datadump)
# -------------------------------------------------------------------------

rule datadump:
    message:
        "Running step: datadump"
    log:
        out_file = f"{component['name']}/log/datadump.out.log",
        err_file = f"{component['name']}/log/datadump.err.log",
    benchmark:
        f"{component['name']}/benchmarks/datadump.benchmark"
    output:
        complete = f"{component['name']}/datadump_complete"
    params:
        samplecomponent_ref_json = samplecomponent.to_reference().json
    script:
        os.path.join(os.path.dirname(workflow.snakefile), "datadump.py")

# -------------------------------------------------------------------------
# END TIME + GIT VERSION
# -------------------------------------------------------------------------

rule git_version:
    message:
        "Running step: git_version"
    log:
        out_file = f"{component['name']}/log/git_version.out.log",
        err_file = f"{component['name']}/log/git_version.err.log",
    benchmark:
        f"{component['name']}/benchmarks/git_version.benchmark"
    input:
        rules.setup.output.init_file
    output:
        git_hash = f"{component['name']}/git_hash.txt"
    run:
        import subprocess, os

        snake_dir = os.path.dirname(workflow.snakefile)

        try:
            git_hash = subprocess.check_output(
                ["git", "-C", snake_dir, "rev-parse", "HEAD"],
                stderr=subprocess.STDOUT,
                text=True
            ).strip()
        except Exception as e:
            git_hash = "-"
            os.makedirs(os.path.dirname(log.err_file), exist_ok=True)
            with open(log.err_file, "a") as fh:
                fh.write(f"[git_version] Could not determine git hash from {snake_dir}: {e}\n")

        with open(output.git_hash, "w") as fh:
            fh.write(str(git_hash))

rule set_time_end:
    input:
        rules.datadump.output.complete,
        rules.git_version.output.git_hash
    output:
        end_file = f"{component['name']}/time_end.txt"
    run:
        import time
        with open(output.end_file, "w") as fh:
            fh.write(str(time.time()))

# -------------------------------------------------------------------------
# DUMP INFO
# -------------------------------------------------------------------------

rule dump_info:
    input:
        start_file = rules.set_time_start.output.start_file,
        end_file = rules.set_time_end.output.end_file,
        git_hash = rules.git_version.output.git_hash
    output:
        runtime_flag = touch(f"{component['name']}/runtime_set")
    run:
        import time
        from bifrostlib.datahandling import SampleComponent

        with open(input.start_file) as fh:
            t_start = float(fh.read().strip())
        with open(input.end_file) as fh:
            t_end = float(fh.read().strip())
        with open(input.git_hash) as fh:
            git_hash = str(fh.read().strip())

        runtime_minutes = (t_end - t_start) / 60.0
        print(f"runtime in minutes {runtime_minutes}")

        sc = SampleComponent.load(samplecomponent.to_reference())
        sc["time_start"] = datetime.datetime.fromtimestamp(t_start).strftime("%Y-%m-%d %H:%M:%S")
        sc["time_end"] = datetime.datetime.fromtimestamp(t_end).strftime("%Y-%m-%d %H:%M:%S")
        sc["time_running"] = round(runtime_minutes, 3)
        sc["git_hash"] = git_hash

        sc.save()

