import os
import subprocess
from colorama import Fore, Style
import time
import csv

if __name__ == "__main__":
    store_patches = False
    use_ranked_patches = True
    if store_patches:
        use_ranked_patches = False
    current_path = os.getcwd()
    tbar_directory = f"{current_path}/TBar"
    patch_directory = f"{tbar_directory}/Results/PerfectFL/TBar/FixedBugs"
    output_fixed = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/FixedBugs"
    output_partial = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/PartiallyFixedBugs"
    output_unfix = f"{tbar_directory}/OUTPUT/PerfectFL/TBar/UnfixedBugs"

    patch_done = []
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

            if proj_bug in patch_done:
                continue
            # if "Lang_21" != proj_bug:
            #     continue
            patch_done.append(proj_bug)

            print(f"{Fore.GREEN}{Style.BRIGHT}Repairing {proj_bug}{Style.RESET_ALL}")

            if store_patches:
                checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -compileOnly -recordAllPatches -storePatchJson" '
            elif use_ranked_patches:
                time_file = "time_spent_entropy"
                checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -recordAllPatches -patchRankFile /home/TBar/entropy_patch_rank.json" '
            else:
                time_file = "time_spent_tbar"
                checkout_command = f'mvn exec:java -Dexec.mainClass=edu.lu.uni.serval.tbar.main.Main -Dexec.args="-bugDataPath /home/TBar/bugdata -bugId {proj_bug} -d4jHome /home/defects4j/ -faultLocFile /home/TBar/BugPositions.txt -faultLocStrategy perfect -failedTests /home/TBar/FailedTestCases -recordAllPatches" '

            start = time.time()
            try:
                output = subprocess.check_output(
                    checkout_command,
                    shell=True,
                    cwd=tbar_directory,
                    timeout=650,
                ).decode()
            except subprocess.TimeoutExpired as e:
                print(
                    f"{Fore.RED}{Style.BRIGHT}Timeout expired for {proj_bug}{Style.RESET_ALL}"
                )
                continue
            except subprocess.CalledProcessError as e:
                continue
            if not store_patches:
                time_spent = time.time() - start
                print(f"Time spent: {time_spent}")
                fields = [proj_bug, time_spent]
                with open(f"{current_path}/patches/{time_file}.csv", "a") as f:
                    writer = csv.writer(f)
                    writer.writerow(fields)
                print(
                    f"{Fore.GREEN}{Style.BRIGHT}Time spent to fix bug: {time_spent}{Style.RESET_ALL}"
                )
