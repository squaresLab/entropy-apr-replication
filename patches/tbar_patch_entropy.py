import os
import subprocess
from colorama import Fore, Style
import time
import sys
sys.path.append('ebfl')
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


def d4j_checkout(repos_directory, project, bug_id, file_path):
    checkout_command = (
        f"defects4j checkout -p {project} -v {bug_id}b -w {repos_directory}/{project}"
    )
    try:
        output = subprocess.check_output(
            checkout_command,
            shell=True,
            cwd=repos_directory,
        ).decode()        
    except:
        return []
    java_file = f"{repos_directory}/{project}/{file_path}"
    if not os.path.exists(java_file):
        java_file = java_file.split(".java")[0]
        java_file += ".java"
    try:
        with open(java_file, "r") as f:
            lines = f.readlines()
    except:
        return []
    return lines


def defects4j(repos_directory, file_path, project, bug_id, diff_line_dict):
    maximum_window = 100
    entropy_dict = {}
    original_entropy_dict = {}
    original_d4j_lines = d4j_checkout(repos_directory, project, bug_id, file_path)
    if not original_d4j_lines:
        return {}, {}
    file_length = len(original_d4j_lines)
    patched_d4j_lines = original_d4j_lines.copy()
    for diff_line, (line_change, change_type) in diff_line_dict.items():
        diff_line = diff_line - 1
        try:
            if change_type == "replace":
                patched_d4j_lines[diff_line] = line_change
            elif change_type == "add":
                patched_d4j_lines.insert(diff_line, line_change)
            elif change_type == "remove":
                patched_d4j_lines.pop(diff_line)
        except:
            pass

        code_before = patched_d4j_lines[:diff_line]
        code_after = patched_d4j_lines[diff_line + 1 :]

        if diff_line > maximum_window:
            code_before = code_before[-maximum_window:]
        if (file_length - diff_line) > maximum_window:
            code_after = code_after[:maximum_window]

        code_before = "".join(code_before)
        code_after = "".join(code_after)

        prompt = form_gen_prompt(code_before, code_after)
        gen_prompt_toks = tokenizer.encode(prompt)
        entropy = 0
        original_entropy = 0
        try:
            entropy, _, _ = get_line_entropy(
                patched_d4j_lines[diff_line], gen_prompt_toks
            )

            original_entropy, _, _ = get_line_entropy(
                original_d4j_lines[diff_line], gen_prompt_toks
            )
        except:
            pass

        if original_entropy:
            original_entropy_dict[diff_line] = original_entropy
        if entropy:
            entropy_dict[diff_line] = entropy

    return entropy_dict, original_entropy_dict


if __name__ == "__main__":
    current_path = os.getcwd()
    patch_directory = f"{current_path}/patches/original_tbar_patches"
    repos_directory = f"{current_path}/repos"
    results_directoy = f"{current_path}/patches/patches_entropy_TBar"
    for subdir, _, files in os.walk(patch_directory):
        for file in files:
            proj_bug = subdir.split("/")[-1]
            project = proj_bug.split("_")[0]
            bug = proj_bug.split("_")[1]
            print(f"{Fore.GREEN}{Style.BRIGHT}{proj_bug}{Style.RESET_ALL}")
            file_id = file.split("_")[1]
            file_path = os.path.join(subdir, file)
            correct = True
            correct_str = "correct"
            if "UnfixedBugs" in file_path or "PartiallyFixedBugs" in file_path:
                correct = False
                correct_str = "incorrect"

            if os.path.isfile(
                f"{results_directoy}/{project}/{bug}/{file_id}_{correct_str}.json"
            ):
                continue

            if not os.path.exists(f"{results_directoy}/{project}"):
                os.mkdir(f"{results_directoy}/{project}")
            if not os.path.exists(f"{results_directoy}/{project}/{bug}"):
                os.mkdir(f"{results_directoy}/{project}/{bug}")

            with open(file_path, "r") as f:
                patch_data = f.readlines()

            diff_line_dict = {}
            for i, patch_line in enumerate(patch_data):
                if patch_line.startswith("---"):
                    java_path = patch_line.replace("--- a/", "").replace("\n", "")
                elif patch_line.startswith("@@"):
                    initial_line = int(
                        patch_line.split(",")[0].replace("@@ -", "").replace("@@ +", "")
                    )
                    for j in range(i + 1, len(patch_data) - 1):
                        try:
                            patch_data_line = patch_data[j]
                        except:
                            continue
                        if patch_data_line.startswith("@@"):
                            break
                        if patch_data_line.startswith("+") and patch_data[
                            j + 1
                        ].startswith("-"):
                            diff_line_dict[initial_line + (j - i - 1)] = (
                                patch_data_line[1:],
                                "replace",
                            )
                        elif patch_data_line.startswith("+"):
                            diff_line_dict[initial_line + (j - i - 1)] = (
                                patch_data_line[1:],
                                "add",
                            )
                        elif patch_data_line.startswith("-") and not patch_data[
                            j - 1
                        ].startswith("+"):
                            diff_line_dict[initial_line + (j - i - 1)] = (
                                patch_data[j][1:],
                                "remove",
                            )

            entropy_dict, original_entropy_dict = defects4j(
                repos_directory, java_path, project, bug, diff_line_dict
            )
            if not entropy_dict:
                print(f"{Fore.RED}{Style.NORMAL}D4J checkout failed{Style.RESET_ALL}")
                continue
            metadata = {
                "project": project,
                "bug_id": int(bug),
                "file_path": file_path,
                "patched_entropy": entropy_dict,
                "original_entropy": original_entropy_dict,
                "correct": correct,
            }
            with open(
                f"{results_directoy}/{project}/{bug}/{file_id}_{correct_str}.json", "w"
            ) as f:
                json.dump(metadata, f)
            subprocess.check_output(
                f"chmod -R a+rw {results_directoy}/{project}/{bug}",
                shell=True,
                cwd=repos_directory,
            ).decode()
