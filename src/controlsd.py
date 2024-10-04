import os
import sys
import runpy

# Force ZMQ
os.environ["ZMQ"] = "1"

# DBC lookup requires this
os.environ["BASEDIR"] = "./"

import openpilot.common.git

openpilot.common.git.get_short_branch = lambda x=0: "v0.9.7"

import openpilot.system.version

openpilot.system.version.get_build_metadata = lambda *args: \
    openpilot.system.version.BuildMetadata('release3',
        openpilot.system.version.OpenpilotMetadata(
            version='v0.9.7',
            release_notes='Release notes',
            git_commit='nvm',
            git_origin='flowy',
            git_commit_date='1970-01-01',
            build_style="unknown",
            is_dirty=False))

runpy.run_module("openpilot.selfdrive.controls.controlsd", run_name= "__main__")