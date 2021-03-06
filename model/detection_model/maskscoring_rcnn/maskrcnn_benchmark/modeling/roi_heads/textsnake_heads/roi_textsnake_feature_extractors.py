# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
from torch import nn
from torch.nn import functional as F

from ..box_head.roi_box_feature_extractors import ResNet50Conv5ROIFeatureExtractor
from maskrcnn_benchmark.modeling.poolers import Pooler
from maskrcnn_benchmark.modeling.level_mapper import LevelMapper
from maskrcnn_benchmark.layers import Conv2d


class MaskRCNNFPNFeatureExtractor(nn.Module):
    """
    Heads for FPN for classification
    """

    def __init__(self, cfg):
        """
        Arguments:
            num_classes (int): number of output classes
            input_size (int): number of channels of the input once it's flattened
            representation_size (int): size of the intermediate representation
        """
        super(MaskRCNNFPNFeatureExtractor, self).__init__()

        resolution = cfg.MODEL.ROI_TEXTSNAKE_HEAD.POOLER_RESOLUTION
        scales = cfg.MODEL.ROI_TEXTSNAKE_HEAD.POOLER_SCALES
        sampling_ratio = cfg.MODEL.ROI_TEXTSNAKE_HEAD.POOLER_SAMPLING_RATIO
        pooler = Pooler(
            output_size=(resolution, resolution),
            scales=scales,
            sampling_ratio=sampling_ratio,
        )
        input_size = cfg.MODEL.BACKBONE.OUT_CHANNELS
        self.pooler = pooler

        layers = cfg.MODEL.ROI_TEXTSNAKE_HEAD.CONV_LAYERS

        next_feature = input_size
        self.blocks = []
        for layer_idx, layer_features in enumerate(layers, 1):
            layer_name = "mask_fcn{}".format(layer_idx)
            module = Conv2d(next_feature, layer_features, 3, stride=1, padding=1)
            # Caffe2 implementation uses MSRAFill, which in fact
            # corresponds to kaiming_normal_ in PyTorch
            nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
            nn.init.constant_(module.bias, 0)
            self.add_module(layer_name, module)
            next_feature = layer_features
            self.blocks.append(layer_name)

    def forward(self, x, proposals):
        x = self.pooler(x, proposals)
        roi_feature = x
        for layer_name in self.blocks:
            x = F.relu(getattr(self, layer_name)(x))
        return x, roi_feature


class TextsnakeFPNFeatureExtractor(nn.Module):
    """
    Heads for FPN for classification
    """

    def __init__(self, cfg):
        """
        Arguments:
            num_classes (int): number of output classes
            input_size (int): number of channels of the input once it's flattened
            representation_size (int): size of the intermediate representation
        """
        super(TextsnakeFPNFeatureExtractor, self).__init__()

        scales = cfg.MODEL.ROI_TEXTSNAKE_HEAD.POOLER_SCALES
        level_mapper = LevelMapper(scales=scales)
        input_size = cfg.MODEL.BACKBONE.OUT_CHANNELS
        self.level_mapper = level_mapper

        layers = cfg.MODEL.ROI_TEXTSNAKE_HEAD.CONV_LAYERS

        next_feature = input_size
        self.blocks = []
        for layer_idx, layer_features in enumerate(layers, 1):
            layer_name = "mask_fcn{}".format(layer_idx)
            module = Conv2d(next_feature, layer_features, 3, stride=1, padding=1)
            # Caffe2 implementation uses MSRAFill, which in fact
            # corresponds to kaiming_normal_ in PyTorch
            nn.init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
            nn.init.constant_(module.bias, 0)
            self.add_module(layer_name, module)
            next_feature = layer_features
            self.blocks.append(layer_name)

    def forward(self, x, proposals):
        crop_feature_list = self.level_mapper(x, proposals)
        roi_feature = crop_feature_list

        # Todo: maybe some extra convolutions needed here
        # for layer_name in self.blocks:
        #     x = F.relu(getattr(self, layer_name)(x))
        return crop_feature_list, roi_feature


_ROI_TEXTSNAKE_FEATURE_EXTRACTORS = {
    "ResNet50Conv5ROIFeatureExtractor": ResNet50Conv5ROIFeatureExtractor,
    "MaskRCNNFPNFeatureExtractor": MaskRCNNFPNFeatureExtractor,
    "TextsnakeFPNFeatureExtractor": TextsnakeFPNFeatureExtractor,
}


def make_roi_textsnake_feature_extractor(cfg):
    func = _ROI_TEXTSNAKE_FEATURE_EXTRACTORS[cfg.MODEL.ROI_TEXTSNAKE_HEAD.FEATURE_EXTRACTOR]
    return func(cfg)
