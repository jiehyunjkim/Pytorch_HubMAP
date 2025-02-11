import os
from typing import Any, Callable, Optional
from torch import nn, utils
import torch
from pytorch_lightning import LightningDataModule, Trainer
import pytorch_lightning as pl
from torch.utils.data import DataLoader
from torch.utils.data.dataset import random_split

from kaggle_dataset import KaggleDataset
from pl_bolts.utils import _TORCHVISION_AVAILABLE
from utils import under_review
from pl_bolts.utils.warnings import warn_missing_pkg

import cv2
from pl_bolts.models.vision.unet import UNet

if _TORCHVISION_AVAILABLE:
    from torchvision import transforms
else:  # pragma: no cover
    warn_missing_pkg("torchvision")


import numpy as np
import torchvision
#import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pandas as pd
import random

DATASET_FOLDER = "/Users/jiehyun/kaggle/input/hubmap-organ-segmentation/"
TRAIN_CSV = DATASET_FOLDER + "train.csv"
train_df = pd.read_csv(TRAIN_CSV)
OUTPUT_FOLDER = "/Users/jiehyun/kaggle/output/"
IMG_NPY_512 = OUTPUT_FOLDER + 'img_npy_512'
MASK_NPY_512 = OUTPUT_FOLDER + 'mask_npy_512'

@under_review()
class KaggleDataModule(LightningDataModule):

    name = "kaggle"

    def __init__(
        self,
        data_dir: Optional[str] = None,
        val_split: float = 0.2,
        test_split: float = 0.1,
        num_workers: int = 0,
        batch_size: int = 32,
        seed: int = 42,
        shuffle: bool = True,
        pin_memory: bool = True,
        drop_last: bool = False,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Kitti train, validation and test dataloaders.
        Note:
            You need to have downloaded the Kitti dataset first and provide the path to where it is saved.
            You can download the dataset here:
            http://www.cvlibs.net/datasets/kitti/eval_semseg.php?benchmark=semantics2015
        Specs:
            - 200 samples
            - Each image is (3 x 1242 x 376)
        In total there are 34 classes but some of these are not useful so by default we use only 19 of the classes
        specified by the `valid_labels` parameter.
        Example::
            from pl_bolts.datamodules import KittiDataModule
            dm = KittiDataModule(PATH)
            model = LitModel()
            Trainer().fit(model, datamodule=dm)
        Args:
            data_dir: where to load the data from path, i.e. '/path/to/folder/with/data_semantics/'
            val_split: size of validation test (default 0.2)
            test_split: size of test set (default 0.1)
            num_workers: how many workers to use for loading data
            batch_size: the batch size
            seed: random seed to be used for train/val/test splits
            shuffle: If true shuffles the data every epoch
            pin_memory: If true, the data loader will copy Tensors into CUDA pinned memory before
                        returning them
            drop_last: If true drops the last incomplete batch
        """
        #if not _TORCHVISION_AVAILABLE:  # pragma: no cover
        #    raise ModuleNotFoundError("You want to use `torchvision` which is not installed yet.")

        super().__init__(*args, **kwargs)
        self.data_dir = data_dir if data_dir is not None else os.getcwd()
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.seed = seed
        self.shuffle = shuffle
        self.pin_memory = pin_memory
        self.drop_last = drop_last

        # split into train, val, test
        kaggle_dataset = KaggleDataset(self.data_dir, transform=self._default_transforms())

        val_len = round(val_split * len(kaggle_dataset))
        test_len = round(test_split * len(kaggle_dataset))
        train_len = len(kaggle_dataset) - val_len - test_len

        self.trainset, self.valset, self.testset = random_split(
            kaggle_dataset, lengths=[train_len, val_len, test_len], generator=torch.Generator().manual_seed(self.seed)
        )

    def train_dataloader(self) -> DataLoader:
        loader = DataLoader(
            self.trainset,
            batch_size=self.batch_size,
            shuffle=self.shuffle,
            num_workers=self.num_workers,
            drop_last=self.drop_last,
            pin_memory=self.pin_memory,
        )
        return loader

    def val_dataloader(self) -> DataLoader:
        loader = DataLoader(
            self.valset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            drop_last=self.drop_last,
            pin_memory=self.pin_memory,
        )
        return loader

    def test_dataloader(self) -> DataLoader:
        loader = DataLoader(
            self.testset,
            batch_size=self.batch_size,
            shuffle=False,
            num_workers=self.num_workers,
            drop_last=self.drop_last,
            pin_memory=self.pin_memory,
        )
        return loader

    def _default_transforms(self) -> Callable:
        kaggle_transforms = transforms.Compose(
            [
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.35675976, 0.37380189, 0.3764753], std=[0.32064945, 0.32098866, 0.32325324]
                ),
            ]
        )
        return kaggle_transforms


def imshow(inp1, title=None):
    """Imshow for Tensor."""
    inp1 = inp1.numpy().transpose((1, 2, 0))
    #inp2 = inp2.numpy().transpose((1, 2, 0))

    mean = np.array([0.485, 0.456, 0.406])
    std = np.array([0.229, 0.224, 0.225])

    inp1 = std * inp1 + mean
    inp1 = np.clip(inp1, 0, 1)
    #inp2 = std * inp2 + mean
    #inp2 = np.clip(1, 0, 1)

    #palette+++

    plt.imshow(inp1)
    #plt.imshow(inp2, cmap='coolwarm', alpha=0.5)

    if title is not None:
        plt.title(title)

    plt.show()

def palette():
    return

def main():
    from PIL import Image
    from torchvision.utils import draw_segmentation_masks

    dm = KaggleDataModule(data_dir='/Users/jiehyun/kaggle/input/hubmap-organ-segmentation/', batch_size=4)

    image, masks = next(iter(dm.train_dataloader()))
    out1 = torchvision.utils.make_grid(image)
    #out2 = torchvision.utils.make_grid(masks)
    #imshow(out1)

    '''
    fig = plt.figure(figsize=(8, 8))
    for i, mask in enumerate(masks):
        fig.add_subplot(1, 4, 1)
        #plt.imshow(mask)
    #plt.show()
    '''
    '''
    img_w_msk = [
        draw_segmentation_masks(image, masks=masks, alpha=0.5)
        for image, masks in zip(image, masks)
    ]

    plt.imshow(img_w_msk)
    '''

    input_L_type_mask = '/Users/jiehyun/kaggle/input/hubmap-organ-segmentation/binary_masks/62.png'  # 'L' type mask
    #input_L_type_mask = '/Users/jiehyun/kaggle/input/hubmap-organ-segmentation/train_annotations/62.json'
    i_mask = Image.open(input_L_type_mask)
    i_mask.convert('P')
    palette = [0, 0, 0, 255, 160, 122, 240, 248, 255, 125, 252, 0, 255, 255, 0, 255, 192, 203]
    i_mask.putpalette(list(palette))  # convert to 'P' type mask
    #imshow(i_mask)
    plt.imshow(i_mask)
    plt.show()

    from pl_bolts.models.vision import UNet
    model = UNet(num_classes=6)
    print(model)

if __name__ == "__main__":
    main()
    