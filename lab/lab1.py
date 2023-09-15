import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.ir import *
from codegen.cpu import *


def PrintCCode(ir):
    code = ''
    for d in ir:
        if d:
            code += to_string(d)
    print(code)



# Loop 0 before interchange:
# int L;
# int M;
# int N;
# torch::Tensor obj_A = torch::empty({N,M,L}, at::kInt);
# auto A = obj_A.accessor<int, 3>();
# for (int _l13 = 0; _l13 < N; _l13 += 1) {
# for (int _l14 = 0; _l14 < M; _l14 += 1) {
# for (int _l15 = 0; _l15 < L; _l15 += 1) {
# A[_l13 + 1][_l14][_l15] = B[_l13 + 1][_l14][_l15 - 1] + 2;
# B[_l13 + 1][_l14 + 2][_l15 - 1] = A[_l13][_l14][_l15 + 1] + B[_l13][_l14 + 2][_l15];
# } 
# } 
# } 
def Loop0():
    ir = []

    N = Scalar('int', 'N')
    M = Scalar('int', 'M')
    L = Scalar('int', 'L')
    A = Ndarray('int', (N, M, L), 'A')
    B = Ndarray('int', (N, M, L), 'B')

    loopi = Loop(0, N, 1, [])
    loopj = Loop(0, M, 1, [])
    loopk = Loop(0, L, 1, [])

    loopi.body.append(loopj)
    loopj.body.append(loopk)

    lhs1 = Index(Index(Index(A, Expr(loopi.iterate, 1, '+')), loopj.iterate), loopk.iterate)
    lhs2 = Index(Index(Index(B, Expr(loopi.iterate, 1, '+')), Expr(loopj.iterate, 2, '+')), Expr(loopk.iterate, 1, '-'))
    rhs1 = Index(Index(Index(B, Expr(loopi.iterate, 1, '+')), loopj.iterate), Expr(loopk.iterate, 1, '-'))
    rhs2 = Index(Index(Index(A, loopi.iterate), loopj.iterate), Expr(loopk.iterate, 1, '+'))
    rhs3 = Index(Index(Index(B, loopi.iterate), Expr(loopj.iterate, 2, '+')), loopk.iterate)

    # body = Assignment(lhs, Expr(rhs1, rhs2, '+'))
    loopk.body.extend([Assignment(lhs1, Expr(rhs1, 2, '+')), Assignment(lhs2, Expr(rhs2, rhs3, '+'))])

    ir.extend([Decl(L)])
    ir.extend([Decl(M)])
    ir.extend([Decl(N)])
    ir.extend([Decl(A)])
    ir.extend([loopi])

    return ir


# for ( k = 0; k < L ; ++k ){
# 	for ( j = 0; j < M; ++ j ){
# 		for ( i = 0; i < N; ++ i ){
# 			a[i+1] [j+1] [k] = a [i] [j] [k] + a [i] [j + 1] [k + 1] ;
# 		}
# 	}
# }

# Distance Vector:
# [1, 1, 0] :  a[i+1] [j+1] [k] and a [i] [j] [k]
# [1, 0, -1] : a[i+1] [j+1] [k] and  a [i] [j + 1] [k + 1]

# Direction Vector:
# [<, <, =]
# [<, =, >]

def Loop1():
    ir = []

    L = Scalar('int', 'L')
    M = Scalar('int', 'M')
    N = Scalar('int', 'N')
    A = Ndarray('int', (N, M, L), 'A')

    loopk = Loop(0, L, 1, [])
    loopj = Loop(0, M, 1, [])
    loopi = Loop(0, N, 1, [])
    loopk.body.append(loopj)
    loopj.body.append(loopi)

    lhs = Index(Index(Index(A, Expr(loopi.iterate, 1, '+')), Expr(loopj.iterate, 1, '+')), loopk.iterate)
    rhs1 = Index(Index(Index(A, loopi.iterate), loopj.iterate), loopk.iterate)
    rhs2 = Index(Index(Index(A, loopi.iterate), Expr(loopj.iterate, 1, '+')), Expr(loopk.iterate, 1, '+'))

    body = Assignment(lhs, Expr(rhs1, rhs2, '+'))
    loopi.body.append(body)

    ir.extend([Decl(L)])
    ir.extend([Decl(M)])
    ir.extend([Decl(N)])
    ir.extend([Decl(A)])
    ir.extend([loopk])

    return ir


