#include <torch/extension.h>

torch::Tensor reduce_a___c2_item1_of_a_item2_of_a_add_item1_of_a_item2_of_a(torch::Tensor obj_a)
{
    auto a = obj_a.accessor<float, 2>();
torch::Tensor obj_arr4 = torch::empty({10}, at::kFloat);
auto arr4 = obj_arr4.accessor<float, 1>();
for (int _l0 = 0; _l0 < 10; _l0 += 1) {
arr4[_l0] = 0;
} 
for (int _l1 = 0; _l1 < 20; _l1 += 1) {
for (int _l2 = 0; _l2 < 10; _l2 += 1) {
arr4[_l2] = (arr4[_l2] + a[_l2][_l1]);
} 
} 
return obj_arr4;

}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("run", &reduce_a___c2_item1_of_a_item2_of_a_add_item1_of_a_item2_of_a);
}