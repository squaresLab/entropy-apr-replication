import os
import subprocess
from colorama import Fore, Style
import time
import csv
import argparse

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run_option", help="Options: store_patches, tbar or tbar_ranked")
    args = ap.parse_args()
    run_option = args.run_option

    current_path = os.getcwd()
    tbar_directory = f"{current_path}/TBar"
    patch_directory = f"{tbar_directory}/Results/PerfectFL/TBar/FixedBugs"
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

            if "tbar" in run_option:
                if run_option == "tbar_ranked":

                    time_file = "time_spent_entropy"
                    checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -recordAllPatches -patchRankFile /home/TBar/entropy_patch_rank.json" '
                elif run_option == "tbar":
                    time_file = "time_spent_tbar"
                    checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -recordAllPatches" '

                # read entire file as string
                with open(f"{current_path}/patches/{time_file}.csv", "r") as f:
                    data = f.read()
                    if f"{proj_bug}," in data:
                        print(
                            f"{Fore.RED}{Style.NORMAL}Already processed {proj_bug}{Style.RESET_ALL}"
                        )
                        continue
            else:
                checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -compileOnly -recordAllPatches -storePatchJson" '

            start = time.time()
            try:
                print(
                    f"{Fore.GREEN}{Style.NORMAL}Running option: {run_option} for {proj_bug}{Style.RESET_ALL}"
                )
                output = subprocess.check_output(
                    checkout_command,
                    shell=True,
                    cwd=tbar_directory,
                    timeout=650,
                ).decode()
            except subprocess.TimeoutExpired as e:
                print(
                    f"{Fore.RED}{Style.NORMAL}Timeout expired for {proj_bug}{Style.RESET_ALL}"
                )
            except subprocess.CalledProcessError as e:
                continue
            if "tbar" in run_option:
                time_spent = time.time() - start
                fields = [proj_bug, time_spent]
                with open(f"{current_path}/patches/{time_file}.csv", "a") as f:
                    writer = csv.writer(f)
                    writer.writerow(fields)
                print(
                    f"{Fore.CYAN}{Style.NORMAL}Time spent to fix bug: {time_spent}{Style.RESET_ALL}"
                )
