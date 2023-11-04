import mysort
import torch

batch_size = 128

th = h = torch.randint(0, 9999, (batch_size, )).int().cuda(0)
tr = r = torch.randint(0, 100, (batch_size, )).int().cuda(0)
tt = t = torch.randint(0, 9999, (batch_size, )).int().cuda(0)

# h = torch.tensor([1, 2, 3, 4])
# t = torch.tensor([10, 20, 30, 40])
# r = torch.tensor([3, 1, 4, 2])

print(h)
print(t)
print(r)
print('after sorting:::')
sorted_indices = torch.argsort(r)

sorted_h = h[sorted_indices]
sorted_t = t[sorted_indices]
sorted_r = r[sorted_indices]
print("Sorted h:", sorted_h)
print("Sorted t:", sorted_t)
print(sorted_r)

runiq = torch.zeros((batch_size//16, 16)).int().cuda(0)
rbuffer = torch.zeros((batch_size//16, 16)).int().cuda(0)
uniq_cnt = torch.zeros((batch_size//16,)).int().cuda(0)

th, tt, tr = mysort.index_building(th, tt, tr, runiq, rbuffer, uniq_cnt, batch_size, 16, 100)
