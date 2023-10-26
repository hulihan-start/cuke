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

__global__ void build_index(long * indices, long * uniq_idx, long * buf_idx, int * uniq_cnt){
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
    
    if (tid == 0) { count[ibuf[C-1]+1] = C; }
    else if (idx[tid] > idx[tid-1]) {
            count[ibuf[tid]] = tid; }
    iuniq[tid] = _REL_ID_;
    __syncthreads();

    // exceed threshold
    if (tid > 0 && count[tid]-count[tid-1]>T) {
        iuniq[tid-1] = idx[count[tid]-1]; }
    __syncthreads();

    bitonic_sort(iuniq, ord_uniq);

    int temp = ord_uniq[ibuf[tid]];
    if (iuniq[temp] < _REL_ID_){
        ibuf[tid] = temp;
    }else{
        ibuf[tid] = idx[tid] + C;
    }
    if (iuniq[tid] < _REL_ID_ && iuniq[tid+1] == _REL_ID_){
        uniq_cnt[blockIdx.x] = tid+1;
    }
    buf_idx[blockIdx.x * C + tid] = ibuf[ord[tid]];
    uniq_idx[blockIdx.x * C + tid] = iuniq[tid];
}