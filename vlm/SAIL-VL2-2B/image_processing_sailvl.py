"""Image processor class for KimiVL."""

import math
import numpy as np
from PIL import Image
from typing import Optional, Union

import torch

import torchvision.transforms as T
from torchvision.transforms.functional import InterpolationMode
from transformers.image_utils import ImageInput, make_list_of_images, valid_images
from transformers.image_processing_utils import BaseImageProcessor, BatchFeature
from transformers.utils import TensorType

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio


def dynamic_preprocess(image, min_num=1, max_num=6, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def dynamic_preprocess_msac1(image, min_num=1, max_num=6, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images, target_aspect_ratio

def dynamic_preprocess_msac2(image, min_num=1, max_num=6, image_size=448, use_thumbnail=False, prior_aspect_ratio=None):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    new_target_ratios = []
    if prior_aspect_ratio is not None:
        for i in target_ratios:
            if prior_aspect_ratio[0]%i[0] != 0 or prior_aspect_ratio[1]%i[1] != 0:
                new_target_ratios.append(i)
            else:
                continue

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, new_target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images


class SAILVLImageProcessor(BaseImageProcessor):
    model_type = "sailvl"

    def __init__(
        self,
        patch_size: int = 14,
        image_mean: tuple[float, float, float] = IMAGENET_MEAN,
        image_std: tuple[float, float, float] = IMAGENET_STD,
        max_dynamic_patch: int = 10,
        image_size: int = 448,
        use_msac: bool = False,

        **kwargs,
    ):
        super().__init__(**kwargs)
        self.patch_size = patch_size
        self.image_mean = image_mean
        self.image_std = image_std
        self.max_dynamic_patch = max_dynamic_patch
        self.image_size = image_size
        self.use_msac = use_msac
    
    def build_transform(self, input_size):
        MEAN, STD = self.image_mean, self.image_std
        transform = T.Compose([
            T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
            T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
            T.ToTensor(),
            T.Normalize(mean=MEAN, std=STD)
        ])
        return transform

    def load_image(self, image, input_size=448, max_num=6, upscale=False):
        # image = Image.open(image_file).convert('RGB')
        if upscale:
            image = image.resize((image.width * 2, image.height * 2), Image.BILINEAR)
        transform = self.build_transform(input_size=input_size)
        images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
        pixel_values = [transform(image) for image in images]
        pixel_values = torch.stack(pixel_values)
        return pixel_values
    
    def load_image_msac(self, image, input_size=448, max_num=6, upscale=False):
        # image = Image.open(image_file).convert('RGB')
        if upscale:
            image = image.resize((image.width * 2, image.height * 2), Image.BILINEAR)
        transform = self.build_transform(input_size=input_size)
        images,target_aspect_ratio = dynamic_preprocess_msac1(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
        images = images[:-1] + dynamic_preprocess_msac2(image,max_num=max_num,image_size=input_size,use_thumbnail=False,prior_aspect_ratio=target_aspect_ratio) + images[-1:]

        pixel_values = [transform(image) for image in images]
        pixel_values = torch.stack(pixel_values)
        return pixel_values

    def preprocess(
        self,
        images: ImageInput,
        return_tensors: Optional[Union[str, TensorType]] = None,
    ) -> BatchFeature:
        images = make_list_of_images(images)

        if not valid_images(images):
            raise ValueError(
                "Invalid image type. Must be of type PIL.Image.Image, numpy.ndarray, "
                "torch.Tensor, tf.Tensor or jax.ndarray."
            )
        # print('图片个数：',len(images))
        image_num = len(images)
        if image_num > 1:
            # image_path = [x['value'] for x in message if x['type'] == 'image']
            num_patches_list = []
            pixel_values_list = []
            for image_idx, image_pil in enumerate(images):
                upscale_flag = False
                curr_pixel_values = self.load_image(
                    image_pil, max_num=self.max_dynamic_patch, upscale=upscale_flag, input_size=self.image_size).cuda().to(torch.bfloat16)
                num_patches_list.append(curr_pixel_values.size(0))
                pixel_values_list.append(curr_pixel_values)
            pixel_values = torch.cat(pixel_values_list, dim=0)
            
        elif image_num == 1:
            # image_path = [x['value'] for x in message if x['type'] == 'image'][0]
            image_pil = images[0]
            upscale_flag = False
            if self.use_msac:
                pixel_values = self.load_image_msac(
                image_pil, max_num=self.max_dynamic_patch, upscale=upscale_flag, input_size=self.image_size).cuda().to(torch.bfloat16)
            else:
                pixel_values = self.load_image(
                    image_pil, max_num=self.max_dynamic_patch, upscale=upscale_flag, input_size=self.image_size).cuda().to(torch.bfloat16)
            num_patches_list = [pixel_values.size(0)]
        else:
            pixel_values = None
            num_patches_list = None

        # pixel_values, image_grid_hws = [], []
        # for image in images:
        #     patches, image_grid_hw = self._preprocess(image)
        #     pixel_values.append(patches)
        #     image_grid_hws.append(image_grid_hw)
        # pixel_values = torch.concat(pixel_values, dim=0)
        # image_grid_hws = np.array(image_grid_hws)
        data = {"pixel_values": pixel_values, "num_patches_list": num_patches_list}

        return BatchFeature(data=data, tensor_type=return_tensors)