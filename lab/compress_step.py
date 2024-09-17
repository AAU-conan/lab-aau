import shutil
import tarfile
from pathlib import Path
import logging
import os

class CompressStep:
    def __init__(self, lab_experiment, target_folder, tmp_folder = None):
        self.lab_experiment = lab_experiment
        self.target_folder = target_folder
        self.tmp_folder = tmp_folder

    def __call__(self):
        if not os.path.exists(self.lab_experiment.path):
            logging.critical(f"Compress step could not find data at: {self.lab_experiment.path}.")
        if self.tmp_folder:
            Path(self.tmp_folder).mkdir(parents=True, exist_ok=True)
            output_filename = f"{self.tmp_folder}/{self.lab_experiment.name}.tar.gz"
        else:
            output_filename = f"{self.target_folder}/{self.lab_experiment.name}.tar.gz"

        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(self.lab_experiment.path, arcname=os.path.basename(self.lab_experiment.path))

        if self.tmp_folder:
            shutil.move(output_filename, f"{self.target_folder}/{self.lab_experiment.name}.tar.gz")
