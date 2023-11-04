from core.ir import *
from batch.ast import *
from batch.ast2ir import *
import codegen
from batch.opt.ir import *

def swap_arr_to_reg(ir, pre, cur):
    # print(codegen.gpu.to_string(ir), codegen.gpu.to_string(pre), codegen.gpu.to_string(cur))
    if isinstance(ir, Indexing):
        temp = ir
        while isinstance(temp, Indexing):
            # print(codegen.gpu.to_string(temp), codegen.gpu.to_string(temp.idx))
            if temp.idx == pre:
                temp.idx = Expr(pre, cur, '+')
            temp = temp.dobject
    elif isinstance(ir, Expr):
        ir.left = swap_arr_to_reg(ir.left, pre, cur)
        ir.right = swap_arr_to_reg(ir.right, pre, cur)
    elif isinstance(ir, Assignment):
        ir.lhs = swap_arr_to_reg(ir.lhs, pre, cur)
        ir.rhs = swap_arr_to_reg(ir.rhs, pre, cur)
    elif isinstance(ir, Loop):
        for i in range(len(ir.body)):
            ir.body[i] = swap_arr_to_reg(ir.body[i], pre, cur)
    return ir

def swap_reg_to_arr(ir, pre, cur, iloop):
    if isinstance(ir, Scalar):
        if ir == pre and iloop.end.name()=='D':
            ir = Indexing(cur, iloop.iterate)
    elif isinstance(ir, Expr):
        ir.left = swap_reg_to_arr(ir.left, pre, cur, iloop)
        ir.right = swap_reg_to_arr(ir.right, pre, cur, iloop)
    elif isinstance(ir, Assignment):
        ir.lhs = swap_reg_to_arr(ir.lhs, pre, cur, iloop)
        ir.rhs = swap_reg_to_arr(ir.rhs, pre, cur, iloop)
    elif isinstance(ir, Loop):
        
        for i in range(len(ir.body)):
            if ir.end.name() == 'D' and isinstance(ir.body[i], Loop) and ir.body[i].end.name() == 'D':
                for j in range(len(ir.body[i].body)):
                    ir.body[i].body[j] = swap_reg_to_arr(ir.body[i].body[j], pre, cur, ir)
            else:
                ir.body[i] = swap_reg_to_arr(ir.body[i], pre, cur, ir)
    return ir

def tile_wD(ir):
    if isinstance(ir, Loop):
        if ir.end.name() == 'dim':
            scalar_D = Scalar('int', 'D')
            tbody = ir.body
            ir.step = scalar_D
            new_loop = Loop(0, scalar_D, 1,[])
            for i in range(len(tbody)):
                tbody[i] = swap_arr_to_reg(tbody[i], ir.iterate, new_loop.iterate)
                # if isinstance(tbody[i], Assignment) and isinstance(tbody[i].rhs, Literal):
                #         print(codegen.gpu.to_string(tbody[i]))
            new_loop.body.extend(tbody)
            # iloops.append(new_loop)
            ir.body = [new_loop]
    return ir

def recursive_tile(ir):
    if isinstance(ir, Loop):
        ir = tile_wD(ir)
        for i in range(len(ir.body)):
            ir.body[i] = recursive_tile(ir.body[i])
         
    return ir

def tile_loops(ir, tile_list):
    if isinstance(ir, Loop) and ir.end.name() == 'dim':
        scalar_D = Scalar('int', 'D')
        ir.step = scalar_D
        new_loop = Loop(0, scalar_D, 1,[])
        tile_list.append(ir)
        for i in range(len(ir.body)):
            ir.body[i] = tile_loops(ir.body[i], tile_list)
    return ir