# for ( i = 0; i < N ; ++i ){
# 	for ( j = 0; j < N; ++ j ){
# 			a[i][j] = a[i+1][j-1];
# 	}
# }

# Distance Vector:
# [-1, 1]

# Direction Vector:
# [<, >]

def Loop2():
    ir = []

    N = Scalar('int', 'N')
    A = Ndarray('int', (N, N), 'A')

    loopi = Loop(0, N, 1, [])
    loopj = Loop(0, N, 1, [])

    loopi.body.append(loopj)

    lhs = Index(Index(A, loopi.iterate), loopj.iterate)
    rhs = Index(Index(A, Expr(loopi.iterate, 1, '+')), Expr(loopj.iterate, 1, '-'))

    loopj.body.append(Assignment(lhs, rhs))

    ir.extend([Decl(N)])
    ir.extend([Decl(A)])
    ir.extend([loopi])

    return ir


'''
A[l0+1][l1][l2] = B[l0+1][l1][l2-1] + 2;
B[l0+1][l1+2][l2-1] = A[l0][l1][l2+1] + B[l0][l1+2][l2];


write statement array: [A[l0+1][l1][l2], B[l0+1][l1+2][l2-1]]
read statement array: [B[l0+1][l1][l2-1], A[l0][l1][l2+1], B[l0][l1+2][l2]]

Group index statement by names
write dict: {'A': [A[l0+1][l1][l2]], 'B': [B[l0+1][l1+2][l2-1]]}
read dict: {'A': [A[l0][l1][l2+1]], 'B': [B[l0+1][l1][l2-1], B[l0][l1+2][l2]]}

write read & write write

Compute the direction vector
Distance vector
A: [1, 0, -1]
B1:[0, 2, 0]
B2:[1, 0, -1]

Direction vector
A: [<, =, >]
B1:[=, <, =]
B2:[<, =, >]

safety checking based on direction vector
Exchange [0,1] first non-equal is '<', this is safe
A: [=, <, >]
B1:[<, =, =]
B2:[=, <, >]

Exchange [0,2]  not safe
A: [>, =, <]    The first non-equal is '>', not valid.
B1:[=, <, =]
B2:[>, =, <]

Exchange [1,2] 
A: [<, >, =]
B1:[=, =, <]
B2:[<, >, =]
'''


def FindBody(loop):
    if not isinstance(loop, Loop):
        return loop
    if isinstance(loop.body[0], Loop):
        return FindBody(loop.body[0])
    else:
        return loop.body


def get_index(statement, is_write, write_expr=[], read_expr=[]):
    if isinstance(statement, Ndarray) or isinstance(statement, Index):
        if is_write:
            write_expr.append(statement)
        else:
            read_expr.append(statement)
    elif isinstance(statement, Assignment):
        get_index(statement.lhs, True, write_expr, read_expr)
        get_index(statement.rhs, False, write_expr, read_expr)
    elif isinstance(statement, Expr):
        get_index(statement.left, is_write, write_expr, read_expr)
        get_index(statement.right, is_write, write_expr, read_expr)
    else:
        return


def get_array(wr_dict, stmt, parent_stmt):
    if isinstance(stmt.dobject, Ndarray):
        if stmt.dobject.name() in wr_dict.keys():
            wr_dict[stmt.dobject.name()].append(parent_stmt)
        else:
            wr_dict[stmt.dobject.name()] = [parent_stmt]
    elif isinstance(stmt.dobject, Index):
        get_array(wr_dict, stmt.dobject, parent_stmt)


