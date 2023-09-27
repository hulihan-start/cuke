from core.ir import *
from batch.ast import *
from batch.ast2ir import *
import codegen

# def loop_idx_change(expr, ori_iter_list, iter_list):
#     # count = 0
#     if isinstance(expr, Loop):
#         for i in expr.body:
#             loop_idx_change(i, ori_iter_list, iter_list)
#     if isinstance(expr, Assignment):
#         loop_idx_change(expr.lhs, ori_iter_list, iter_list)
#         loop_idx_change(expr.rhs, ori_iter_list, iter_list)
#     if isinstance(expr, Expr):
#         loop_idx_change(expr.left, ori_iter_list, iter_list)
#         loop_idx_change(expr.right, ori_iter_list, iter_list)
#     while isinstance(expr, Index):
#         try:
#             print("index:::", expr.index.__name__, ori_iter_list)
#             for idx, item in enumerate(ori_iter_list):
#                 if expr.index.__name__ == item.__name__:
#                     expr.index.__name__ = iter_list[idx].__name__
#             expr = expr.dobject
#         except:
#             expr = expr.dobject
#             break

# def fuse_elementwise(node):
    
    
#     eval_len = len(node.eval.size)
#     temp = node.operators[0].compute[0]
#     print("operator0:",codegen.cpu.to_string(temp))
#     print("operator1:",codegen.cpu.to_string(node.operators[1].compute[0]))
#     loop_count = 0
#     while isinstance(temp, Loop):
#         if loop_count == eval_len:
#             break
#         temp = temp.body[0]
#         loop_count += 1
#     lhs = node.operators[0].eval
#     rhs = node.operators[1].eval
#     res = node.eval

#     t = node.operators[0].compute[0]
#     pre_loop = None
#     iter_list = []
#     ori_iter_list = []
#     for i in range(eval_len):
#         i_loop = Loop(0, node.eval.size[i], 1, [])
#         lhs = bind(lhs, i_loop.iterate)
#         rhs = bind(rhs, i_loop.iterate)
#         res = bind(res, i_loop.iterate)
#         iter_list.append(i_loop.iterate)
#         ori_iter_list.append(t.iterate)
#         t = t.body[0]
#         if i == 0:
#             pre_loop = i_loop
#             t_loop = i_loop
#         else:
#             t_loop.body.append(i_loop)
#             t_loop = i_loop
#     assign = Assignment(res, Expr(lhs, rhs, '+'))
#     loop_idx_change(temp, ori_iter_list, iter_list)

#     i_loop.body.append(temp)
#     i_loop.body.append(assign)
#     node.operators[0].compute.clear()
#     node.compute = [pre_loop]
#     # ir = []
#     # codegen.cpu.gen_cpp(node, ir)
#     # code = ''
#     # for d in ir:
#     #     if d:
#     #         code += codegen.cpu.to_string(d)
#     # print(code)

# def fuse_innerprod(node):
#     temp = fused_loop = node.operators[0].compute[0]
#     ori_iter_list = []
#     while isinstance(temp, Loop):
#         ori_iter_list.append(temp.iterate)
#         temp = temp.body[0]
        
#     pre_loop = Loop(0, node.eval.size[0], 1, [])
#     node.compute = [pre_loop]
#     lhs = bind(node.operators[0].eval, pre_loop.iterate)
#     rhs = bind(node.operators[1].eval, pre_loop.iterate)
#     res = bind(node.eval, pre_loop.iterate)
#     inner_loop =  Loop(0, node.operators[0].eval.size[1], 1, [])
#     pre_loop.body.append(inner_loop)
#     lhs = bind(lhs, inner_loop.iterate)
#     rhs = bind(rhs, inner_loop.iterate)
#     assign = Assignment(res, Expr(lhs, rhs, '*'), '+')
#     loop_idx_change(temp.lhs,ori_iter_list, [pre_loop.iterate, inner_loop.iterate])
#     inner_loop.body.append(temp)
#     inner_loop.body.append(assign)
#     node.operators[0].compute.clear()

def loop_idx_change(oloop, fusedloop):
    # if isinstance(oloop, Loop):
    #     print('oloop:', codegen.cpu.to_string(oloop), oloop.iterate)
    # if isinstance(fusedloop[0], Loop) :
    #     print('iloop 0 :', codegen.cpu.to_string(fusedloop[0]), fusedloop[0].iterate)
    # if len(fusedloop) > 1:
    #     print('iloop 1 :', codegen.cpu.to_string(fusedloop[1]))
    # print(fusedloop, codegen.cpu.to_string(fusedloop[0]))
    for iloop in fusedloop:
        while (isinstance(oloop, Loop) and isinstance(iloop, Loop)) and oloop.start == iloop.start and oloop.end.__name__ == iloop.end.__name__ and oloop.step == iloop.step:
            # iloop.iterate = oloop.iterate
            iloop.iterate.__name__ = oloop.iterate.__name__
            iloop.iterate = oloop.iterate
            oloop = oloop.body[0]
            iloop = iloop.body
            
            loop_idx_change(oloop, iloop)

