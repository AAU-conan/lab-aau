import shutil
import tarfile

class CompressStep:
    def __init__(self, lab_experiment, target_folder, tmp_folder = None):
        self.lab_experiment = lab_experiment
        self.target_folder = target_folder
        self.tmp_folder = tmp_folder

    def step(self):
        if self.tmp_folder:
            output_filename = f"{self.tmp_folder}/{self.lab_experiment.name()}.tar.gz"
        else:
            output_filename = f"{self.target_folder}/{self.lab_experiment.name()}.tar.gz"

        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(self.lab_experiment.path)

        if self.tmp_folder:
            shutil.move(output_filename, self.target_folder)
