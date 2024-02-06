import json
try:
    from sus_line import *
except:
    from ebfl.sus_line import *
import os


class Sample:
    def __init__(self, proj, bug_id, fl_dir, results_dir):
        self.proj = proj
        self.id = bug_id
        self.fl_directory = fl_dir
        self.results_directory = results_dir
        self.bug_line, self.classpath, self.num_lines = self.set_metadata()
        self.sus_lines = self.set_sus_lines()
        self.results = self.set_results()
        self.fl_results = self.get_fl_results()

    def meta_path(self):
        return f"{self.fl_directory}/{self.proj}/{self.id}/metadata.json"

    def fl_path(self):
        return f"{self.fl_directory}/{self.proj}/{self.id}/sus.json"

    def code_path(self):
        return f"buggycode_artifact/{self.proj}/{self.id}/b{self.id}.java"

    def get_results_path(self):
        if not os.path.exists(f"{self.results_directory}/{self.proj}/{self.id}"):
            os.mkdir(f"{self.results_directory}/{self.proj}/{self.id}")
        return f"{self.results_directory}/{self.proj}/{self.id}/entropy.json"

    def get_results(self):
        results = []
        try:
            with open(self.get_results_path(), "r") as f:
                for line in f:
                    results.append(json.loads(line))
        except:
            return results
        return results

    def set_results(self):
        results = self.get_results()

    def get_fl_results(self):
        results = self.get_results()
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

    def get_metadata(self):
        with open(self.meta_path(), "r") as f:
            return json.load(f)

    def set_metadata(self):
        meta_data = self.get_metadata()
        return (
            meta_data["bug_line_number"],
            meta_data["classpath"],
            meta_data["num_lines"],
        )

    def get_sus_dic(self):
        with open(self.fl_path(), "r") as f:
            return json.load(f)

    def set_sus(self):
        sus_dic = self.get_sus_dic()
        sus_dic = keys_to_int(sus_dic)
        sus_dic = vals_to_float(sus_dic)
        sus_dic = sort_by_value_desc(sus_dic)
        return sus_dic

    def get_code(self):
        with open(self.code_path(), "r") as f:
            return f.readlines()

    def set_code(self):
        code = self.get_code()
        code_dic = {
            i + 1: code[i] for i in range(len(code))
        }  # note, this keeps newlines in for some reason
        return code_dic

    def set_sus_lines(self):
        sus_dic = self.set_sus()
        code_dic = self.set_code()
        sus_lines = []
        for line in sus_dic:
            sus_lines.append(SusLine(line, code_dic))
        return sus_lines


def keys_to_int(dic):
    return {int(k): v for k, v in dic.items()}


def vals_to_float(dic):
    return {k: float(v) for k, v in dic.items()}


def sort_by_key(dic):
    return {k: dic[k] for k in sorted(dic)}


def sort_by_value(dic):
    return {k: v for k, v in sorted(dic.items(), key=lambda item: item[1])}


def sort_by_value_desc(dic):
    return {
        k: v for k, v in sorted(dic.items(), key=lambda item: item[1], reverse=True)
    }
