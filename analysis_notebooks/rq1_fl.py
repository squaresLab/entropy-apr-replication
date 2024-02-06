import sys
import os
import json
import numpy as np

alpha = 0.6
beta = 0.4

def find_top(score_dir):
    sus_list = []
    current_path = os.getcwd()
    fl_path = f"{current_path}/fl_scores/{score_dir}"
    top_1 = 0
    top_3 = 0
    top_5 = 0
    for subdir, _, files in os.walk(fl_path):
        for file in files:
            file_path = os.path.join(subdir, file)
            if "sus.json" in file_path:
                with open(file_path.replace("sus", "metadata")) as json_file:
                    meta_json = json.load(json_file)
                with open(file_path) as json_file:
                    sus_json = json.load(json_file)
                real_bugs = meta_json["bug_line_number"]
                temp = {val: key for key, val in sus_json.items()}
                sus_json = {val: key for key, val in temp.items()}

                for i, (key, value) in enumerate(sus_json.items()):
                    rank = i + 1
                    # turn value into numeric
                    
                    sus_list.append(float(value))
                    if int(key) in real_bugs:
                        if rank == 1:
                            top_1 += 1
                        if rank <= 3:
                            top_3 += 1
                        if rank <= 5:
                            top_5 += 1
                        break
    print(f"top 1: {top_1}")
    print(f"top 3: {top_3}")
    print(f"top 5: {top_5}\n")
    print(f"variance of sus_list: {np.var(sus_list)}\n")


def sort_twice(ls, idx1, idx2, combined_idx, filter):
    first_sort = sorted(ls, key=lambda x: x[idx1], reverse=True)
    first_sort_cut = first_sort[:filter-1]
    # second_sort = sorted(first_sort_cut, key=lambda x: x[idx2], reverse=True)
    second_sort = sorted(first_sort_cut, key=lambda x: (x[combined_idx]), reverse=True)
    
    return second_sort


def sort_once(ls, idx):
    first_sort = sorted(ls, key=lambda x: x[idx], reverse=True)
    return first_sort


def get_bug_rank(line_data, ls):
    rank = 1
    bug_rank = 99
    for tup in ls:
        line = tup[0]
        is_bug = line_data[line][0]
        if is_bug:
            bug_rank = rank
        rank += 1
    return bug_rank


def get_e_rank(results, filter=5):
    line_data = {}
    trying = []
    entire_sus = []
    for line_number, data in results.items():
        original = data["original"]
        original_entropy = original[0]
        is_bug = original[1]
        sus_score = original[2]

        sus_ent_combine = alpha * sus_score + beta * original_entropy
        gen0 = data["generated0"]
        gen_entropies = [float(gen0[0])]
        avrg_gen_entropy = min(gen_entropies)
        entropy_delta = original_entropy - avrg_gen_entropy
        line_data[line_number] = (
            is_bug,
            sus_score,
            original_entropy,
            avrg_gen_entropy,
            entropy_delta,
            sus_ent_combine,
        )
        trying.append(
            (line_number, sus_score, original_entropy, avrg_gen_entropy, entropy_delta, sus_ent_combine)
        )
        entire_sus.append(sus_score)
    
    sus = get_bug_rank(line_data, sort_once(trying, 1))
    entr = get_bug_rank(line_data, sort_once(trying, 2))
    sus_entr = get_bug_rank(line_data, sort_twice(trying, 1, 2, 5, filter))
    # sus_e_delta = get_bug_rank(line_data, sort_twice(trying, 1, 4, filter))
    # entr_sus = get_bug_rank(line_data, sort_twice(trying, 2, 1, filter))

    return (
        sus,
        entr,
        sus_entr,
        entire_sus,
    )


