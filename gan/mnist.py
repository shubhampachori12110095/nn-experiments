import numpy as np
import time
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from torchvision import datasets, transforms
from torch.autograd import Variable

BATCH_SIZE = 128
DATA_DIR = 'data'
EPOCH = 100
SEED = 1
k = 2
Z_DIM = 50
IMG_DIM = 28 * 28

use_cuda = torch.cuda.is_available()

train_loader = torch.utils.data.DataLoader(
    datasets.MNIST(DATA_DIR,
            train=True,
            download=True,
            transform=transforms.Compose([
                transforms.ToTensor()
            ])),
    batch_size=BATCH_SIZE,
    shuffle=True,
)

class Generator(nn.Module):
    def __init__(self):
        super(Generator, self).__init__()
        self.fc1 = nn.Linear(Z_DIM, 256)
        self.fc2 = nn.Linear(256, 512)
        self.fc3 = nn.Linear(512, 1024)
        self.fc4 = nn.Linear(1024, IMG_DIM)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        x = self.sigmoid(x)
        return x.view(-1, 1, 28, 28)

class Discriminator(nn.Module):
    def __init__(self):
        super(Discriminator, self).__init__()
        self.fc1 = nn.Linear(784, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.fc3 = nn.Linear(512, 256)
        self.fc4 = nn.Linear(256, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = F.dropout(x, 0.3)
        x = F.relu(self.fc2(x))
        x = F.dropout(x, 0.3)
        x = F.relu(self.fc3(x))
        x = F.dropout(x, 0.3)
        x = self.fc4(x)
        x = self.sigmoid(x)
        return x

generator = Generator()
discriminator = Discriminator()
if use_cuda:
    generator.cuda()
    discriminator.cuda()

generator_optim = optim.Adam(generator.parameters(), lr = 0.000002)
discriminator_optim = optim.Adam(discriminator.parameters(), lr = 0.0002)

BCE_loss = nn.BCELoss()

generator_losses = []
discriminator_losses = []

def train_discriminator(x, z):
    discriminator.train()
    generator.eval()
    discriminator_optim.zero_grad()
    d, d_ = discriminator(x), discriminator(generator(z))
    y, y_ = torch.ones(z.size(0), 1), torch.zeros(z.size(0), 1)
    if use_cuda:
        y, y_ = y.cuda(), y_.cuda()
    y, y_ = Variable(y), Variable(y_)
    loss = BCE_loss(d, y) + BCE_loss(d_, y_)
    discriminator_losses.append(loss.data[0])
    loss.backward()
    discriminator_optim.step()

def train_generator(z):
    discriminator.eval()
    generator.train()
    generator_optim.zero_grad()
    d_ = discriminator(generator(z))
    y_ = torch.ones(z.size(0), 1)
    if use_cuda:
        y_ = y_.cuda()
    y_ = Variable(y_)
    loss = BCE_loss(d_, y_)
    generator_losses.append(loss.data[0])
    loss.backward()
    generator_optim.step()

def train_epoch():
    for batch_idx, (x, _) in enumerate(train_loader):
        z = torch.randn(x.size(0), Z_DIM)
        if use_cuda:
            x, z = x.cuda(), z.cuda()
        train_discriminator(Variable(x), Variable(z))
        if (batch_idx + 1) % k == 0:
            z = torch.randn(x.size(0), Z_DIM)
            if use_cuda:
                z = z.cuda()
            train_generator(Variable(z))

def train():
    for e in range(EPOCH):
        print 'Step %d' % e
        train_epoch()
        plt.plot(generator_losses[::469], 'g')
        plt.plot(discriminator_losses[::k*469], 'b')
        plt.savefig('results/loss_%d.png' % e)
        plt.close()
        z = torch.randn(1, Z_DIM)
        if use_cuda:
            z = z.cuda()
        img = generator(Variable(z))
        plt.imshow(img.cpu().data.numpy().reshape(28, 28), cmap='gray')
        plt.savefig('results/test_%d.png' % e)
        plt.close()

torch.manual_seed(1)
if use_cuda:
    torch.cuda.manual_seed(1)

start = time.time()
train()
print time.time() - start