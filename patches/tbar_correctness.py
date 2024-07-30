import os
import pandas as pd


def find_buggy_file(proj_bug, match_counter):
    current_path = os.getcwd()
    tbar_bugs = f"{current_path}/original_tbar_patches/PerfectFL/TBar/FixedBugs"
    artifact_file = ""
    delete_list = []
    add_list = []
    for subdir, _, files in os.walk(tbar_bugs):
        for file in files:
            file_path = os.path.join(subdir, file)
            artifact_proj_bug = subdir.split("/")[-1].replace("_", "")
            if artifact_proj_bug == proj_bug:
                match_counter += 1
                with open(file_path, "r") as f:
                    artifact_file = f.readlines()

                for line in artifact_file:
                    if line.startswith("-  "):
                        target_line = line.replace("-  ", "").replace("\n", "").strip()
                        delete_list.append(target_line)
                    elif line.startswith("+  "):
                        target_line = line.replace("+  ", "").replace("\n", "").strip()
                        add_list.append(target_line)
                break

    return delete_list, add_list, match_counter


if __name__ == "__main__":
    current_path = os.getcwd()
    patch_directory = "iter_patches"
    bug_list = []
    repos_directory = f"{current_path}/repos"
    results_directoy = f"{current_path}/patches/patches_entropy_iter"
    tbar_bugs = f"{current_path}/original_tbar_patches/PerfectFL/TBar/FixedBugs"

    pandas_output = []
    exact_match = 0
    total_counter = 0
    match_counter = 0
    for subdir, _, files in os.walk(tbar_bugs):
        for file in files:
            proj_bug = subdir.split("/")[-1]

            proj_bug = proj_bug.replace("_", "")

            file_path = os.path.join(subdir, file)
            if "plausible" in file_path:
                continue

            if proj_bug not in bug_list:
                bug_list.append(proj_bug)
            else:
                continue

            print(proj_bug)
            with open(file_path, "r") as f:
                patch_data = f.readlines()

            delete_list, add_list, match_counter = find_buggy_file(
                proj_bug, match_counter
            )

            if not delete_list and not add_list:
                # No plausible patch, only correct
                total_counter += 1
                print(subdir)
                continue

            diff_line_dict = {}
            correct_delete_list = []
            correct_add_list = []
            for i, patch_line in enumerate(patch_data):
                if patch_line.startswith(" - "):
                    correct_delete_list.append(
                        patch_line.replace(" - ", "").replace("\n", "")
                    )
                elif patch_line.startswith(" + "):
                    correct_add_list.append(
                        patch_line.replace(" + ", "").replace("\n", "")
                    )

            diff_line_dict["bugID"] = proj_bug
            diff_line_dict["Tbar_delete"] = delete_list
            diff_line_dict["Tbar_add"] = add_list
            diff_line_dict["Correct_delete"] = correct_delete_list
            diff_line_dict["Correct_add"] = correct_add_list
            print(diff_line_dict)
            pandas_output.append(diff_line_dict)

            delete_list = [delete.replace(" ", "") for delete in delete_list]
            add_list = [add.replace(" ", "") for add in add_list]
            correct_delete_list = [
                delete.replace(" ", "") for delete in correct_delete_list
            ]
            correct_add_list = [add.replace(" ", "") for add in correct_add_list]

            if any(delete in correct_delete_list for delete in delete_list) and any(
                add in correct_add_list for add in add_list
            ):
                exact_match += 1
            total_counter += 1
    print(f"Match Counter: {match_counter}")
    df = pd.DataFrame(pandas_output)
    df.to_csv("tbar_correctness.csv", index=False)
    print(f"Exact Match: {exact_match}, Total Counter: {total_counter}")
