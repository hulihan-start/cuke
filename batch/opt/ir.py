from core.ir import *

# class ThreadMapping():
#     loop_id = 0
#     def __init__(self, start, end, step, body: list):
#         self.lid = ThreadMapping.loop_id
#         ThreadMapping.loop_id += 1
#         self.start = start
#         self.end = end
#         self.step = step
#         self.body = body
#         self.iterate = Scalar('int', f'_l{self.lid}')

class BlockIdy(IR):
    def __init__(self):
        super().__init__()

class BlockIdx(IR):
    def __init__(self):
        super().__init__()

class BlockDimy(IR):
    def __init__(self):
        super().__init__()

class BlockDimx(IR):
    def __init__(self):
        super().__init__()

class ThreadIdy(IR):
    def __init__(self):
        super().__init__()

class ThreadIdx(IR):
    def __init__(self):
        super().__init__()

class SyncThreads(IR):
    def __init__(self):
        super().__init__()

class SyncWarps(IR):
    def __init__(self):
        super().__init__()

class ShuffleDown(IR):
    def __init__(self, dobject):
        super().__init__()
        self.dobject = dobject

class ShuffleUp(IR):
    def __init__(self, dobject):
        super().__init__()
        self.dobject = dobject

class ShuffleXor(IR):
    def __init__(self, dobject):
        super().__init__()
        self.dobject = dobject

class SaveAtThread(IR):
    def __init__(self, src, dst, threadid):
        super().__init__()
        self.src = src
        self.dst = dst
        self.threadid = threadid

class BroadCast(IR):
    def __init__(self, dobject):
        super().__init__()
        self.dobject = dobject