def get_iterates(idx, vecs):
    if isinstance(idx.dobject, Index):
        # print(idx.index)
        if isinstance(idx.index, Scalar):
            if idx.index.val is None:
                vecs.append(0)
        elif isinstance(idx.index, Expr):
            if idx.index.op == '+':
                vecs.append(idx.index.right)
            elif idx.index.op == '-':
                vecs.append(-idx.index.right)
        get_iterates(idx.dobject, vecs)
    else:
        if isinstance(idx.index, Scalar):
            if idx.index.val is None:
                vecs.append(0)
        elif isinstance(idx.index, Expr):
            if idx.index.op == '+':
                vecs.append(idx.index.right)
            elif idx.index.op == '-':
                vecs.append(-idx.index.right)


def direction_vec(write_idx, read_idx):
    wvec = []
    rvec = []
    get_iterates(write_idx, wvec)
    get_iterates(read_idx, rvec)
    print(wvec, rvec)
    return [x - y for x, y in zip(wvec, rvec)]


def safety_checking(i0, i1, vecs):
    tmp = []
    for i in vecs:
        subtmp = []
        for j in i:
            subtmp.append(j)
        tmp.append(subtmp)
    for i in tmp:
        i[i0], i[i1] = i[i1], i[i0]

    for i in tmp:
        for j in i:
            if j == 0:
                continue
            elif j > 0:
                return True
            elif j < 0:
                return False
    # print('after change: ', tmp)
    # print('original vec:', vecs)


def InterchangeLoop(ir, loop_idx=[]):
    ir_res = []
    interchangeable = True
    our_loop = None
    write_expr = []
    read_expr = []
    write_dict = dict()
    read_dict = dict()
    for ir_item in ir:
        if isinstance(ir_item, Loop):
            body = FindBody(ir_item)
            for body_item in body:
                get_index(body_item, False, write_expr, read_expr)

            PrintCCode(write_expr)
            PrintCCode(read_expr)
            print(write_expr, read_expr)
            for i in write_expr:
                get_array(write_dict, i, i)
            for i in read_expr:
                get_array(read_dict, i, i)
            print(write_dict)
            print(read_dict)

            PrintCCode(write_dict['A'])
            PrintCCode(write_dict['B'])

            PrintCCode(read_dict['A'])
            PrintCCode(read_dict['B'])

            vecs = []
            get_iterates(write_dict['A'][0], vecs)
            get_iterates(write_dict['B'][0], vecs)

            get_iterates(read_dict['A'][0], vecs)
            get_iterates(read_dict['B'][0], vecs)
            get_iterates(read_dict['B'][1], vecs)
            print(vecs)
            d_vec = []
            for key in write_dict.keys():
                if len(write_dict[key]) > 1:
                    tmp = write_dict[key]
                    for i in range(len(tmp)):
                        for j in range(i + 1, len(tmp)):
                            vec = direction_vec(tmp[i], tmp[j])
                            d_vec.append(vec[::-1])

                tmp = read_dict[key]
                for i in tmp:
                    vec = direction_vec(write_dict[key][0], i)
                    d_vec.append(vec[::-1])
            print(d_vec)

            for i in range(len(d_vec[0])):
                for j in range(i + 1, len(d_vec[0])):
                    x = safety_checking(i, j, d_vec)
                    print(x)

    # print("Please implement the pass here")
    return interchangeable, ir_res


if __name__ == "__main__":
    loop0_ir = Loop0()
    loop1_ir = Loop1()
    loop2_ir = Loop2()
    # PrintCCode(loop0_ir)

    optimized_loop0_ir, ir_res = InterchangeLoop(loop0_ir, [0, 1])
    # PrintCCode(optimized_loop0_ir)
    # optimized_loop1_ir = InterchangeLoop(loop1_ir, [1, 2]):
    # optimized_loop2_ir = InterchangeLoop(loop2_ir, [0, 1]):

    # optimized_ir = LoopInterchange(ir)
    # print("Loop after interchange:")
    # PrintCCode(optimized_ir)
