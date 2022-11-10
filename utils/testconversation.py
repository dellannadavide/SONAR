import time

from transformers import pipeline, Conversation

from transformers.utils import logging

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

import constants as Constants

# from sentence_transformers import SentenceTransformer, util
# import numpy as np
# model = SentenceTransformer('stsb-mpnet-base-v2')
# sentence1 =  "what is this"
# sentence2 =  "can you tell me what is this"
# # encode sentences to get their embeddings
# embedding1 = model.encode(sentence1, convert_to_tensor=True)
# embedding2 = model.encode(sentence2, convert_to_tensor=True)
# # compute similarity scores of two embeddings
# cosine_scores = util.pytorch_cos_sim(embedding1, embedding2)
# print("Sentence 1:", sentence1)
# print("Sentence 2:", sentence2)
# print("Similarity score:", cosine_scores.item())
# exit()
#
# x = torch.randn(1, 2)
# print(x)
# x = torch.cat([x,x], dim=-1)
# print(x)
# x = torch.cat([x,x], dim=-1)
# print(x)
# exit()

tgenerator = pipeline('text-generation', model="facebook/opt-350m")
# for emotion in Constants.EMOTIONS_RELATED_QUESTIONS.keys():
#     g = tgenerator("Today you look "+emotion+". Is it because", max_length=50,
#                                         do_sample=True,
#                                         top_p=0.92,
#                                         top_k=100,
#                                         temperature=0.75,
#                    num_return_sequences=10)
#     for i in g:
#         print(i['generated_text'].split("?")[0]+"?")

# for obje in ["cellphone", "teddybear", "cup", "airplane", "clock", "toothbrush"]:
#     types_of_questions = ["Did you know that a "+obje,
#                           "What kind of "+obje,
#                           "Is that a "+obje,
#                           "I noticed a "+obje+". Is it"]
#     for toq in types_of_questions:
#         g = tgenerator(toq, max_length=50,
#                                             do_sample=True,
#                                             top_p=0.92,
#                                             top_k=100,
#                                             temperature=0.75,
#                        num_return_sequences=10)
#         for i in g:
#             print(i['generated_text'].split("?")[0]+"?")



conversation = "Hi. Good to meet you! Did you just arrive here? Yeah, We arrived last week. How do you like it? It’s exciting! It’s much busier than the last city we lived in. I was working in Seattle for the last 3 years. It really is very busy. I moved here from Tokyo 5 years ago and I still have trouble sometimes. Did you move here with your wife? Actually, I’m not married. I moved here with my dog, Charles. We are very close. Oh. I see. What about you? Yes, I am married and I have two children. How old are they? 6 and 8 years old Oh, great. That age is a lot of fun. But it is exhausting. I understand. My brother has kids the same age. Every time we visit he falls asleep on the sofa. Must be nice. We don’t have time to sleep, we have to drink a lot of coffee."
# conversation = "Hello there,  What's your name,  Sir, , hey name is David, Your name is David, correct, , yes that's correct, Got it,  Nice to meet you David, , nice to meet you how are you today, Sir, I'm good thanks,  Sir, , what's your favourite colour, The colour of the sky, you're so romantic, Sir, I try Sir, , what is love, david, thank you for trusting me with this,  That's so sweet of you, yes but do you know what is it, Sir, It's a lie Sir, , so you're not very romantic, Sir, I'm sorry, but I'm afraid I'm not very romantic, , ok nevermind then, you're not very romantic, instead I think I am, That's nice, , 10cc, Sir, Oh no, that's too many,  Sir, , what you say, What do you say when you're not speaking, , nothing, Sir, What do you say when you're not speaking,  Sir, , you say nothing if you're not speaking, No, Sir, you say nothing, , tell me what you see, Nothing really, , why is that, because im not listening, can you see with your ears you see with your eyes, I can see with my ears, yes, , you're super funny, Sir, Thanks :D Sir"
g = tgenerator(conversation+". Can you tell me more about ", max_length=50,
                                    do_sample=True,
                                    top_p=0.92,
                                    top_k=100,
                                    temperature=0.75,
               num_return_sequences=10)
for i in g:
    print(i['generated_text'].split("?")[0]+"?")


exit()

sentences = ["I'm afraid not"
             ]

