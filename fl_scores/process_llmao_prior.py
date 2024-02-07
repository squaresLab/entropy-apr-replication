import os
import json
from itertools import chain
import torch.utils.checkpoint
import torch
from llmao.transformer import VoltronTransformerPretrained, TokenizeMask


def load_model(pretrain_type):
    num_layer = 2
    target_dim = 512
    num_head = 8
    if pretrain_type == "16B":
        target_dim = 1024
        dim_model = 6144
        num_head = 16
    elif pretrain_type == "6B":
        dim_model = 4096
    elif pretrain_type == "350M":
        dim_model = 1024
    model = VoltronTransformerPretrained(
        num_layer=num_layer,
        dim_model=dim_model,
        num_head=num_head,
        target_dim=target_dim,
    )
    model.load_state_dict(
        torch.load(f"llmao/model_checkpoints/defects4j_{pretrain_type}"), strict=False
    )
    model.eval()

    return model


def llmao_prediction(model, tokenize_mask, filtered_code):
    code_lines = "".join(filtered_code)
    try:
        input, mask, input_size, decoded_input = tokenize_mask.generate_token_mask(
            code_lines
        )
    except:
        return {}
    input = input[None, :]
    mask = mask[None, :]
    predictions = model(input, mask)
    probabilities = torch.flatten(torch.sigmoid(predictions))
    real_indices = torch.flatten(mask == 1)
    probabilities = probabilities[real_indices].tolist()
    decoded_input_list = decoded_input.split("\n")
    decoded_input = [line.lstrip("\t") for line in decoded_input_list]
    decoded_input = "\n".join(decoded_input)
    probabilities = probabilities[: input_size + 1]
    most_sus = list(map(lambda x: 1 if x > 0 else 0, probabilities))
    result_list = []
    for i, _ in enumerate(most_sus):
        result_list.append(
            {"code": filtered_code[i - 1], "score": round(probabilities[i], 5)}
        )

    ## sort top scores
    result_list = sorted(result_list, key=lambda d: d["score"], reverse=True)
    #########
    return result_list


def use_prior_technique(model, tokenize_mask, code_lines, sbfl_list):
    result_dict = {}
    llmao_list = llmao_prediction(model, tokenize_mask, code_lines)
    combined_list = []
    for line in llmao_list:
        llmao_code = line["code"]
        llmao_score = float(line["score"])

        for line in sbfl_list:
            sbfl_line_num = line["line"]
            sbfl_score = float(line["score"])
            sbfl_code = line["code"]

            if sbfl_code == llmao_code:
                combined_list.append(
                    {
                        "line": sbfl_line_num,
                        "code": llmao_code,
                        "score": round((llmao_score + sbfl_score) / 2, 5),
                    }
                )
                break
    combined_list = sorted(combined_list, key=lambda d: d["score"], reverse=True)
    for res in combined_list:
        result_dict[res["line"]] = res["score"]
    return result_dict


def llmao_gen(pretrain_type, output_dir):
    model = load_model(pretrain_type)
    tokenize_mask = TokenizeMask(pretrain_type)
    current_path = os.getcwd()
    priorfl_path = f"{current_path}/score_transferfl"
    for subdir, _, files in os.walk(priorfl_path):
        for file in files:
            file_path = os.path.join(subdir, file)
            bug_num = subdir.split("/")[-1]
            d4j_proj = subdir.split("/")[-2]
            if not os.path.exists(f"{output_dir}{d4j_proj}"):
                os.mkdir(f"{output_dir}{d4j_proj}")
            if not os.path.exists(f"{output_dir}{d4j_proj}/{bug_num}"):
                os.mkdir(f"{output_dir}{d4j_proj}/{bug_num}")
            # else:
            #     continue
            sbfl_list = []
            code_lines = []
            if "sus.json" in file_path:
                with open(file_path.replace("sus", "metadata")) as json_file:
                    meta_json = json.load(json_file)
                    code_path = f"buggycode_artifact/{d4j_proj}/{bug_num}/b{bug_num}.java"
                    buglines = meta_json["bug_line_number"]
                    with open(code_path, "r") as jcode:
                        code = jcode.readlines()
                with open(file_path) as json_file:
                    sus_json = json.load(json_file)
                sus_json = {
                    k: v
                    for k, v in sorted(
                        sus_json.items(), key=lambda item: item[1], reverse=True
                    )
                }
                counter = 0
                bug_line = buglines[0]
                print(bug_line)
                bugcode_line = code[int(bug_line) - 1]
                # sbfl_list.append(
                #     {"line": bug_line, "code": bugcode_line, "score": "1"}
                # )
                for line_num, prediction in sus_json.items():
                    if int(line_num) > len(code):
                        continue
                    sus_line = code[int(line_num) - 1]
                    sbfl_list.append(
                        {"line": line_num, "code": sus_line, "score": prediction}
                    )
                    code_lines.append(sus_line)
                    counter += 1
                    if counter > 5:
                        break

                result_dict = use_prior_technique(
                    model, tokenize_mask, code_lines, sbfl_list
                )

                test_dict = {k: v for k, v in result_dict.items() if str(k) in sus_json}
                if test_dict:
                    result_dict = test_dict
                print(
                    f"Writing {d4j_proj} {bug_num} to {output_dir}{d4j_proj}/{bug_num}/sus.json"
                )
                write_file = f"{output_dir}{d4j_proj}/{bug_num}/sus.json"
                meta_file = f"{output_dir}{d4j_proj}/{bug_num}/metadata.json"
                with open(os.path.join(subdir, write_file), "w") as fp:
                    json.dump(result_dict, fp)
                with open(os.path.join(subdir, meta_file), "w") as fp:
                    json.dump(meta_json, fp)


if __name__ == "__main__":
    current_path = os.getcwd()
    output_dir = f"{current_path}/fl_scores/score_llmao/"
    llmao_gen("6B", output_dir)