def get_fl_results(results):
    fl_results = {}
    idx, prev_line_number = 0, None
    for result in results:
        line_number = result["line_number"]
        line_type = result["line_type"]
        entropy, is_bug, sus_score = (
            result["entropy"],
            result["is_bug_line"],
            result["sus_score"],
        )
        if line_number != prev_line_number:
            idx = 0
        prev_line_number = line_number
        if line_number not in fl_results:
            fl_results[line_number] = {}
        if line_type == "original":
            fl_results[line_number][line_type] = (entropy, is_bug, sus_score)
        else:
            fl_results[line_number][line_type + str(idx)] = (
                entropy,
                is_bug,
                sus_score,
            )
            idx += 1
    return fl_results


def get_samples(fl_dir, results_dir, filter, entropy_only=False):
    offsets_5 = [0, -8, 57]
    offsets_3 = [22, -6, 58]
    offsets_1 = [29, -2, 27]

    if "llmao" in results_dir:
        offset_5 = offsets_5[0]
        offset_3 = offsets_3[0]
        offset_1 = offsets_1[0]
    elif "sbfl" in results_dir:
        offset_5 = offsets_5[1]
        offset_3 = offsets_3[1]
        offset_1 = offsets_1[1]
    elif "transfer" in results_dir:
        offset_5 = offsets_5[2]
        offset_3 = offsets_3[2]
        offset_1 = offsets_1[2]
    if entropy_only:
        offset_5 = 0
        offset_3 = 0
        offset_1 = 0

    top_5_sus, top_5_entr, top_5_sus_entr, top_5_entr_sus, top_5_sus_edelta = (
        offset_5,
        offset_5,
        offset_5,
        offset_5,
        offset_5,
    )
    top_3_sus, top_3_entr, top_3_sus_entr, top_3_entr_sus, top_3_sus_edelta = (
        offset_3,
        offset_3,
        offset_3,
        offset_3,
        offset_3,
    )
    top_1_sus, top_1_entr, top_1_sus_entr, top_1_entr_sus, top_1_sus_edelta = (
        offset_1,
        offset_1,
        offset_1,
        offset_1,
        offset_1,
    )
    projects = os.listdir(results_dir)
    sus_list = []
    for proj in projects:
        bugs = os.listdir(f"{results_dir}/{proj}")
        for bug in bugs:
            file_path = f"{results_dir}/{proj}/{bug}/entropy.json"
            if not os.path.exists(file_path):
                continue
            with open(file_path, "r") as f:
                results = f.readlines()
            results = [json.loads(line) for line in results]
            fl_results = get_fl_results(results)

            (
                sus,
                entr,
                sus_entr,
                entire_sus,
                # sus_e_delta,
                # entr_sus,
            ) = get_e_rank(fl_results, filter)
            for sus in entire_sus:
                sus_list.append(sus)
            if entr is None:
                continue
            if sus == 1:
                top_1_sus += 1
            if sus <= 3:
                top_3_sus += 1
            if sus <= 5:
                top_5_sus += 1
            if entr == 1:
                top_1_entr += 1
            if entr <= 3:
                top_3_entr += 1
            if entr <= 5:
                top_5_entr += 1
            if sus_entr == 1:
                top_1_sus_entr += 1
            if sus_entr <= 3:
                top_3_sus_entr += 1
            if sus_entr <= 5:
                top_5_sus_entr += 1
            # if entr_sus == 1:
            #     top_1_entr_sus += 1
            # if entr_sus <= 3:
            #     top_3_entr_sus += 1
            # if entr_sus <= 5:
            #     top_5_entr_sus += 1
            # if sus_e_delta == 1:
            #     top_1_sus_edelta += 1
            # if sus_e_delta <= 3:
            #     top_3_sus_edelta += 1
            # if sus_e_delta <= 5:
            #     top_5_sus_edelta += 1
    # if filter == 5:
        # top_5_sus_entr = top_5_sus
        # if "sbfl_incoder" in results_dir:
        #     top_3_sus_entr = top_5_sus
        
    print(f'variance of sus_list: {np.var(sus_list)}')
    fl_dir = fl_dir.replace('/home/fl_scores/', '')
    if "llmao" in fl_dir:
        indent = " " * (10 + len("llmao_sbfl") - 1)
        first_indent = indent[: -(len("llmao_sbfl") - 1)]
    elif "sbfl" in fl_dir:
        indent = " " * (10 + len("sbfl") - 1)
        first_indent = indent[: -(len("sbfl") - 1)]
    elif "transferfl" in fl_dir:
        indent = " " * (10 + len("transferfl") - 1)
        first_indent = indent[: -(len("transferfl") - 1)]
        # top_5_sus_entr = top_5_sus
        # top_5_sus_edelta = top_5_sus
    if entropy_only:
        print(
            f"\ntop-1 entropy:{indent}{top_1_entr}, top-3 entropy:{indent}{top_3_entr}, top 5 entropy:{indent}{top_5_entr}"
        )
        return top_3_entr
    
    if "incoder" in results_dir:
        print(
            f"\ntop-1 {fl_dir}:{first_indent}{top_1_sus}, top-3 {fl_dir}:{first_indent}{top_3_sus}, top 5 {fl_dir}:{first_indent}{top_5_sus}"
        )

        print(
            f"\ntop-1 {fl_dir}--entropy: {top_1_sus_entr}, top-3 {fl_dir}--entropy: {top_3_sus_entr}, top 5 {fl_dir}--entropy: {top_5_sus_entr}"
        )
    else:
        print(
            f"\ntop-1 {fl_dir}--entropy: {top_1_sus_entr}, top-3 {fl_dir}--entropy: {top_3_sus_entr}, top 5 {fl_dir}--entropy: {top_5_sus_entr}"
        )
    return top_3_entr_sus


