import os
import json


def find_metadata(proj, bug):
    found = False
    current_path = os.getcwd()
    for subdir, dirs, files in os.walk(f"{current_path}/buggycode_artifact"):
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


def transfer(output_dir):
    # read all the files in the transferfl folder
    i = 0
    nomatch_counter = 0
    total_counter = 0
    current_path = os.getcwd()
    transfer_path = f"{current_path}/fl_scores/transferfl_unprocessed"
    for subdir, _, files in os.walk(transfer_path):
        for file in files:
            result_dict = {}
            file_path = os.path.join(subdir, file)
            subdir_split = subdir.split("/")[-1].split("_")
            d4j_proj = subdir_split[0]
            bug_num = subdir_split[1]

            class_path, metadata, found = find_metadata(d4j_proj, bug_num)

            if not found:
                nomatch_counter += 1
                continue

            f = open(file_path, "r")
            lines = f.readlines()
            for line in lines:
                line_split = line.split("@")
                sus_score = line_split[1].split(" ")
                file_name = line_split[0]
                line_num = sus_score[0]
                prediction = sus_score[1].replace("\n", "")
                result_dict[line_num] = prediction
                if file_name == class_path:
                    # add to result dict if file matches
                    result_dict[line_num] = prediction

            try:
                os.mkdir(f"{output_dir}{d4j_proj}")
            except:
                pass
            try:
                os.mkdir(f"{output_dir}{d4j_proj}/{bug_num}")
            except:
                pass

            write_file = f"{output_dir}{d4j_proj}/{bug_num}/sus.json"
            meta_file = f"{output_dir}{d4j_proj}/{bug_num}/metadata.json"
            with open(os.path.join(subdir, write_file), "w") as fp:
                json.dump(result_dict, fp)
            with open(os.path.join(subdir, meta_file), "w") as fp:
                json.dump(metadata, fp)


if __name__ == "__main__":
    current_path = os.getcwd()
    output_dir = f"{current_path}/fl_scores/score_transferfl/"
    transfer(output_dir)
