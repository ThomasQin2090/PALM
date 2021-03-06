# -*- coding: UTF-8 -*-
#   Copyright (c) 2019 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from paddlepalm.interface import reader
from paddlepalm.reader.utils.reader4ernie import MaskLMReader
import numpy as np

class Reader(reader):
    
    def __init__(self, config, phase='train', dev_count=1, print_prefix=''):
        """
        Args:
            phase: train, eval, pred
            """

        self._is_training = phase == 'train'

        reader = MaskLMReader(config['vocab_path'],
            max_seq_len=config['max_seq_len'],
            do_lower_case=config.get('do_lower_case', False),
            for_cn=config.get('for_cn', False),
            random_seed=config.get('seed', None))
        self._reader = reader
        self._dev_count = dev_count

        self._batch_size = config['batch_size']
        self._max_seq_len = config['max_seq_len']
        if phase == 'train':
            self._input_file = config['train_file']
            self._num_epochs = None # 防止iteartor终止
            self._shuffle = config.get('shuffle', True)
            self._shuffle_buffer = config.get('shuffle_buffer', 5000)
        elif phase == 'eval':
            self._input_file = config['dev_file']
            self._num_epochs = 1
            self._shuffle = False
            self._batch_size = config.get('pred_batch_size', self._batch_size)
        elif phase == 'pred':
            self._input_file = config['pred_file']
            self._num_epochs = 1
            self._shuffle = False
            self._batch_size = config.get('pred_batch_size', self._batch_size)

        self._phase = phase
        # self._batch_size = 
        self._print_first_n = config.get('print_first_n', 1)


    @property
    def outputs_attr(self):
        return {"token_ids": [[-1, -1], 'int64'],
                "position_ids": [[-1, -1], 'int64'],
                "segment_ids": [[-1, -1], 'int64'],
                "input_mask": [[-1, -1, 1], 'float32'],
                "task_ids": [[-1, -1], 'int64'],
                "mask_label": [[-1], 'int64'],
                "mask_pos": [[-1], 'int64'],
                }


    def load_data(self):
        self._data_generator = self._reader.data_generator(self._input_file, self._batch_size, self._num_epochs, dev_count=self._dev_count, shuffle=self._shuffle, phase=self._phase)

    def iterator(self): 

        def list_to_dict(x):
            names = ['token_ids', 'position_ids', 'segment_ids', 'input_mask', 
                'task_ids', 'mask_label', 'mask_pos']
            outputs = {n: i for n,i in zip(names, x)}
            # outputs['batchsize_x_seqlen'] = [self._batch_size * len(outputs['token_ids'][0]) - 1]
            return outputs

        for batch in self._data_generator():
            # print(np.shape(list_to_dict(batch)['token_ids']))
            # print(list_to_dict(batch)['mask_label'].tolist())
            yield list_to_dict(batch)

    def get_epoch_outputs(self):
        return {'examples': self._reader.get_examples(self._phase),
                'features': self._reader.get_features(self._phase)}

    @property
    def num_examples(self):
        return self._reader.get_num_examples(phase=self._phase)

