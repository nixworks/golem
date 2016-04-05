from __future__ import print_function

import glob
import os
import shutil
import subprocess
import sys
import tempfile

import params  # This module is generated before this script is run

LUXRENDER_COMMAND = "luxconsole"
OUTPUT_DIR = "/golem/output"
WORK_DIR = "/golem/work"
RESOURCES_DIR = "/golem/resources"


def symlink_or_copy(source, target):
    try:
        os.symlink(source, target)
    except OSError:
        if os.path.isfile(source):
            shutil.copy(source, target)
        else:
            shutil.copytree(source, target)


def find_flm(directory):
    if not os.path.exists(directory):
        return None
    try:
        for root, dirs, files in os.walk(directory):
            for names in files:
                if names[-4:] == ".flm":
                    return os.path.join(root,names)
    except:
        import traceback
        # Print the stack traceback
        traceback.print_exc()
        return None


def format_lux_renderer_cmd(start_task, output_basename, scene_file, num_cores):
    flm_file = find_flm(WORK_DIR)
    if flm_file is not None:
        cmd = [
            "{}".format(LUXRENDER_COMMAND),
            "{}".format(scene_file),
            "-R", "{}".format(flm_file),
            "-t", "{}".format(num_cores)
        ]
    else:
        cmd = [
            "{}".format(LUXRENDER_COMMAND),
            "{}".format(scene_file),
            "-o", "{}/{}{}.png".format(OUTPUT_DIR, output_basename, start_task),
            "-t", "{}".format(num_cores)
        ]
    print(cmd, file=sys.stderr)
    return cmd


def exec_cmd(cmd):
    pc = subprocess.Popen(cmd)
    return pc.wait()


def run_lux_renderer_task(start_task, outfilebasename, scene_file_src,
                          scene_dir, num_cores):

    with tempfile.NamedTemporaryFile(mode="w", suffix=".lxs", dir=WORK_DIR,
                                     delete=False) as tmp_scene_file:
        tmp_scene_file.write(scene_file_src)

    # Create symlinks for all the resources from the scene dir
    # (from which scene_file_src is read) to the work dir:
    for f in os.listdir(scene_dir):
        source = os.path.join(scene_dir, f)
        target = os.path.join(WORK_DIR, f)
        symlink_or_copy(source, target)

    flm_file = find_flm(RESOURCES_DIR)
    if flm_file:
        symlink_or_copy(flm_file, WORK_DIR)

    cmd = format_lux_renderer_cmd(start_task, outfilebasename,
                                  tmp_scene_file.name, num_cores)

    exit_code = exec_cmd(cmd)
    if exit_code is not 0:
        sys.exit(exit_code)
    else:
        outfile = "{}/{}{}.png".format(OUTPUT_DIR, outfilebasename, start_task)
        if not os.path.isfile(outfile):
            flm_file = find_flm(WORK_DIR)
            png_file = flm_file[:-4] + ".png"
            if not os.path.isfile(png_file):
                print("No png file produced", file=sys.stderr)
                sys.error()
            else:
                shutil.copy(png_file, outfile)


run_lux_renderer_task(params.start_task, params.outfilebasename,
                      params.scene_file_src, params.scene_dir,
                      params.num_threads)


