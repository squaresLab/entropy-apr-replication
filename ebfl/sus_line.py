class SusLine:
    def __init__(self, line_num, code_dic, context_window=50):
        self.line_num = line_num
        self.code_dic = code_dic
        self.context_window = context_window
        self.file_start = self.set_file_start()
        self.file_end = self.set_file_end()
        self.c_start, self.c_end = self.set_index()
        self.context = self.set_context()
        self.prefix = self.set_prefix(self.c_start, self.line_num)
        self.suffix = self.set_suffix(self.line_num, self.c_end)

    def set_file_start(self):
        return min(self.code_dic.keys())

    def set_file_end(self):
        return max(self.code_dic.keys())

    def lines_from_top(self):
        return self.line_num - self.file_start

    def lines_from_bot(self):
        return self.file_end - self.line_num

    def set_prefix(self, start, end):
        return_dict = {}
        for k in range(start, end):
            if k in self.code_dic.keys():
                return_dict[k] = self.code_dic[k]
        # return {k:self.code_dic[k] for k in range(start, end)}
        return return_dict

    def set_suffix(self, start, end):
        return {k: self.code_dic[k] for k in range(start + 1, end)}

    def set_index(self):
        lines_from_top, lines_from_bot = self.lines_from_top(), self.lines_from_bot()
        if (
            lines_from_top > self.context_window
            and lines_from_bot > self.context_window
        ):
            start = self.line_num - self.context_window
            end = self.line_num + self.context_window
        elif lines_from_top <= self.context_window:
            start = self.file_start
            add = self.context_window - lines_from_top
            end = self.line_num + self.context_window + add
            if end > self.file_end:
                end = self.file_end
        elif lines_from_bot <= self.context_window:
            end = self.file_end
            add = self.context_window - lines_from_bot
            start = self.line_num - self.context_window - add
            if start < self.file_start:
                start = self.file_start
        else:
            start = self.file_start
            end = self.file_end
        return start, end

    def set_context(self):
        return {i: self.code_dic[i] for i in range(self.c_start, self.c_end + 1)}

    def get_context(self):
        return self.context

    def get_line_code(self):
        try:
            line_code = self.code_dic[self.line_num]
            return line_code
        except:
            return "\n"

    def get_prefix(self):
        return self.prefix

    def get_suffix(self):
        return self.suffix

    def to_string(self, dic):
        code_str = ""
        for k, v in dic.items():
            code_str += v
        return code_str

    def form_gen_prompt(self):
        code_before = self.to_string(self.prefix)
        code_after = self.to_string(self.suffix)
        prompt = code_before + "<|mask:0|>" + "\n" + code_after + "<|mask:1|><|mask:0|>"
        return prompt

    def decode_query(self, query):
        decoded = self.tokenizer.decode(query)
        return decoded

    def parse_output(self, output, gen_prompt_toks):
        input_len = len(gen_prompt_toks)
        output_ids = output.flatten().tolist()
        gen_ids = output_ids[input_len:]
        prompt_ids = output_ids[:input_len]
        gen_str = self.decode_query(gen_ids)
        return gen_ids, gen_str
