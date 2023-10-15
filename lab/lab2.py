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

def Loop0():
    ir = []

    L = Scalar('int', 'L')
    M = Scalar('int', 'M')
    N = Scalar('int', 'N')
    A = Ndarray('int', (N, M, L), 'A')
    B = Ndarray('int', (N, M, L), 'B')

    loopi = Loop(0, 20, 1, [])
    loopj = Loop(Expr(loopi.iterate, 3, '+'),  Expr(loopi.iterate, 10, '+'), 1, [])
    loopk = Loop(Expr(loopj.iterate, 20, '+'), Expr(loopj.iterate, 30, '+'), 1, [])

    loopi.body.append(loopj)
    loopj.body.append(loopk)

    lhs1 = Index(Index(Index(A, Expr(loopi.iterate, 1, '+')), loopj.iterate), loopk.iterate)
    rhs1 = Index(Index(Index(B, loopi.iterate), loopj.iterate), loopk.iterate)
	
    # body = Assignment(lhs, Expr(rhs1, rhs2, '+'))
    loopk.body.extend([Assignment(lhs1, Expr(rhs1, 2, '+'))])

    ir.extend([Decl(L)])
    ir.extend([Decl(M)])
    ir.extend([Decl(N)])
    ir.extend([Decl(A)])
    ir.extend([Decl(B)])
    ir.extend([loopi])

    return ir

def get_boundry(ir, boundry_list, index_dict={}, level=0):
    if isinstance(ir, Loop):
        boundry_list.append((ir.start, ir.end))
        index_dict[ir.iterate] = level
        for item in ir.body:
            get_boundry(item, boundry_list, index_dict, level+1)


def check_iterate(ir, iterate):
    if isinstance(ir, Scalar):
        if ir.name() == iterate.name():
            return True
        else:
            return False

    elif isinstance(ir, Expr):
        return check_iterate(ir.left, iterate)
    return False

def replace_iterate(ir, o_list, c_list):
    if isinstance(ir, Scalar):
        for idx,item in enumerate(o_list):
            if ir == item:
                return c_list[idx]
        return ir
    if isinstance(ir, Index):
        ir.index = replace_iterate(ir.index, o_list, c_list)
        if isinstance(ir.dobject, Index):
            ir.dobject = replace_iterate(ir.dobject, o_list, c_list)
    elif isinstance(ir, Expr):
        ir.left = replace_iterate(ir.left, o_list, c_list)
        ir.right = replace_iterate(ir.right, o_list, c_list)
    elif isinstance(ir, Assignment):
        ir.lhs = replace_iterate(ir.lhs, o_list, c_list)
        ir.rhs = replace_iterate(ir.rhs, o_list, c_list)
    return ir


def get_new_bound(ir, b_list, index_dict, tile_size):
    o_loop = ir
    it = Scalar('float')
    it_list = []
    new_it_list = []
    for i in range(len(b_list)):
        lower = b_list[i][0]
        upper = b_list[i][1]

        if type(upper) == Expr and check_iterate(upper, it):
            iterate = upper.left
            new_upper = Expr(upper, tile_size[index_dict[iterate]], '+')
            o_loop.end = new_upper

        new_lower = Expr(lower, tile_size[i], '-')
        o_loop.start = Max(Round(new_lower), tile_size[i])
        o_loop.step = tile_size[i]
        it_list.append(o_loop.iterate)
        it = o_loop.iterate
        item = o_loop.body[0]
        if isinstance(item, Loop):
            o_loop = o_loop.body[0]
    assign = o_loop.body[0]
    o_loop.body = []

    for i in range(len(b_list)):
        lower = b_list[i][0]
        upper = b_list[i][1]
        new_loop = Loop(Max(it_list[i], lower), Min(Expr(it_list[i], tile_size[i], '+'), upper), 1, [])
        new_it_list.append(new_loop.iterate)
        o_loop.body.append(new_loop)
        o_loop = o_loop.body[0]

    assign = replace_iterate(assign, it_list, new_it_list)
    o_loop.body.append(assign)
def LoopTiling(loop_ir, tile_size=[]):
    new_ir_list = []
    for i in loop_ir:
        if isinstance(i, Loop):
            b_list = []
            index_dict = {}
            get_boundry(i, b_list, index_dict,0)

            # index_dict is a dict {l0:0, l1:1, l2:2}

            get_new_bound(i, b_list, index_dict, tile_size)
            new_ir_list.append(i)
        else:
            new_ir_list.append(i)
    return new_ir_list

if __name__ == "__main__":
    loop0_ir = Loop0()
    loop0_ir = LoopTiling(loop0_ir, [3, 4, 5])
    PrintCCode(loop0_ir)

# How to calculate new lower bounds and new upper bounds
# New lower bound(i) = original lower bound(i) - (tile_size(i) - 1)
# if i is an expression of k:
#     new upper bound(i) = original upper bound(i) + (tile_size(i) - 1)
# else:
#     new upper bound(i) = original upper bound(i)
# for (int _l0 = 0; _l0 < 20; _l0 += 1) {
#     for (int _l1 = _l0 + 3; _l1 < _l0 + 10; _l1 += 1) {
#         for (int _l2 = _l1 + 20; _l2 < _l1 + 30; _l2 += 1) {
#             A[_l0 + 1][_l1][_l2] = B[_l0][_l1][_l2] + 2;
#         }
#     }
# }

# for (int _l0 = ceil((0-(tile_size[0]-1)) / tile_size[0]); _l0 < 20; _l0 += tile_size[0]) {
#     for (int _l1 = _l0 + 3 - (tile_size[1]-1); _l1 < _l0 + 10+(tile_size[1]-1); _l1 += tile_size[1]) {
#         for (int _l2 = _l1 + 20-(tile_size[2]-1); _l2 < _l1 + 30+(tile_size[2]-1); _l2 += tile_size[2]) {

# for point loop
#     corresponding tile loop index for point-loop level(i)=iT
#     new lower bound = max(iT, original lower bound)
#     new upper bound = min(iT + tile_size(i)-1, original upper bound)

# original lower bound(l0p) = original lower bound(l0) = 0
# original upper bound(l0p) = original upper bound(l0) = 20

#             for (int _l0p = max(0, l0); _l0p < min(l0+tile_size[0], 20); _l0p += 1) {
#
#                 for (int _l1p = max(l0+3, l1); _l1p < (l1+tile_size[1], _l0 + 10); _l1p += 1) {
#
#                     for (int _l2p = max(_l1 + 20, l2); _l2p < (l2+tile_size[2], _l1 + 30); _l2p += 1) {
#                         A[_l3 + 1][_l4][_l5] = B[_l3][_l4][_l5] + 2;
# }}}}}}