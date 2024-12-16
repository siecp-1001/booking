import nltk 
nltk.download('punkt')
from nltk.stem.porter import PorterStemmer
import numpy as np
import torch
stemmer = PorterStemmer()

def toknization(sentence):
    return nltk.word_tokenize(sentence)
    

def stem(word):
    return stemmer.stem(word.lower())

def allwords(tokenized_sentence,allwords):
    tokenized_sentence=[stem(w) for w in tokenized_sentence]
    bag = np.zeros(len(allwords),dtype = np.float64)
    # bag =np.zeros(len(allwords),dtype = np.float32)
    for idx , w in enumerate(allwords):
        if w in tokenized_sentence:
            bag[idx] = 1.0
    return bag

# sentence = ['hello','how','are','you']
# words = ['hi','hello','bye','are','thank','cool','I']
# bog = allwords(sentence, words)
# print(bog)
# x = all