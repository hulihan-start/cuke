from core.ir import *
from batch.ast import *
from batch.ast2ir import *
import codegen
from batch.opt.ir import *


def tile_loop(ast):

    
    if ast.compute and ast.valid:
        pass