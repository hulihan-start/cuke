#include <stdio.h>
#include <iostream>
#include <thrust/device_vector.h>
#include <cuda_runtime.h>
#include <torch/extension.h>
#include <torch/torch.h>
using namespace std;

#define BLOCK_SIZE 256
#define C 16
#define T 3
#define DIV(x, ts) ((x) % (ts) != 0 ? (x) / (ts) + 1 : (x) / (ts))

__device__ void swap(int& a, int& b, int& a_idx, int& b_idx) {
    int tmp = a;
    a = b;
    b = tmp;
    tmp = a_idx;
    a_idx = b_idx;
    b_idx = tmp;
}

__device__ void bitonic_sort(int* arr, int* ord) {
    __shared__ int shared_arr[C];
    __shared__ int shared_ord[C];

    int tid = threadIdx.x;
    shared_arr[tid] = arr[tid];
    shared_ord[tid] = tid;
    __syncthreads();

    for (int k = 2; k <= C; k <<= 1) {
        for (int j = k >> 1; j > 0; j >>= 1) {
            __syncthreads();
            int ixj = tid ^ j;
            if (ixj > tid) {
                if ((tid & k) == 0 && shared_arr[tid] > shared_arr[ixj])
                    swap(shared_arr[tid], shared_arr[ixj], shared_ord[tid], shared_ord[ixj]);
                if ((tid & k) != 0 && shared_arr[tid] < shared_arr[ixj])
                    swap(shared_arr[tid], shared_arr[ixj], shared_ord[tid], shared_ord[ixj]);
            }
        }
    }

    __syncthreads();
    arr[tid] = shared_arr[tid];
    ord[shared_ord[tid]] = tid;
}

__global__ void build_index(torch::PackedTensorAccessor32<int, 1, torch::RestrictPtrTraits> indices, torch::PackedTensorAccessor32<int, 2, torch::RestrictPtrTraits> r_Uniq, torch::PackedTensorAccessor32<int, 2, torch::RestrictPtrTraits> r_Buffer, torch::PackedTensorAccessor32<int, 1, torch::RestrictPtrTraits> uniq_cnt, int rel_num){
    __shared__ int idx[C], ord[C], ibuf[C], iuniq[C], pcount[C], ord_uniq[C];
    int tid = threadIdx.x;
    idx[tid] = indices[blockIdx.x * C + tid];
    ord[tid] = tid;
    ord_uniq[tid] = tid;
    pcount[tid] = 0;
    __syncthreads();

    bitonic_sort(idx, ord);
    ibuf[tid] = (tid > 0 && idx[tid] > idx[tid-1]) ? 1:0;
    __syncthreads();
    
    for (int offset = 1; offset < C; offset *= 2) {
        __syncthreads();
        if (tid >= offset) {
            ibuf[tid] += ibuf[tid - offset];
        }
    }
    
    if (tid == 0) { pcount[ibuf[C-1]+1] = C; }
    else if (idx[tid] > idx[tid-1]) {
            pcount[ibuf[tid]] = tid; }
    iuniq[tid] = rel_num;
    __syncthreads();

    // exceed threshold
    if (tid > 0 && pcount[tid]-pcount[tid-1]>T) {
        iuniq[tid-1] = idx[pcount[tid]-1]; }
    __syncthreads();

    bitonic_sort(iuniq, ord_uniq);

    int temp = ord_uniq[ibuf[tid]];
    if (iuniq[temp] < rel_num){
        ibuf[tid] = temp;
    }else{
        ibuf[tid] = idx[tid] + C;
    }
    if (iuniq[tid] < rel_num && iuniq[tid+1] == rel_num){
        uniq_cnt[blockIdx.x] = tid+1;
    }
    r_Buffer[blockIdx.x][tid] = ibuf[ord[tid]];
    r_Uniq[blockIdx.x][tid] = iuniq[tid];
}


void gpu_sort(torch::Tensor head, torch::Tensor tail, torch::Tensor relation, torch::Tensor r_Uniq, torch::Tensor r_Buffer, torch::Tensor uniq_cnt, int batch, int group_size, int rel_num) {
    // int batch=4096;
    dim3 nblocks(DIV(batch, C));
    dim3 nthreads(32, C);

    torch::Tensor sorted_indices = torch::argsort(relation);
    std::cout << "Original Head: " << relation << std::endl;

    head = torch::index_select(head, 0, sorted_indices);
    tail = torch::index_select(tail, 0, sorted_indices);
    relation = torch::index_select(relation, 0, sorted_indices);

    
    std::cout << "Sorted Head: " << relation << std::endl;

    build_index<<< batch/C, C>>>(relation.packed_accessor32<int, 1, torch::RestrictPtrTraits>(), r_Uniq.packed_accessor32<int, 2, torch::RestrictPtrTraits>(), r_Buffer.packed_accessor32<int, 2, torch::RestrictPtrTraits>(), uniq_cnt.packed_accessor32<int, 1, torch::RestrictPtrTraits>(), rel_num);

    std::cout << "uniq: " << r_Uniq << std::endl;
    std::cout << "buffer: " << r_Buffer << std::endl;
    std::cout << "uniq_cnt: " << uniq_cnt << std::endl;
}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("gpu_sort", &gpu_sort, "ss");
}