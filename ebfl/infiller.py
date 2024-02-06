from typing import List 
import torch 
from math import exp, log 
from torch import nn 
import tokenizers 
from math import log2
import json
from colorama import Fore, Back, Style
from transformers import AutoModelForCausalLM, AutoTokenizer

CUDA = True 
BIG_MODEL = True
BOS = "<|endoftext|>"
EOS = "<|endofmask|>"


class Infiller: 
    def __init__(self, model_name):
        self.model_name = model_name
        if 'incoder' in model_name:
            self.kwargs = dict(revision="float16",torch_dtype=torch.float16,low_cpu_mem_usage=True,)
        else:
            self.kwargs = dict(torch_dtype=torch.float16,low_cpu_mem_usage=True,)
        
    def load_model(self): 
        print(f"{Style.DIM}{Fore.BLUE}Loading model...{Style.RESET_ALL}")
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name, **self.kwargs)
        self.model = self.model.half().cuda()
        
    def load_tokenizer(self):
        print(f"{Style.DIM}{Fore.BLUE}Loading tokenizer...{Style.RESET_ALL}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        return self.tokenizer

    def load(self):
        self.load_model()
        self.load_tokenizer()
        print("Loading complete")
        if CUDA:
            self.model = self.model.half().cuda()

    def tokenize_line(self, line):
        return self.tokenizer.encode(line+'\n', add_special_tokens=False)

    def detokenize(self, context):
        return self.tokenizer.decode(context, clean_up_tokenization_spaces=False)
    
    def get_bos_id(self):
        return self.tokenizer.bos_token_id

    def get_mask_id(self, index):
        mask_str = f'<|mask:{index}|>'
        tok = self.tokenizer.encode(mask_str, add_special_tokens=False)
        return tok[0]

    def generate(self, input_ids, num_return_sequences, max_to_generate: int=52, temperature : float=0.5):
        input_ids = tensorize(input_ids).cuda()
        max_length = max_to_generate + input_ids.flatten().size(0)
        if max_length > 2048:
            print('Max length exceeded')
        with torch.no_grad():
            output = self.model.generate(input_ids=input_ids, do_sample=True, top_p=0.95, temperature=0.5, max_length=max_length, return_dict_in_generate=True, output_scores=True, num_return_sequences=num_return_sequences, pad_token_id=self.tokenizer.eos_token_id)
            detok_hypo_str = self.tokenizer.decode(output["sequences"].flatten(), clean_up_tokenization_spaces=False)
            #if detok_hypo_str.startswith(BOS):
            #    detok_hypo_str = detok_hypo_str[len(BOS):]
            #return output, detok_hypo_str
            return output
    
    def entropy(self, input_ids, start_loc, target_len):
        newline = self.tokenizer.encode('\n')[0]
        encodings = tensorize(input_ids)
        end_loc = start_loc + target_len
        context_mask = encodings.clone()
        context_mask[0][0:start_loc] = -100
        context_mask[0][end_loc:] = -100
        encodings = encodings.to("cuda")
        context_mask = context_mask.to("cuda")
        with torch.no_grad():
            outputs = self.model(encodings, labels=context_mask)
            logits = outputs.logits
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = context_mask[..., 1:].contiguous()
            loss_fct = nn.CrossEntropyLoss(reduction="none")
            loss = loss_fct(shift_logits.view(-1, shift_logits.size(-1)), shift_labels.view(-1))
            loss_list = loss.tolist()
            entropy = loss_list[start_loc-1:end_loc-1]   
            avrg_entropy = loss.sum() / (target_len)
        return avrg_entropy.item(), entropy

def tensorize(token_list):
    tensor = torch.tensor(token_list)
    tensor = tensor[None, :]
    return tensor