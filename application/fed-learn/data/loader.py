from typing import Tuple, Dict
import torch
from data.UNSW_NB15 import UNSWNB15
import torchvision.transforms as transforms

DATA_ROOT = "../data/datasets/"

def load_data() -> Tuple[torch.utils.data.DataLoader, torch.utils.data.DataLoader, Dict]:
    """Load UNSW-NB15 (training and test set)."""
    trainset = UNSWNB15(DATA_ROOT, train=True)
    trainloader = torch.utils.data.DataLoader(trainset, batch_size=32, shuffle=True)
    testset = UNSWNB15(DATA_ROOT, train=False)
    testloader = torch.utils.data.DataLoader(testset, batch_size=32, shuffle=False)
    num_examples = {"trainset" : len(trainset), "testset" : len(testset)}
    return trainloader, testloader, num_examples