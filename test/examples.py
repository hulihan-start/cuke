from core.ast2ir import *
import run
import helpers
import codegen
import torch




def f18():
    A = Tensor('A', (100, 20))
    B = Tensor('B', (100, 20))
    b1 = Var('b1')
    b2 = Var('b2')

    return A[b1:b2][2:4] + B[b1:b2][2:4]

def test19():
    A = Tensor('A', (100, 20))
    B = Tensor('B', (100, 20))
    b1 = Var('b1')
    b2 = Var('b2')

    ast = A[:][b1:b2] + B[:][b1:b2]
    print(helpers.get_input_nodes(ast))
    ir = gen_ir(ast)

    code = codegen.cpu.print_cpp(ir)
    A = torch.rand(100, 20)
    B = torch.rand(100, 20)
    b1 = 4
    b2 = 5
    d = run.cpu.compile_and_run(code, b2, b1, A, B)

    print(A[:, b1:b2] + B[:, b1:b2])
    print(torch.equal(A[:, b1:b2] + B[:, b1:b2], d))



def test20():
    d = Var('d')
    A = Tensor('A', (100, 20, d))
    B = Tensor('B', (100, 20, d))
    b1 = Var('b1')
    b2 = Var('b2')
    idx = Tensor('idx', (5, ), dtype='int')

    ast = A[:][idx][b1:b2] + B[:][idx][b1:b2]
    print(helpers.get_input_nodes(ast))
    ir = gen_ir(ast)

    code = codegen.cpu.print_cpp(ir)
    d = 7
    A = torch.rand(100, 20, d)
    B = torch.rand(100, 20, d)
    b1 = 4
    b2 = 5
    idx = torch.IntTensor(5)

    d = run.cpu.compile_and_run(code, b2, b1, d, A, idx, B)

    print(A[:, idx][:, :, b1:b2] + B[:, idx][:, :, b1:b2])
    print(torch.equal(A[:, idx][:, :, b1:b2] + B[:, idx][:, :, b1:b2], d))



def f21():
    d = Var('d')
    A = Tensor('A', (100, 20, d))
    B = Tensor('B', (50, 100, d+d))
    b1 = Var('b1')
    b2 = Var('b2')
    idx = Tensor('idx', (5, ), dtype='int')

    return A[3:0:-1][idx][b1:b2] + B[3:0:-1][idx][b1:b2]



def f30():
    d1 = Var('d1')
    d2 = Var('d2')
    T = Tensor('T', size=(10, d1, d2))
    A = Set(T)
    B = Set([1,2,3,4])

    return A.num_elem() + B.num_elem()


def f31():
    d1 = Var('d1')
    d2 = Var('d2')
    T = Tensor('T', size=(10, d1, d2))
    A = Set(T)

    return A


def f32():
    T = Tensor('T', val=[1,2,3,4])
    A = Set(T)

    return A


def f33():
    x = Var('x')
    A = Set(x)

    return A.num_elem() + Set([1,2,3,4]).num_elem()

def f34():
    x = Var('x')
    A = Set(x)

    return A

def f35():
    T = Tensor('T', size=(100, ))
    A = Set(T[20:40])

    return A

def f36():
    T = Tensor('T', size=(100, ))
    A = Set(T[20:40])
    d = Var('d')

    return A.num_elem() + Set(T[40:]).num_elem() + Set(T[1:d]).num_elem()


def compression():
    input = Tensor('input', (1024, ))
    input = input.reshape((32, 33))
    x = (input * 1000).round()
    y = x.apply(lambda y:y[1:31]-y[0:30], axis=0)
    res = y.encoding()

    ir = gen_ir(res)
    code = codegen.cpu.print_cpp(ir)
    code = codegen.cerebra.print_code(ir)
    print(code)


def conv1d_v1():
    A = Tensor('a', (100, ))
    ast = A[0:97] + A[1:98] + A[2:99]
    ir = gen_ir(ast)
    print(helpers.get_input_nodes(ir))
    code = codegen.cpu.print_cpp(ir)
    print(code)

def conv1d_v2(width):
    A = Tensor('a', (100, ))
    res = Zeros(A[width:]._size())
    for i in range(width):
        res = res + A[i:i+97]
    ir = gen_ir(res)
    print(helpers.get_input_nodes(ir))
    code = codegen.cpu.print_cpp(ir)
    print(code)

