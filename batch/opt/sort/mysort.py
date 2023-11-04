
import torch
from torch.utils.cpp_extension import load

sort_func = load(name='sort', sources=['sort.cu'])

class build_index(torch.autograd.Function):
    @staticmethod
    def forward(ctx, head, tail, relation, r_uniq, r_buffer, uniq_cnt, n, gs, rel_num):
        sort_func.gpu_sort(head, tail, relation, r_uniq, r_buffer, uniq_cnt, n, gs, rel_num)
        return head, tail, relation

    @staticmethod
    def backward(ctx):
        pass


index_building = build_index.apply