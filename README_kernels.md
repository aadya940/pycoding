# Installing Jupyter Kernels for Multiple Languages

Jupyter supports multiple programming languages via kernels. This guide provides instructions on installing kernels for:

- **Python**
- **C/C++**
- **Julia**
- **Rust**
- **Bash**
- **R**

## 1. Python Kernel
Jupyter's default kernel is Python. Ensure it is installed and updated with:
```bash
pip install ipykernel
python -m ipykernel install --user
```

## 2. C/C++ Kernel
To run C/C++ in Jupyter, install **xeus-cling**:
```bash
conda install -c conda-forge xeus-cling
```
For additional setup, refer to [xeus-cling GitHub](https://github.com/jupyter-xeus/xeus-cling).

## 3. Julia Kernel
Julia's Jupyter integration is managed by **IJulia**:
```julia
using Pkg
Pkg.add("IJulia")
```
This automatically configures Julia in Jupyter.

## 4. Rust Kernel
Install the Rust kernel using **Evcxr**:
```bash
cargo install evcxr_jupyter
evcxr_jupyter --install
```

## 5. Bash Kernel
To execute Bash commands in Jupyter, install the Bash kernel:
```bash
pip install bash_kernel
python -m bash_kernel.install
```

## 6. R Kernel
To use R in Jupyter, install the **IRkernel** package:
```r
install.packages("IRkernel")
IRkernel::installspec(user = TRUE)
```

## Verifying Installation
Check installed kernels with:
```bash
jupyter kernelspec list
```
This should display all installed kernels along with their paths.

## Additional Resources
- [Jupyter Kernels Documentation](https://jupyter.readthedocs.io/en/latest/projects/kernels.html)
- [IRkernel GitHub](https://github.com/IRkernel/IRkernel)
