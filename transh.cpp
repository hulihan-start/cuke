#include <torch/extension.h>

torch::Tensor sub_add_sub_index_Eemb_h_index_Eemb_t_index_Remb_r_scal_mul_vec_vec_mul_vec_index_Remb_r_sub_index_Eemb_h_index_Eemb_t_index_Remb_r(int batch_size, int dim, int nnodes, torch::Tensor obj_Eemb, torch::Tensor obj_h, torch::Tensor obj_t, int nedges, torch::Tensor obj_Remb, torch::Tensor obj_r)
{
    auto Eemb = obj_Eemb.accessor<float, 2>();
auto h = obj_h.accessor<int, 1>();
auto t = obj_t.accessor<int, 1>();
torch::Tensor obj_arr6 = torch::empty({batch_size,dim}, at::kFloat);
auto arr6 = obj_arr6.accessor<float, 2>();
for (int _l0 = 0; _l0 < batch_size; _l0 += 1) {
for (int _l1 = 0; _l1 < dim; _l1 += 1) {
arr6[_l0][_l1] = (Eemb[h[_l0]][_l1] - Eemb[t[_l0]][_l1]);
} 
} 
auto Remb = obj_Remb.accessor<float, 2>();
auto r = obj_r.accessor<int, 1>();
torch::Tensor obj_arr12 = torch::empty({batch_size,dim}, at::kFloat);
auto arr12 = obj_arr12.accessor<float, 2>();
for (int _l2 = 0; _l2 < batch_size; _l2 += 1) {
for (int _l3 = 0; _l3 < dim; _l3 += 1) {
arr12[_l2][_l3] = (arr6[_l2][_l3] + Remb[r[_l2]][_l3]);
} 
} 
torch::Tensor obj_arr15 = torch::empty({batch_size,dim}, at::kFloat);
auto arr15 = obj_arr15.accessor<float, 2>();
for (int _l4 = 0; _l4 < batch_size; _l4 += 1) {
for (int _l5 = 0; _l5 < dim; _l5 += 1) {
arr15[_l4][_l5] = (Eemb[h[_l4]][_l5] - Eemb[t[_l4]][_l5]);
} 
} 
torch::Tensor obj_arr18 = torch::empty({batch_size}, at::kFloat);
auto arr18 = obj_arr18.accessor<float, 1>();
for (int _l6 = 0; _l6 < batch_size; _l6 += 1) {
for (int _l7 = 0; _l7 < dim; _l7 += 1) {
arr18[_l6] += (Remb[r[_l6]][_l7] * arr15[_l6][_l7]);
} 
} 
torch::Tensor obj_arr21 = torch::empty({batch_size,dim}, at::kFloat);
auto arr21 = obj_arr21.accessor<float, 2>();
for (int _l8 = 0; _l8 < batch_size; _l8 += 1) {
for (int _l9 = 0; _l9 < dim; _l9 += 1) {
arr21[_l8][_l9] = (arr18[_l8] * Remb[r[_l8]][_l9]);
} 
} 
torch::Tensor obj_arr24 = torch::empty({batch_size,dim}, at::kFloat);
auto arr24 = obj_arr24.accessor<float, 2>();
for (int _l10 = 0; _l10 < batch_size; _l10 += 1) {
for (int _l11 = 0; _l11 < dim; _l11 += 1) {
arr24[_l10][_l11] = (arr12[_l10][_l11] - arr21[_l10][_l11]);
} 
} 
return obj_arr24;

}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("run", &sub_add_sub_index_Eemb_h_index_Eemb_t_index_Remb_r_scal_mul_vec_vec_mul_vec_index_Remb_r_sub_index_Eemb_h_index_Eemb_t_index_Remb_r);
}
[<core.ir.Assignment object at 0x7f241842f1f0>] <core.ir.Scalar object at 0x7f241842f2e0>
arr6[_l0][_l1] = (Eemb[h[_l0]][_l1] - Eemb[t[_l0]][_l1]);