classifier = pipeline("text-classification",model='bhadresh-savani/bert-base-uncased-emotion', top_k=1)
for s in sentences:
    emotion = classifier(s)[0][0]
    print(emotion)
    if emotion["score"] > 0.7:
        print("is high")
exit()


# model_name = "microsoft/DialoGPT-large"
model_name = "microsoft/DialoGPT-medium"
# model_name = "microsoft/DialoGPT-small"


logging.set_verbosity(40) #errors

# model_name = "microsoft/DialoGPT-large"
model_name = "microsoft/DialoGPT-medium"
# model_name = "facebook/opt-350m"
# model_name = "microsoft/DialoGPT-small"


class Converser:

    def __init__(self, model_name) -> None:
        super().__init__()
        self.model_name = model_name
        self.chat_history_ids = None
        self.bot_input_ids = None
        # self.chat_history_ids_list = None
        self.input_ids = None
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.step = 0
        self.user_inputs = []
        self.generated_responses = []
        self.first_indeces_steps = []
        self.max_length_history = 3

    def getResponse(self, text):
        self.user_inputs.append(text)
        self.input_ids = self.tokenizer.encode(text + self.tokenizer.eos_token, return_tensors="pt")
        # concatenate new user input with chat history (if there is)
        self.bot_input_ids = torch.cat([self.chat_history_ids, self.input_ids], dim=-1) if self.step > 0 else self.input_ids
        # print(self.bot_input_ids)
        # print(self.bot_input_ids.shape[-1])
        # generate a bot response
        self.chat_history_ids = self.model.generate(
            self.bot_input_ids,
            # min_length=self.bot_input_ids.shape[-1] + 2,
            max_length=1000,
            do_sample=True,
            top_p=0.95,
            top_k=50,
            temperature=0.75,
            pad_token_id=self.tokenizer.eos_token_id
        )
        # print(self.chat_history_ids)
        # print(self.chat_history_ids[:,self.bot_input_ids.shape[-1]:])
        # print(self.chat_history_ids[:,self.bot_input_ids.shape[-1]:][0])
        # print the outputs
        output = self.tokenizer.decode(self.chat_history_ids[:,self.bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
        # test_chat_history = self.chat_history_ids[:,:]
        # self.chat_history_ids = torch.unsqueeze(self.chat_history_ids_list[0], dim=0)
        self.generated_responses.append(output)
        self.step += 1
        self.first_indeces_steps.append(self.chat_history_ids.shape[-1])
        # print("indeces step ", self.first_indeces_steps)
        # print("step ", self.step)

        # every self.max_length_history interactions (1 user input and 1 respionse), I remove the oldest one from the chat history
        # I do this bvecause apparently after a certain number of sentences in the history the whole generator breaks
        if (len(self.first_indeces_steps)%self.max_length_history)==0:
            self.removeOldestInteractionFromChatHistory()

        return output

    def removeOldestInteractionFromChatHistory(self):
        self.chat_history_ids  = self.chat_history_ids[:,self.first_indeces_steps[0]:]
        self.first_indeces_steps = self.first_indeces_steps[1:]

    def removeLastBotResponseFromChatHistory(self):
        idx_first_token_last_bot_response = self.bot_input_ids.shape[-1]
        print("last response was: ", self.chat_history_ids[:,self.bot_input_ids.shape[-1]:][0])
        self.chat_history_ids = self.chat_history_ids[:,0:idx_first_token_last_bot_response]
        self.generated_responses = self.generated_responses[:-1]

    def addBotResponseToChatHistory(self, response_text, tokenized_response):
        self.chat_history_ids = torch.cat([self.chat_history_ids, tokenized_response], dim=-1)
        self.generated_responses.append(response_text)

    def replaceLastBotResponseWith(self, new_response):
        encoded_new_response = self.tokenizer.encode(new_response + self.tokenizer.eos_token, return_tensors="pt")
        print("encoded new response is ", encoded_new_response)
        self.removeLastBotResponseFromChatHistory()
        self.addBotResponseToChatHistory(new_response, encoded_new_response)

    def getConversation(self):
        """ Returns a list of pairs is_user, text"""
        conv = []
        for i in range(len(self.user_inputs)):
            conv.append((True, self.user_inputs[i]))
            if i < len(self.generated_responses):
                conv.append((False, self.generated_responses[i]))
        return conv

    def printConversation(self):
        print(self.chat_history_ids)
        conv = self.getConversation()
        for is_user, text in conv:
            if is_user:
                print("user >> ", text)
            else:
                print("bot >> ", text)

    def getConversationString(self):
        conv_str = ""
        for is_user, text in self.getConversation():
            conv_str += (" " if (
                    conv_str == "" or conv_str.endswith(".") or conv_str.endswith("!") or conv_str.endswith(
                "?")) else ". ") + text
        return conv_str

    #
    # TODO:
    # 1.
    #  add functions and test them to add external inputs as answers
    # (how to integrate them also in the ids history?)
    # somewhat needs to be encoded for torch
    # 2.
    #  integrate all of this in the chatter
    #




# def getResponse(text, conversation, pipeline):
#     conversation.add_user_input(text)
#     r = pipeline([conversation],
#              max_length=1000,
#             do_sample=True,
#             top_p=0.95,
#             top_k=50,
#             temperature=0.85)
#     return conversation.generated_responses[len(conversation.generated_responses)-1]


# conversational_pipeline = pipeline("conversational", model=model_name)
# conv = Conversation()
#
# for sentence in sentences:
#     print("pipeline: ", getResponse(sentence, conv, conversational_pipeline))
#
# print(conv)
#
# print("......")

converser = Converser(model_name)
for sentence in sentences:
    print("converser: ", converser.getResponse(sentence))
    print("length history tokens after response", converser.chat_history_ids.shape[-1])

converser.printConversation()

print("Replacing last bot response with blablabla")
converser.replaceLastBotResponseWith("blablabla")

print("Replacing last bot response  again, now with this is my new response to your question")
converser.replaceLastBotResponseWith("this is my new response to your question.")


converser.printConversation()

print("Now trying to continue conversation as if nothing happened")

for sentence in sentences:
    print("converser: ", converser.getResponse(sentence))

converser.printConversation()

print("Replacing last bot response with blablabla")
converser.replaceLastBotResponseWith("i know many things but among others I know nothing")

converser.printConversation()

print("Now trying to continue conversation as if nothing happened")

for sentence in sentences:
    print("converser: ", converser.getResponse(sentence))

converser.printConversation()

#
# conv_str = ""
# for is_user, text in conv.iter_texts():
#     conv_str += (" " if (conv_str=="" or conv_str.endswith(".") or conv_str.endswith("!") or conv_str.endswith("?")) else ". ") + text
# print(conv_str)

exit()

def getTextFor(t2tpip, task, text):
    if task=="generate questions":
        r = t2tpip("generate questions : "+text,
                   max_length=20,
                   do_sample=True,
                 top_p=0.92,
                 top_k=100,
                 temperature=0.75
                   , num_return_sequences=10
                   )
        print("questions for ", text, ": ")
        for s in r:
            first = s['generated_text'].split("<sep>")[0]
            print(first)
        print("")
        return r[0]['generated_text'].split("<sep>")[0]
    return "ok"


generator = pipeline('text-generation', model = "facebook/opt-350m")
# conversation = "Hi. Good to meet you! Did you just arrive here? Yeah, We arrived last week. How do you like it? It’s exciting! It’s much busier than the last city we lived in. I was working in Seattle for the last 3 years. It really is very busy. I moved here from Tokyo 5 years ago and I still have trouble sometimes. Did you move here with your wife? Actually, I’m not married. I moved here with my dog, Charles. We are very close. Oh. I see. What about you? Yes, I am married and I have two children. How old are they? 6 and 8 years old Oh, great. That age is a lot of fun. But it is exhausting. I understand. My brother has kids the same age. Every time we visit he falls asleep on the sofa. Must be nice. We don’t have time to sleep, we have to drink a lot of coffee."
conversation = "are you certain of this. i. review as we know it. i don'te"
g = generator(conversation, max_length=len(conversation.split(" "))+20,
                   do_sample=True,
                 top_p=0.92,
                 top_k=100,
                 temperature=0.75, num_return_sequences=10)
for t in g:
    print(t)

t2tpipeline = pipeline("text2text-generation", model = "valhalla/t5-base-e2e-qg")
g = getTextFor(t2tpipeline, "generate questions", conversation)
print(g)

exit()

conv.past_user_inputs.append("")
conv.past_user_inputs.append("")
# conv.generated_responses.append("I like the color blue.")

for sentence in sentences2:
    print("pipeline: ", getResponse(sentence, conv, conversational_pipeline))

print(conv)

exit()


texts = [
    # "The book on the right",
    #      "The clock on the top",
    #      "The laptop on the left",
    #      "The coffee on the left",
    #      "The book",
    #      "the coffee",
    #      "the clock",
    #      "the laptop",
         "You are paying attention to the book on your right.",
         "You are paying attention to the book.",
        "You are paying attention to the coffee.",
        "There is a person in the room.",
"You like hat."

         ]


class_labels = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
                        "trafficlight", "firehydrant", "stopsign", "parkingmeter", "bench", "bird", "cat",
                        "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
                        "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sportsball",
                        "kite", "baseballbat", "baseballglove", "skateboard", "surfboard", "tennisracket",
                        "bottle", "wineglass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
                        "sandwich", "orange", "broccoli", "carrot", "hotdog", "pizza", "donut", "cake", "chair",
                        "sofa", "pottedplant", "bed", "diningtable", "toilet", "tvmonitor", "laptop", "mouse",
                        "remote", "keyboard", "cellphone", "microwave", "oven", "toaster", "sink",
                        "refrigerator",
                        "book", "clock", "vase", "scissors", "teddybear", "hairdrier", "toothbrush"]


t2tpipeline = pipeline("text2text-generation", model = "valhalla/t5-base-e2e-qg")
# for t in texts:
#     getTextFor(t2tpipeline, "generate questions", t)

# for cl in class_labels:
#     getTextFor(t2tpipeline, "generate questions", "You are looking at the "+cl+ ". You find a "+cl+" interesting. You know what a "+cl+" is.")


# generator = pipeline('text-generation', model = "facebook/opt-350m")
conversation = "Hi. Good to meet you! Did you just arrive here? Yeah, We arrived last week. How do you like it? It’s exciting! It’s much busier than the last city we lived in. I was working in Seattle for the last 3 years. It really is very busy. I moved here from Tokyo 5 years ago and I still have trouble sometimes. Did you move here with your wife? Actually, I’m not married. I moved here with my dog, Charles. We are very close. Oh. I see. What about you? Yes, I am married and I have two children. How old are they? 6 and 8 years old Oh, great. That age is a lot of fun. But it is exhausting. I understand. My brother has kids the same age. Every time we visit he falls asleep on the sofa. Must be nice. We don’t have time to sleep, we have to drink a lot of coffee."
    # g = generator("a ", max_length=30,
    #                    do_sample=True,
    #                  top_p=0.92,
    #                  top_k=100,
    #                  temperature=0.75)
    # # print(g)
    # getTextFor(t2tpipeline, "generate questions", "You can tell me that "+ g[0]["generated_text"])


summarizer = pipeline("summarization")
summary= summarizer(["Hi.", "Good to meet you!"], min_length=5, max_length=20)
print(summary)
summary = summary[0]["summary_text"]

getTextFor(t2tpipeline, "generate questions", "You can tell me more about " + summary)



# from transformers import DetrFeatureExtractor, DetrForObjectDetection
# import torch
# from PIL import Image
# import requests
#
# url = "https://media.istockphoto.com/photos/shot-of-a-young-businessman-using-a-laptop-in-a-modern-office-picture-id1354898581?k=20&m=1354898581&s=170667a&w=0&h=ztJpkq5nyK4j7B3Aac2GbU20E_IZnUjUVrFFqrppsbw="
# image = Image.open(requests.get(url, stream=True).raw)
#
# feature_extractor = DetrFeatureExtractor.from_pretrained("facebook/detr-resnet-50")
# model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50")
#
# print("starting feature extraction")
# n = time.time()
# inputs = feature_extractor(images=image, return_tensors="pt")
# outputs = model(**inputs)
#
# # convert outputs (bounding boxes and class logits) to COCO API
# target_sizes = torch.tensor([image.size[::-1]])
# results = feature_extractor.post_process(outputs, target_sizes=target_sizes)[0]
# print(time.time()-n)
# print("done")
# for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
#     box = [round(i, 2) for i in box.tolist()]
#     # let's only keep detections with score > 0.9
#     if score > 0.9:
#         print(
#             f"Detected {model.config.id2label[label.item()]} with confidence "
#             f"{round(score.item(), 3)} at location {box}"
#         )

