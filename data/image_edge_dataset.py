import os

from PIL import Image

from data.base_dataset import BaseDataset, get_transform
from data.image_folder import ImageFolder


class ImageEdgeDataset(BaseDataset):

    def __init__(self, opt):
        super(ImageEdgeDataset, self).__init__(opt)
        self.image_paths = ImageFolder(os.path.join(self.root, opt.path_image))  # image path list
        self.edge_paths = ImageFolder(os.path.join(self.root, opt.path_edge))  # edge path list
        assert len(self.image_paths) == len(self.edge_paths)

        self.transform = get_transform()

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, item):
        image_pil = Image.open(self.image_paths[item]).convert("RGB")
        edge_pil = Image.open(self.edge_paths[item]).convert("RGB")

        image_tensor = self.transform(image_pil)
        edge_tensor = self.transform(edge_pil)

        return {"image": image_tensor, "edge": edge_tensor}
