import json
from .nltk_ut import toknization,stem,allwords
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import Dataset,DataLoader

from .models import neuralnet



with open('intents.json','r') as f:
    intents = json.load(f)
    
all_words = []
tags=[]
xy = []

for intent in intents['intents']:
    tag = intent['tag']
    tags.append(tag)
    for pattern in intent['patterns']:
        w = toknization(pattern)
        all_words.extend(w)
        xy.append((w, tag))
        
ignore_words = ['?','!','<>','.']
all_words = [stem(w) for w in all_words if w not in ignore_words]
all_words=sorted(set(all_words))
tags = sorted(set(tags))
# print(tags)


X_train = []
y_train=[]

for (pattern_sentence, tag) in xy:
    # bag=all_words(pattern_sentence,all_words)
    bag = allwords(pattern_sentence,all_words)
    X_train.append(bag)
    
    label = tags.index(tag)
    y_train.append(label)
    
X_train = np.array(X_train)
y_train = np.array(y_train) 
    
class ChatDataset(Dataset):
    def __init__(self):
        self.n_samples = len(X_train)
        self.x_data = X_train
        self.y_data = y_train
        
        
    def __getitem__(self,index):
        return self.x_data[index], self.y_data[index]
    
    def __len__(self):
        return self.n_samples
    
batch_size = 8 
hidden_size = 8 

output_size = len(tags)
input_size = len(X_train[0])

learning_rate = 0.001 
num_epochs = 1500 

# print(input_size , len(all_words))
# print (output_size,tags)

dataset = ChatDataset()
train_loader = DataLoader(dataset = dataset , 
                            batch_size = batch_size , 
                            shuffle = True ,
                            num_workers = 0 )


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

model = neuralnet(input_size , hidden_size , output_size)

criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(),lr = learning_rate)

# training model
for epoch in range(num_epochs):
    for (words,labels) in train_loader:
        words = words.to(device).float()
        labels = labels.to(device).long()
        # labels= labels.float()
        # print(words, labels)
        outputs = model(words)
        # print(outputs)
       
        loss = criterion(outputs, labels)
        
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    
    if (epoch +1) % 100 == 0 :
        print (f'epoch {epoch+1}/{num_epochs} , loss = {loss.item():.4f}')


data= {
    "model_state":model.state_dict(),
    "input_size":input_size,
    "output_size" : output_size,
    "hidden_size":hidden_size,
    "all_words":all_words,
    "tags":tags
}


FILE = 'data.pth'
torch.save(data,FILE)
print(f"training finished. file saved to {FILE}")