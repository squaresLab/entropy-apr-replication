import os
import subprocess
from colorama import Fore, Style


if __name__ == "__main__":
    current_path = os.getcwd()
    tbar_directory = f"{current_path}/TBar"
    patch_directory = f"{tbar_directory}/Results/NormalFL/TBar"
    output_fixed = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/FixedBugs"
    output_partial = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/PartiallyFixedBugs"
    output_unfix = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/UnfixedBugs"

    for subdir, _, files in os.walk(patch_directory):
        for file in files:
            proj_bug = subdir.split("/")[-1]
            proj_bug = proj_bug.replace("-P", "").replace("_P", "").replace("----", "").replace("---", "")
            project = proj_bug.split("_")[0]
            bug = proj_bug.split("_")[1]

            print(f"{Fore.GREEN}{Style.BRIGHT}{proj_bug}{Style.RESET_ALL}")

            if (
                os.path.exists(f"{output_fixed}/{proj_bug}")
                or os.path.exists(f"{output_partial}/{proj_bug}")
                or os.path.exists(f"{output_unfix}/{proj_bug}")
            ):
                print(f"{Fore.RED}{Style.BRIGHT}Already processed {proj_bug}{Style.RESET_ALL}")
                continue

            checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/SuspiciousCodePositionsEntropy -faultLocStrategy normal -failedTests /home/TBar/FailedTestCases"'
            print(checkout_command)
            try:
                output = subprocess.check_output(
                    checkout_command,
                    shell=True,
                    cwd=tbar_directory,
                ).decode()
            except:
                continue