def get_same_loop(outloop, fusedloop):
    pre_o = outloop
    pre_i = fusedloop
    oloop = outloop.body[0]
    iloop = fusedloop.body[0]
    
    pre_iter_i = []
    pre_iter_o = []

    pre_iter_i.append(pre_i.iterate)
    pre_iter_o.append(pre_o.iterate)
    while (isinstance(oloop, Loop) and isinstance(iloop, Loop)) and oloop.start == iloop.start and oloop.end.__name__ == iloop.end.__name__ and oloop.step == iloop.step:
        pre_o = oloop
        pre_i = iloop
        pre_iter_i.append(pre_i.iterate)
        pre_iter_o.append(pre_o.iterate)

        oloop = oloop.body[0]
        iloop = iloop.body[0]
        
    return pre_o, pre_i, pre_iter_o, pre_iter_i

def change_index(iassign, iter_o, iter_i):
    if isinstance(iassign, Index):
        for idx, item in enumerate(iter_i):
            if iassign.index == item:
                iassign.index = iter_o[idx]
        if isinstance(iassign.dobject, Index):
            change_index(iassign.dobject, iter_o, iter_i)
        
    elif isinstance(iassign, Expr):
        # both item.left and item.right
        change_index(iassign.left, iter_o, iter_i)
        change_index(iassign.right, iter_o, iter_i)
    elif isinstance(iassign, Assignment):
        # both item.lhs and item.rhs
        change_index(iassign.lhs, iter_o, iter_i)
        change_index(iassign.rhs, iter_o, iter_i)
    elif isinstance(iassign, Loop):
        # oloop.body[0] and item.body
        for i in iassign.body:
            change_index(i, iter_o, iter_i)
    


def fuse_elementwise(ast):

    if type(ast.operators[0]) == BatchOp:
        fuse_elementwise(ast.operators[0])
    if type(ast.operators[1]) == BatchOp:
        fuse_elementwise(ast.operators[1])
    
    if type(ast) == Batch or not ast.op_type in core.ast.op_mapping:
        return 

    if ast.operators[1].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[1].compute[0]

        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        iloop.body.clear()
        ast.operators[1].compute.clear()

    if ast.operators[0].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[0].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[0].compute.clear()


def fuse_innerprod(ast):
    if type(ast.operators[0]) == BatchOp:
        fuse_innerprod(ast.operators[0])
    if type(ast.operators[1]) == BatchOp:
        fuse_innerprod(ast.operators[1])

    if type(ast) == Batch or not ast.op_type == 'vec_mul_vec':
        return 

    if ast.operators[1].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[1].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[1].compute.clear()

    if ast.operators[0].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[0].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[0].compute.clear()


def fuse_bsv(ast):
    print(type(ast.operators[0]), type(ast.operators[1]), type(ast), ast.op_type)
    if type(ast.operators[0]) == BatchOp:
        fuse_bsv(ast.operators[0])
    if type(ast.operators[1]) == BatchOp:
        fuse_bsv(ast.operators[1])

    if type(ast) == Batch or not ast.op_type == 'scal_mul_vec':
        return 
    print(ast.op_type, ast.operators[0].compute , ast.compute)
    if ast.operators[1].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[1].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[1].compute.clear()

    if ast.operators[0].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[0].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[0].compute.clear()
    

def fuse_bvm(ast):
    if type(ast.operators[0]) == BatchOp:
        fuse_bvm(ast.operators[0])
    if type(ast.operators[1]) == BatchOp:
        fuse_bvm(ast.operators[1])

    if type(ast) == Batch or not ast.op_type == 'vec_mul_mat':
        return 
    if ast.operators[1].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[1].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[1].compute.clear()

    if ast.operators[0].compute and ast.compute:
        outer_loop = ast.compute[0]
        loop = ast.operators[0].compute[0]
        
        oloop, iloop, iter_o, iter_i = get_same_loop(outer_loop, loop)
        for i in iloop.body:
            change_index(i, iter_o, iter_i)
        for i in range(len(iloop.body)):
            oloop.body.insert(i, iloop.body[i])
        
        iloop.body.clear()
        ast.operators[0].compute.clear()