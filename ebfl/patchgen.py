from sample import *
from sus_line import *
from infiller import *
import os
import time
from colorama import Fore, Style
import math
import argparse
import subprocess

ap = argparse.ArgumentParser()
ap.add_argument("model_name")
args = ap.parse_args()
model_name = args.model_name

if model_name == "incoder":
    model_infiller = "facebook/incoder-6B"
elif model_name == "starcoder":
    model_infiller = "bigcode/starcoder"
elif model_name == "llama":
    model_infiller = "codellama/CodeLlama-13b-hf"

infiller = Infiller(model_infiller)
tokenizer = infiller.load_tokenizer()
start = time.time()
infiller.load_model()
end = time.time()
print(
    f"{Fore.BLUE}{Style.BRIGHT}Time to load model: {end - start} sec{Style.RESET_ALL}"
)
print(f"{Fore.BLUE}{Style.BRIGHT}Starting entropy calculation...{Style.RESET_ALL}")


def get_samples(fl_dir, results_dir):
    samples = []
    projects = os.listdir(fl_dir)
    for proj in projects:
        bugs = os.listdir(f"{fl_dir}/{proj}")
        for bug in bugs:
            samples.append(Sample(proj, bug, fl_dir, results_dir))
    return samples


def get_first_line(gen_ids):
    eom = tokenizer.encode("<|endofmask|>")[1]
    if "incoder" in model_name:
        newline = tokenizer.encode("\n")[1]
        two_newlines = tokenizer.encode("\n\n")[1]
    else:
        newline = tokenizer.encode("\n")[0]
        two_newlines = tokenizer.encode("\n\n")[0]
    if eom in gen_ids:
        gen_ids = gen_ids[: gen_ids.index(eom)]
    if len(gen_ids) == 1:
        return gen_ids
    if newline in gen_ids:
        gen_ids = gen_ids[: gen_ids.index(newline)]
    if two_newlines in gen_ids:
        gen_ids = gen_ids[: gen_ids.index(two_newlines)]
    return gen_ids


def trim_output(output, gen_prompt_toks):
    input_len = len(gen_prompt_toks)
    output_ids = output.flatten().tolist()
    assert output_ids[:input_len] == gen_prompt_toks
    gen_ids = output_ids[input_len:]
    gen_ids = get_first_line(gen_ids)
    gen_str = tokenizer.decode(gen_ids)
    try:
        assert "\n" not in gen_str
        return gen_ids, gen_str
    except:
        return gen_ids, gen_str


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
    subprocess.check_output(
        checkout_command,
        shell=True,
        cwd=repos_directory,
    ).decode()
    java_file = f"{repos_directory}/{project}/{file_path}"
    if not os.path.exists(java_file):
        java_file = java_file.split(".java")[0]
        java_file += ".java"
    try:
        with open(java_file, "r") as f:
            lines = f.readlines()
    except:
        return []
    return lines, java_file


def get_entropy():
    fl_dir = f"score_sbfl"
    repos_directory = "repos"
    results_dir = f"results_patchgen"
    if not os.path.exists(results_dir):
        os.mkdir(results_dir)
    samples = get_samples(fl_dir, results_dir)
    idx = 1

    for s in samples:
        print(
            f"Running for {Fore.BLUE}{s.proj} {s.id}{Style.RESET_ALL}...{idx}/{len(samples)}"
        )
        start = time.time()
        if not os.path.exists(f"{results_dir}/{s.proj}"):
            os.mkdir(f"{results_dir}/{s.proj}")
        if not os.path.exists(f"{results_dir}/{s.proj}/{s.id}"):
            os.mkdir(f"{results_dir}/{s.proj}/{s.id}")
        else:
            # don't remake if already exists
            continue
        data_f = open(f"{results_dir}/{s.proj}/{s.id}/entropy.json", "w")
        sus_lines = s.set_sus_lines()
        bug_line_list = s.bug_line
        sus_dic = s.set_sus()

        if "Chart" not in s.proj and "1" not in s.id:
            continue
        d4j_code, java_file = d4j_checkout(repos_directory, s.proj, s.id, s.classpath)

        for sl in bug_line_list:
            sus_score = sus_dic[sl.line_num]
            original_line = sl.get_line_code().replace("\n", "")
            prompt = sl.form_gen_prompt()
            gen_prompt_toks = tokenizer.encode(prompt)

            orig_line_entropy, orig_line_ids, per_tok_entropy = get_line_entropy(
                original_line, gen_prompt_toks
            )
            if math.isnan(orig_line_entropy):
                orig_line_entropy = "10"
            og_data = {
                "line_number": sl.line_num,
                "line_type": "original",
                "code": original_line,
                "entropy": orig_line_entropy,
                "is_bug_line": True,
                "sus_score": sus_score,
                "per_token_entropy": per_tok_entropy,
                "tokens": orig_line_ids,
            }
            data_f.write(json.dumps(og_data) + "\n")

            outputs = infiller.generate(gen_prompt_toks, num_return_sequences=5)
            for output in outputs["sequences"]:
                gen_ids, gen_str = trim_output(output, gen_prompt_toks)
                entropy_prompt, start_loc = form_entropy_prompt(
                    gen_prompt_toks, gen_ids
                )
                entropy, per_tok_entropy = infiller.entropy(
                    entropy_prompt, start_loc, len(gen_ids)
                )
                if math.isnan(entropy):
                    entropy = "10"
                gen_data = {
                    "line_number": sl.line_num,
                    "line_type": "generated",
                    "code": gen_str,
                    "entropy": entropy,
                    "is_bug_line": False,
                    "sus_score": sus_score,
                    "per_token_entropy": per_tok_entropy,
                    "tokens": gen_ids,
                }
                data_f.write(json.dumps(gen_data) + "\n")
        data_f.close()
        end = time.time()
        print(
            f"{Fore.BLUE}{Style.BRIGHT}Time to run for {s.proj} {s.id}: {end - start} sec{Style.RESET_ALL}"
        )
        print(f"{Fore.GREEN}{len(samples)-idx} remaining {Style.RESET_ALL}")
        idx += 1

    print(f"{Fore.GREEN}{Style.BRIGHT}Done!{Style.RESET_ALL}")


if __name__ == "__main__":
    get_entropy()