import numpy as np
from cset.ast2ir import *
def subgraph_matching_test_code():

    pattern_size = 4

    num_node = 10
    num_edges = 20

    rowptr = Tensor('rowptr', (num_node+1,), dtype='int')
    colidx = Tensor('colidx', (num_edges,), dtype='int')
    edge_list =  Set(Tensor('edge_list', (num_edges, 2), dtype='int'))

    count = Zero(dtype='int')

    class inner_subgraph_matching:
        def __init__(self, level, *path):
             self.level = level
             self.path = list(*path)

        def __call__(self, item):

            if self.level == pattern_size-1:
                return  count+1

            if self.level==1:
                v0_nb =  Set(colidx[rowptr[item[0]]:rowptr[item[0]+1]])
                v1_nb =  Set(colidx[rowptr[item[1]]:rowptr[item[1]+1]])
                candidate_set = v0_nb.intersect(v1_nb)
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, [item[0], item[1]]))
            else:
                candidate_set = Set(colidx[rowptr[item]:rowptr[item+1]])
                candidate_set = candidate_set.filter(SmallerThan(self.path[-1]))
                for v in self.path:
                    v_nb =  Set(colidx[rowptr[v]:rowptr[v+1]])
                    candidate_set = candidate_set.intersect(v_nb)
    
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, self.path + [item]))
    
    res = edge_list.applyfunc(inner_subgraph_matching(1))
    code = codegen.cpu.print_cpp(res._gen_ir())
    print(code)


def triangle_counting():
    np_rowptr = np.fromfile("../MiCo/snap.txt.vertex.bin", dtype=np.int64)
    np_colidx = np.fromfile("../MiCo/snap.txt.edge.bin", dtype=np.int32)

    torch_rowptr = torch.from_numpy(np_rowptr, ).to(torch.int32)
    torch_colidx =torch.from_numpy(np_colidx)
    torch_edge_list = torch.zeros([torch_colidx.shape[0], 2], dtype=torch.int32)

    edge_idx = 0
    for i in range(0, torch_rowptr.shape[0]-1):
        for j in range(torch_rowptr[i].item() , torch_rowptr[i+1].item()):
            if(torch_colidx[j]<i):
                torch_edge_list[edge_idx][0] = i
                torch_edge_list[edge_idx][1] = torch_colidx[j]
                edge_idx = edge_idx+1

    #Cuke
    pattern_size = 3

    num_node = torch_rowptr.shape[0]-1
    num_edges = torch_colidx.shape[0]

    rowptr = Tensor('rowptr', (num_node+1,), dtype='int')
    colidx = Tensor('colidx', (num_edges,), dtype='int')
    edge_list =  Set(Tensor('edge_list', (int(num_edges/2), 2), dtype='int'))

    count = Zero(dtype='int')

    class inner_subgraph_matching:
        def __init__(self, level, *path):
             self.level = level
             self.path = list(*path)

        def __call__(self, item):

            if self.level == pattern_size-1:
                return Set(count).addone()

            if self.level==1:
                v0_nb =  Set(colidx[rowptr[item[0]]:rowptr[item[0]+1]])
                v1_nb =  Set(colidx[rowptr[item[1]]:rowptr[item[1]+1]])
                candidate_set = v0_nb.filter(SmallerThan(item[1])).intersect(v1_nb)
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, [item[0], item[1]]))
            else:
                candidate_set = Set(colidx[rowptr[item]:rowptr[item+1]])
                candidate_set = candidate_set.filter(SmallerThan(item))
                for v in self.path:
                    v_nb =  Set(colidx[rowptr[v]:rowptr[v+1]])
                    candidate_set = candidate_set.intersect(v_nb)
    
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, self.path + [item]))
    
    res = edge_list.applyfunc(inner_subgraph_matching(1)).ret_val(count)
    code = codegen.cpu.print_cpp(res._gen_ir())
    print(code)
    d = run.cpu.compile_and_run(code, torch_edge_list, torch_rowptr, torch_colidx)
    print(d)



