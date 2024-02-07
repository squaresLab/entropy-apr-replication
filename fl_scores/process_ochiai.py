import os
import json


def find_metadata(proj, bug):
    found = False
    current_path = os.getcwd()
    for subdir, _, files in os.walk(f"{current_path}/buggycode_artifact"):
        for file in files:
            file_path = os.path.join(subdir, file)
            bug_sbfl = subdir.split("/")[-1]
            proj_sbfl = subdir.split("/")[-2]
            if (
                proj_sbfl == proj
                and int(bug_sbfl) == int(bug)
                and "metadata.json" in file_path
            ):
                with open(file_path) as f:
                    data = json.load(f)
                    class_path = data["classpath"]
                    found = True
    if found:
        return class_path, data, True
    else:
        return None, None, False


def process(output_dir):
    counter = 0
    current_path = os.getcwd()
    ochiai_path = f"{current_path}/fl_scores/ochiai_unprocessed"
    entropy_path = f"{current_path}/fl_entropy_results/results_sbfl_incoder"
    tbar_path = f"{current_path}/TBar/SuspiciousCodePositionsEntropy"
    for subdir, _, files in os.walk(ochiai_path):
        for file in files:
            result_list = []
            file_path = os.path.join(subdir, file)
            subdir_split = subdir.split("/")
            d4j_proj = subdir_split[-2]
            bug_num = subdir_split[-1]

            class_path, _, _ = find_metadata(d4j_proj, bug_num)
            print(f"Processing {d4j_proj}_{bug_num}")
            entropy_file = f"{entropy_path}/{d4j_proj}/{bug_num}/entropy.json"
            if os.path.exists(entropy_file):
                f = open(entropy_file, "r")
                lines = f.readlines()
                for line in lines:
                    code_line = json.loads(line)
                    if code_line["line_type"] == "generated":
                        continue
                    line_number = code_line["line_number"]
                    output_line = class_path + "@" + str(line_number)
                    if len(result_list) < 10:
                        result_list.append(output_line)
            else:
                f = open(file_path, "r")
                lines = f.readlines()
                for line in lines:
                    if "name;suspiciousness_value" in line:
                        continue
                    line_rank = line.split(";")[0]
                    function_name = line_rank.split(":")[0]
                    line_number = line_rank.split(":")[1]
                    file_name = function_name.split("#")[0].replace("$", ".")
                    output_line = file_name + "@" + line_number
                    if len(result_list) < 10:
                        result_list.append(output_line)

            tbar_file = f"{tbar_path}/{d4j_proj}_{bug_num}/Ochiai.txt"

            if not os.path.exists(f"{tbar_path}/{d4j_proj}_{bug_num}"):
                os.mkdir(f"{tbar_path}/{d4j_proj}_{bug_num}")
            with open(tbar_file, "w") as f:
                for line in result_list:
                    f.write("%s\n" % line)

        #     counter += 1
        #     if counter > 2:
        #         break
        # if counter > 2:
        #         break


if __name__ == "__main__":
    current_path = os.getcwd()
    output_dir = f"{current_path}/fl_scores/score_sbfl/"
    process(output_dir)
