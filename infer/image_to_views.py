# Open Source Model Licensed under the Apache License Version 2.0 and Other Licenses of the Third-Party Components therein:
# The below Model in this distribution may have been modified by THL A29 Limited ("Tencent Modifications"). All Tencent Modifications are Copyright (C) 2024 THL A29 Limited.

# Copyright (C) 2024 THL A29 Limited, a Tencent company.  All rights reserved. 
# The below software and/or models in this distribution may have been 
# modified by THL A29 Limited ("Tencent Modifications"). 
# All Tencent Modifications are Copyright (C) THL A29 Limited.

# Hunyuan 3D is licensed under the TENCENT HUNYUAN NON-COMMERCIAL LICENSE AGREEMENT 
# except for the third-party components listed below. 
# Hunyuan 3D does not impose any additional limitations beyond what is outlined 
# in the repsective licenses of these third-party components. 
# Users must comply with all terms and conditions of original licenses of these third-party 
# components and must ensure that the usage of the third party components adheres to 
# all relevant laws and regulations. 

# For avoidance of doubts, Hunyuan 3D means the large language models and 
# their software and algorithms, including trained model weights, parameters (including 
# optimizer states), machine-learning model code, inference-enabling code, training-enabling code, 
# fine-tuning enabling code and other elements of the foregoing made publicly available 
# by Tencent in accordance with TENCENT HUNYUAN COMMUNITY LICENSE AGREEMENT.

import os
import time
import torch
import random
import numpy as np
from PIL import Image
from einops import rearrange
from PIL import Image, ImageSequence

from .utils import seed_everything, timing_decorator, auto_amp_inference
from .utils import get_parameter_number, set_parameter_grad_false
from mvd.hunyuan3d_mvd_std_pipeline import HunYuan3D_MVD_Std_Pipeline
from mvd.hunyuan3d_mvd_lite_pipeline import Hunyuan3d_MVD_Lite_Pipeline

import os
import folder_paths

comfy_path = os.path.dirname(folder_paths.__file__)

hunyuan3d_path = f'{comfy_path}/custom_nodes/ComfyUI-Hunyuan3D-1-wrapper'

def save_gif(pils, save_path, df=False):
    # save a list of PIL.Image to gif
    spf = 4000 / len(pils)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    pils[0].save(save_path, format="GIF", save_all=True, append_images=pils[1:], duration=spf, loop=0)
    return save_path
    

class Image2Views():
    def __init__(self, pipeline_config):
        """
        接收pipeline配置初始化Image2Views
        Args:
            pipeline_config: 从ImageToViewsPipelineLoad获取的配置字典
        """
        self.pipe = pipeline_config.get_pipeline_config()['pipe']
        self.device = pipeline_config.get_pipeline_config()['device']
        self.order = pipeline_config.get_pipeline_config()['order']
        
    @torch.no_grad()
    @timing_decorator("image to views")
    @auto_amp_inference
    def __call__(self, pil_img, seed=0, steps=50, guidance_scale=2.0, guidance_curve=lambda t:2.0):
        seed_everything(seed)
        generator = torch.Generator(device=self.device)
        res_img = self.pipe(pil_img, 
                            num_inference_steps=steps,
                            guidance_scale=guidance_scale, 
                            guidance_curve=guidance_curve, 
                            generat=generator).images
        show_image = rearrange(np.asarray(res_img[0], dtype=np.uint8), '(n h) (m w) c -> (n m) h w c', n=3, m=2)
        pils = [res_img[1]]+[Image.fromarray(show_image[idx]) for idx in self.order] 
        torch.cuda.empty_cache()
        return res_img, pils
        