def clique4():
    np_rowptr = np.fromfile("../MiCo/snap.txt.vertex.bin", dtype=np.int64)
    np_colidx = np.fromfile("../MiCo/snap.txt.edge.bin", dtype=np.int32)

    torch_rowptr = torch.from_numpy(np_rowptr, ).to(torch.int32)
    torch_colidx =torch.from_numpy(np_colidx)
    torch_edge_list = torch.zeros([torch_colidx.shape[0], 2], dtype=torch.int32)

    edge_idx = 0
    for i in range(0, torch_rowptr.shape[0]-1):
        for j in range(torch_rowptr[i].item() , torch_rowptr[i+1].item()):
            if(torch_colidx[j]<i):
                torch_edge_list[edge_idx][0] = i
                torch_edge_list[edge_idx][1] = torch_colidx[j]
                edge_idx = edge_idx+1

    #Cuke
    pattern_size = 4

    num_node = torch_rowptr.shape[0]-1
    num_edges = torch_colidx.shape[0]

    rowptr = Tensor('rowptr', (num_node+1,), dtype='int')
    colidx = Tensor('colidx', (num_edges,), dtype='int')
    edge_list =  Set(Tensor('edge_list', (int(num_edges/2), 2), dtype='int'))

    count = Zero(dtype='int')

    class inner_subgraph_matching:
        def __init__(self, level, *path):
             self.level = level
             self.path = list(*path)

        def __call__(self, item):

            if self.level == pattern_size-1:
                return Set(count).addone()

            if self.level==1:
                v0_nb =  Set(colidx[rowptr[item[0]]:rowptr[item[0]+1]])
                v1_nb =  Set(colidx[rowptr[item[1]]:rowptr[item[1]+1]])
                candidate_set = v0_nb.filter(SmallerThan(item[1])).intersect(v1_nb)
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, [item[0], item[1]]))
            else:
                candidate_set = Set(colidx[rowptr[item]:rowptr[item+1]])
                candidate_set = candidate_set.filter(SmallerThan(item))
                for v in self.path:
                    v_nb =  Set(colidx[rowptr[v]:rowptr[v+1]])
                    candidate_set = candidate_set.intersect(v_nb)
    
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, self.path + [item]))
    
    res = edge_list.applyfunc(inner_subgraph_matching(1)).ret_val(count)
    code = codegen.cpu.print_cpp(res._gen_ir())
    print(code)
    d = run.cpu.compile_and_run(code, torch_edge_list, torch_rowptr, torch_colidx)
    print(d)


def star5():
    np_rowptr = np.fromfile("../MiCo/snap.txt.vertex.bin", dtype=np.int64)
    np_colidx = np.fromfile("../MiCo/snap.txt.edge.bin", dtype=np.int32)

    torch_rowptr = torch.from_numpy(np_rowptr, ).to(torch.int32)
    torch_colidx =torch.from_numpy(np_colidx)
    torch_edge_list = torch.zeros([torch_colidx.shape[0], 2], dtype=torch.int32)

    edge_idx = 0
    for i in range(0, torch_rowptr.shape[0]-1):
        for j in range(torch_rowptr[i].item() , torch_rowptr[i+1].item()):
                torch_edge_list[edge_idx][0] = i
                torch_edge_list[edge_idx][1] = torch_colidx[j]
                edge_idx = edge_idx+1
    #Cuke
    pattern_size = 5

    num_node = torch_rowptr.shape[0]-1
    num_edges = torch_colidx.shape[0]

    rowptr = Tensor('rowptr', (num_node+1,), dtype='int')
    colidx = Tensor('colidx', (num_edges,), dtype='int')
    edge_list =  Set(Tensor('edge_list', (num_edges, 2), dtype='int'))

    count = Zero(dtype='int')

    class inner_subgraph_matching:
        def __init__(self, level, *path):
             self.level = level
             self.path = list(*path)

        def __call__(self, item):
            if self.level == pattern_size-1:
                return Set(count).addone()

            if self.level==1:
                v0_nb =  Set(colidx[rowptr[item[0]]:rowptr[item[0]+1]])
                v1_nb =  Set(colidx[rowptr[item[1]]:rowptr[item[1]+1]])
                candidate_set = v0_nb.filter(SmallerThan(item[1])).difference(v1_nb)
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, [item[0], item[1]]))
            else:
                v0 = self.path[0]
                v0_nb =  Set(colidx[rowptr[v0]:rowptr[v0+1]])
                candidate_set = v0_nb.filter(SmallerThan(item))
                for v in self.path[1:]:
                    v_nb =  Set(colidx[rowptr[v]:rowptr[v+1]])
                    candidate_set = candidate_set.difference(v_nb)
                
                item_nb = Set(colidx[rowptr[item]:rowptr[item+1]])
                candidate_set = candidate_set.difference(item_nb)
    
                return candidate_set.applyfunc(inner_subgraph_matching(self.level+1, self.path + [item]))
    
    res = edge_list.applyfunc(inner_subgraph_matching(1)).ret_val(count)
    code = codegen.cpu.print_cpp(res._gen_ir())
    print(code)
    d = run.cpu.compile_and_run(code, torch_edge_list, torch_rowptr, torch_colidx)
    print(d)