def swap_loops_tile(ir):
    decl = []
    del_decl = []
    replace_pair = []
    if isinstance(ir, Loop):
        # print(ir, codegen.gpu.to_string(ir))
        for i in range(len(ir.body)):
            # print(ir.body[i], codegen.gpu.to_string(ir.body[i]))
            if isinstance(ir.body[i], Loop) and ir.body[i].end.name() != 'dim':
                # print(ir.body[i], codegen.gpu.to_string(ir.body[i]))
                ir.body[i], temp_decl, temp_del = swap_loops_tile(ir.body[i])
                decl.extend(temp_decl)
                del_decl.extend(temp_del)
            
            elif isinstance(ir.body[i], Loop) and ir.body[i].end.name() == 'dim':
                # print(ir.body[i], codegen.gpu.to_string(ir.body[i]))
                tile_list = []
                tile_loops(ir.body[i], tile_list)
                multi_lv_loop = {}

                
                # print(tile_list)
                for lidx in range(len(tile_list)):
                    t = tile_list[lidx]
                    # print(t, codegen.gpu.to_string(t))
                    # add tiled loop here 
                    scalar_D = Scalar('int', 'D')
                    new_loop = Loop(0, scalar_D, 1,[])
                    temp_body = []
                    for k in range(len(t.body)):
                        item = t.body[k]
                        # print(item, codegen.gpu.to_string(item))
                        if isinstance(item, Loop) and item.end.name() == 'dim':
                            if new_loop.body != []:
                                # add new_tiled loop and create a new one
                                temp_body.append(new_loop)
                                new_loop = Loop(0, scalar_D, 1,[])
                            
                            if item in multi_lv_loop.keys():
                                multi_lv_loop[item].append([multi_lv_loop[item][-1][0]+1, t])
                            else:
                                multi_lv_loop[item] = [[1, t]]
                            temp_body.append(item)
                        elif t in multi_lv_loop.keys():
                            oloop = Loop(0, scalar_D, 1,[])
                            for jj in range(len(t.body)):
                                t.body[jj] = swap_arr_to_reg(t.body[jj], multi_lv_loop[t][0][1].iterate, oloop.iterate)
                            loop1 = oloop
                            for i in range(len(multi_lv_loop[t])):
                                tloop = Loop(0, scalar_D, 1,[])
                                loop1.body.append(tloop)
                                if i+1 < len(multi_lv_loop[t]):
                                    for jj in range(len(t.body)):
                                        t.body[jj] = swap_arr_to_reg(t.body[jj], multi_lv_loop[t][i+1][1].iterate, tloop.iterate)
                                    loop1 = tloop
                            for jj in range(len(t.body)):
                                t.body[jj] = swap_arr_to_reg(t.body[jj], t.iterate, tloop.iterate)
                            tloop.body = t.body
                            temp_body.append(oloop)
                        else:
                            # add tiled loop here
                            # print(codegen.gpu.to_string(item), item.lhs, item.rhs)
                            if isinstance(item, Assignment) and isinstance(item.rhs, Literal):
                                new_lhs = Ndarray(item.lhs.dtype, [scalar_D])
                                decl.append(Decl(new_lhs))
                                del_decl.append(item.lhs)
                                replace_pair.append([new_lhs, item.lhs])

                            item = swap_arr_to_reg(item, t.iterate, new_loop.iterate)
                            new_loop.body.append(item)
                    if new_loop.body != []:
                        temp_body.append(new_loop)
                    tile_list[lidx].body = temp_body
        for i in range(len(ir.body)):
            if replace_pair:
                for jj in replace_pair:
                    # print(codegen.gpu.to_string(jj[0]), codegen.gpu.to_string(jj[1]), codegen.gpu.to_string(ir.body[i]))
                    if isinstance(ir.body[i], Loop):
                        for temp in ir.body[i].body:
                            temp = swap_reg_to_arr(temp, jj[1], jj[0], ir.body[i])
                    else:
                        ir.body[i] = swap_reg_to_arr(ir.body[i], jj[1], jj[0], ir)
            # print(ir.body[i], codegen.gpu.to_string(ir.body[i]))
    return ir, decl, del_decl

def tile_loop(ast, eval_list=[]):
    
    
    if ast.compute and ast.valid:
    # if ast.compute:
        # print(ast.compute[0], codegen.gpu.to_string(ast.compute[0]))
        # print(codegen.gpu.to_string(ast.eval), codegen.gpu.to_string(ast.operators[0].eval), codegen.gpu.to_string(ast.operators[1].eval), ast.operators[0].eval)
        # print(ast.eval, codegen.gpu.to_string(ast.eval))
        for i in ast.compute:
            # recursive_tile(i)
            body, decl, del_decl = swap_loops_tile(i)
            for i in range(len(decl)):
                # print(decl[i], del_decl[i], codegen.gpu.to_string(decl[i]), codegen.gpu.to_string(del_decl[i]))
                eval_list.append([del_decl[i], decl[i].dobject])
            ast.decl.extend(decl)
            for dd in ast.decl:
                if dd.dobject in del_decl:
                    ast.decl.remove(dd)

    if type(ast) == BatchOp:
        if type(ast.operators[1]) == BatchOp:
            tile_loop(ast.operators[1], eval_list)
        if type(ast.operators[0]) == BatchOp:
            tile_loop(ast.operators[0], eval_list)
    else:
        return 
    
    if not ast.valid:
        # print(ast.op_type, eval_list, ast.eval, ast.decl)
        for id, item in enumerate(eval_list):
            if item[0] == ast.eval:
                ast.eval = item[1]
                eval_list.pop(id)