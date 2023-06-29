from torch.utils.data import Dataset
from torchvision.datasets import CIFAR10
import pandas as pd
import os.path as path

class UNSWNB15(Dataset):
    """UNSW_NB15 dataset"""
    
    def __init__(self, root_dir, train=True) -> None:

        # UNSW_NB15_testing-set.csv is actually more suitable for training because it has more data
        self.train = train
        csv_file = path.join(root_dir, "UNSW_NB15_" + "testing" if self.train else "training" + "-set.csv")
        self.df = pd.read_csv(csv_file)

    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, index):
        return self.df.iloc[index]
    
    def extra_repr(self) -> str:
        split = "Train" if self.train is True else "Test"
        return f"Split: {split}"
        