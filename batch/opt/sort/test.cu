#include <stdio.h>
#include<iostream>
#include <thrust/device_vector.h>
#include <cuda_runtime.h>
using namespace std;

#define BLOCK_SIZE 256
#define C 16
#define T 2


__device__ void swap(long& a, long& b, long& a_idx, long& b_idx) {
    int tmp = a;
    a = b;
    b = tmp;
    tmp = a_idx;
    a_idx = b_idx;
    b_idx = tmp;
}

__device__ void bitonic_sort(long* arr, long* ord) {
    __shared__ long shared_arr[C];
    __shared__ long shared_ord[C];

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

__global__ void build_index(long * indices, long * uniq_idx, long * buf_idx, long * uniq_cnt){
    __shared__ long idx[C], ord[C], ibuf[C], iuniq[C], count[C], ord_uniq[C];
    int tid = threadIdx.x;
    idx[tid] = indices[blockIdx.x * C + tid];
    ord[tid] = tid;
    ord_uniq[tid] = tid;
    count[tid] = 0;
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
    
    // buf_idx[blockIdx.x * C + tid] = ibuf[ord[tid]];
    if (tid == 0) { count[ibuf[C-1]+1] = C; }
    else if (idx[tid] > idx[tid-1]) {
            count[ibuf[tid]] = tid; }
    iuniq[tid] = 999;
    __syncthreads();

    // exceed threshold
    if (tid > 0 && count[tid]-count[tid-1]>T) {
        iuniq[tid-1] = idx[count[tid]-1]; }
    __syncthreads();

    bitonic_sort(iuniq, ord_uniq);

    int temp = ord_uniq[ibuf[tid]];
    // if(threadIdx.x == 0 && blockIdx.x == 0){
    //     for(int i=0;i<C;i++){
    //         printf("%d ", iuniq[i]);
    //     }
    // }
    if (iuniq[temp] < 999){
        ibuf[tid] = temp;
    }else{
        ibuf[tid] = idx[tid] + C;
    }
    if (iuniq[tid] < 999 && iuniq[tid+1] == 999){
        uniq_cnt[blockIdx.x] = tid+1;
    }
    buf_idx[blockIdx.x * C + tid] = ibuf[ord[tid]];
    uniq_idx[blockIdx.x * C + tid] = iuniq[tid];
}


int main() {
    // long data[64] = { 2, 5, 5, 3, 1, 2, 5, 3, 1, 3, 5, 5, 3, 4, 5, 3, 5, 4, 2, 2, 5, 5, 1, 3, 5, 5, 3, 1, 4, 5, 5, 2, 1, 5, 2, 5, 7, 5, 5, 4, 5, 4, 6, 6, 4, 3, 4, 2, 2, 2, 3, 4, 7, 2, 1, 3, 1, 3, 1, 1, 4, 5, 2, 1};
    // long data[256] = {
    //     42, 41, 42, 42, 42, 42, 30, 50, 20,  1, 43, 18,  0, 17, 42, 42, 
    //     42, 40, 14, 44, 19, 41, 41, 42, 23, 17,  8, 46, 42, 43, 46, 19, 
    //     38, 43, 17, 50, 42, 42, 42, 46, 43, 42, 43, 45, 33, 43, 43, 42, 
    //      6, 49,  5, 13, 43, 42, 45, 43,  3, 43, 42, 42, 42, 43, 43, 45, 
    //     41, 36, 39, 50, 41, 42, 43, 45, 10, 44, 42, 19, 42, 42, 45, 42, 
    //     42,  6, 42, 14, 46, 19, 42,  0, 22, 42, 45, 40, 43, 43,  0, 43, 
    //     45, 45, 42, 38, 13, 45, 42, 30, 45, 46, 50, 46, 43, 45, 43, 42,
    //     42, 43, 42, 43, 50, 41, 42, 50, 43, 43, 42, 23, 42, 46, 50, 50, 
    //     43, 42, 34, 50, 22, 43, 46, 42, 42, 42, 46, 43, 42, 42, 45, 42, 
    //     42, 43, 43, 43, 31, 38, 43, 13, 43, 43, 43, 42,  4,  0, 50, 18, 
    //     50, 43, 43, 45, 42, 46, 44, 42, 48, 42, 42, 43, 22, 42, 42, 45, 
    //     42, 43, 42, 43, 42, 45, 22, 30, 42, 41, 50, 41,  2, 45, 42, 42, 
    //     42, 43,  5, 43, 43, 50, 38, 42, 11, 46, 43, 43,  8, 50, 45, 48, 
    //     40, 42, 42, 50, 46, 42, 42, 22, 46, 46, 50,  6, 14, 42, 11, 43,
    //     42, 35, 42, 43, 45, 13, 42, 42, 43, 42, 43, 45, 42, 42, 41, 43, 
    //     42, 14, 31, 42,  2, 42, 38, 43, 42,  2, 42, 19, 31, 42, 40, 43
    // };
    long data[512] = {0,  0,  0,  0,  0,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  2,  3,  3,  3,  4,  4,  4,  5,  5,  5,  5,
         5,  5,  5,  5,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  6,  7,  8,  8,  8, 10, 10, 10, 10,
        11, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 13, 13, 13, 13, 14, 14, 14, 14, 14, 14, 14, 14, 14,
        18, 18, 18, 18, 18, 19, 19, 19, 19, 19, 19, 19, 22, 22, 22, 22, 22, 22, 22, 22, 22, 22, 23, 23, 23, 23, 23, 28,
        30, 31, 31, 31, 31, 31, 31, 31, 31, 31, 33, 33, 33, 33, 35, 35, 35, 36, 37, 37, 38, 38, 38, 38, 38, 39, 39, 39,
        39, 39, 39, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41, 41,
        41, 41, 41, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42,
        42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42,
        42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42,
        42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42,
        42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42, 42,
        42, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43,
        43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43,
        43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43, 43,
        44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 44, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45,
        45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 45, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46,
        46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 46, 47, 48, 48, 48, 48, 50, 50, 50, 50, 50, 50,
        50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50, 50,
        50, 50, 50, 50, 50, 50, 50, 50};
    int n = sizeof(data) / sizeof(data[0]);
    printf("%d\n", n);
    long  *uniq_idx=(long*)malloc(sizeof(long) * n), *buf_idx=(long*)malloc(sizeof(long) * n);
    

    long *d_data, *d_uniq_idx, *d_buf_idx, *d_uniq_cnt, *uniq_cnt=(long*)malloc(sizeof(long) * n/C);
    cudaMalloc(&d_data, n * sizeof(long));
    cudaMalloc(&d_uniq_idx, n * sizeof(long));
    cudaMalloc(&d_buf_idx, n * sizeof(long));

    cudaMalloc(&d_uniq_cnt, n * sizeof(long));

    cudaMemcpy(d_data, data, n * sizeof(long), cudaMemcpyHostToDevice);


    build_index<<< n/C, C>>>(d_data, d_uniq_idx, d_buf_idx, d_uniq_cnt);

    // print result
    // for (int i = 0; i < n; i++) {
    //     printf("%d ", data[i]);
    // }
    // printf("\n%d\n", n);

    cudaMemcpy(uniq_idx, d_uniq_idx, n*sizeof(long), cudaMemcpyDeviceToHost);
    cudaMemcpy(buf_idx, d_buf_idx, n*sizeof(long), cudaMemcpyDeviceToHost);
    cudaMemcpy(uniq_cnt, d_uniq_cnt, n/C*sizeof(long), cudaMemcpyDeviceToHost);
    printf("unique idx:\n");
    for(int i=0;i<n;++i){
        if(i%C == 0){
            printf("\n");
        }
        // printf("%d,%d ", uniq_idx[i], buf_idx[i]);
        printf("%ld ", uniq_idx[i]);
    }
    printf("buffer idx:\n");
    for(int i=0;i<n;++i){
        if(i%C == 0){
            printf("\n");
        }
        // printf("%d,%d ", uniq_idx[i], buf_idx[i]);
        printf("%ld ", buf_idx[i]);
    }
    printf("\n");
    for(int i=0;i<n/C;++i){
        printf("%ld ", uniq_cnt[i]);
    }
    return 0;
}