import os
import time
import sys
from colorama import Fore, Style


sys.path.append("../ebfl")
from infiller import *

model_infiller = "facebook/incoder-6B"
infiller = Infiller(model_infiller)
tokenizer = infiller.load_tokenizer()
start = time.time()
infiller.load_model()
end = time.time()
print(
    f"{Fore.BLUE}{Style.BRIGHT}Time to load model: {end - start} sec{Style.RESET_ALL}"
)
print(f"{Fore.BLUE}{Style.BRIGHT}Starting entropy calculation...{Style.RESET_ALL}")


def form_gen_prompt(code_before, code_after):
    prompt = code_before + "<|mask:0|>" + "\n" + code_after + "<|mask:1|><|mask:0|>"
    return prompt


def get_first_line(gen_ids):
    eom = tokenizer.encode("<|endofmask|>")[1]
    newline = tokenizer.encode("\n")[1]
    two_newlines = tokenizer.encode("\n\n")[1]
    if eom in gen_ids:
        gen_ids = gen_ids[: gen_ids.index(eom)]
    if len(gen_ids) == 1:
        return gen_ids
    if newline in gen_ids:
        gen_ids = gen_ids[: gen_ids.index(newline)]
    if two_newlines in gen_ids:
        gen_ids = gen_ids[: gen_ids.index(two_newlines)]
    return gen_ids


def form_entropy_prompt(gen_prompt_toks, gen_ids):
    eom = tokenizer.encode("<|endofmask|>")[1]
    start_loc = len(gen_prompt_toks)
    entropy_prompt = gen_prompt_toks + gen_ids + [eom]
    return entropy_prompt, start_loc


def get_line_entropy(line, gen_prompt_toks):
    line_ids = tokenizer.encode(line, add_special_tokens=False)
    if len(line_ids) == 0:
        line_ids = tokenizer.encode("\n", add_special_tokens=False)
    entropy_prompt, start_loc = form_entropy_prompt(gen_prompt_toks, line_ids)
    line_entropy, per_tok_entropy = infiller.entropy(
        entropy_prompt, start_loc, len(line_ids)
    )
    return line_entropy, line_ids, per_tok_entropy


def find_buggy_file(proj_bug):
    current_path = os.getcwd()
    buggycode_artifact = f"{current_path}/../buggycode_artifact"
    artifact_file = ""
    for subdir, _, files in os.walk(buggycode_artifact):
        for file in files:
            file_path = os.path.join(subdir, file)
            if ".java" not in file_path:
                continue
            bug_id = subdir.split("/")[-1]
            project = subdir.split("/")[-2]
            artifact_proj_bug = str(project) + str(bug_id)
            if artifact_proj_bug == proj_bug:
                # open file
                with open(file_path, "r") as f:
                    artifact_file = f.readlines()
                    break
    return artifact_file


if __name__ == "__main__":
    current_path = os.getcwd()
    patch_directory = "iter_patches"
    repos_directory = f"{current_path}/repos"
    results_directoy = f"{current_path}/patches/patches_entropy_iter"

    plausible_entropy_dict = {}
    correct_entropy_dict = {}

    better_rank_counter = 0
    total_counter = 0
    for subdir, _, files in os.walk(patch_directory):
        for file in files:
            proj_bug = subdir.split("/")[-1]

            file_path = os.path.join(subdir, file)

            correct = True
            if "plausible" in file_path:
                correct = False
                print(proj_bug, " plausible")
            else:
                print(proj_bug, " correct")

            with open(file_path, "r") as f:
                patch_data = f.readlines()

            original_d4j_lines = find_buggy_file(proj_bug)
            if original_d4j_lines == "":
                if correct:
                    better_rank_counter += 1
                    total_counter += 1
                continue

            diff_line_dict = {}

            for i, patch_line in enumerate(patch_data):

                if patch_line.startswith(" - "):
                    del_line = patch_line.replace(" - ", "").replace("\n", "")
                elif patch_line.startswith(" + "):
                    replace_line = patch_line.replace(" + ", "").replace("\n", "")

                patch_line = patch_line.lower()
                if patch_line.startswith("buggy location"):
                    patch_line = patch_line.split(",")[0]
                    diff_line = patch_line.replace("buggy location: ", "").replace(
                        "\n", ""
                    )
                    diff_line = int(diff_line) - 1

            patched_d4j_lines = original_d4j_lines
            patched_d4j_lines[diff_line] = replace_line

            maximum_window = 100

            code_before = patched_d4j_lines[:diff_line]
            code_after = patched_d4j_lines[diff_line + 1 :]

            if diff_line > maximum_window:
                code_before = code_before[-maximum_window:]
            if (len(original_d4j_lines) - diff_line) > maximum_window:
                code_after = code_after[:maximum_window]

            code_before = "".join(code_before)
            code_after = "".join(code_after)

            prompt = form_gen_prompt(code_before, code_after)
            gen_prompt_toks = tokenizer.encode(prompt)
            entropy = 0
            original_entropy = 0
            try:
                entropy, _, _ = get_line_entropy(replace_line, gen_prompt_toks)
                original_entropy, _, _ = get_line_entropy(del_line, gen_prompt_toks)
            except:
                pass

            entropy_delta = abs(entropy - original_entropy)

            print(f"Entropy delta: {entropy_delta}")

            if correct:
                correct_entropy_dict[proj_bug] = entropy_delta
                total_counter += 1
            else:
                if proj_bug in correct_entropy_dict:
                    if entropy_delta <= correct_entropy_dict[proj_bug]:
                        better_rank_counter += 1

    print(f"Better rank counter: {better_rank_counter}, Total counter: {total_counter}")