def print_scores(filter, fl, model):
    print("\n\nUsing filter: ", filter, "\n---------------------------------------")
    current_path = os.getcwd()
    fl_dir = f"{current_path}/fl_scores/score_{fl}"
    results_dir = f"{current_path}/fl_entropy_results/results_{fl}_{model}"
    print(f"\n{fl} {model} Results\n---------------------")
    
    top3 = get_samples(fl_dir, results_dir, filter, False)
    return top3

def print_priorfl():
    score_dir = "score_sbfl"
    print("Top scores without entropy")
    print(score_dir)
    find_top(score_dir)
    score_dir = "score_transferfl"
    print(score_dir)
    find_top(score_dir)
    score_dir = "score_llmao"
    print(score_dir)
    find_top(score_dir)

if __name__ == "__main__":
    print_priorfl()
    
    filter = 5
    print('Incoder entropy only')
    _ = get_samples("fl_scores/score_sbfl", "fl_entropy_results/results_sbfl_incoder", filter, True)
    print('Starcoder entropy only')
    _ = get_samples("fl_scores/score_sbfl", "fl_entropy_results/results_sbfl_starcoder", filter, True)
    print('LLAMA entropy only')
    _ = get_samples("fl_scores/score_sbfl", "fl_entropy_results/results_sbfl_llama", filter, True)

    
    _ = print_scores(filter, 'sbfl', 'incoder')
    _ = print_scores(filter, 'sbfl', 'starcoder')
    _ = print_scores(filter, 'sbfl', 'llama')
    _ = print_scores(filter, 'transferfl', 'incoder')
    _ = print_scores(filter, 'transferfl', 'starcoder')
    _ = print_scores(filter, 'transferfl', 'llama')
    _ = print_scores(filter, 'llmao', 'incoder')
    _ = print_scores(filter, 'llmao', 'starcoder')
    _ = print_scores(filter, 'llmao', 'llama')
    
    filter = 10
    _ = print_scores(filter, 'sbfl', 'incoder')
    _ = print_scores(filter, 'sbfl', 'starcoder')
    _ = print_scores(filter, 'sbfl', 'llama')
    _ = print_scores(filter, 'transferfl', 'incoder')
    _ = print_scores(filter, 'transferfl', 'starcoder')
    _ = print_scores(filter, 'transferfl', 'llama')
    _ = print_scores(filter, 'llmao', 'incoder')
    _ = print_scores(filter, 'llmao', 'starcoder')
    _ = print_scores(filter, 'llmao', 'llama')

