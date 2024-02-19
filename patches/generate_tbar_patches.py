import os
import subprocess
from colorama import Fore, Style
import time
import csv

if __name__ == "__main__":
    store_patches = False
    current_path = os.getcwd()
    tbar_directory = f"{current_path}/TBar"
    patch_directory = f"{tbar_directory}/Results/PerfectFL/TBar"
    output_fixed = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/FixedBugs"
    output_partial = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/PartiallyFixedBugs"
    output_unfix = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/UnfixedBugs"

    for subdir, _, files in os.walk(patch_directory):
        for file in files:
            proj_bug = subdir.split("/")[-1]
            proj_bug = (
                proj_bug.replace("-P", "")
                .replace("_P", "")
                .replace("----", "")
                .replace("---", "")
            )
            project = proj_bug.split("_")[0]
            bug = proj_bug.split("_")[1]

            print(f"{Fore.GREEN}{Style.BRIGHT}{proj_bug}{Style.RESET_ALL}")

            if (
                os.path.exists(f"{output_fixed}/{proj_bug}")
                or os.path.exists(f"{output_partial}/{proj_bug}")
                or os.path.exists(f"{output_unfix}/{proj_bug}")
            ):
                print(
                    f"{Fore.RED}{Style.BRIGHT}Already processed {proj_bug}{Style.RESET_ALL}"
                )
                continue

            start = time.time()

            if store_patches:
                checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -compileOnly -recordAllPatches -storePatchJson" '
            else:
                checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -patchRankFile /home/TBar/entropy_patch_rank.json" '

            print(checkout_command)
            try:
                output = subprocess.check_output(
                    checkout_command,
                    shell=True,
                    cwd=tbar_directory,
                ).decode()
            except:
                continue

            end = time.time()
            time_spent = end - start

            fields = [proj_bug, time_spent]
            with open(f"{current_path}/patches/time_spent_entropy.csv", "a") as f:
                writer = csv.writer(f)
                writer.writerow(fields)
            print(f"{Fore.GREEN}{Style.BRIGHT}Time spent to fix bug: {time_spent}{Style.RESET_ALL}")
