'''
环境模块
包含对实验环境的操作，例如初始化随机数种子
'''

import os
import shutil
import numpy as np
import torch
import random
import torch.backends.cudnn as cudnn
import argparse
from config.config import get_cfg_defaults
from yacs.config import CfgNode as CN

class Env(object):

    def __init__(self):
        '''
        进行一系列初始化之后，将命令行参数给的配置文件读出来，交予类变量self
        '''

        self.opt = self.readCommand()
        self.seedInit()
        self.setVisibleGpu()
        self.setCudnnBenchmark()
        self.checkAddressExist()

    def seedInit(self):
        '''
        随机数种子初始化
        '''
        manualSeed = random.randint(1, 10000)

        np.random.seed(manualSeed)
        random.seed(manualSeed)
        torch.manual_seed(manualSeed)

    def setCudnnBenchmark(self):
        '''
        设置cudnn.benchmark
        '''
        cudnn.benchmark = True

    def readCommand(self):
        '''
        读取命令行参数
        将读取到的配置文件交给config读取模块
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument('--config_file', required=True, help='path to config file')
        arg = parser.parse_args()
        # print("Parameters CONFIG_FILE: ", arg.config_file)

        # cfg = get_cfg_defaults()
        # cfg.merge_from_file(arg.config_file)
        # cfg.freeze()
        # return cfg

        opt = self.read_config_file(arg.config_file)
        return opt


    def read_config_file(self,config_file):
        # 用yaml重构配置文件
        f = open(config_file)
        opt = CN.load_cfg(f)
        return opt

    def getOpt(self):
        '''
        返回解析好的配置文件opt
        '''
        return self.opt

    def setVisibleGpu(self):
        '''
        设置可用gpu编号
        '''
        num_gpu = self.opt.BASE.NUM_GPUS
        gpu_list = [str(i) for i in self.opt.BASE.GPU_ID]
        os.environ["CUDA_VISIBLE_DEVICES"] = ','.join(gpu_list[:num_gpu])

    def checkAddressExist(self):
        '''
        检查路径是否存在
        路径分为两类：
        1.指定了就一定要存在：例如数据集文件夹
        2.指定了并不一定要存在，如果不存在即由程序创建：例如checkpoint
        '''

        def folderExist(key,value):
            '''
            对于必须存在的路径的检查
            如果是空value，则不需要考虑
            '''
            if value == '':
                return

            if os.path.exists(value):
                pass
            else:
                assert False, "Address " + key + " : " + value + ' doesn\'t exist!'

        def createFolder(rootList, removeOrigin=False):
            '''
            对于不必要存在的路径，将由程序处理
            removeOrigin用于判断是否删除原有文件
            TODO 从参数文件中解析出Address部分
            '''

            if isinstance(rootList, str):
                '''
                不考虑空字符串
                '''
                if rootList == '':
                    return
                rootList = [rootList]

            if removeOrigin == True:
                for root in rootList:
                    if os.path.exists(root):
                        shutil.rmtree(root)
                    os.makedirs(root)
            else:
                for root in rootList:
                    if os.path.exists(root):
                        print('Path always exists: ', root)
                    else:
                        print('Make folder: ' , root)
                        os.makedirs(root)

        model_type = self.opt.BASE.TYPE
        if model_type == 'D':
            '''检测模型'''
            folderExist('opt.ADDRESS.DETECTION.TRAIN_DATA_DIR', self.opt.ADDRESS.DETECTION.TRAIN_DATA_DIR)
            folderExist('opt.ADDRESS.DETECTION.TRAIN_GT_DIR', self.opt.ADDRESS.DETECTION.TRAIN_GT_DIR)
            folderExist('opt.ADDRESS.DETECTION.TEST_DATA_DIR', self.opt.ADDRESS.DETECTION.TEST_DATA_DIR)
            folderExist('opt.ADDRESS.DETECTION.TEST_GT_DIR', self.opt.ADDRESS.DETECTION.TEST_GT_DIR)
            folderExist('opt.ADDRESS.DETECTION.VAL_DATA_DIR', self.opt.ADDRESS.DETECTION.VAL_DATA_DIR)
            folderExist('opt.ADDRESS.DETECTION.VAL_GT_DIR', self.opt.ADDRESS.DETECTION.VAL_GT_DIR)
        elif model_type == 'R':
            '''识别模型'''
            folderExist('opt.ADDRESS.RECOGNITION.TRAIN_DATA_DIR', self.opt.ADDRESS.RECOGNITION.TRAIN_DATA_DIR)
            folderExist('opt.ADDRESS.RECOGNITION.TRAIN_LABEL_DIR', self.opt.ADDRESS.RECOGNITION.TRAIN_LABEL_DIR)
            folderExist('opt.ADDRESS.RECOGNITION.TEST_DATA_DIR', self.opt.ADDRESS.RECOGNITION.TEST_DATA_DIR)
            folderExist('opt.ADDRESS.RECOGNITION.TEST_LABEL_DIR', self.opt.ADDRESS.RECOGNITION.TEST_LABEL_DIR)
            folderExist('opt.ADDRESS.RECOGNITION.VAL_DATA_DIR', self.opt.ADDRESS.RECOGNITION.VAL_DATA_DIR)
            folderExist('opt.ADDRESS.RECOGNITION.VAL_LABEL_DIR', self.opt.ADDRESS.RECOGNITION.VAL_LABEL_DIR)

        folderExist('opt.ADDRESS.RECOGNITION.ALPHABET', self.opt.ADDRESS.RECOGNITION.ALPHABET)


        createFolder(self.opt.ADDRESS.CHECKPOINTS_DIR)
        createFolder(self.opt.ADDRESS.CACHE_DIR)
        createFolder(self.opt.ADDRESS.LOGGER_DIR)