[<core.ir.Assignment object at 0x7f241842e350>] <core.ir.Scalar object at 0x7f241842e440>
arr21[_l8][_l9] = (arr18[_l8] * Remb[r[_l8]][_l9]);

[<core.ir.Assignment object at 0x7f241842f1f0>, <core.ir.Assignment object at 0x7f241842ece0>] <core.ir.Scalar object at 0x7f241842edd0>
arr6[_l2][_l3] = (Eemb[h[_l2]][_l3] - Eemb[t[_l2]][_l3]);

arr12[_l2][_l3] = (arr6[_l2][_l3] + Remb[r[_l2]][_l3]);

#include <torch/extension.h>

torch::Tensor sub_add_sub_index_Eemb_h_index_Eemb_t_index_Remb_r_scal_mul_vec_vec_mul_vec_index_Remb_r_sub_index_Eemb_h_index_Eemb_t_index_Remb_r(int batch_size, int dim, int nnodes, torch::Tensor obj_Eemb, torch::Tensor obj_h, torch::Tensor obj_t, int nedges, torch::Tensor obj_Remb, torch::Tensor obj_r)
{
    auto Eemb = obj_Eemb.accessor<float, 2>();
auto h = obj_h.accessor<int, 1>();
auto t = obj_t.accessor<int, 1>();
torch::Tensor obj_arr6 = torch::empty({batch_size,dim}, at::kFloat);
auto arr6 = obj_arr6.accessor<float, 2>();
auto Remb = obj_Remb.accessor<float, 2>();
auto r = obj_r.accessor<int, 1>();
torch::Tensor obj_arr12 = torch::empty({batch_size,dim}, at::kFloat);
auto arr12 = obj_arr12.accessor<float, 2>();
torch::Tensor obj_arr15 = torch::empty({batch_size,dim}, at::kFloat);
auto arr15 = obj_arr15.accessor<float, 2>();
for (int _l4 = 0; _l4 < batch_size; _l4 += 1) {
for (int _l5 = 0; _l5 < dim; _l5 += 1) {
arr15[_l4][_l5] = (Eemb[h[_l4]][_l5] - Eemb[t[_l4]][_l5]);
} 
} 
torch::Tensor obj_arr18 = torch::empty({batch_size}, at::kFloat);
auto arr18 = obj_arr18.accessor<float, 1>();
for (int _l6 = 0; _l6 < batch_size; _l6 += 1) {
for (int _l7 = 0; _l7 < dim; _l7 += 1) {
arr18[_l6] += (Remb[r[_l6]][_l7] * arr15[_l6][_l7]);
} 
} 
torch::Tensor obj_arr21 = torch::empty({batch_size,dim}, at::kFloat);
auto arr21 = obj_arr21.accessor<float, 2>();
torch::Tensor obj_arr24 = torch::empty({batch_size,dim}, at::kFloat);
auto arr24 = obj_arr24.accessor<float, 2>();
for (int _l10 = 0; _l10 < batch_size; _l10 += 1) {
for (int _l11 = 0; _l11 < dim; _l11 += 1) {
arr6[_l2][_l3] = (Eemb[h[_l2]][_l3] - Eemb[t[_l2]][_l3]);
arr12[_l10][_l11] = (arr6[_l10][_l11] + Remb[r[_l10]][_l11]);
arr21[_l10][_l11] = (arr18[_l10] * Remb[r[_l10]][_l11]);
arr24[_l10][_l11] = (arr12[_l10][_l11] - arr21[_l10][_l11]);
} 
} 
return obj_arr24;

}

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("run", &sub_add_sub_index_Eemb_h_index_Eemb_t_index_Remb_r_scal_mul_vec_vec_mul_vec_index_Remb_r_sub_index_Eemb_h_index_Eemb_t_index_Remb_r);
}
