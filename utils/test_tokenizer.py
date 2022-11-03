from torch import tensor
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_name = "microsoft/DialoGPT-medium"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

t = [13787,  5549,     0,  1320,   338,   826,    11,   314,  1101,   407,
           257, 21219,    13,   314,  1101,   257, 24240,    13, 50256]

output = tokenizer.decode(t, skip_special_tokens=False)
print(output)



# conversation is
# user >>  You are soon going to have a conversation, be ready!
# bot >>  You are soon going to have a conversation, be ready! Hello there! What's your name?
# user >>  hi my name is David
# bot >>  Your name is David, correct?
# user >>  yes
# bot >>  Got it! Nice to meet you David!
# user >>  nice to meet you too
# bot >>  nice to meet you too
# user >>  how are you doing today
# bot >> im good, just trying to keep the brain off of it