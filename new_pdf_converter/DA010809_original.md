# Page 1

#### E(n)-Equivariant Graph Neural Networks Emulating Mesh-Discretized Physics March 2023 Masanobu Horie




# Page 2

#### E(n)-Equivariant Graph Neural Networks Emulating Mesh-Discretized Physics

###### Graduate School of Science and Technology Degree Programs in Systems and Information Engineering University of Tsukuba

#### March 2023 Masanobu Horie




# Page 3

# **Acknowledgment**

First and foremost, I would like to thank my supervisor Asst. Prof. Naoto Mitsume for all


his support. I tremendously appreciate his inspiring advice for research, countless fruitful


discussions, and enjoyable time. In addition to technical matters, he has shown me the


importance of telling a clear story, thinking about the relationship between my and others’


research, and having social connections with other researchers.


I am grateful to Prof. Daigoro Isobe, Assoc. Prof. Tetsuya Matsuda, Assoc. Prof.


Mayuko Nishio, and Assoc. Prof. Mitsuteru Asai for reviewing my research and providing


insightful feedback as my dissertation committee.


I would like to thank my collaborators, Asst. Prof. Naoki Morita, Dr. Toshiaki Hish

inuma, and Mr. Yu Ihara. I learned a lot of technical things thanks to their support.


This work was supported by JSPS KAKENHI (Grant Number 19H01098), JSPS Grant

in-Aid for Scientific Research (B) (Grant Number 22H03601), JST PRESTO (Grant Num

ber JPMJPR21O9), and NEDO (Grant Number JPNP14012). I gratefully acknowledge


their support.


RICOS Co. Ltd. also supports the work in terms of computational resources and pro

vides me an opportunity to pursue this Ph.D. project.


Finally, I would like to thank my family, my father Jun-ichi, mother Naoko, sister


Yuriko, and wife Suzuka, for their continuous support. My wife, Suzuka, has been encour

aging me at any time. She made me excellent food like tempura, karaage, and ozouni when


I was happy or unhappy with my research. It is awesome to share my life with you.


i




# Page 4



# Page 5

# **Contents**

**List of Figures** **ix**


**List of Tables** **xv**


**Nomenclature** **xix**


**1** **Introduction** **1**


1.1 Motivation . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 1


1.2 Objective and Scope . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 3


1.3 Outline of Dissertation . . . . . . . . . . . . . . . . . . . . . . . . . . . . 4


**2** **Background** **7**


2.1 Machine Learning . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 7


2.1.1 Foundations of Supervised Learning . . . . . . . . . . . . . . . . . 7


2.1.2 Graph Neural Networks (GNNs) . . . . . . . . . . . . . . . . . . . 9


2.1.2.1 Graph . . . . . . . . . . . . . . . . . . . . . . . . . . . 9


2.1.2.2 Pointwise MLP . . . . . . . . . . . . . . . . . . . . . . 12


2.1.2.3 Message Passing Neural Networks (MPNNs) . . . . . . . 14


2.1.2.4 Graph Convolutional Network (GCN) . . . . . . . . . . 15


2.1.3 Equivariance . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 17


iii




# Page 6

2.1.3.1 Group Theory . . . . . . . . . . . . . . . . . . . . . . . 17


2.1.3.2 Equivariant Model . . . . . . . . . . . . . . . . . . . . . 18


2.2 Numerical Analysis . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 21


2.2.1 Partial Differential Equations (PDEs) with Boundary Conditions . . 21


2.2.2 Discretization . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23


2.2.3 Nonlinear Solver and Optimization . . . . . . . . . . . . . . . . . 24


2.2.3.1 Basic Formula for Iterative Methods . . . . . . . . . . . 24


2.2.3.2 Newton–Raphson Method and Quasi-Newton Method . . 25


2.2.3.3 Gradient Descent Method . . . . . . . . . . . . . . . . . 26


2.2.3.4 Barzilai–Borwein Method . . . . . . . . . . . . . . . . . 27


2.2.4 Numerical Analysis from a Graph Representation View . . . . . . . 29


2.2.4.1 Finite Difference Method . . . . . . . . . . . . . . . . . 29


2.2.4.2 Finite Element Method (FEM) . . . . . . . . . . . . . . 32


2.2.4.3 Least Squares Moving Particle Semi-Implicit (LSMPS)


Method . . . . . . . . . . . . . . . . . . . . . . . . . . . 36


**3** **IsoGCN: E(** _**n**_ **)-Equivariant Graph Convolutional Network** **39**


3.1 Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 39


3.2 Related Prior Work . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41


3.2.1 GCN . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41


3.2.2 TFN . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 41


3.2.3 GNN Model for Physical Simulation . . . . . . . . . . . . . . . . . 42


3.3 Method . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42


3.3.1 Discrete Tensor Field . . . . . . . . . . . . . . . . . . . . . . . . . 42


3.3.2 Isometric Adjacency Matrix (IsoAM) . . . . . . . . . . . . . . . . 44




# Page 7

3.3.2.1 Definition of IsoAM . . . . . . . . . . . . . . . . . . . . 44


3.3.2.2 Property of IsoAM . . . . . . . . . . . . . . . . . . . . . 46


3.3.3 Construction of IsoGCN . . . . . . . . . . . . . . . . . . . . . . . 50


3.3.3.1 E( _n_ )-Invariant Layer . . . . . . . . . . . . . . . . . . . 51


3.3.3.2 E( _n_ )-Equivariant Layer . . . . . . . . . . . . . . . . . . 51


3.3.4 IsoAM Refined for Numerical Analysis . . . . . . . . . . . . . . . 54


3.3.4.1 Definition of Differential IsoAM . . . . . . . . . . . . . 54


3.3.4.2 Partial Derivative . . . . . . . . . . . . . . . . . . . . . 55


3.3.4.3 Gradient . . . . . . . . . . . . . . . . . . . . . . . . . . 56


3.3.4.4 Divergence . . . . . . . . . . . . . . . . . . . . . . . . . 56


3.3.4.5 Laplacian Operator . . . . . . . . . . . . . . . . . . . . 57


3.3.4.6 Jacobian and Hessian Operators . . . . . . . . . . . . . . 58


3.3.5 IsoGCN Modeling Details . . . . . . . . . . . . . . . . . . . . . . 59


3.3.5.1 Activation and Bias . . . . . . . . . . . . . . . . . . . . 59


3.3.5.2 Preprocessing of Input Feature . . . . . . . . . . . . . . 59


3.3.5.3 Scaling . . . . . . . . . . . . . . . . . . . . . . . . . . . 60


3.3.5.4 Tensor Rank . . . . . . . . . . . . . . . . . . . . . . . . 60


3.3.5.5 Implementation . . . . . . . . . . . . . . . . . . . . . . 60


3.4 Numerical Experiments . . . . . . . . . . . . . . . . . . . . . . . . . . . . 61


3.4.1 Differential Operator Dataset . . . . . . . . . . . . . . . . . . . . . 62


3.4.1.1 Task Definition . . . . . . . . . . . . . . . . . . . . . . 62


3.4.1.2 Model Architectures . . . . . . . . . . . . . . . . . . . . 63


3.4.1.3 Results . . . . . . . . . . . . . . . . . . . . . . . . . . . 64


3.4.2 Anisotropic Nonlinear Heat Equation Dataset . . . . . . . . . . . . 68




# Page 8

3.4.2.1 Task Definition . . . . . . . . . . . . . . . . . . . . . . 68


3.4.2.2 Dataset . . . . . . . . . . . . . . . . . . . . . . . . . . . 69


3.4.2.3 Input and Output Features . . . . . . . . . . . . . . . . . 71


3.4.2.4 Model Architectures . . . . . . . . . . . . . . . . . . . . 72


3.4.2.5 Results . . . . . . . . . . . . . . . . . . . . . . . . . . . 74


3.5 Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 79


**4** **Physics-Embedded Neural Network:** **Boundary Condition and Implicit**


**Method** **81**


4.1 Introduction . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 81


4.2 Related Prior Work . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 83


4.2.1 Physics-Informed Neural Network (PINN) . . . . . . . . . . . . . 83


4.2.2 Graph Neural Network Based PDE Solver . . . . . . . . . . . . . . 84


4.3 Method . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 84


4.3.1 Dirichlet Boundary Model . . . . . . . . . . . . . . . . . . . . . . 85


4.3.1.1 Boundary Encoder . . . . . . . . . . . . . . . . . . . . . 85


4.3.1.2 Dirichlet Layer . . . . . . . . . . . . . . . . . . . . . . . 86


4.3.1.3 Pseudoinverse Decoder . . . . . . . . . . . . . . . . . . 86


4.3.2 Neumann Boundary Model . . . . . . . . . . . . . . . . . . . . . . 87


4.3.2.1 Definition of NeumannIsoGCN (NIsoGCN) . . . . . . . 88


4.3.2.2 Derivation of NIsoGCN . . . . . . . . . . . . . . . . . . 88


4.3.2.3 Generalization of NIsoGCN . . . . . . . . . . . . . . . . 91


4.3.3 Neural Nonlinear Solver . . . . . . . . . . . . . . . . . . . . . . . 92


4.3.3.1 Implicit Euler Method in Encoded Space . . . . . . . . . 92


4.3.3.2 Barzilai–Borwein Method for Neural Nonlinear Solver . 93




# Page 9

4.3.3.3 Formulation of Neural Nonlinear Solver . . . . . . . . . 94


4.4 Numerical Experiments . . . . . . . . . . . . . . . . . . . . . . . . . . . . 95


4.4.1 Gradient Dataset . . . . . . . . . . . . . . . . . . . . . . . . . . . 95


4.4.1.1 Taks Definition . . . . . . . . . . . . . . . . . . . . . . 95


4.4.1.2 Model Architecture . . . . . . . . . . . . . . . . . . . . 96


4.4.1.3 Results . . . . . . . . . . . . . . . . . . . . . . . . . . . 97


4.4.2 Advection-Diffusion Dataset . . . . . . . . . . . . . . . . . . . . . 98


4.4.2.1 Task Definition . . . . . . . . . . . . . . . . . . . . . . 98


4.4.2.2 Dataset . . . . . . . . . . . . . . . . . . . . . . . . . . . 98


4.4.2.3 Model Architecture . . . . . . . . . . . . . . . . . . . . 99


4.4.2.4 Results . . . . . . . . . . . . . . . . . . . . . . . . . . . 104


4.4.3 Incompressible Flow Dataset . . . . . . . . . . . . . . . . . . . . . 108


4.4.3.1 Task Definition . . . . . . . . . . . . . . . . . . . . . . 108


4.4.3.2 Dataset . . . . . . . . . . . . . . . . . . . . . . . . . . . 109


4.4.3.3 Machine Learning Models . . . . . . . . . . . . . . . . . 112


4.4.3.4 Training Details . . . . . . . . . . . . . . . . . . . . . . 114


4.4.3.5 Results . . . . . . . . . . . . . . . . . . . . . . . . . . . 118


4.4.3.6 Ablation Study Results . . . . . . . . . . . . . . . . . . 121


4.4.3.7 Detailed Results . . . . . . . . . . . . . . . . . . . . . . 124


4.4.3.8 Evaluation of Out-of-Distribution Generalization . . . . . 128


4.5 Conclusion . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 130


**5** **Conclusion** **133**


**Bibliography** **137**




# Page 10

**Index** **145**




# Page 11

# **List of Figures**

2.1 (a) An example of a graph, (b) the same graph with permutated indices,


and (c) corresponding adjacency and permutation matrices. . . . . . . . . . 11


2.2 A path graph with five vertices. . . . . . . . . . . . . . . . . . . . . . . . . 12


2.3 Schematic diagrams of (a) pointwise MLP, (b) MPNN, and (c) GCN. . . . . 14


2.4 An example of a graph and its corresponding adjacency matrix _**A**_, degree

matrix _**D**_ [˜], renormalized adjacency matrix _**A**_ [ˆ], and resulting output _**h**_ out _,_ 1 .


their can be seen that the GCN model considers information on neighboring


vertices through a weighted sum determined from the graph structure. . . . 16


2.5 Examples of (a) a domain Ω and (b) a mesh representing the corresponding


discretized domain. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 23


2.6 An example of a 1D _u_ field spatially discretized using FDM. . . . . . . . . 29


2.7 An example of 2D _u_ field spatially discretized using FDM and its corre

sponding edge connectivity. . . . . . . . . . . . . . . . . . . . . . . . . . 31


2.8 An example of a 1D _u_ field spatially discretized using FEM. . . . . . . . . 34


2.9 An example of 2D spatially discretized unstructured grid for FEM (black)


and its corresponding edge connectivity (blue). The connectivity of the


graph is not necessarily the same as the edges of the mesh. . . . . . . . . . 35


3.1 Schematic diagrams of (a) rank-1 tensor field _**H**_ [(1)] with the number of


features equaling 2 and (b) the simplest case of _**G**_ _ij_ ;;: = _δ_ _il_ _δ_ _jk_ _A_ _ij_ _**I**_ ( _**x**_ _k_ _−_


_**x**_ _l_ ) = _A_ _ij_ ( _**x**_ _j_ _−_ _**x**_ _i_ ). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 42


ix




# Page 12

3.2 The IsoGCN models used for (a) the scalar field to the gradient field, (b) the


scalar field to the Hessian field, (c) the gradient field to the Laplacian field,


(d) the gradient field to the Hessian field of the gradient operator dataset.


Gray boxes are trainable components. In each trainable cell, we put the


number of units in each layer along with the activation functions used. _∗⃝_


denotes the multiplication in the feature direction. . . . . . . . . . . . . . 63


3.3 (Top) the gradient field and (bottom) the error vector between the prediction


and the ground truth of a test data sample. The error vectors are exaggerated


by a factor of 2 for clear visualization. . . . . . . . . . . . . . . . . . . . . 65


3.4 The process of generating the dataset. A smaller clscale parameter gener

ates smaller meshes. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 70


3.5 The IsoGCN model used for the anisotropic nonlinear heat equation


dataset. Gray boxes are trainable components. In each trainable cell, we


put the number of units in each layer along with the activation functions


used. Below the unit numbers, the activation function used for each layer


is also shown. _∗⃝_ denotes the multiplication in the feature direction, _⊙_


denotes the contraction, and _⊕_ denotes the addition in the feature direction. 72


3.6 (Top) the temperature field of the ground truth and inference results and


(bottom) the error between the prediction and the ground truth of a test


data sample. The error is exaggerated by a factor of 2 for clear visualization. 75


3.7 Comparison between (left) samples in the training dataset, (center) ground


truth computed through FEA, and (right) IsoGCN inference result. For


both the ground truth and inference result, _|V|_ = 1 _,_ 011 _,_ 301. One can see


that IsoGCN can predict the temperature field for a mesh, which is much


larger than these in the training dataset. . . . . . . . . . . . . . . . . . . . 76




# Page 13

4.1 Overview of the proposed method. On decoding input features, we apply


boundary encoders to boundary conditions. Thereafter, we apply a nonlin

ear solver consisting of an E( _n_ )-equivariant graph neural network in the


encoded space. Here, we apply encoded boundary conditions for each it

eration of the nonlinear solver. After the solver stops, we apply the pseu

doinverse decoder to satisfy Dirichlet boundary conditions. . . . . . . . . . 83


4.2 Architecture used for (a) original IsoGCN and (b) NIsoGCN training. In


each trainable cell, we put the number of units in each layer along with the


activation functions used. . . . . . . . . . . . . . . . . . . . . . . . . . . 96


4.3 Gradient field (top) and the magnitude of error between the predicted gradi

ent and the ground truth (bottom) of a test data sample, sliced on the center


of the mesh. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 97


4.4 The concept of the neural nonlinear solver for time series data with au

toregressive architecture. The solver’s output is fed to the same solver to


obtain the state at the next time step (bold red arrow). Please note that this


architecture can be applied to arbitrary time series lengths. . . . . . . . . . 101


4.5 The overview of the PENN architecture for the advection-diffusion dataset.


Gray boxes with continuous (dotted) lines are trainable (untrainable) com

ponents. Arrows with dotted lines correspond to the loop. In each trainable


cell, we put the number of units in each layer along with the activation


functions used. The bold red arrow corresponds to the one in Figure 4.4. . 102


4.6 The overview of the PENN architecture for the advection-diffusion dataset.


Gray boxes with continuous (dotted) lines are trainable (untrainable) com

ponents. In each trainable cell, we put the number of units in each layer


along with the activation functions used. . . . . . . . . . . . . . . . . . . 103


4.7 Visual comparison on a test sample between (left) ground truth obtained


from OpenFOAM computation with fine spatial-temporal resolution and

(right) prediction by PENN. Here, _c_ = 0 _._ 9, _D_ = 0 _._ 0, and _T_ [ˆ] = 0 _._ 4. . . . . . 105




# Page 14

4.8 Visual comparison on a test sample between (left) ground truth obtained


from OpenFOAM computation with fine spatial-temporal resolution and

(right) prediction by PENN. Here, _c_ = 0 _._ 0, _D_ = 0 _._ 4, and _T_ [ˆ] = 0 _._ 3. . . . . . 106


4.9 Visual comparison on a test sample between (left) ground truth obtained


from OpenFOAM computation with fine spatial-temporal resolution and

(right) prediction by PENN. Here, _c_ = 0 _._ 6, _D_ = 0 _._ 3, and _T_ [ˆ] = 0 _._ 8. . . . . . 107


4.10 Three template shapes used to generate the dataset. _a_ 1, _b_ 1, _b_ 2, _c_ 1, and _c_ 2 are


the design parameters. . . . . . . . . . . . . . . . . . . . . . . . . . . . . 110


4.11 Boundary conditions of _**u**_ used to generate the dataset. The continuous


lines and dotted lines correspond to Dirichlet and Neumann boundaries. . . 111


4.12 Boundary conditions of _p_ used to generate the dataset. The continuous lines


and dotted lines correspond to Dirichlet and Neumann boundaries. . . . . . 111


4.13 The overview of the PENN architecture for the incompressible flow dataset.


Gray boxes with continuous (dotted) lines are trainable (untrainable) com

ponents. Arrows with dotted lines correspond to the loop. In each trainable


cell, we put the number of units in each layer along with the activation


functions used. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 115


4.14 The neural nonlinear solver for velocity. Gray boxes with continuous (dot

ted) lines are trainable (untrainable) components. Arrows with dotted lines


correspond to the loop. In each trainable cell, we put the number of units


in each layer along with the activation functions used. . . . . . . . . . . . 116


4.15 The neural nonlinear solver for pressure. Gray boxes with continuous (dot

ted) lines are trainable (untrainable) components. In each trainable cell, we


put the number of units in each layer along with the activation functions


used. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 117




# Page 15

4.16 Comparison of the velocity field (top two rows) and the pressure field (bot

tom two rows) without (first and third rows) and with (second and fourth


rows) random rotation and translation. PENN prediction is consistent under


rotation and translation due to the E( _n_ )-equivariance nature of the model,


while MP-PDE’s predictive performance degrades under transformations. . 119


4.17 Comparison of computation time and total MSE loss ( _**u**_ and _p_ ) on the


test dataset (with and without transformation) between OpenFOAM, MP

PDE, and PENN. The error bar represents the standard error of the mean.


All computation was done using one core of Intel Xeon CPU E5-2695


v2@2.40GHz. Data used to plot this figure are shown in Tables 4.6, 4.7,


and 4.8. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 120


4.18 Visual comparison of the ablation study of (i) ground truth, (ii) the model


without the neural nonlinear solver (Model (C)), (iii) the model without


pseudoinverse decoder with Dirichlet layer after decoding (Model (G)), and


(iv) PENN. It can be observed that PENN improves the prediction smooth

ness, especially for the velocity field. . . . . . . . . . . . . . . . . . . . . 123


4.19 The relationship between the relative MSE of the velocity _**u**_ and inlet velocity.128


4.20 The relationship between the relative MSE of the pressure _p_ and inlet velocity.129


4.21 The visualization of velocity fields with inlet velocities _u_ inlet of 2.0 and 0.5. 129


4.22 The visualization of velocity fields for a larger sample. . . . . . . . . . . . 130


4.23 The visualization of pressure fields for a larger sample. . . . . . . . . . . . 131




# Page 16



# Page 17

# **List of Tables**

3.1 Correspondence between the differential operators and the expressions us
ing the IsoAM _**G**_ [˜] . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 55


3.2 Summary of the hyperparameter setting for both the TFN and SE(3)

Transformer. For the parameters not in the table, we used the default setting


[in the implementation of https://github.com/FabianFuchsML/](https://github.com/FabianFuchsML/se3-transformer-public)


[se3-transformer-public.](https://github.com/FabianFuchsML/se3-transformer-public) . . . . . . . . . . . . . . . . . . . . . . 64


3.3 Summary of the test losses (mean squared error _±_ the standard error of the


mean in the original scale) of the differential operator dataset: 0 _→_ 1 (the


scalar field to the gradient field), 0 _→_ 2 (the scalar field to the Hessian


field), 1 _→_ 0 (the gradient field to the Laplacian field), and 1 _→_ 2 (the


gradient field to the Hessian field). Here, if “ _**x**_ ” is “Yes”, _**x**_ is also in the


input feature. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 66


3.4 Summary of the prediction time on the test dataset. 0 _→_ 1 corresponds to


the scalar field to the gradient field, and 0 _→_ 2 corresponds to the scalar


field to the Hessian field. Each computation was run on the same GPU


(NVIDIA Tesla V100 with 32 GiB memory). OOM denotes the out-of

memory of the GPU. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 67


3.5 Summary of the hyperparameter setting for both the TFN and SE(3)

Transformer. For the parameters not written in the table, we used


[the default setting in the implementation of https://github.com/](https://github.com/FabianFuchsML/se3-transformer-public)


[FabianFuchsML/se3-transformer-public. . . . . . . . . . . .](https://github.com/FabianFuchsML/se3-transformer-public) 74


xv




# Page 18

3.6 Summary of the test losses (mean squared error _±_ the standard error of the


mean in the original scale) of the anisotropic nonlinear heat dataset. Here,


if “ _**x**_ ” is “Yes”, _**x**_ is also in the input feature. OOM denotes the out-of

memory on the applied GPU (32 GiB). . . . . . . . . . . . . . . . . . . . . 77


3.7 Comparison of computation time. To generate the test data, we sampled


CAD data from the test dataset and then generated the mesh for the graph


to expand while retaining the element volume at almost the same size. The


initial temperature field and the material properties are set randomly using


the same methodology as the dataset sample generation. For a fair com

parison, each computation was run on the same CPU (Intel Xeon E5-2695


v2@2.40GHz) using one core, and we excluded file I/O time from the mea

sured time. OOM denotes the out-of-memory (500 GiB). . . . . . . . . . . 78


4.1 MSE loss ( _±_ the standard error of the mean) on test dataset of gradient


prediction. ˆ _g_ Neumann is the loss computed only on the boundary where the


Neuman condition is set. . . . . . . . . . . . . . . . . . . . . . . . . . . . 97


4.2 MSE loss ( _±_ the standard error of the mean) on test dataset of the


advection-diffusion dataset. . . . . . . . . . . . . . . . . . . . . . . . . . 104


4.3 MSE loss ( _±_ the standard error of the mean) on test dataset of incompress

ible flow. If ”Trans.” is ”Yes,” it means evaluation is done on randomly


rotated and transformed test dataset. ˆ _·_ Dirichlet is the loss computed only on


the boundary where the Dirichlet condition is set for each _**u**_ and _p_ . MP

PDE’s results are based on the time window size equaling 40 as it showed


the best performance in the tested MP-PDEs. For complete results, see


Table 4.5. . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 118


4.4 Ablation study on the incompressible flow dataset. The value represents


MSE loss ( _±_ standard error of the mean) on the test dataset. ”Divergent”


means the implicit solver does not converge and the loss gets extreme value


( _∼_ 10 [14] ). . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 122




# Page 19

4.5 MSE loss ( _±_ the standard error of the mean) on test dataset of incompress

ible flow. If ”Trans.” is ”Yes”, it means evaluation on randomly rotated and


transformed test dataset. _n_ denotes the number of hidden features, _r_ de

notes the number of iterations in the neural nonlinear solver used in PENN


models, and TW denotes the time window size used in MP-PDE models. . 125


4.6 MSE loss ( _±_ the standard error of the mean) of PENN models on test


dataset of incompressible flow. . . . . . . . . . . . . . . . . . . . . . . . . 126


4.7 MSE loss ( _±_ the standard error of the mean) of MP-PDE models on test


dataset of incompressible flow. . . . . . . . . . . . . . . . . . . . . . . . . 126


4.8 MSE loss ( _±_ the standard error of the mean) of OpenFOAM computations


on test dataset of incompressible flow. . . . . . . . . . . . . . . . . . . . . 127


4.9 MSE loss ( _±_ the standard error of the mean) on the dataset with larger


samples. ˆ _g_ Neumann is the loss computed only on the boundary where the


Neuman condition is set. . . . . . . . . . . . . . . . . . . . . . . . . . . . 130




# Page 20



# Page 21

# **Nomenclature**

**General**


R Set of real numbers


Z Set of integers


Z [+] Set of positive integers


Z [0+] Set of non-negative integers


_M_ _ij_ Element ( _i, j_ ) of matrix _**M**_


_v_ _i_ Element _i_ of vector _**v**_


**Chapter 2**


_G_ Graph


_V_ Vertex set


_|V|_ Number of vertices


_N_ _v_ Set of neighboring vertices of vertex _v_ (Equation 2.12)


_**A**_ Adjacency matrix (Equation 2.14)


_J_ Index set


_π_ : _J →_ _J_ Permutation


_**P**_ Permutation matrix (Equation 2.15)


_**L**_ Graph Laplacian matrix (Equation 2.17)


xix




# Page 22

_**D**_ Degree matrix (Equation 2.18)


_**W**_ Weight matrix


_**b**_ Bias


_σ_ Activation function


_**H**_ _∈_ R _[V×][d]_ Vertex features


_{_ _**h**_ _i_ _}_ _i∈V_ Set of vertex features


_{_ _**e**_ _ij_ _}_ ( _i,j_ ) _∈E_ Set of edge features


_**A**_ ˆ Renormalized adjacency matrix


_**A**_ ˜ Adjacency matrix with added self-connections


_**D**_ ˜ Degree matrix of _**A**_ [˜]


_**I**_ _N_ Identity matrix of size _N_


_G_ Group


GL( _n_ ) General linear group


SO( _n_ ) Special orthogonal group


_S_ _n_ Symmetric group


E( _n_ ) Euclidean group


_α_ ( _g, x_ ) Group action of _g ∈_ _G_ to _x ∈_ _X_ (also denoted as _g · x_ )


_δ_ _ij_ Kronecker delta (Equation 2.48)


_D_ Nonlinear differential operator (Equation 2.52)


Ω Analysis domain (Equation 2.52)


_∂_ Ω Boundary of Ω


_∂_ Ω Dirichlet Dirichlet boundary (Equation 2.54)


_∂_ Ω Neumann Neumann boundary (Equation 2.55)


_**r**_ Residual (Equations 2.60, 2.62)




# Page 23

_**R**_ Residual vector (Equations 2.63)


_**e**_ _x_ _,_ _**e**_ _y_ The unit vectors in the _X_ and _Y_ directions


**Chapter 3**


_**H**_ [(] _[p]_ [)] _∈_ R _[|V|×][d]_ [f] _[×][n]_ _[p]_ A rank- _p_ discrete tensor field (Equation 3.5)


_**G**_ _∈_ R _[|V|×]_ [1] _[×][d]_ [1] IsoAM (Equation 3.8)


_**G**_ ˜ _∈_ R _[|V|×]_ [1] _[×][d]_ [1] Differential IsoAM (Equation 3.46)


_**G**_ _ij_ ;;: = _**g**_ _ij_ _∈_ R _[n]_ Slice in the spatial index of _**G**_


**Chapter 4**


_D_ NIsoGCN Nonlinear differential operator constructed using NIsoGCN




# Page 24



# Page 25

# **Chapter 1** **Introduction**

1.1 M OTIVATION


Partial differential equations (PDEs) are of great interest to many scientists due to their


wide-ranging applications in fields such as mathematics, physics, and engineering. Numer

ical analysis is commonly used to solve PDEs since most real-life PDE problems cannot be


solved analytically. For instance, predicting fluid behavior in complex shapes is of particu

lar significance in various fields, including product design, disaster reduction, and weather


forecasting. However, solving these problems using classical solvers is time-consuming


and challenging. Machine learning has emerged as a promising alternative for addressing


these complex problems because, unlike classical solvers, it can leverage data that is similar


to the state being predicted.


The main challenge in tackling complex phenomena like fluids mechanics using ma

chine learning is to achieve good generalization performance, mainly owing to the follow

ing two reasons:


   - **Variable degrees of freedom** : Classical numerical analysis methods discretize con

tinuous fields of physical quantities (e.g., temperature or velocity fields) into vari

ables at finite points in a mesh. The number of points, which correspond to the


degrees of freedom of the analysis model, can vary depending on the shape of inter

1




# Page 26

**2** 1. Introduction


est, which requires some flexibility of the machine learning model to tolerate such


uncertainty.


   - **Large number of degrees of freedom** : A practical analysis often consists of a


huge number of degrees of freedom, typically over a million. This is considerably


larger than typical machine learning datasets, such as CIFAR-10 (Krizhevsky et al.,


2009), which has 3072 features per sample. The number of possible states in such


a complex system can be large and a purely data-driven approach may not cover


them due to the curse of dimensionality.


To address these challenges, we must incorporate appropriate assumptions and knowl

edge about the phenomena of interest into the machine learning model, which is known


as inductive bias. Numerous studies have successfully introduced various inductive biases,


such as local connectedness using graph neural networks (GNNs) (Chang & Cheng, 2020;


Sanchez-Gonzalez et al., 2020; Pfaff et al., 2021; Brandstetter et al., 2022). These studies


have shown that GNNs are effective in constructing PDE solvers as they can handle inputs


with an arbitrary number of degrees of freedom.


Although these methods have made significant progress in solving PDEs using ma

chine learning, there is still room for improvement. Specifically, we can incorporate more


inductive biases to reduce the numbers of degrees of freedom, for example, by considering


only half of the analysis domain if the phenomenon has bilateral symmetry, such as in the


aerodynamic analysis of a symmetric aircraft.


First, the physical symmetry regarding isometric transformation, i.e., E( _n_ ) transforma

tions, must be addressed when considering PDEs in Euclidean spaces because the nature


of physical phenomena in such spaces does not change under these transformations. Thus,


models that can accurately reflect physical symmetries, which are known as _equivariant_


functions regarding the transformation of interest, must be used.


Second, there is a need for an efficient and provable way to satisfy mixed boundary


conditions, i.e., Dirichlet and Neumann. Rigorous fulfillment of Dirichlet boundary condi

tions is indispensable because they are hard constraints, with different Dirichlet conditions


corresponding to different problems users would like to solve.




# Page 27

1.2. Objective and Scope **3**


Finally, we need to enhance the treatment of global interactions to predict the state


after a long time, when interactions tend to be global. GNNs have excellent generalization


properties because of their locally connected nature, but they may miss global interactions


owing to their localness.


1.2 O BJECTIVE AND S COPE


In this dissertation, we focus on mesh-based time-dependent numerical analysis. Mesh

based methods are widely utilized in practical numerical analysis due to their ability to


handle complex shapes often encountered in industrial design. Time-dependent analysis


typically demands a significant amount of computational time, as compared with steady

state analysis, because of the small time step required to ensure stable computation of the


time evolution. Therefore, we aim to exploit the full potential of machine learning for


conducting mesh-based time-dependent analyses.


The objective of this study is to develop a machine learning method that addresses


the challenges previously discussed. We aim to build a machine learning model with the


following key features:


1. Flexibility to handle arbitrary meshes using GNNs


2. E( _n_ )-equivariance to account for physical symmetries


3. Computational efficiency to provide faster predictions than conventional numerical


analysis methods


4. Capability to rigorously consider boundary conditions


5. Stability for predicting over long time steps by considering global interactions


In a previous study (Horie et al., 2021), we introduced _IsoGCN_, a computationally ef

ficient GNN that features E( _n_ )- invariance and equivariance, hence, complying with the


first three requirements outlined above. Specifically, this model simply modifies the defini

tion of an adjacency matrix essential for describing a graph, to realize E( _n_ )-equivariance.


Because the proposed approach relies on graphs, it can handle complex shapes that are usu

ally modeled using mesh or point cloud data structures. Furthermore, a specific form of the




# Page 28

**4** 1. Introduction


IsoGCN layer can describe essential physical laws by acting as a spatial differential opera

tor. Additionally, we demonstrated the computational efficiency of the proposed approach


for processing graphs with up to 1M vertices, which are common in real physical simula

tions, as well as its capacity to produce faster prediction with the same level of accuracy


compared with conventional finite element methods. Consequently, an IsoGCN can suit

ably replace physical simulations thanks to its power to express physical laws and faster,


scalable computation. The corresponding implementation code and dataset are available


online [1] .


Similarly, in a follow-up study (Horie & Mitsume (2022)), we proposed a _physics-_


_embedded neural network (PENN)_, which is a machine learning framework featuring prop

erties 3, 4, and 5 in the above list. We built PENN based on an IsoGCN to capture physical


symmetry and ensure fast prediction. Furthermore, we developed a method for consid

ering mixed boundary conditions and modified the stacking of GNNs using a nonlinear


solver, enabling the natural inclusion of global interactions in GNNs through global pool

ing and improving their interpretability. By conducting numerical experiments, we demon

strated the improved predictive performance of the model when dealing with Neumann


boundary conditions, as well as its ability to correctly fulfill Dirichlet boundary condi

tions. This method displayed state-of-the-art performance compared with that of a clas

sical, well-optimized numerical solver and a baseline machine learning model in terms of


speed-accuracy trade-off. The implementation code and dataset used for the experiments


are also available online [2] .


1.3 O UTLINE OF D ISSERTATION


In Chapter 2, we provide an overview of the background necessary for discussing our


research. We introduce essential machine learning models, particularly GNNs, that can


learn PDEs on complex shapes. In addition, we establish the concept of equivariance,


which is the focus of this study, and review the basics of numerical analysis and its rela

tionship to graphs.


1 [https://github.com/yellowshippo/isogcn-iclr2021](https://github.com/yellowshippo/isogcn-iclr2021)
2 [https://github.com/yellowshippo/penn-neurips2022](https://github.com/yellowshippo/penn-neurips2022)




# Page 29

1.3. Outline of Dissertation **5**


Chapter 3 presents IsoGCN, our essential computationally efficient GNN model with


E(n)-equivariance. First, we elaborate on the motivation for equivariance. Then, we explain


the method and prove its equivariance and its relationship to numerical analysis. Finally,


we report numerical experiments that demonstrate the effectiveness of IsoGCNs.


Chapter 4 discusses PENNs, which can correctly satisfy boundary conditions and global


interactions based on IsoGCNs. Here, we describe the methods for handling Dirichlet


and Neumann boundary conditions, and for including global interactions using a nonlin

ear solver. Subsequently, we demonstrate the superiority of the proposed method through


numerical experiments.


Finally, in Chapter 5, we summarize the main conclusions of this dissertation and men

tion the limitations of the research, pointing out an interesting future direction to address


them.




# Page 30

**6** 1. Introduction




# Page 31

# **Chapter 2** **Background**

2.1 M ACHINE L EARNING


In this section, we review the basics of machine learning and the essential models for


learning numerical analysis.


2.1.1 F OUNDATIONS OF S UPERVISED L EARNING


For the purposes of this study, we focus on supervised learning, which is informally


defined as constructing a function that maps a given input to a given output as accurately


as possible.


Supervised learning involves minimizing the error between the given target and the


prediction from the machine learning model. Let D _n_ := _{_ ( _**x**_ _i_ _∈X_ _,_ _**y**_ _i_ _∈Y_ ) _}_ _[n]_ _i_ =1 [denote]


a given training dataset, where _X_ and _Y_ are the input and output spaces, respectively. A


machine learning model with a set of learnable parameters _θ_ is defined as _**f**_ _θ_ : _X →Y_ .


Training is expressed as follows:


_θ_ _[∗]_ := arg min _R_ _n_ ( _θ_ ) _,_ (2.1)
_θ_


7




# Page 32

**8** 2. Background


where the training loss _R_ _n_ ( _θ_ ) is:


_R_ _n_ ( _θ_ ) := [1]

_n_



_n_
Y _L_ ( _**f**_ _θ_ ( _**x**_ _i_ ) _,_ _**y**_ _i_ ) _._ (2.2)


_i_ =1



and _L_ : _Y × Y →_ R is the _loss function_, which serves as an error scale.


Although training is performed using a training dataset, the goal of supervised learn

ing is to obtain a model applicable to the statistical population behind the dataset, unlike


a typical optimization problem where it is sufficient to obtain an optimal model for the


given data. However, because evaluating a model using a population in a practical set

ting is not feasible, we evaluate the trained model using a test dataset D [test] _n_ [test] [ :=] _[ {]_ [(] _**[x]**_ _i_ [test] _∈_

_X_ _,_ _**y**_ _i_ [test] _∈Y_ ) _}_ _[n]_ _i_ =1 [test] [, Which is different from the training dataset but sampled from the same]


distribution. The population loss is approximated as follows:


_R_ ( _θ_ _[∗]_ ) := _E_ [ _L_ ( _**f**_ _θ_ _∗_ ( _**x**_ ) _,_ _**y**_ )] (2.3)



_≈_ [1]

_n_ [test]



_n_ [test]
Y _L_ ( _**f**_ _θ_ _∗_ ( _**x**_ [test] _i_ ) _,_ _**y**_ _i_ [test] ) _,_ (2.4)


_i_ =1



where _E_ [ _·_ ] is the expected value.


As an example of supervised learning, let us consider linear regression. If _X_ = _Y_ = R,


it becomes a one-dimensional linear regression, which is the simplest case. In this case, the


machine learning model is expressed as:


_f_ _θ_ ( _x_ ) = _wx_ + _b_ (2.5)


_θ_ = ( _w ∈_ R _, b ∈_ R) _._ (2.6)


Using the least squares method, we define the loss function as


_L_ ( _y_ prediction _, y_ target ) = ( _y_ prediction _−_ _y_ target ) [2] _._ (2.7)




# Page 33

2.1. Machine Learning **9**


This can be easily generalized to higher-dimensional cases by letting


_X_ = R _[d]_ [in] (2.8)


_Y_ = R _[d]_ [out] (2.9)


_**f**_ _θ_ ( _x_ ) = _**W x**_ + _**b**_ (2.10)


_θ_ = ( _**W**_ _∈_ R _[d]_ [out] _[×][d]_ [in] _,_ _**b**_ _∈_ R _[d]_ [out] ) _,_ (2.11)


where _d_ in and _d_ out are the input and output dimensions, respectively. For more information


on machine learning, including supervised learning, see Bishop (2006).


2.1.2 G RAPH N EURAL N ETWORKS (GNN S )


This section provides an overview of the foundations of graph neural networks (GNNs),


which are a class of neural networks designed to handle graph-structured data. GNNs were


first proposed by Baskin et al. (1997); Sperduti & Starita (1997), and subsequently im

proved by (Gori et al., 2005; Scarselli et al., 2008). Because various data can be regarded


as graphs, GNNs have a broad range of application domains such as 3D shape recogni

tion (Fey et al., 2018; Monti et al., 2017), structural chemistry (Gilmer et al., 2017; Klicpera


et al., 2020), and social network analysis (Fan et al., 2019).


2.1.2.1 G RAPH


A finite _graph G_ = ( _V, E_ ) is defined as a tuple of a finite set of vertices (nodes) _V_ and


edges _E ⊂V × V_ . In general, note that the edges are _directed_, i.e., that ( _u, v_ ) _∈E_ does not


imply ( _v, u_ ) _∈E_ . However, in this dissertation we assume that all graphs are _undirected_


(i.e., ( _u, v_ ) _∈E_ implies ( _v, u_ ) _∈E_ for all _u, v ∈V_ ) because of Newton’s third law of


motion, which states that every action has an equal and opposite to reaction. The set of


neighboring vertices of _v_ is defined as:


_N_ _v_ := _{u ∈V|_ ( _v, u_ ) _∈E} ._ (2.12)




# Page 34

**10** 2. Background


The square matrix describing the edge connectivity of a graph is called the _adjacency_


_matrix_ and defined as:


_**A**_ _∈_ R _[|V|×|V|]_ (2.13)



(2.14)
0 otherwise _,_



_A_ _ij_ =








 1 if edge ( _v_ _i_ _, v_ _j_ ) _∈E_

 0 otherwise _,_



where _|V|_ denotes the number of vertices in the index set _J_ = _{_ 1 _,_ 2 _, . . ., |V|}_ . Although


the definition of an adjacency matrix depends on the indexing of the vertices, adjacency


matrices of the same graph but with different indexing can be shown to be isomorphic


using the _permutation π_ : _J →_ _J_ to describe the changes in indices. Using the permutation


matrix, _**P**_ _∈_ R _[|V|×|V|]_ defined as:



(2.15)
0 otherwise _,_



_P_ _ij_ =








1 if _π_ ( _i_ ) = _j_



 0 otherwise _,_



one can show that:


_**A**_ _[′]_ = _**P AP**_ _[⊤]_ _,_ (2.16)


where _A_ _[′]_ _ij_ [=] _[ A]_ _[π]_ [(] _[i]_ [)] _[ π]_ [(] _[j]_ [)] [is the adjacency matrix with permutated indices. Figure 2.1 presents]


an example of a graph and its permutated representation. Because the discussion regarding


permutations of graph vertex indices is well defined, in the subsequent discussions we


represent vertices using an index, i.e., _v_ _i_ _8→_ _i_ .


The _graph Laplacian matrix_ _**L**_ can be defined as:


_**L**_ = _**D**_ _−_ _**A**_ _,_ (2.17)


where _**D**_ is the _degree matrix_ of the graph, which is defined by:



(2.18)
0 otherwise _._



_D_ _ij_ :=










Q



_k_ _[A]_ _[ik]_ if _i_ = _j_




# Page 35

主要ノード：1, 2, 3, 4  
クラスタ：1-2-3-4  
強い接続：1と2、2と3、3と4、4と1、1と3

主要ノード：ノード2（中心）、ノード3、ノード5  
クラスタ：{2, 3, 5}  
強い接続：2-3、2-5、3-5（辺4）
###### 4 5



2.1. Machine Learning **11**

###### 2 1




###### 6



(c)


_**A**_ =



0

B
B
B
B
B
B
@



1 1 0 0 0 0

1 0 1 1 0 0

0 1 0 1 0 0

0 1 1 1 0 0

0 0 0 0 0 1

0 0 0 0 1 0



_**P**_ =



1

C
C
C
C
C
C
A



1

C
C
C
C
C
C
A



1

C
C
C
C
C
C
A



0

B
B
B
B
B
B
@



0 0 0 0 0 1

0 1 1 1 0 0

0 1 0 1 0 0

0 1 1 0 1 0

0 0 0 1 1 0

1 0 0 0 0 0



0

B
B
B
B
B
B
@



0 0 0 0 1 0

0 0 0 1 0 0

0 0 1 0 0 0

0 1 0 0 0 0

1 0 0 0 0 0

0 0 0 0 0 1



_**A**_ _[0]_ =



Figure 2.1: (a) An example of a graph, (b) the same graph with permutated indices, and (c)


corresponding adjacency and permutation matrices.


For the path graph with five vertices shown in Figure 2.2, the adjacency matrix is expressed


as follows:

















0 1 0 0 0



1 0 1 0 0



_**A**_ =


Thus, the graph Laplacian matrix is:

















0 1 0 1 0



0 0 1 0 1



0 0 0 1 0



(2.19)


(2.20)



_**L**_ =

















1 _−_ 1 0 0 0


_−_ 1 2 _−_ 1 0 0


0 _−_ 1 2 _−_ 1 0



0 0 _−_ 1 2 _−_ 1



0 0 0 _−_ 1 1


















# Page 36

**12** 2. Background


As will be discussed in Section 2.2.4, the graph Laplacian matrix is closely related to the


Laplacian operator.

## 1 2 3 4 5


Figure 2.2: A path graph with five vertices.


A function defined at a set of vertices _**f**_ vertex : _V →_ R _[N]_ is called a vertex signal or


_vertex feature_ . Similarly, a function defined at a set of edges _**f**_ edge : _E →_ R _[N]_ is called an


edge signal or _edge feature_ . _Graph signal processing_ is a research domain that deals with


node and edge signals on graphs, that is, graph signals. For more details regarding graph


signal processing, refer to, e.g., Ortega et al. (2018); Dong et al. (2020).


2.1.2.2 P OINTWISE MLP


One of the most basic neural network models is the _multilayer perceptron_ (MLP). An


_L_ -layer MLP _L_ : R _[d]_ [in] _→_ R _[d]_ [out] is defined as a stacking of affine transformations and


component-wise functions, called activation functions, as follows:


MLP( _**x**_ ) := _σ_ [(] _[L]_ [)] _◦_ Affine [(] _[L]_ [)] _◦_ _σ_ [(] _[L][−]_ [1)] _◦_ Affine [(] _[L][−]_ [1)] _◦· · · ◦_ _σ_ [(1)] _◦_ Affine [(1)] ( _**x**_ ) (2.21)


Affine [(] _[l]_ [)] ( _**h**_ _l_ ) := _**W**_ [(] _[l]_ [)] _**h**_ [(] _[l]_ [)] + _**b**_ [(] _[l]_ [)] _∀l ∈{_ 1 _,_ 2 _, . . ., L}_ (2.22)


_**W**_ [(] _[l]_ [)] _∈_ R _[d]_ [(] _[l]_ [+1)] _[×][d]_ [(] _[l]_ [)] _∀l ∈{_ 1 _,_ 2 _, . . ., L}_ (2.23)


_**b**_ [(] _[l]_ [)] _∈_ R _[d]_ [(] _[l]_ [+1)] _∀l ∈{_ 1 _,_ 2 _, . . ., L}_ (2.24)

















 [=]



...


_σ_ [(] _[l]_ [)] ( _v_ _i_ )

...






 _∀l ∈{_ 1 _,_ 2 _, . . ., L},_ (2.25)





_σ_ [(] _[l]_ [)]












...


_v_ _i_

...



where _d_ [(1)] = _d_ in and _d_ [(] _[L]_ [+1)] = _d_ out, and _**W**_ [(] _[l]_ [)], _**b**_ [(] _[l]_ [)], and _σ_ [(] _[l]_ [)] are the _weight matrix_, _bias_, and


_activation function_, respectively. An MLP is known as a universal approximator (Hornik,




# Page 37

2.1. Machine Learning **13**


1991; Cybenko, 1992; Nakkiran et al., 2021) that can approximate any continuous function


if the number of hidden features _d_ [(] _[l]_ [)] ( _l ̸_ = 1 _, L_ ) is increased.


However, an MLP cannot handle an input with an arbitrary length by itself because the


dimensions of the input are fixed. Instead, one can use a _pointwise MLP_ to handle inputs


with arbitrary lengths. An _L_ -layer pointwise MLP, PointwiseMLP _L_ : R _[|V|×][d]_ [in] _→_ R _[|V|×][d]_ [out],


is constructed by separately applying an _L_ -layer MLP, MLP _L_ : R _[d]_ [in] _→_ R _[d]_ [out], to each point,


as follows:







 (2.26)






PointwiseMLP _L_ ( _**H**_ in ) :=


_**H**_ in =

























MLP _L_ ( _**h**_ in _,_ 1 )


MLP _L_ ( _**h**_ in _,_ 2 )

...


MLP _L_ ( _**h**_ in _,N_ )



_**h**_ in _,_ 1


_**h**_ in _,_ 2

...


_**h**_ in _,|V|_







 _∈_ R _[|V|×][d]_ [in] _,_ (2.27)





where every MLP represents an identical function. Figure 2.3 (a) presents the architecture


of a pointwise MLP. It can be seen that an MLP “pointwise” is applied, resulting in the


capability to incorporate an arbitrary input length.


Alternatively, a pointwise MLP is expressed as:


PointwiseMLP _L_ ( _**H**_ in ) := _σ_ [(] _[L]_ [)] _◦_ PointwiseAffine [(] _[L]_ [)] _◦· · · ◦_ _σ_ [(1)] _◦_ PointwiseAffine [(1)] ( _**H**_ in ) _,_


(2.28)


where


PointwiseAffine [(] _[l]_ [)] ( _**H**_ [(] _[l]_ [)] ) := _**H**_ [(] _[l]_ [)] _**W**_ [(] _[l]_ [)] + **1** _|V|_ _**b**_ [(] _[l]_ [)] _∀l ∈{_ 1 _,_ 2 _, . . ., L}_ (2.29)

_**W**_ [(] _[l]_ [)] _∈_ R _[d]_ [(] _[l]_ [+1)] _[×][d]_ [(] _[l]_ [)] _∀l ∈{_ 1 _,_ 2 _, . . ., L}_ (2.30)


_**b**_ [(] _[l]_ [)] _∈_ R [1] _[×][d]_ [(] _[l]_ [)] _∀l ∈{_ 1 _,_ 2 _, . . ., L}_ (2.31)




# Page 38

**14** 2. Background







 _∈_ R _[V×]_ [1] _._ (2.32)






**1** _|V|_ =














1


1

...


1



Because the trainable parameters in the model do not depend on the number of vertices,


pointwise MLPs can handle arbitrary input lengths, i.e., arbitrary graphs, but they ignore


the edges, that is, the connections between vertices. Nevertheless, pointwise MLPs are


widely used as part of GNNs because of their simplicity.



(a)


(b)



画像は機械学習のニューラルネットワークの構造を示しています。入力層（h_in,k）から隠れ層（h_out,i）へと信号が伝わっており、各層間で複数のノード（橙色）が相互に接続しています。各ノードは入力値を加算し、活性化関数を通じて出力値（h）を生成しています。

_**h**_ in _,i_



_**h**_ in _,j_



_**h**_ out _,j_



画像は機械学習の更新関数を示すブロック図で、入力値$h_{in,j}$、$h_{in,k}$を含む多層ネットワークの構造を示しています。各層間の値が更新関数$h_{out,j}, h_{out,i}$を通じて変化し、最終的に出力$h$が生成される様子が説明されています。



Message function:
_**f**_ message ( _**h**_ in _,i_ _,_ _**h**_ in _,j_ _,_ _**e**_ in _,ij_ )





(c)









_**h**_ out _,k_


_**h**_ out _,k_



画像はニューラルネットワークの層間通信を示した図です。左側の立方体は入力層の活性化関数（\(\hat{A}_{ij}h_{in,j}\)）を表し、各ノード間の入力信号（\(h_{in,i}\), \(h_{in,k}\)）が伝播します。中央の橙色図形は活性化関節を示し、入力信号が加算され、出力信号\(h_{out,i}\)に変換されます。右側の青色立方体は出力層で、\(n_{out,j}\)を生成し、最終的な出力\(h\)を出力します。各層間の信号は橙色の矢印で伝播し、層間の相互作用を示しています。

Update function


Figure 2.3: Schematic diagrams of (a) pointwise MLP, (b) MPNN, and (c) GCN.


2.1.2.3 M ESSAGE P ASSING N EURAL N ETWORKS (MPNN S )


The term GNN is an umbrella denomination for any neural network that can handle


graph-structured data. Although there are many GNN variants, most are unified under


the concept of _message passing neural networks_ (MPNNs) (Gilmer et al., 2017), which


comprise two main parts: the message function _**f**_ messaga and update function _**f**_ update . One




# Page 39

2.1. Machine Learning **15**


MPNN operation is defined as:


MPNN( _{_ _**h**_ in _,i_ _}_ _i∈V_ _, {_ _**e**_ in _,ij_ _}_ ( _i,j_ ) _∈E_ ) := _**f**_ update ( _**h**_ in _,i_ _,_ _**m**_ _i_ ) (2.33)

_**m**_ _i_ := Y _**f**_ message ( _**h**_ in _,i_ _,_ _**h**_ in _,j_ _,_ _**e**_ in _,ij_ ) _,_ (2.34)

_j∈N_ _i_


where _{_ _**h**_ in _,i_ _}_ _i∈V_ and _{_ _**e**_ in _,ij_ _}_ ( _i,j_ ) _∈E_ are the vertex and edge features, respectively. Note that


_**f**_ message and _**f**_ update are machine learning models usually based on neural networks.


Figure 2.3 (b) shows a schematic of an MPNN. The message function models the effect


from neighboring vertices. A typical example of an update function is a pointwise MLP that


predicts the state of vertices using vertex features and aggregated messages. The trainable


parameters of the message and update functions independent of the number of vertices


or edges, which implies that an MPNN can handle a graph with arbitrary dimensions. A


single MPNN layer considers neighboring vertices as one hop away, hence, the information


of vertices _k_ -hops away can be considered by stacking _k_ MPNN layers.


2.1.2.4 G RAPH C ONVOLUTIONAL N ETWORK (GCN)


Generally, deep neural networks are used for message passing, which can incur tremen

dous computational cost. In contrast, the _Graph Convolutional Network_ (GCN) developed


by Kipf & Welling (2017) is a considerable simplification of an MPNN, that uses a linear


message-passing scheme expressed as:


GCN( _**H**_ in ) := PointwiseMLP _L_ =1 ( _**AH**_ [ˆ] in ) _,_ (2.35)


where _**A**_ [ˆ] denotes a renormalized adjacency matrix with self-loops and defined as:


_**A**_ ˆ := _**D**_ [˜] _[−]_ [1] _[/]_ [2] [ ˜] _**AD**_ [˜] _[−]_ [1] _[/]_ [2] _,_ (2.36)


where _**A**_ [˜] is an adjacency matrix of the graph with added self-connections and _**D**_ [˜] is the

degree matrix of _**A**_ [˜] .




# Page 40

**16** 2. Background


The formulation of a GCN comprehends that of an MPNN, as follows:



_**m**_ _i_ =
Y



Y _**f**_ message ( _**h**_ in _,_ _**h**_ in _,j_ ) = Y

_j∈N_ _i_ _∪{i}_ _j∈N_ _i_



Y _A_ ˆ _ij_ _**h**_ in _,j_

_j∈N_ _i_ _∪{i}_



ˆ
= _**AH**_ in
i j



(2.37)
_i_



_**f**_ update ( _**m**_ _i_ ) = MLP _L_ =1 ( _**m**_ _i_ ) _,_ (2.38)


Note that Equation 2.37 is derived based on the fact that _A_ [ˆ] _ij_ = 0 (if _j /∈N_ _i_ _∪{i}_ ).


From Equation 2.37, one can consider that GCNs use linearized message passing, which

can accelerate their. Furthermore, if the graph is sparse, i.e., _|E| ≪|V|_ [2], implying that the

number of actual edges _|E|_ is significantly smaller than the possible number of edges _|V|_ [2],


efficient algorithms can be utilized for sparse matrix operations. Figure 2.3 (c) shows the


architecture of a GCN and Figure 2.4 shows an example of GCN operation. Owing to its


computational efficiency, a GCN is the basis for constructing our proposed IsoGCN, a fast


machine learning model to learn physics, as presented in Chapter 3


2


1

図は四面体の立体図示で、底面は正方形で各辺の長さを4とし、頂点から底面への高さも4と示されています。各辺に粉ピンクの矢印が描かれており、底面周囲の方向を示しています。


3



_p_



図は四面体の立体構造を示し、橙色の矢印は頂点方向に作用する力の方向を表しています。四面体は青緑色とオレンジ色で区別され、各面が三角形の形状を有しています。この図は力学的力の分析や運動学の問題を解くための基本的な図示として使用されます。

図は2つの立方体を示しています。左側の立方体の各辺の長さが4、5と示されています。右側の立方体内に橙色の四角形が存在し、その周囲には橙色の線が延びています。立方体と橙色四角形の間には、橙色の矢印が指向しています。

_p_



5 4



1

C
C
C
C
A



1

C
C
C
C
A



20 4



_p_

_p_



5 6


5 6



_p_

_p_



0

B
B
B
B
@



20 4 5 4 5 0 0

4 _p_ 5 12 12 6 _p_ 5 6 _p_



4 5 12 12 6 5 6 5

4 _p_ 5 12 12 6 _p_ 5 6 _p_ 5



_p_

_p_



5 12 12 6 5 6 5

0 6 _p_ 5 6 _p_ 5 15 15



0 6 5 6 5 15 15

0 6 _p_ 5 6 _p_ 5 15 15



5 12 12 6


5 12 12 6



_p_

_p_



5 6


5 6



0

B
B
B
B
@



3 0 0 0 0

0 5 0 0 0

0 0 5 0 0

0 0 0 4 0

0 0 0 0 4



_**A**_ ˆ = [1]

60



_**A**_ =



0

B
B
B
B
@



0 1 1 0 0

1 0 1 1 1

1 1 0 1 1

0 1 1 0 1

0 1 1 1 0



_**D**_ ˜ =



1

C
C
C
C
A



_p_

_p_



5 15 15







_**h**_ out _,_ 1 = [GCN( _**H**_ in )] 1 = MLP



1

_p_

✓ 60 [[20] _**[h]**_ [in] _[,]_ [1] [ + 4]



5 _**h**_ in _,_ 2 + 4



_p_ 5 _**h**_ in _,_ 3 ]



Figure 2.4: An example of a graph and its corresponding adjacency matrix _**A**_, degree

matrix _**D**_ [˜], renormalized adjacency matrix _**A**_ [ˆ], and resulting output _**h**_ out _,_ 1 . their can be seen


that the GCN model considers information on neighboring vertices through a weighted sum


determined from the graph structure.


If we consider a graph with no edges, then _A_ _ij_ = 0 ( _∀i, j ∈{_ 1 _,_ 2 _, . . ., |V|}_ ) and _**D**_ [˜] =


_**I**_ _|V|_, where _**I**_ _|V|_ denotes an identity matrix of size _|V|_ . In such case, the GCN layer becomes


a pointwise MLP PointwiseMLP _L_ =1 ( _**I**_ _|V|_ _**H**_ in ) = PointwiseMLP _L_ =1 ( _**H**_ in ). Therefore, the




# Page 41

2.1. Machine Learning **17**


GCN model can be considered a generalization of a pointwise MLP for a model-capturing


graph structure.


2.1.3 E QUIVARIANCE


Equivariance is an essential concept for characterizing the predictable behavior of a


function under certain transformations, such as rotation or translation. Because this is


closely related to group theory, we first introduce groups and related concepts.


2.1.3.1 G ROUP T HEORY


A _group_ is a set _G_ with a binary operation (usually called “multiplication”), _·_ : _G×G →_


_G_, that satisfies the following requirements:


(Associativity) _∀a, b, c ∈_ _G,_ ( _a · b_ ) _· c_ = _a ·_ ( _b · c_ ) (2.39)


(Identity element) _∃e_ s _._ t _. ∀a ∈_ _G,_ _e · a_ = _a · e_ = _a_ (2.40)


(Inverse element) _∀a ∈_ _G, ∃b ∈_ _G_ s _._ t _._ _a · b_ = _b · a_ = _e._ (2.41)


For a group _G_ and a set _X_, a (left) _group action_ is a function _·_ : _G × X →_ _X_, which


satisfies the following conditions:


(Identity) _∀x ∈_ _X,_ _e · x_ = _x_ (2.42)


(Compatibility) _∀a, b ∈_ _G, ∀x ∈_ _X,_ _a ·_ ( _b · x_ ) = ( _a · b_ ) _· x,_ (2.43)


where _e_ is the identity element of the group. We denote _α_ ( _a, x_ ) := _a · x_ when we must


clarify that the operation is a group action.


Groups appear in various fields, such as physics, engineering, and computer science;


next, we provide a few examples of groups and their actions. A first example is the _general_


_linear group_ GL( _n_ ), the set of all _n_ -dimensional invertible matrices. One can confirm


GL( _n_ ) is a group because the multiplication of matrices is associative, the identity matrix


is in GL( _n_ ), and by definition an inverse matrix always exists for a given element in GL( _n_ ).


Another example is the _orthogonal group_ O( _n_ ), the set of _n_ -dimensional orthogonal


matrices representing rotation and reflection, which also satisfies the group requirements.




# Page 42

**18** 2. Background


In addition, one can consider the multiplication between an element of O( _n_ ) and an _n_ 

dimensional vector _**x**_ _∈_ R _[n]_ . Such multiplication satisfies the definition of group action as


well. Furthermore, a rank-2 tensor _**T**_ _∈_ R _[n][×][n]_ can be transformed into an orthogonal matrix


_**U**_ _∈_ O( _n_ ) By computing _α_ ( _**U**_ _,_ _**T**_ ) = _**UT U**_ _[⊤]_, Which is also a group action. Therefore,


the concrete form of a group action might differ depending on the set on which the group


acts.


Two more examples of groups are the _symmetric group S_ _n_, a group of permutations,


and the _Euclidean group_ E( _n_ ), which is a group of isometric transformations, namely,


translation, rotation, and reflection. In particular, E( _n_ ) plays an essential role in developing


neural PDE solvers because most physical phenomena occur in the Euclidean space, with


its essence remaining the same under E( _n_ ) transformations.


2.1.3.2 E QUIVARIANT M ODEL


A function _f_ : _X →_ _Y_ is said to be _G_  - _equivariant_ when:


_∀g ∈_ _G, ∀x ∈_ _X, f_ ( _g · x_ ) = _g · f_ ( _x_ ) _,_ (2.44)


assuming that the group _G_ acts on both _X_ and _Y_ . The concept of equivariance is also


explained by the following commutative diagram:


_X_ _g·_ _X_


_f_ _f_



In particular, when:



_Y_ _g·_ _Y_


_∀g ∈_ _G, f_ ( _g · x_ ) = _f_ ( _x_ ) _,_ (2.45)



_f_ is said to be _G_ - _invariant_, and the corresponding commutative diagram is as follows:


_X_ _g·_ _X_


_f_


_Y_




# Page 43

2.1. Machine Learning **19**


This invariance is a special case of equivariance because _g · x_ = _x_ qualifies as a group


action (trivial group action).


Most numerical analysis schemes and models for physical simulations have equivari

ance. The principle of material objectivity (Ignatieff, 1996), which is similar to equivari

ance, is considered essential for constitutive laws. For instance, the tensor product between


two rank-1 tensors _**f**_ prod : R _[n]_ _×_ R _[n]_ _∋_ ( _**v**_ _,_ _**u**_ ) _8→_ _**v**_ _⊗_ _**u**_ _∈_ R _[n][×][n]_ is O( _n_ )-equivariant because,


for any orthogonal matrix _**U**_ :


[ _**f**_ prod ( _α_ ( _**U**_ _,_ _**v**_ ) _, α_ ( _**U**_ _,_ _**u**_ ))] _ij_ = [ _**Uv**_ _⊗_ _**Uu**_ ] _ij_


= [ _**Uv**_ ] _i_ [ _**Uu**_ ] _j_


= Y _U_ _ik_ _v_ _k_ _U_ _jl_ _u_ _l_


_kl_

= Y _U_ _ik_ _v_ _k_ _u_ _l_ _U_ _lj_ _[⊤]_


_kl_


= _**Uv**_ _⊗_ _**uU**_ _[⊤]_ []
 _ij_


= [ _α_ ( _**U**_ _,_ _**f**_ prod ( _**v**_ _,_ _**u**_ ))] _ij_ _,_ (2.46)


satisfying the definition of equivariance (Equation 2.44). The squared norm operator _f_ norm :

R _[n]_ _∋_ _**v**_ _8→∥_ _**v**_ _∥_ [2] _∈_ R is O( _n_ )-invariant because


_f_ norm ( _α_ ( _**U**_ _,_ _**v**_ )) = _∥_ _**Uv**_ _∥_ [2]


= ( _**Uv**_ ) _·_ ( _**Uv**_ )


= _U_ _ik_ _v_ _k_ _U_ _il_ _v_ _l_
Y


_ikl_

= Y _U_ _li_ _[⊤]_ _[U]_ _[ik]_ _[v]_ _[k]_ _[v]_ _[l]_


_ikl_


= _δ_ _lk_ _v_ _k_ _v_ _l_
Y


_kl_


= _v_ _k_ _v_ _k_
Y


_k_


= _∥_ _**v**_ _∥_ [2]


= _f_ norm ( _**v**_ ) _,_ (2.47)




# Page 44

**20** 2. Background


which satisfies the definition of invariance (Equation 2.45). Here, _δ_ _lk_ is the _Kronecker delta_,


defined as:



(2.48)
0 otherwise _._



_δ_ _ij_ =








1 if _i_ = _j_



0





In addition to O( _n_ ), a symmetric group _S_ _n_ is also worth considering because it corre

sponds to the permutation of the vertex indices. In numerical analysis, we choose arbitrary


indexing for the nodes and elements in the meshes. Therefore, permutation equivariance is


an essential indicator for a preferable numerical analysis scheme [1] . We can demonstrate a


GCN layer operation (Equation 2.35) is permutation equivariant for all permutation matri

ces as follows: _**P**_,


GCN( _α_ ( _**P**_ _,_ _**H**_ )) = PointwiseMLP( _α_ ( _**P**_ _,_ _**AH**_ [ˆ] ))


= PointwiseMLP( _**P**_ _**AP**_ [ˆ] _[⊤]_ _**P H**_ ))


= PointwiseMLP( _**P**_ _**AH**_ [ˆ] ))


= _**P**_ PointwiseMLP( _**AH**_ [ˆ] ))


= _α_ ( _**P**_ _,_ GCN( _**H**_ )) _._ (2.49)


We use the fact that any permutation matrix is orthogonal, i.e., _**P**_ _[⊤]_ = _**P**_ _[−]_ [1], and that all


pointwise MLP layers are trivially permutation equivariant.


Group equivariant convolutional neural networks (CNNs) were first proposed by Cohen


& Welling (2016) for discrete groups. Subsequent studies have categorized such networks


as continuous groups (Cohen et al., 2018), three-dimensional data (Weiler et al., 2018),


and general manifolds (Cohen et al., 2019). These methods are based on CNNs; thus,


they cannot directly handle mesh or point cloud data structures. Specifically, 3D steerable


CNNs (Weiler et al., 2018) which use voxels (regular grids) and are deemed relatively


easy to handle, are inefficient because they represent both occupied and empty parts of an


object (Ahmed et al., 2018). In addition, a voxelized object tends to lose smoothness of


1 However, several schemes are not permutation equivariant, e.g., one iteration in the successive overrelaxation (SOR) method. Nevertheless, we can assume that the entire SOR process is nearly permutationequivariant if it converges to an accurate solution.




# Page 45

2.2. Numerical Analysis **21**


its shape, which can lead to a drastically different behavior in a physical simulation, as is


typically observed in heat analyses and computational fluid dynamics.


Thomas et al. (2018); Kondor (2018) discussed how to provide rotation equivariance


to point clouds. Specifically, Thomas et al. (2018) proposed a tensor field network (TFN),


which is a point-cloud-based rotation and translation equivariant neural network, whose


layer can be written as:


_̸_



_**H**_ ˜ [(] _[l]_ [)] _**H**_ [(] _[k]_ [)] _**H**_ [(] _[l]_ [)]
out _,i_ [= TFN] _[l]_ [(] _[{]_ [ ˜] in _,i_ _[}]_ _[k][≥]_ [0] [) =] _[ w]_ _[ll]_ [ ˜] in _,i_ [+] Y

_k≥_ 0 _̸_



Y _**W**_ _[lk]_ ( _**x**_ _j_ _−_ _**x**_ _i_ ) _**H**_ [˜] in [(] _[k]_ _,j_ [)] (2.50)

_j_ = _̸_ _i_



_̸_


_**W**_ _[lk]_ ( _**x**_ ) =



_̸_


_k_ + _l_
Y _φ_ _[lk]_ _J_ [(] _[∥]_ _**[x]**_ _[∥]_ [)]

_J_ = _|k−l|_



Y _**W**_ _[lk]_ ( _**x**_ _j_ _−_ _**x**_ _i_ ) _**H**_ [˜] in [(] _[k]_ _,j_ [)] (2.50)

_j_ = _̸_ _i_


_J_
Y _Y_ _Jm_ ( _**x**_ _/∥_ _**x**_ _∥_ ) _**Q**_ _[lk]_ _Jm_ _[,]_ (2.51)


_m_ = _−J_



_̸_


_J_
Y



_̸_


where _**H**_ [˜] in [(] _[l]_ [)] _,i_ [(] _**H**_ [ ˜] out [(] _[l]_ [)] _,i_ [): is a type-] _[l]_ [ input (output) features at the] _[ i]_ [th vertex,] _[ φ]_ _J_ _[lk]_ [:][ R] _[≥]_ [0] _[ →]_ [R]

is a trainable function, _Y_ _Jm_ is the _m_ th component of the _J_ th spherical harmonic, and _**Q**_ _[lk]_ _Jm_

is the Clebsch-Cordan coefficient. The SE(3)-Transformer (Fuchs et al., 2020) is a TFN


variant with self-attention. Dym & Maron (2020) showed that both the TFN and SE(3)

Transformer are universal in terms of translation, rotation, and permutation equivariance.


E( _n_ )-equivariance is essential for solving physical PDEs because it describes rigid

body motion, i.e., translation, rotation, and reflection. Ling et al. (2016) and Wang et al.


(2021) introduced equivariance into a simple neural network and a CNN to predict flow


phenomena. Both studies showed that the predictive and generalization performance im

proved due to equivariance.


2.2 N UMERICAL A NALYSIS


In this section, we review the foundations of PDEs to clarify the problems we aim to


solve and introduce related works in which machine learning models are used to solve


PDEs.


2.2.1 P ARTIAL D IFFERENTIAL E QUATIONS (PDE S ) WITH B OUNDARY C ONDITIONS


The general form of the spatiotemporal PDEs for a field, _**u**_ : (0 _, T_ ) _×_ Ω _→_ R _[d]_, of


a _d_ -dimensional physical quantity defined in an _n_ -dimensional domain, Ω _⊂_ R _[n]_, can be




# Page 46

**22** 2. Background


expressed as follows:


_∂_ _**u**_

_∂t_ [(] _[t,]_ _**[ x]**_ [) =] _[ D]_ [(] _**[u]**_ [)(] _[t,]_ _**[ x]**_ [)] ( _t,_ _**x**_ ) _∈_ (0 _, T_ ) _×_ Ω (2.52)


_**u**_ ( _t_ = 0 _,_ _**x**_ ) = ˆ _**u**_ 0 ( _**x**_ ) _**x**_ _∈_ Ω (2.53)


_**u**_ ( _t,_ _**x**_ ) = ˆ _**u**_ ( _t,_ _**x**_ ) ( _t,_ _**x**_ ) _∈_ (0 _, T_ ) _× ∂_ Ω Dirichlet (2.54)


ˆ
_**f**_ ( _∇_ _**u**_ ( _t,_ _**x**_ ) _,_ _**n**_ ( _**x**_ )) = **0** ( _t,_ _**x**_ ) _∈_ (0 _, T_ ) _× ∂_ Ω Neumann _,_ (2.55)


where _∂_ Ω Dirichlet and _∂_ Ω Neumann are mixed _Dirichlet_ and _Neumann_ boundary conditions,


respectively, such that _∂_ Ω Dirichlet _∩_ _∂_ Ω Neumann = _∅_ and _∂_ Ω Dirichlet _∪_ _∂_ Ω Neumann = _∂_ Ω, _∂_ Ω


ˆ
denotes the boundary of Ω, _·_ is a known function, _D_ is a known nonlinear differential oper

ator, which can be nonlinear and contains spatial differential operators, and _**n**_ ( _**x**_ ) denotes


the normal vector at _**x**_ _∈_ _∂_ Ω. Equation 2.54 is called the Dirichlet boundary condition,


where the value of _∂_ Ω Dirichlet is set as a constraint, whereas Equation 2.55 corresponds to


the Neumann boundary condition, where the value of the derivative _**u**_ in the direction of _**n**_


is set to _∂_ Ω Neumann rather than _**u**_ . _**u**_ is the solution of the (initial) boundary value problem


when it satisfies Equations 2.52 – 2.55.


Equation 2.52 may represent various types of PDEs. For instance, in the case of the


heat equation:


_D_ heat ( _u_ ) = _c∇· ∇u,_ (2.56)


where _u_ is the temperature field ( _d_ = 1) and _c_ is the diffusion coefficient. For an incom

pressible Navier–Stokes equations:


_D_ NS ( _**u**_ ) = _−_ ( _**u**_ _· ∇_ ) _**u**_ + [1] (2.57)

Re _[∇· ∇]_ _**[u]**_ _[ −∇][p,]_


where _∇·_ _**u**_ = 0 expresses the incompressible condition, _**u**_ denotes the flow velocity field,


_p_ is the pressure field, and Re denotesthe Reynolds number.




# Page 47

2.2. Numerical Analysis **23**


2.2.2 D ISCRETIZATION


PDEs must be defined in a continuous space for the differentials to be meaningful.


Discretization can be applied to both space and time to enable computers to easily solve


the PDE.


In the numerical analysis of complex-shaped domains, we commonly use _meshes_ (dis

cretized shape data), which can be regarded as a graph, as shown in Figure 2.5. We denote


the position of the _i_ th vertex as _**x**_ _i_ and the value of a function _f_, _g_, _. . ._ at _**x**_ _i_ as _f_ _i_ _g_ _i_, _. . ._ .


Therefore, _{f_ _i_ _}_ _i∈V_, _{g_ _i_ _}_ _i∈V_, and _. . ._ are the vertex features [2] . For concrete examples of


spatial discretization, see Section 2.2.4.


###### (a)


###### (b)



主要ノード：頂点A、B、C、D、E、F、G、H、I、J、K、L、M、N、O、P、Q、R、S、T、U、V、W、X、Y、Z。  
クラスタ：A-B-C-D-E-F-G-H-I-J-K-L-M-N-O-P-Q-R-S-T-U-V-W-X-Y-Z。  
強い接続：A-F、B-G、C-H、D-I、E-J、F-K、G-L、H-M、I-N、J-O、K-P、L-Q、M-R、N-S、O-T、P-U、Q-V、R-W、S-X、T-Y、U-Z。
###### Spatial discretization (meshing)

##### ⌦

Figure 2.5: Examples of (a) a domain Ω and (b) a mesh representing the corresponding


discretized domain.


One of the simplest methods to discretize time is the _explicit Euler method_ which is


formulated as:


_**u**_ ( _t_ + ∆ _t,_ _**x**_ _i_ ) _≈_ _**u**_ ( _t,_ _**x**_ _i_ ) + _D_ ( _**u**_ )( _t,_ _**x**_ _i_ )∆ _t,_ (2.58)


where _**u**_ ( _t,_ _**x**_ _i_ ) is updated via a small increment _D_ ( _**u**_ )( _t,_ _**x**_ _i_ )∆ _t_ . Another way to discretize


time is the _implicit Euler method_ formulated as:


_**u**_ ( _t_ + ∆ _t,_ _**x**_ _i_ ) _≈_ _**u**_ ( _t,_ _**x**_ _i_ ) + _D_ ( _**u**_ )( _t_ + ∆ _t,_ _**x**_ _i_ )∆ _t,_ (2.59)


2 Strictly speaking, the components of the PDE, e.g. _D_ and Ω, can be different before and after discretization. However, we use the same notation regardless of discretization to keep the notation simple.




# Page 48

**24** 2. Background


which solves Equation 2.59 rather than simply updating the variables to ensure that the


original PDE is numerically satisfied. The equation can be viewed as a nonlinear optimiza

tion problem by formulating it as:


_**r**_ ( _**v**_ ) := _**v**_ _−_ _**u**_ ( _t, ·_ ) _−D_ ( _**v**_ )∆ _t_ (2.60)


Solve _**v**_ _**r**_ ( _**v**_ )( _**x**_ _i_ ) = **0** _, ∀i ∈{_ 1 _, . . ., |V|},_ (2.61)


where _**r**_ : (Ω _→_ R _[d]_ ) _→_ (Ω _→_ R _[d]_ ) is the operator of the residual vector of the discretized


PDE. Since _**r**_ is a map from functions Ω _→_ R _[d]_ to functions Ω _→_ R _[d]_, _**r**_ ( _**v**_ ) : Ω _→_ R _[d]_ is


also a function. Therefore:


_**r**_ ( _**v**_ )( _**x**_ _i_ ) = _**v**_ ( _**x**_ _i_ ) _−_ _**u**_ ( _t,_ _**x**_ _i_ ) _−D_ ( _**v**_ )( _**x**_ _i_ )∆ _t ∈_ R _[d]_ (2.62)


corresponds to the error in the current numerical solution _**v**_ at _**x**_ _i_ . If


_**r**_ ( _**v**_ )( _**x**_ _i_ ) = **0**, _**v**_ satisfies the discretized equation at _**x**_ _i_ . Here, by

letting _**V**_ = ( _**v**_ ( _**x**_ 1 ) _[⊤]_ _,_ _**v**_ ( _**x**_ 2 ) _[⊤]_ _, . . .,_ _**v**_ ( _**x**_ _|V|_ ) _[⊤]_ ) _[⊤]_ _∈_ R _[d][|V|]_ and _**U**_ ( _t_ ) =

( _**u**_ ( _t,_ _**x**_ 1 ) _[⊤]_ _,_ _**u**_ ( _t,_ _**x**_ 2 ) _[⊤]_ _, . . .,_ _**u**_ ( _t,_ _**x**_ _|V|_ ) _[⊤]_ ) _[⊤]_ _∈_ R _[d][|V|]_, Equation 2.60 and Equation 2.61


become:


_**R**_ ( _**V**_ ) := _**V**_ _−_ _**U**_ ( _t_ ) _−D_ ( _**V**_ )∆ _t ∈_ R _[d][|V|]_ (2.63)


Solve _**V**_ _**R**_ ( _**V**_ ) = **0** _._ (2.64)


The solution to Equation 2.64 corresponds to _**U**_ ( _t_ + ∆ _t_ ) = ( _**u**_ ( _t_ + ∆ _t,_ _**x**_ 1 ) _[⊤]_ _,_ _**u**_ ( _t_ +

∆ _t,_ _**x**_ 2 ) _[⊤]_ _, . . .,_ _**u**_ ( _t_ + ∆ _t,_ _**x**_ _|V|_ ) _[⊤]_ ) _[⊤]_ _∈_ R _[d][|V|]_ .


2.2.3 N ONLINEAR S OLVER AND O PTIMIZATION


2.2.3.1 B ASIC F ORMULA FOR I TERATIVE M ETHODS


Because Equation 2.64 can be a nonlinear and high-dimensional problem, there is no


general formula for solving it. A common method to obtain an approximate solution is to




# Page 49

2.2. Numerical Analysis **25**


apply an iterative method to a linearized system, such as:


_**V**_ [[0]] = _**U**_ ( _t_ ) (2.65)


_**V**_ [[] _[i]_ [+1]] = _**V**_ [[] _[i]_ []] + ∆ _**V**_ [[] _[i]_ []] _,_ (2.66)


where ∆ _**V**_ [[] _[i]_ []] is an unknown update of the approximate solution. The first-order approxi

mation can be applied to obtain the update, as follows:


_**R**_ ( _**V**_ [[] _[i]_ []] + ∆ _**V**_ [[] _[i]_ []] ) _≈_ _**R**_ ( _**V**_ [[] _[i]_ []] ) + _∇_ _**V**_ _⊗_ _**R**_ ( _**V**_ [[] _[i]_ []] )∆ _**V**_ [[] _[i]_ []] = **0** _,_ (2.67)


where _∇_ _**V**_ _⊗_ _**R**_ _∈_ R _[d][|V|×][d][|V|]_ denotes the Jacobian matrix of _**R**_ with respect to _**V**_ . Instead


of using Equation 2.61, we can iteratively solve Equation 2.67.


If a function _φ_ : R _[d][|V|]_ _→_ R satisfying _∇_ _**V**_ _φ_ = _**R**_ exists, solving Equation 2.64 cor

responds to the optimization of _φ_ in an ( _d|V|_ )-dimensional space, where _|V|_ denotes the


number of vertices in the considered mesh. Therefore, the implicit Euler method is closely


related to optimization in a high-dimensional space. From this viewpoint, the Jacobian ma

trix _∇_ _**V**_ _⊗_ _**R**_ corresponds to the Hessian matrix _∇_ _**V**_ _⊗∇_ _**V**_ _φ_ . However, it should be noted


that the Hessian matrix is always symmetric, which is not always the case for the Jacobian


matrix.


2.2.3.2 N EWTON –R APHSON M ETHOD AND Q UASI -N EWTON M ETHOD


The _Newton–Raphson method_ solves Equation 2.67 as follows:


∆ _**V**_ [[] _[i]_ []] = _−_  _∇_ _**V**_ _⊗_ _**R**_ ( _**V**_ [[] _[i]_ []] )  _−_ 1 _**R**_ ( _**V**_ [ _i_ ] ) _,_ (2.68)


which requires solving a linear system with a large number of degrees of freedom, ( _d|V|_ ).


Solving such a large system of linear equations occasionally requires considerable compu

tational resources and time. To address this issue, _quasi-Newton methods_ approximate the


inverse of the Jacobian matrix using a matrix _**H**_ [[] _[i]_ []] to obtain:


∆ _**V**_ [[] _[i]_ []] _≈−_ _**H**_ [[] _[i]_ []] _**R**_ ( _**V**_ [[] _[i]_ []] ) _._ (2.69)




# Page 50

**26** 2. Background


Various methods can be used to initialize, compute, and update _**H**_ [[] _[i]_ []] . A key concern in


quasi-Newton methods is their massive memory consumption because _**H**_ [[] _[i]_ []] could be dense


even if _∇_ _**V**_ _⊗_ _**R**_ is sparse. Thus, a lot of effort has been dedicated to reducing the memory


demand of this method, as in Liu & Nocedal (1989).


2.2.3.3 G RADIENT D ESCENT M ETHOD


The _gradient descent_ method implements yet another approximation, as follows:


∆ _**V**_ [[] _[i]_ []] _≈−α_ [[] _[i]_ []] _**R**_ ( _**V**_ [[] _[i]_ []] ) _,_ (2.70)


where _α_ [[] _[i]_ []] _∈_ R is a scalar that controls the update magnitude. The approximation has no


error when all eigenvalues _λ_ _i_ ( _i ∈_ 1 _, . . ., d|V|_ ) are the same, i.e., _λ_ _i_ = _λ_, because:



_∇_ _**V**_ _⊗_ _**R**_ ( _**V**_ [[] _[i]_ []] ) = _**Q**_











_λ_

...



_λ_





 (2.71)
 _**[Q]**_ _[−]_ [1]



= _**Q**_ _λ_ _**I**_ _d|V|_ _**Q**_ _[−]_ [1] (2.72)


= _λ_ _**I**_ _d|V|_ _,_ (2.73)


where _**Q**_ where is the eigenvectors matrix. Thus, by letting _α_ [[] _[i]_ []] = 1 _/λ_, we can show that


Equations 2.68 and 2.70 are the same. In contrast, if the eigenvalues are not identical and


broadly distributed, the gradient descent approximation introduces some error. This fact is


reasonable because such a situation corresponds to a linear system with a large condition


number for the matrix _∇_ _**V**_ _**R**_ ( _**V**_ [[] _[i]_ []] ) and, hence, constitutes a challenging problem.


The update using gradient descent is expressed as:


_**V**_ [[] _[i]_ [+1]] = _**V**_ [[] _[i]_ []] _−_ _α_ [[] _[i]_ []] _**R**_ ( _**V**_ [[] _[i]_ []] ) _._ (2.74)


This method is termed gradient descent because _**R**_ ( _**V**_ [[] _[i]_ []] ) corresponds to the “gradient”, and


the equation is updated to reduce the error.




# Page 51

2.2. Numerical Analysis **27**


_α_ [[] _[i]_ []] is typically determined using line search. However, owing to the high computational


cost of this search, _α_ [[] _[i]_ []] can be fixed to a small value _α_, which corresponds to the explicit


Euler method with a time step size _α_ ∆ _t_ because


_**V**_ [[] _[i]_ [+1]] = _**V**_ [[] _[i]_ []] _−_ _α_ _**R**_ ( _**V**_ [[] _[i]_ []] ) (2.75)


= _**V**_ [[] _[i]_ []] _−_ _α_  _**V**_ [[] _[i]_ []] _−_ _**U**_ ( _t_ ) _−D_ ( _**V**_ [[] _[i]_ []] )∆ _t_  (2.76)


= (1 _−_ _α_ ) _**V**_ [[] _[i]_ []] + _α_ _**U**_ ( _t_ ) + _D_ ( _**V**_ [[] _[i]_ []] ) _α_ ∆ _t._ (2.77)


If we explicitly write the first few steps:


_**V**_ [[0]] = _**U**_ ( _t_ ) (2.78)


_**V**_ [[1]] = (1 _−_ _α_ ) _**V**_ [[0]] + _α_ _**U**_ ( _t_ ) + _D_ ( _**V**_ [[0]] ) _α_ ∆ _t_ (2.79)


= _**U**_ ( _t_ ) + _D_ ( _**U**_ ( _t_ )) _α_ ∆ _t,_ (2.80)


obtaining the same update scheme as that in Equation 2.58. For more information regard

ing optimization, including quasi-Newton methods and gradient descent, see, e.g., Luen

berger et al. (1984).


2.2.3.4 B ARZILAI –B ORWEIN M ETHOD


Barzilai & Borwein (1988) suggested another simple, yet effective, way to determine


the step size _α_ [[] _[i]_ []] in the gradient-descent method by using a two-point approximation of the


secant equation underlying the quasi-Newton method. Using this method, we can derive


the step size for the current state as:



_α_ [[] _[i]_ []] _≈_ _α_ [[] _[i]_ []]
BB [=]



 _**V**_ [[] _[i]_ []] _−_ _**V**_ [[] _[i][−]_ [1]] [] _·_  _**R**_ ( _**V**_ [[] _[i]_ []] ) _−_ _**R**_ ( _**V**_ [[] _[i][−]_ [1]] ) 

(2.81)

[ _**R**_ ( _**V**_ [[] _[i]_ []] ) _−_ _**R**_ ( _**V**_ [[] _[i][−]_ [1]] )] _·_ [ _**R**_ ( _**V**_ [[] _[i]_ []] ) _−_ _**R**_ ( _**V**_ [[] _[i][−]_ [1]] )] _[,]_



We now derive Equation 2.81.


First, to avoid using future information, we assume that


∆ _**V**_ [[] _[i][−]_ [1]] = _**V**_ [[] _[i]_ []] _−_ _**V**_ [[] _[i][−]_ [1]] _≈−α_ [[] _[i]_ []] _**R**_ ( _**V**_ [[] _[i][−]_ [1]] ) _,_ (2.82)




# Page 52

**28** 2. Background


instead of using Equation 2.70, which contains the state at a future step ( _i_ + 1). Equa

tion 2.82 implies:


_∇_ _**V**_ _⊗_ _**R**_ ( _**V**_ [[] _[i][−]_ [1]] ) _≈_ [1] (2.83)

_α_ [[] _[i]_ []] _[.]_


By substituting Equation 2.83 into Equation 2.67 and replacing _i_ with ( _i −_ 1), we obtain:


_**R**_ ( _**V**_ [[] _[i]_ []] ) _≈_ _**R**_ ( _**V**_ [[] _[i][−]_ [1]] ) + [1]

_α_ [[] _[i]_ []] [∆] _**[V]**_ [ [] _[i][−]_ [1]]


∆ _**V**_ [[] _[i][−]_ [1]] _−_ _α_ [[] _[i]_ []] ∆ _**R**_ [[] _[i][−]_ [1]] _≈_ **0** _,_ (2.84)


where ∆ _**R**_ [[] _[i][−]_ [1]] = _**R**_ ( _**V**_ [[] _[i]_ []] ) _−_ _**R**_ ( _**V**_ [[] _[i][−]_ [1]] ), We want to find a good _α_ [[] _[i]_ []] that best satisfies

Equation 2.84 in terms of least squares. Thus, we obtain _α_ BB [[] _[i]_ []] [as follows:]


_α_ BB [[] _[i]_ []] [:= arg min] _L_ [[] _[i]_ []] ( _α_ ) (2.85)

_α_



R _∋L_ [[] _[i]_ []] ( _α_ ) := [1]

2



 ∆ _**V**_ [ _i−_ 1] _−_ _α_ ∆ _**R**_ [ _i−_ 1]  2 (2.86)



Because of the convexity of the problem, it is sufficient to find an _α_ that satisfies:



_dL_ [[] _[i]_ []]


_dα_



= ∆ _**v**_ [[] _[i][−]_ [1]] _−_ _α_ BB [[] _[i]_ []] [∆] _**[R]**_ [[] _[i][−]_ [1]] [] _·_  _−_ ∆ _**R**_ [[] _[i][−]_ [1]] [] = 0 _._ (2.87)

_α_ [[] BB _[i]_ []]



Using the linearity of the inner product, we obtain:


_−_ ∆ _**v**_ [[] _[i][−]_ [1]] _·_ ∆ _**R**_ [[] _[i][−]_ [1]] + _α_ BB [[] _[i]_ []] [∆] _**[R]**_ [[] _[i][−]_ [1]] _[ ·]_ [ ∆] _**[R]**_ [[] _[i][−]_ [1]] [ = 0] _[,]_


therefore,


_α_ BB [[] _[i]_ []] [=] ∆ [∆] _**R**_ _**[v]**_ [[][[] _[i][i][−][−]_ [1]][1]] _[ ·]_ _·_ [ ∆] ∆ _**[R]**_ _**R**_ [[][[] _[i][i][−][−]_ [1]][1]] _[.]_ (2.88)


Equation 2.88 is equivalent to Equation 2.81.


As can be seen, the derivation above aims to establish an _α_ BB [[] _[i]_ []] [that satisfies Equa-]


tion 2.84 as closely as possible for all vertices and all feature components. This means

that _α_ [[] _[i]_ []]
BB [contains global information because it considers all vertices, making the inclu-]




# Page 53

2.2. Numerical Analysis **29**


sion of global interactions possible. Additionally, _α_ BB [[] _[i]_ []] [is][ E(] _[n]_ [)][-invariant because it is scalar]

that is independent of coordinates. Therefore, _α_ BB [[] _[i]_ []] [is suitable for realizing efficient PDE]


solvers with E( _n_ )-equivariance. Owing to its satisfactory balance between low computa

tional cost and accuracy, the Barzilai–Borwein method is adopted to develop the neural


nonlinear solver presented in Chapter 4


2.2.4 N UMERICAL A NALYSIS FROM A G RAPH R EPRESENTATION V IEW


In this section, we provide an overview of several numerical analysis methods and dis

cuss how they are related to graphs. In particular, we see that the discretized representation


of spatial differentiation is closely related to graphs. For simplicity, we consider the heat


equation _D_ = _c∇· ∇_ . However, the same discussion holds for other PDEs.


2.2.4.1 F INITE D IFFERENCE M ETHOD


The _finite difference method_ (FDM) is one of the most basic numerical analysis


schemes. This method is typically applied to structured grids, where the space is discretized


using lines (1D), squares (2D), or cubes (3D), as shown in Figure 2.6.

##### _u_



図は時間tと位置x_i-1、x_i、x_i+1の関数u(t,x_i)を示し、各点間の距離をhとし、左から右に信号が伝わる様子を説明します。右端の点は左端の点よりhだけ右に移動しています。




##### _x_ x i− 1 x i x i +1

Figure 2.6: An example of a 1D _u_ field spatially discretized using FDM.




# Page 54

**30** 2. Background


In FDM, the gradient operator can be expressed as:


_∂_
_∂x_ _[u]_ [(] _[t, x]_ [)] _[ ≈]_ _[u]_ [(] _[t][,][ x]_ [ +] _[ h]_ _h_ [)] _[ −]_ _[u]_ [(] _[t][,][ x]_ [)] _,_ (2.89)


where _h_ denotes the step size of the spatial discretization. The Laplacian operator is com

puted as follows:


_∇· ∇u_ ( _t, x_ ) _≈∇·_ _[u]_ [(] _[t][,][ x]_ [ +] _[ h]_ [)] _[ −]_ _[u]_ [(] _[t][,][ x]_ [)]

_h_




[1] [ _u_ ( _t, x_ + _h_ ) _−_ _u_ ( _t, x_ )] _−_ [ _u_ ( _t, x_ ) _−_ _u_ ( _t, x −_ _h_ )]

_h_ _h_



_≈_ [1]



_h_



= _h_ [1] [2] [[] _[u]_ [(] _[t, x]_ [ +] _[ h]_ [) +] _[ u]_ [(] _[t, x][ −]_ _[h]_ [)] _[ −]_ [2] _[u]_ [(] _[t, x]_ [)]] _[ .]_ (2.90)



If the vertex positions are denoted using indices as follows:


_x_ _i_ +1 = _x_ + _h_


_x_ _i_ = _x_


_x_ _i−_ 1 = _x −_ _h._


The spatially discretized heat equation becomes


_∂_
_∂t_ _[u]_ [(] _[t, x]_ _[i]_ [) =] _h_ _[c]_ [2] [[] _[u]_ [(] _[t, x]_ _[i][−]_ [1] [)] _[ −]_ [2] _[u]_ [(] _[t, x]_ _[i]_ [) +] _[ u]_ [(] _[t, x]_ _[i]_ [+1] [)]] _[ .]_ (2.91)


This expression involves interactions between vertices, that is, edge connectivity, implying


a graphical structure. By using a matrix form, we can write:

















...

















_u_ ( _t, x_ _i_ +1 )

...



...



_∂_

_∂t_

















_u_ ( _t, x_ _i−_ 1 )

















...


_. . ._ _−_ 1 2 _−_ 1 _. . ._


...



_u_ ( _t, x_ _i_ )



= _−_ _[c]_

_h_ [2]



_u_ ( _t, x_ _i_ )

















_._ (2.92)



...

















Note that the matrix appearing on the right-hand side has the same form as the Laplacian


graph matrix, computed in Equation 2.20, meaning that the Laplacian operator corresponds




# Page 55

2.2. Numerical Analysis **31**


to the Laplacian graph matrix in a spatially discretized setting [3] . By denoting Equation 2.92


as


_∂_

(2.93)

_∂t_ _**[U]**_ [(] _[t]_ [) =] _[ −]_ _h_ _[c]_ [2] _**[L]**_ [FDM] _**[U]**_ [(] _[t]_ [)] _[,]_


one can see that


_D ≈−_ _[c]_ (2.94)

_h_ [2] _**[L]**_ [FDM]


in the present case. The temporal discretization methods discussed in Section 2.2.2 can be


applied to Equation 2.93. For instance, using the explicit Euler method, we obtain:


_**U**_ ( _t_ + ∆ _t_ ) _≈_ _**U**_ ( _t_ ) _−_ _[c]_ (2.95)

_h_ [2] _**[L]**_ [FDM] _**[U]**_ [(] _[t]_ [)∆] _[t.]_


where the coefficient _c_ ∆ _t/h_ [2], is the diffusion number, which must be less than 1 _/_ 2 for


stable computation.





|Col1|Col2|(i, j + 1)|Col4|
|---|---|---|---|
||-1<br>-1|(_i, j_)<br>-1|(_i, j_)<br>-1|
||-1|4||
|||||


( _i, j −_ 1)



Figure 2.7: An example of 2D _u_ field spatially discretized using FDM and its corresponding


edge connectivity.


3 The matrices may differ on the boundary, where some boundary conditions are required.




# Page 56

**32** 2. Background


For the 2D case, we denote the vertex positions using the following indices:


_**x**_ _i,j_ +1 = _**x**_ _i_ + _h_ _**e**_ _y_


_**x**_ _i−_ 1 _,j_ = _**x**_ _i_ _−_ _h_ _**e**_ _x_ _**x**_ _i,j_ = _**x**_ _**x**_ _i_ +1 _,j_ = _**x**_ _i_ + _h_ _**e**_ _x_


_**x**_ _i,j−_ 1 = _**x**_ _i_ _−_ _h_ _**e**_ _y_ _,_


where _**e**_ _x_ and _**e**_ _y_ denote the unit vectors in the _X_ and _Y_ directions, respectively. A sim

ilar discussion leads to the following spatially discretized representation of the 2D heat


equation:


_∂_

[[] _[−][u]_ [(] _[t,]_ _**[ x]**_ _[i][−]_ [1] _[,j]_ [)] _[ −]_ _[u]_ [(] _[t,]_ _**[ x]**_ _[i]_ [+1] _[,j]_ [)]

_∂t_ _[u]_ [(] _[t,]_ _**[ x]**_ _[i]_ [) =] _[ −]_ _h_ _[c]_ [2]


_−u_ ( _t,_ _**x**_ _i,j−_ 1 ) _−_ _u_ ( _t,_ _**x**_ _i,j_ +1 ) + 4 _u_ ( _t,_ _**x**_ _i,j_ )] _,_ (2.96)


which also corresponds to the Laplacian matrix of a corresponding graph, as shown in


Figure 2.7.


2.2.4.2 F INITE E LEMENT M ETHOD (FEM)


The _finite element method_ (FEM) utilizes a set of functions called shape functions,


_N_ : R _[n]_ _→_ R, for the spatial discretization of the weak form of the PDE of interest.


First, we obtain the weak form by integrating the PDE over the domain Ω And multi

plying by an arbitrary test function _v_, as follows:



_v_ ( _**x**_ ) _[∂]_
Ω



_v_ ( _**x**_ ) _c∇· ∇u_ ( _t,_ _**x**_ ) _d_ Ω( _**x**_ ) _._ (2.97)
Ω




[




_[∂]_

_∂t_ _[u]_ [(] _[t,]_ _**[ x]**_ [)] _[d]_ [Ω(] _**[x]**_ [) =] [



Using



_∇·_ ( _v_ ( _**x**_ ) _∇u_ ( _t,_ _**x**_ )) _d_ Ω( _**x**_ )

[ Ω



=

[



( _∇v_ ( _**x**_ )) _·_ ( _∇u_ ( _t,_ _**x**_ )) _d_ Ω( _**x**_ ) +
Ω [



_v_ ( _**x**_ ) _∇· ∇u_ ( _t,_ _**x**_ ) _d_ Ω( _**x**_ ) _,_ (2.98)
Ω




# Page 57

2.2. Numerical Analysis **33**



we obtain:


_c_ _v_ ( _**x**_ ) _∇· ∇u_ ( _t,_ _**x**_ ) _d_ Ω( _**x**_ )

[ Ω



_∇·_ ( _v_ ( _**x**_ ) _∇u_ ( _t,_ _**x**_ )) _d_ Ω( _**x**_ ) _−_ _c_
Ω [



= _c_

[



( _∇v_ ( _**x**_ )) _·_ ( _∇u_ ( _t,_ _**x**_ )) _d_ Ω( _**x**_ ) _._
Ω



(2.99)



Using Stokes’ theorem, the first term on the right-hand side is transformed into:



_c_

[



_∇·_ ( _v_ ( _**x**_ ) _∇u_ ( _t,_ _**x**_ )) _d_ Ω( _**x**_ ) = _c_
Ω [



_v_ ( _**x**_ )( _∇u_ ( _t,_ _**x**_ )) _·_ _**n**_ ( _**x**_ ) _d_ Γ( _**x**_ ) _,_ (2.100)
_∂_ Ω



where _**n**_ ( _**x**_ ) is the normal vector at _**x**_ _∈_ _∂_ Ω. Now, if we assume ( _∇u_ ( _t,_ _**x**_ )) _·_ _**n**_ ( _**x**_ ) = 0


for all _**x**_ _∈_ _∂_ Ω, i.e., the adiabatic condition, Equation 2.100 is equal to zero. Therefore, the


equation to solve is:



_v_ ( _**x**_ ) _[∂]_
Ω



( _∇v_ ( _**x**_ )) _·_ ( _∇u_ ( _t,_ _**x**_ )) _d_ Ω( _**x**_ ) _._ (2.101)
Ω




[




_[∂]_

_∂t_ _[u]_ [(] _[t,]_ _**[ x]**_ [)] _[d]_ [Ω(] _**[x]**_ [) =] _[ −][c]_ [



Next, we consider the spatial discretization using the set of shape functions


_{N_ _i_ ( _**x**_ ) _}_ _i∈{_ 1 _,...,|V|}_, which is typically required to satisfy the following properties:


_∀_ _**x**_ _∈_ Ω _,_ Y _N_ _i_ ( _**x**_ ) =1 (2.102)

_i∈{_ 1 _,...,|V|}_


_∀i ∈{_ 1 _, . . ., |V|},_ supp( _N_ _i_ ) : compact (2.103)


_∀i, j ∈{_ 1 _, . . ., |V|}, N_ _i_ ( _**x**_ _j_ ) = _δ_ _ij_ _,_ (2.104)


where supp( _N_ _i_ ) := _{_ _**x**_ _∈_ Ω _|N_ _i_ ( _**x**_ ) _̸_ = 0 _}_ is the closed support of _N_ _i_ ~~(~~ ~~_·_~~ denotes closure), and


compactness corresponds to the notion of a bounded and closed subset of the Euclidean


space. A typical example of a shape function is the Lagrange interpolating polynomial


shown in Figure 2.8. Using a Lagrange interpolating polynomial of degree one, one can


approximate the field of _u_ and _v_ as follows:


_u_ ( _t,_ _**x**_ ) _≈_ Y _N_ _i_ ( _**x**_ ) _u_ _i_ ( _t_ ) (2.105)

_i∈{_ 1 _,...,|V|}_




# Page 58

**34** 2. Background



_v_ ( _**x**_ ) _≈_ Y _N_ _i_ ( _**x**_ ) _v_ _i_ _,_ (2.106)

_i∈{_ 1 _,...,|V|}_



where _u_ _i_ ( _t_ ) and _v_ _i_ and denotes the value of _u_ ( _t,_ _**x**_ _i_ ) and _v_ ( _**x**_ _i_ ), respectively.

##### _u_









1



|X<br>N u(t, x )<br>i i<br>i<br>N5m+Ufrb0q6VL327thW/OvnSdYJXesTj8Fpkw=<laxi>u(t, x )<br>/latexi>u(t, x i−1) i fr/xpskbZ8vdPS5e+XV3n2l06Cc9L7oH1mJBOqgM=<ati>u(t, x )<br>i+1<br>N N N<br>i−1 i i+1|Col2|Col3|Col4|Col5|
|---|---|---|---|---|
||_Ni−_1||_Ni_|_Ni_+1|

##### x i− 1 x i x i +1


##### _x_



Figure 2.8: An example of a 1D _u_ field spatially discretized using FEM.


Using the shape function, we discretize Equation 2.101 as follows:



( _∇N_ _i_ ( _**x**_ ) _v_ _i_ ) _·_ ( _∇N_ _j_ ( _**x**_ ) _u_ _j_ ( _t_ )) _d_ Ω( _**x**_ )

[ Ω



_ij_



Y

_ij_




[



_∂_
_N_ _i_ ( _**x**_ ) _v_ _i_ Y
Ω _∂t_ _[N]_ _[j]_ [(] _**[x]**_ [)] _[u]_ _[j]_ [(] _[t]_ [)] _[d]_ [Ω(] _**[x]**_ [) =] _[ −][c]_



_∂_
_∂t_ _[u]_ _[j]_ [(] _[t]_ [)] [



_u_ _j_ ( _t_ )

[
_ij_



( _∇N_ _i_ ( _**x**_ )) _·_ ( _∇N_ _j_ ( _**x**_ )) _d_ Ω( _**x**_ ) _._
Ω



Y

_ij_



_N_ _i_ ( _**x**_ ) _N_ _j_ ( _**x**_ ) _d_ Ω( _**x**_ ) = _−c_ Y
Ω



By letting



(2.107)


_M_ _ij_ := _N_ _i_ ( _**x**_ ) _N_ _j_ ( _**x**_ ) _d_ Ω( _**x**_ ) (2.108)

[ Ω



_K_ _ij_ := _−_ _c_ ( _∇N_ _i_ ( _**x**_ )) _·_ ( _∇N_ _j_ ( _**x**_ )) _d_ Ω( _**x**_ ) _,_ (2.109)

[ Ω




# Page 59

one can obtain:


In particular, for the 1D case:



2.2. Numerical Analysis **35**


_**M**_ _[∂]_ (2.110)

_∂t_ _**[U]**_ [(] _[t]_ [) =] _**[ KU]**_ [(] _[t]_ [)] _[.]_



_K_ _ij_ =














_−_ 2 _c/h_ if _i_ = _j_


_c/h_ if _|i −_ _j|_ = 1


0 otherwise



_,_ (2.111)



thus establishing a relationship to the graph Laplacian matrix in the FEM case. Finally, we


obtain:


_∂_
(2.112)
_∂t_ _**[U]**_ [(] _[t]_ [) =] _**[ M]**_ _[ −]_ [1] _**[KU]**_ [(] _[t]_ [)] _[.]_


Again, we confirm that the spatial discretization introduces interactions between vertices,


that is, graph-like message passing. The connectivity of the graph corresponding to the 2D


case is shown in Figure 2.9. It should be noted that the connectivity of the graph is not


necessarily the same as the edges of the mesh.

中心の黒いノードが主要ノード。周囲のノードをクラスタとし、強い接続を示す。青い矢印が主な接続方向、橙色の回転矢印を含む。


Figure 2.9: An example of 2D spatially discretized unstructured grid for FEM (black) and


its corresponding edge connectivity (blue). The connectivity of the graph is not necessarily


the same as the edges of the mesh.




# Page 60

**36** 2. Background


2.2.4.3 L EAST S QUARES M OVING P ARTICLE S EMI -I MPLICIT (LSMPS) M ETHOD


The _least qquares moving particle semi-implicit_ (LSMPS) method is a mesh-free tech

nique for solving PDEs proposed by Tamai & Koshizuka (2014). Although the scheme


proposes a general method to approximate the differential up to an arbitrary order, for sim

plicity, we introduce only the first-order gradient model, which, using the LSMPS method,


is expressed as



_⟨∇u⟩|_ _**x**_ _i_ := _**M**_ _i_ _[−]_ [1] Y

_j∈N_ _i_



_u_ _j_ _−_ _u_ _i_ _**x**_ _j_ _−_ _**x**_ _i_
(2.113)
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[w]_ _[ij]_



_**M**_ _i_ :=
Y


_l_



_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
(2.114)
_∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[w]_ _[il]_ _[,]_



where _u_ : Ω _→_ R is a scalar field, _u_ _i_ denotes _u_ ( _**x**_ _i_ ), and _w_ _ij_ is a weight determined


depending on the distance between _**x**_ _i_ and _**x**_ _j_ . Because this method does not require a


mesh, _N_ _i_ is determined using the effective radius set by the users.


The first-order model is derived using the first-order Taylor expansion as follows:


_u_ _j_ _≈_ _u_ _i_ + ( _**x**_ _j_ _−_ _**x**_ _i_ ) _·_ ( _∇u_ ) _|_ _**x**_ _i_ _, ∀j ∈N_ _i_ _._ (2.115)


Since _∇u|_ _**x**_ _i_ is what we want to obtain, and we let _∇u|_ _**x**_ _i_ = _**X**_ _i_, then we rewrite the


equation as:


_**x**_ _j_ _−_ _**x**_ _i_ _u_ _j_ _−_ _u_ _i_
(2.116)
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[·]_ _**[ X]**_ _[i]_ _[ −]_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[≈]_ [0] _[,][ ∀][j][ ∈N]_ _[i]_ _[.]_


We consider a situation in which _|N_ _i_ _| ≥_ _n_ ( _n_ denotes the spatial dimension), then one can


obtain _**X**_ _i_ in terms of least squares, by defining a weighted evaluation function _J_ ( _**X**_ _i_ ) as


follows:



2

_._ (2.117)




_J_ ( _**X**_ _i_ ) := [1]

2



Y _w_ _ij_

_j∈N_ _i_



Y



_**x**_ _j_ _−_ _**x**_ _i_ _u_ _j_ _−_ _u_ _i_
 _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[·]_ _**[ X]**_ _[i]_ _[ −]_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_



_**x**_ _j_ _−_ _**x**_ _i_
 _∥_ _**x**_ _j_ _−_ _**x**_ _i_




# Page 61

2.2. Numerical Analysis **37**


The best approximation to the gradient _**X**_ _i_ _[∗]_ _[≈∇][u][|]_ _**[x]**_ _i_ [in terms of least squares can be]


obtained when _∇_ _**X**_ _i_ _J_ ( _**X**_ _i_ _[∗]_ [) =] **[ 0]** [, therefore, we solve:]



_**x**_ _j_ _−_ _**x**_ _i_

(2.118)

 _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ [=] **[ 0]** _[.]_



_∇_ _**X**_ _i_ _J_ ( _**X**_ _i_ _[∗]_ [) =] Y _w_ _ij_

_j∈N_ _i_



_**x**_ _j_ _−_ _**x**_ _i_ _u_ _j_ _−_ _u_ _i_

_i_ _[−]_

 _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[·]_ _**[ X]**_ _[∗]_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_



For any vectors _**v**_ _,_ _**w**_ _∈_ R _[n]_, the following condition holds:


( _**v**_ _·_ _**w**_ ) _**v**_ = ( _**v**_ _⊗_ _**v**_ ) _**w**_ _,_ (2.119)


because


[( _**v**_ _·_ _**w**_ ) _**v**_ ] _i_ = Y _v_ _k_ _w_ _k_ _v_ _i_ (2.120)


_k_

= Y ( _v_ _i_ _v_ _k_ ) _w_ _k_ (2.121)


_k_


= [( _**v**_ _⊗_ _**v**_ ) _**w**_ ] _i_ _._ (2.122)


Therefore, by substituting



_j_ _−_ _**x**_ _i_ _**x**_ _j_ _−_ _**x**_ _i_

_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_



_**x**_ _j_ _−_ _**x**_ _i_

_i_

 _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[·]_ _**[ X]**_ _[∗]_



_**x**_ _j_ _−_ _**x**_ _i_
 _∥_ _**x**_ _j_ _−_ _**x**_ _i_



_**x**_ _j_ _−_ _**x**_ _i_ _**x**_ _j_ _−_ _**x**_ _i_

_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ [=]  _∥_ _**x**_ _j_ _−_ _**x**_ _i_



_**X**_ _i_ _[∗]_ (2.123)




into Equation 2.118, we get:



_u_ _j_ _−_ _u_ _i_ _**x**_ _j_ _−_ _**x**_ _i_
(2.124)
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[.]_



Y

_l∈N_ _i_



_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
 _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_



_**X**_ _i_ _[∗]_ [=] Y


_j∈N_ _i_



_**X**_ _i_ _[∗]_ [=] Y




By solving this, we finally obtain:



_−_ 1
Y
$ _j∈N_ _i_



_u_ _j_ _−_ _u_ _i_ _**x**_ _j_ _−_ _**x**_ _i_
(2.125)
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[,]_



_**X**_ _i_ _[∗]_ [=]



#Y _l∈N_ _i_



_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
_∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_



which is equivalent to Equation 2.113.


Although the Laplacian model can be derived in a different manner, one can apply


the gradient operator twice, and then compute the trace to obtain a representation of the




# Page 62

**38** 2. Background


Laplacian operator. Nevertheless, we again confirm that Equation 2.113 introduces edge


connectivity through the spatial differentiation. The LSMPS model is also important be

cause it is used as the foundation of our IsoGCN model, owing to its high generalizability,


as seen in Chapter 3.




# Page 63

# **Chapter 3** **_n_** **IsoGCN: E( )-Equivariant Graph** **Convolutional Network**

3.1 I NTRODUCTION


Graph-structured data embedded in Euclidean spaces can be utilized in many differ

ent fields such as object detection, structural chemistry analysis, and physical simulations.


Graph neural networks (GNNs) have been introduced to deal with such data. The cru

cial properties of GNNs include permutation invariance and equivariance, as seen in Sec

tion 2.1.3.2. Besides permutations, E( _n_ )-invariance and equivariance must be addressed


when considering graphs in Euclidean spaces because many properties of objects in the


Euclidean space do not change under translation and rotation. Due to such invariance and


equivariance, we can expect:


1. the interpretation of the model is facilitated;


2. the output of the model is stabilized and predictable; and


3. the training is rendered efficient by eliminating the necessity of data augmentation,


as discussed in the literature (Thomas et al., 2018; Weiler et al., 2018; Fuchs et al., 2020).


E( _n_ )-invariance and equivariance are inevitable, especially when applied to physical


simulations, because every physical quantity and physical law is either invariant or equiv

39




# Page 64

**40** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


ariant to such a transformation. Another essential requirement for such applications is


computational efficiency because the primary objective of learning a physical simulation is


to replace a computationally expensive simulation method with a faster machine learning


model.


In this chapter, we present _IsoGCNs_, a set of simple yet powerful models that pro

vide computationally-efficient E( _n_ )- invariance and equivariance based on GCNs (Kipf &


Welling, 2017). Specifically, by simply tweaking the definition of an adjacency matrix,


the proposed model can realize E( _n_ )-invariance. Because the proposed approach relies on


graphs, it can deal with the complex shapes that are usually presented using mesh or point


cloud data structures. Besides, a specific form of the IsoGCN layer can be regarded as a


spatial differential operator that is essential for describing physical laws. In addition, we


have shown that the proposed approach is computationally efficient in terms of process

ing graphs with up to 1M vertices that are often presented in real physical simulations.


Moreover, the proposed model exhibited faster inference compared to a conventional fi

nite element analysis approach at the same level of accuracy. Therefore, IsoGCN models


can suitably replace physical simulations regarding its power to express physical laws and


faster, scalable computation. The corresponding implementation and the dataset are avail

able online [1] .


The main contributions of the present study can be summarized as follows:


   - We construct E( _n_ )- invariant and equivariant GCNs, called IsoGCNs for the speci

fied input and output tensor ranks.


   - We demonstrate that an IsoGCN model enjoys competitive performance against


state-of-the-art baseline models on the considered tasks related to physical simula

tions.


   - We confirm that IsoGCNs can be scalable to graphs with 1M vertices and achieve


inference considerably faster than conventional finite element analysis, while exist

ing state-of-the-art baseline machine learning models cannot.


1 [https://github.com/yellowshippo/isogcn-iclr2021](https://github.com/yellowshippo/isogcn-iclr2021)




# Page 65

3.2. Related Prior Work **41**


3.2 R ELATED P RIOR W ORK


3.2.1 GCN


Our IsoGCN models are based on GCN (Kipf & Welling, 2017), a lightweight GNN


model, because GCN shows computational efficiency compared to other GNNs, where


message functions are constructed using deep neural networks (Equations 2.35 and 2.37).


In addition, GCN models can be E( _n_ )-invariant if all input features are E( _n_ )-equivariant


because the renormalized adjacency matrix is also invariant.


However, since the message function in the GCN models is determined only by in

formation on edge connectivities in the graphs, there have been difficulties in capturing


geometrical information of meshes, e.g., the distance between vertices and angles between


edges. GCN models can consider geometrical information, e.g., by feeding vertex posi

tions to the model; however, this kind of ad-hoc solution will destroy the E( _n_ )-invariance,


resulting in unstable prediction for geometrical data. The IsoGCN model successfully in

corporates geometrical data through IsoAM (Equation 3.8), a set of adjacency matrices


reflecting the geometry of meshes while retaining the computational efficiency of GCNs.


3.2.2 TFN


Another essential basis of our model is TFN (Thomas et al., 2018) (Equation 2.50).


Their model incorporates SE(3)- invariance and equivariance, where SE(3) is a subgroup


of E(3) without reflection. The idea of TFN is to guarantee SE(3)-equivariance using spher

ical harmonics, which are SE(3)-equivariant functions, and nonlinear neural networks are


applied to the norm of relative positions of vertices so that equivariance is not destroyed


due to nonlinearity.


The TFN model achieves high expressibility based on spherical harmonics and message


passing with nonlinear neural networks. However, for this reason, considerable computa

tional resources are required. In contrast, the present study allows a significant reduction in


the computational costs because it eliminates spherical harmonics and nonlinear message


passing. From this perspective, IsoGCNs are also regarded as a simplification of the TFN,


as seen in equation 3.45.




# Page 66

**42** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


3.2.3 GNN M ODEL FOR P HYSICAL S IMULATION


Several related studies, including those by Sanchez-Gonzalez et al. (2018; 2019); Alet


et al. (2019); Chang & Cheng (2020) focused on applying GNNs to learn physical sim

ulations. These approaches allowed the physical information to be introduced to GNNs;


however, addressing E( _n_ )-equivariance was out of the scope of their research.


In the present study, we incorporate E( _n_ )-invariance and equivariance into GCNs,


thereby, ensuring the stability of the training and inference under E( _n_ ) transformation.


Moreover, the proposed approach is efficient in processing large graphs with up to 1M


vertices that have a sufficient number of degrees of freedom to express complex shapes.


3.3 M ETHOD


In this section, we discuss how to construct IsoGCN layers that correspond to the E( _n_ )

invariant and equivariant GCN layers. To formulate a model, we assume that:


1. only attributes associated with vertices and not edges; and


2. graphs do not contain self-loops.


Here, _n_ denotes the dimension of the Euclidean space we are working on.


3.3.1 D ISCRETE T ENSOR F IELD


### ( )



中心ノード「i」を主軸とし、強い接続を示す赤色の「H^(1)_{i;1};;」と緑色の接続が主な特徴です。周囲のノード間には、赤緑の矢印で示された相互作用が存在します。


### ( b )







中心ノード「i」を主軸とし、その周囲のノード間で強い接続が示された図。各ノードは「i」と「j」を表し、強い相互接続を示す青色の矢印が存在。





Figure 3.1: Schematic diagrams of (a) rank-1 tensor field _**H**_ [(1)] with the number of features


equaling 2 and (b) the simplest case of _**G**_ _ij_ ;;: = _δ_ _il_ _δ_ _jk_ _A_ _ij_ _**I**_ ( _**x**_ _k_ _−_ _**x**_ _l_ ) = _A_ _ij_ ( _**x**_ _j_ _−_ _**x**_ _i_ ).




# Page 67

3.3. Method **43**


First, we introduce the concept of _discrete tensor fields_, which play an essential role to


constract E( _n_ )-equivariant models. In the present study, we refer to tensor as geometric


tensors, i.e., a rank- _p_ tensor field _**u**_ : Ω _→_ [(] _[p]_ [)] _∈_ R _[n]_ _[p]_ is equivariant with regard to the


orthogonal transformation using _**U**_ expressed as:


_**U**_ : _u_ [(] _k_ _[p]_ 1 [)] _k_ 2 _...k_ _p_ _[8→]_ _[U]_ _[k]_ 1 _[l]_ 1 _[U]_ _[k]_ 2 _[l]_ 2 _[. . . U]_ _[k]_ _p_ _[l]_ _p_ _[u]_ _l_ [(] 1 _[p]_ _l_ [)] 2 _...l_ _p_ _[.]_ (3.1)


To exploit the expressive power of neural networks, we consider a collection of _d_ f tensors


with rank- _p_ such as:


_**h**_ [(] _[p]_ [)] := ( _**u**_ [(] _[p]_ [)] _,_ _**v**_ [(] _[p]_ [)] _,_ _**w**_ [(] _[p]_ [)] _, . . ._ ) : Ω _→_ R _[d]_ [f] _[×][n]_ _[p]_ _._ (3.2)
} |{ ~~~~~
_d_ f items


This is a collection of rank- _p_ tensor field, so note that


_**h**_ [(] _[p]_ [)] ( _**x**_ ) _∈_ R _[d]_ [f] _[×][n]_ _[p]_ (3.3)


and


_**U**_ : _h_ [(] _g_ _[p]_ ; _k_ [)] 1 _k_ 2 _...k_ _p_ _[8→]_ _[U]_ _[k]_ 1 _[l]_ 1 _[U]_ _[k]_ 2 _[l]_ 2 _[. . . U]_ _[k]_ _p_ _[l]_ _p_ _[h]_ [(] _g_ _[p]_ ; _l_ [)] 1 _l_ 2 _...l_ _p_ (3.4)


hold.


Now, we consider a _discrete rank-p tensor field_ _**H**_ [(] _[p]_ [)] _∈_ R _[|V|×][d]_ [f] _[×][n]_ _[p]_, as follows:




















_**H**_ [(] _[p]_ [)] :=




















_**h**_ [(] _[p]_ [)] ( _**x**_ 1 )


_**h**_ [(] _[p]_ [)] ( _**x**_ 2 )


...



_,_ (3.5)



_**h**_ [(] _[p]_ [)] ( _**x**_ _|V|_ )



where _d_ f denotes the number of features (channels) of _**H**_ [(] _[p]_ [)], and _**x**_ _i_ _∈_ Ω _⊂_ R _[n]_ is the


position of the _i_ th vertex. An example of the discrete tensor field is shown in Figure 3.1




# Page 68

**44** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


(a). With the indices, we denote _H_ _i_ [(] ; _[p]_ _g_ [)] ; _k_ 1 _k_ 2 _...k_ _p_ [, where] _[ i]_ [ permutes under the permutation of]


vertices and _k_ 1 _, . . ., k_ _p_ refers to the Euclidean representation. _g_ is the index of features, so


invariant with regard to permutation and E( _n_ ) transformation. Thus, under the permutation


_π_, _**H**_ [(] _[p]_ [)] is equivariant with regard to the vertex indices:


_π_ : _H_ _i_ [(] ; _[p]_ _g_ [)] ; _k_ 1 _k_ 2 _...k_ _p_ _[8→]_ _[H]_ _π_ [(] _[p]_ ( _i_ [)] ); _g_ ; _k_ 1 _k_ 2 _...k_ _p_ _[,]_ (3.6)


and under orthogonal transformation _**U**_, _**H**_ [(] _[p]_ [)] is equivariant with regard to the dimensional


indices:


_**U**_ : _H_ _i_ [(] ; _[p]_ _g_ [)] ; _k_ 1 _k_ 2 _...k_ _p_ _[8→]_ Y _U_ _k_ 1 _l_ 1 _U_ _k_ 2 _l_ 2 _. . . U_ _k_ _p_ _l_ _p_ _H_ _i_ [(] ; _[p]_ _g_ [)] ; _l_ 1 _l_ 2 _...l_ _p_ _[.]_ (3.7)

_l_ 1 _,l_ 2 _,...,l_ _p_


We use discrete tensor fields for inputs, hidden state, and outputs of our IsoGCN models.


3.3.2 I SOMETRIC A DJACENCY M ATRIX (I SO AM)


Before constructing an IsoGCN, an _isometric adjacency matrix_ (IsoAM), which is at


the core of the IsoGCN concept must be defined.


3.3.2.1 D EFINITION OF I SO AM


An IsoAM _**G**_ _∈_ R _[|V|]_ [2] _[×]_ [1] _[×][n]_ is defined as:


R _[d]_ _∋_ _**G**_ _ij_ ;;: := _**g**_ _ij_ := Y _**T**_ _ijkl_ ( _**x**_ _k_ _−_ _**x**_ _l_ ) _,_ (3.8)

_k,l∈V,k_ = _̸_ _l_


where _**G**_ _ij_ ;;: is a slice in the spatial index of _**G**_, and _**T**_ _ijkl_ _∈_ R _[n][×][n]_ is an untrainable trans

formation invariant and orthogonal transformation equivariant rank-2 tensor defined de

pending on the problem of interest. Note that we denote _G_ _ij_ ;; _k_ to be consistent with the

notation of the discrete tensor field _H_ _i_ [(] ; _[p]_ _g_ [)] ; _k_ 1 _k_ 2 _...k_ _p_ [because] _[ i]_ [ and] _[ j]_ [ permutes under the vertex]


permutation and _k_ represents the spatial index while the number of features is always 1.


The IsoAM can be viewed as a weighted adjacency matrix for each direction and reflects


spatial information while the usual weighted adjacency matrix cannot because a graph has


only one adjacency matrix. Also, IsoAM can be viewed as a rank-1-tensor-valued matrix




# Page 69

expressed as:



3.3. Method **45**


_._ (3.9)



_**G**_ =




















_**g**_ 11 _**g**_ 12 _. . ._ _**g**_ 1 _|V|_


_**g**_ 21 _**g**_ 22 _. . ._ _**g**_ 2 _|V|_


... ... ... ...



_**g**_ _|V|_ 1 _**g**_ _|V|_ 2 _. . ._ _**g**_ _|V||V|_




















For the simplest case, one can define _**T**_ _ijkl_ = _δ_ _il_ _δ_ _jk_ _A_ _ij_ _**I**_ _n_ (Figure 3.1 (b)), where _δ_ _ij_ is


the Kronecker delta, _**A**_ is the adjacency matrix of the graph, and _**I**_ _n_ is the _n_ -dimensional


identity matrix that is the simplest rank-2 tensor. With the simplification, the definition of


IsoAM (Equation 3.8) is expressed as:


_**g**_ _ij_ = _A_ _ij_ ( _**x**_ _j_ _−_ _**x**_ _i_ ) _._ (3.10)


In the case of the path graph with five vertices (Figure 2.2), it can be expressed as:



**0** _**x**_ 2 _−_ _**x**_ 1 **0** **0** **0**



_**x**_ 1 _−_ _**x**_ 2 **0** _**x**_ 3 _−_ _**x**_ 2 **0** **0**



_**G**_ =

















**0** _**x**_ 2 _−_ _**x**_ 3 **0** _**x**_ 4 _−_ _**x**_ 3 **0**


**0** **0** _**x**_ 3 _−_ _**x**_ 4 **0** _**x**_ 5 _−_ _**x**_ 4


**0** **0** **0** _**x**_ 4 _−_ _**x**_ 5 **0**

















_._ (3.11)



Therefore, one can see the IsoAMs are based on relative positions of vertices, which are


translation invariant and orthogonal transformation equivariant.


In another case, _**T**_ _ijkl_ can be determined from the geometry of a graph, as defined


in Equation 3.47. Nevertheless, in the bulk of this section, we retain _**T**_ _ijkl_ abstract to cover


various forms of interaction, such as position-aware GNNs (You et al., 2019). Here, _**G**_ is


composed of only untrainable parameters and thus can be determined before training.




# Page 70

**46** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


3.3.2.2 P ROPERTY OF I SO AM


Here, we present the properties of the IsoAM defined by Equation 3.8. We let R [3] _∋_


_**d**_ ( _**x**_ _l_ _,_ _**x**_ _k_ ) = ( _**x**_ _k_ _−_ _**x**_ _l_ ) for the proofs. Note that _**G**_ is expressed using _**d**_ ( _**x**_ _i_ _,_ _**x**_ _j_ ) as


_**G**_ _ij_ ;;: = _**g**_ _ij_ = Y _**T**_ _ijkl_ _**d**_ ( _**x**_ _l_ _,_ _**x**_ _k_ ) _._ (3.12)

_k,l∈V,k_ = _̸_ _l_


**Proposition 3.3.1.** _IsoAM defined in Equation 3.8 is translation invariant and orthogonal_


_transformation equivariant, i.e., for any_ E( _n_ ) _transformation ∀_ _**t**_ _∈_ R _[n]_ _,_ _**U**_ _∈_ O( _n_ ) _, T_ :


_**x**_ _8→_ _**Ux**_ + _**t**_ _,_


_T_ : _G_ _ij_ ;; _k_ _8→_ Y _U_ _kl_ _G_ _ij_ ;; _l_ _._ (3.13)


_l_


_Proof._ First, we demonstrate the invariance with respect to the translation with _∀_ _**t**_ _∈_ R _[d]_ .


_**d**_ ( _**x**_ _i_ _,_ _**x**_ _j_ ) is transformed invariantly as follows under translation:


_**d**_ ( _**x**_ _i_ + _**t**_ _,_ _**x**_ _j_ + _**t**_ ) = [ _**x**_ _j_ + _**t**_ _−_ ( _**x**_ _i_ + _**t**_ )]


= ( _**x**_ _j_ _−_ _**x**_ _i_ )


= _**d**_ ( _**x**_ _i_ _,_ _**x**_ _j_ ) _._ (3.14)


By definition, _**T**_ _ijkl_ is also translation invariant. Thus,


_̸_ _̸_



_̸_


Y _**T**_ _ijkl_ _**d**_ ( _**x**_ _l_ + _**t**_ _,_ _**x**_ _k_ + _**t**_ ) = Y

_k,l∈V,k_ = _̸_ _l_ _k,l∈V,k̸_



_̸_


Y

_̸_ _̸_



_̸_


Y _**T**_ _ijkl_ _**d**_ ( _**x**_ _l_ _,_ _**x**_ _k_ )
_̸_ _k,l∈V,k_ = _̸_ _l_



_̸_


_̸_ _̸_


= _**G**_ _ij_ ;;: _._ (3.15)


We then show an equivariance regarding the orthogonal transformation with _∀_ _**U**_ _∈_ O( _d_ ).


_**d**_ ( _**x**_ _i_ _,_ _**x**_ _j_ ) is transformed as follows by orthogonal transformation:


_**d**_ ( _**Ux**_ _i_ _,_ _**Ux**_ _j_ ) = _**Ux**_ _j_ _−_ _**Ux**_ _i_


= _**U**_ ( _**x**_ _j_ _−_ _**x**_ _i_ )


= _**Ud**_ ( _**x**_ _i_ _,_ _**x**_ _j_ ) _._ (3.16)




# Page 71

3.3. Method **47**


By definition, _**T**_ _ijkl_ is transformed to _**UT**_ _ijkl_ _**U**_ _[−]_ [1] by orthogonal transformation. Thus,


_̸_ _̸_



Y _**UT**_ _ijkl_ _**U**_ _[−]_ [1] _**d**_ ( _**Ux**_ _l_ _,_ _**Ux**_ _k_ ) = Y

_k,l∈V,k_ = _̸_ _l_ _k,l∈V,k̸_



Y

_̸_ _̸_



Y _**UT**_ _ijkl_ _**U**_ _[−]_ [1] _**Ud**_ ( _**x**_ _l_ _,_ _**x**_ _k_ )
_̸_ _k,l∈V,k_ = _̸_ _l_



_̸_ _̸_


= _**UG**_ _ij_ ;;: _._ (3.17)


Therefore, _**G**_ is translation invariant and an orthogonal transformation equivariant.


Here, we define essential operations between IsoAMs and discrete tensor fields. Based


on the definition of the GCN layer in the equation 2.35, let _**G**_ _∗_ _**H**_ [(0)] _∈_ R _[|V|×][f]_ _[×][d]_ denote


the _convolution_ between _**G**_ and the rank-0 tensor field _**H**_ [(0)] _∈_ R _[|V|×][d]_ [f] as follows:


( _**G**_ _∗_ _**H**_ [(0)] ) _i_ ; _g_ ; _k_ := Y _**G**_ _ij_ ;; _k_ _H_ _j_ [(0)] ; _g_ ; _[.]_ (3.18)

_j_


With a rank-1 tensor field _**H**_ [(1)] _∈_ R _[|V|×][f]_ _[×][d]_, let _**G**_ _⊙_ _**H**_ [(1)] _∈_ R _[|V|×][f]_ and _**G**_ _⊙_ _**G**_ _∈_


R _[|V|×|V|]_ denote the _contractions_ which are defined as follows:


( _**G**_ _⊙_ _**H**_ [(1)] ) _i_ ; _g_ ; := Y _G_ _ij_ ;; _k_ _H_ _j_ [(1)] ; _g_ ; _k_ (3.19)

_j,k_

( _**G**_ _⊙_ _**G**_ ) _il_ ;; := Y _G_ _ij_ ;; _k_ _G_ _jl_ ; _k_ _._ (3.20)

_j,k_


The contraction of IsoAMs _**G**_ _⊙_ _**G**_ can be interpreted as the inner product of each compo

nent in the IsoAMs. Thus, the subsequent proposition follows.


**Proposition 3.3.2.** _The contraction of IsoAMs_ _**G**_ _⊙_ _**G**_ _is_ E( _n_ ) _-invariant, i.e., for any_ E( _n_ )


_transformation ∀_ _**t**_ _∈_ R [3] _,_ _**U**_ _∈_ O( _d_ ) _, T_ : _**x**_ _8→_ _**Ux**_ + _**t**_ _,_ _**G**_ _⊙_ _**G**_ _8→_ _**G**_ _⊙_ _**G**_ _._


_Proof._ Here, _**G**_ _⊙_ _**G**_ is translation invariant because _**G**_ is translation invariant. We prove


rotation invariance under an orthogonal transformation _∀_ _**U**_ _∈_ O( _n_ ). In addition, _**G**_ _⊙_ _**G**_ is




# Page 72

**48** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


transformed under _**U**_ as follows:



Y



Y _G_ _ij_ ;; _k_ _G_ _jl_ ;; _k_ _8→_ Y

_j,k_ _j,k,m,n_



Y _U_ _km_ _G_ _ij_ ;; _m_ _U_ _kn_ _G_ _jl_ ;; _n_

_j,k,m,n_



= Y _U_ _km_ _U_ _kn_ _G_ _ij_ ;; _m_ _G_ _jl_ ;; _n_

_j,k,m,n_



= Y _U_ _mk_ _[T]_ _[U]_ _[kn]_ _[G]_ _[ij]_ [;;] _[m]_ _[G]_ _[jl]_ [;;] _[n]_

_j,k,m,n_



= Y _δ_ _mn_ _G_ _ij_ ;; _m_ _G_ _jl_ ;; _n_ (∵ property of the orthogonal matrix)

_j,m,n_



= Y _G_ _ij_ ;; _m_ _G_ _jl_ ;; _m_

_j_



= Y _G_ _ij_ ;; _k_ _G_ _jl_ ;; _k_ _._ (∵ Change the dummy index _m →_ _k_ )

_j,k_



(3.21)


Therefore, _**G**_ _⊙_ _**G**_ is E( _n_ )-invariant.


With a rank- _p_ tensor field _**H**_ [(] _[p]_ [)] _∈_ R _[|V|×][f]_ _[×][d]_ _[p]_, let _**G**_ _⊗_ _**H**_ [(] _[p]_ [)] _∈_ R _[|V|×][f]_ _[×][d]_ [1+] _[p]_ . and _**G**_ _⊗_ _**G**_ _∈_

R _[|V|×|V|×][d]_ [2] denote the **tensor products** defined as follows:


( _**G**_ _⊗_ _**H**_ [(] _[p]_ [)] ) _i_ ; _g_ ; _km_ 1 _m_ 2 _...m_ _p_ := Y _**G**_ _ij_ ;; _k_ _H_ _j_ [(] ; _[p]_ _g_ [)] ; _m_ 1 _m_ 2 _...m_ _p_ _[,]_ (3.22)

_j_

( _**G**_ _⊗_ _**G**_ ) _il_ ;; _k_ 1 _k_ 2 := Y _**G**_ _ij_ ;; _k_ 1 _**G**_ _jl_ ;; _k_ 2 _._ (3.23)

_j_


The tensor product of IsoAMs _**G**_ _⊗_ _**G**_ can be interpreted as the tensor product of each of


the IsoAMs components. Thus, the subsequent proposition follows:


**Proposition 3.3.3.** _The tensor product of the IsoAMs_ _**G**_ _⊗_ _**G**_ _is_ E( _n_ ) _-equivariant in terms of_


_the rank-2 tensor, i.e., for any_ E( _n_ ) _transformation ∀_ _**t**_ _∈_ R [3] _,_ _**U**_ _∈_ O( _d_ ) _, T_ : _**x**_ _8→_ _**Ux**_ + _**t**_ _,_


_and ∀i, j ∈_ 1 _, . . ., |V|,_ ( _**G**_ _⊗_ _**G**_ ) _ij_ ;; _k_ 1 _k_ 2 _8→_ _**U**_ _k_ 1 _l_ 1 _**U**_ _k_ 2 _l_ 2 ( _**G**_ _⊗_ _**G**_ ) _ij_ ;; _l_ 1 _l_ 2 _._




# Page 73

3.3. Method **49**



_Proof._ _**G**_ _⊗_ _**G**_ is transformed under _∀_ _**U**_ _∈_ O( _n_ ) as follows:



Y



_U_ _kn_ _G_ _ij_ ;; _n_ _U_ _mo_ _G_ _jl_ ;; _o_

_n,o_



_G_ _ij_ ;; _k_ _G_ _jl_ ;; _m_ _8→_ Y
_j_ _n,o_



= Y _U_ _kn_ _G_ _ij_ ;; _n_ _G_ _jl_ ;; _o_ _U_ _om_ _[T]_ _[.]_ (3.24)


_n,o_



By regarding _G_ _ij_ ;; _n_ _G_ _jl_ ;; _o_ as one matrix _H_ _no_, it follows the coordinate transformation of


rank-2 tensor _**UHU**_ _[T]_ for each _i_, _j_, and _l_ .


This proposition is easily generalized to the tensors of higher ranks by defining the _p_ th


tensor power of _**G**_ as follows:


0

_**G**_ = 1 (3.25)
P


1

_**G**_ = _**G**_ (3.26)
P



_p_
P _**G**_ =



_p−_ 1
P _**G**_ _⊗_ _**G**_ ( _p >_ 1) _._ (3.27)



Namely, [O] _[p]_ _**G**_ is E( _n_ )-equivariant in terms of rank- _p_ tensor. Also, one can compute the


tensor product between the rank- _p_ IsoAM and rank- _q_ discrete tensor field as follows:



_p_
P _**G**_
! "



_⊗_ _**H**_ [(] _[q]_ [)] =


=



_p−_ 1
P _**G**_
! "



_p−_ 2
P _**G**_
! "



_⊗_ ( _**G**_ _⊗_ _**H**_ [(] _[q]_ [)] )
} ~~|~~ { ~~~~~

Let _**H**_ [(] _[q]_ [+1)]


_⊗_ ( _**G**_ _⊗_ _**H**_ [(] _[q]_ [+1)] )
} ~~|{~~ ~~~~~

Let _**H**_ [(] _[q]_ [+2)]



= _. . ._


= _**H**_ [(] _[q]_ [+] _[p]_ [)] (3.28)


Similarly, the convolution can be generalized for [O] _[p]_ _**G**_ and the rank-0 tensor field _**H**_ [(0)] _∈_


R _[|V|×][f]_ as follows:



_p_
P _**G**_
#! "



_∗_ _**H**_ [(0)]
$



=
Y
_i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_ _j_



_H_ _j_ [(0)] ; _g_ ; _[.]_ (3.29)

_ij_ ;; _k_ 1 _k_ 2 _...k_ _p_



_p_
P _**G**_
!



"




# Page 74

**50** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


The contraction can be generalized for [O] _[p]_ _**G**_ and the rank- _q_ tensor field _**H**_ [(] _[q]_ [)] _∈_ R _[|V|×][f]_ _[×][d]_ _[q]_


( _p ≥_ _q_ ) as specified below:



_p_
P _**G**_
#! "



_⊙_ _**H**_ [(] _[q]_ [)]
$



=
Y
_i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p−q_ _j,m_ 1 _,m_ 2 _,...,m_ _q_



_H_ [(] _[q]_ [)]
_j_ ; _g_ ; _m_ 1 _m_ 2 _...m_ _q_ _[.]_

_ij_ ;; _k_ 1 _k_ 2 _...k_ _p−q_ _m_ 1 _m_ 2 _...m_ _q_



_p_
P _**G**_
!



"



(3.30)


For the case _p < q_, the contraction can be defined similarly.


By construction, one can see the the IsoAM is permutation equivariant as:


_π_ : _**G**_ _8→_ _**P GP**_ _[⊤]_ _,_ (3.31)


where _**P**_ is the corresponding permutation matrix, as discussed in Maron et al. (2018).


This property is the same as that of ordinary adjacency matrices. The contraction and


tensor product of IsoAMs are also permutation equivariant because:


_π_ : _**G**_ _⊙_ _**G**_ _8→_ _**P GP**_ _[⊤]_ _⊙_ _**P GP**_ _[⊤]_ (3.32)


= _**P G**_ _⊙_ _**GP**_ _[⊤]_ (3.33)


_π_ : _**G**_ _⊗_ _**G**_ _8→_ _**P GP**_ _[⊤]_ _⊗_ _**P GP**_ _[⊤]_ (3.34)


= _**P G**_ _⊗_ _**GP**_ _[⊤]_ _._ (3.35)


This discussion is also easily generalized for the higher order tensor cases.


Finally, we can conclude that convolution, contraction, and tensor product between


rank-p IsoAM and discrete tensor field are permutation and E( _n_ )-equivariant because each


component has such equivariance. Therefore, these operations are essential to construct


E( _n_ )-equivariant GCN layers, IsoGCNs.


3.3.3 C ONSTRUCTION OF I SO GCN


Using the operations defined above, we can construct IsoGCN layers, which take the


discrete tensor field of any rank as input, and output the tensor field of any rank, which can


differ from those of the input.




# Page 75

3.3. Method **51**


3.3.3.1 E( _n_ )-I NVARIANT L AYER


As can be seen in Proposition 3.3.1, the contraction of IsoAMs is E( _n_ )-invariant. There

fore, an E( _n_ )-invariant layer with a rank-0 input discrete tensor field and rank-0 output dis
crete tensor field, IsoGCN 0 _→_ 0 : R _[|V|×][d]_ [in] _∋_ _**H**_ in [(0)] _[8→]_ _**[H]**_ out [(0)] _[∈]_ [R] _[|V|×][d]_ [out] [, can be constructed]


as


_**H**_ out [(0)] [= IsoGCN] [0] _[→]_ [0] [(] _**[H]**_ in [(0)] [) = PointwiseMLP] ( _**G**_ _⊙_ _**G**_ ) _**H**_ in [(0)] _,_ (3.36)
 


where PointwiseMLP : R _[|V|×][d]_ [in] _→_ R _[|V|×][d]_ [out] is the pointwise MLP defined in Equa

tion 2.26. By defining _**L**_ := _**G**_ _⊙_ _**G**_ _∈_ R _[|V|×|V|]_, it can be simplified as


_**H**_ out [(0)] [= PointwiseMLP] _**LH**_ in [(0)] _,_ (3.37)
 


which has the same form as a GCN (equation 2.35), with the exception that _**A**_ [ˆ] is replaced


with _**L**_ . It is noteworthy that _**L**_ incorporates geometry information, which was missing


in the GCN formulation, even though the equations are similar. Therefore, we see that


IsoGCN successfully leverages geometry information in addition to graph topology.


An E( _n_ )-invariant layer with the rank- _p_ input tensor field and rank-0 output tensor field,

IsoGCN _p→_ 0 : R _[|V|×][d]_ [in] _[×][n]_ _[p]_ _∋_ _**H**_ in [(] _[p]_ [)] _[8→]_ _**[H]**_ out [(0)] _[∈]_ [R] _[|V|×][d]_ [out] [, can be formulated as]



_**H**_ out [(0)] [= IsoGCN] _[p][→]_ [0] [(] _**[H]**_ in [(] _[p]_ [)] [) = PointwiseMLP]



_p_
P _**G**_
!# $



_⊙_ _**H**_ in [(] _[p]_ [)]



"



_._ (3.38)



If _p_ = 1, such approaches utilize the inner products of the vectors in R _[d]_, these operations


correspond to the extractions of a relative distance and an angle of each pair of vertices,


which are employed in Klicpera et al. (2020).


3.3.3.2 E( _n_ )-E QUIVARIANT L AYER


To construct an E( _n_ )-equivariant layer, one can use linear transformation, convolution


and tensor product to the input tensors. If both the input and the output tensor ranks are


greater than 0, one can apply neither nonlinear activation nor bias addition because these


operations will cause an inappropriate distortion of the isometry because E( _n_ ) transforma



# Page 76

**52** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


tion does not commute with them in general. However, a conversion that uses only a linear


transformation, convolution, and tensor product does not have nonlinearity, which limits


the predictive performance of the model. To add nonlinearity to such a conversion, we can


first convert the input tensors to rank-0 ones, apply nonlinear activations, and then multiply


them to the higher rank tensors, as done in TFN model (Equation 2.50).


To achieve nonlinearity, first we define the E( _n_ ) _-equivariant pointwise MLP_ layer,


EquivariantPointwiseMLP : R _[|V|×][d]_ [in] _[×][n]_ _[p]_ _→_ R _[|V|×][d]_ [out] _[×][n]_ _[p]_, as follows:


2 []
( _p_ )
EquivariantPointwiseMLP( _**H**_ in [(] _[p]_ [)] [) := PointwiseMLP] _**H**_ in _∗⃝_ feat _**H**_ in [(] _[p]_ [)] _[∗⃝]_ feat _**[W]**_ _[,]_




(3.39)


where _∗⃝_ feat is the multiplication in the feature direction and _**W**_ _∈_ R _[d]_ [in] _[×][d]_ [out] is a trainable


weight matrix. The pointwise MLP, PointwiseMLP : R _[|V|×][d]_ [in] _[×][n]_ _[p]_ _→_ R _[|V|×][d]_ [out] _[×][n]_ _[p]_, is cho

sen to have the consistent output dimension. Using the index notation, Equation 3.39 turns


into:



_**H**_ [(] _[p]_ [)]
EquivariantPointwiseMLP( in [)]
i j



_i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_



_i_ ; _h_ ; _k_ 1 _k_ 2 _...k_ _p_ _[W]_ _[hg]_ _[.]_


(3.40)



=
Y


_h_



2 []
( _p_ )
PointwiseMLP _**H**_
in

  _i_ ; _h_ ;



_**H**_ [(] _[p]_ [)]
in
i j



One can easily see that EquivariantPointwiseMLP defined in Equation 3.39 is translation


invariant and orthogonal transformation equivariant because



2
( _p_ )
_**H**_
in
  _i_



_i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_



(3.41)
_i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_



_i_ ; _g_ ; [=] Y



_**H**_ [(] _[p]_ [)]
in
i j



_**H**_ [(] _[p]_ [)]
in
i j



_k_ 1 _k_ 2 _...k_ _p_



is E( _n_ )-invariant. We use _∥·∥_ [2] instead of _∥·∥_ in the function because computation of _∥·∥_


requires computation of the square root, which leads extreme gradient around zero. One


can regard EquivariantPointwiseMLP as an equivariant function that does not change the


input tensor rank and may change the number of features.




# Page 77

3.3. Method **53**


The nonlinear E( _n_ )-equivariant layer with the rank- _p_ input discrete tensor field and the

rank- _q_ ( _p ≤_ _q_ ) output discrete tensor field, IsoGCN _p→q_ : R _[|V|×][d]_ [in] _[×][n]_ _[p]_ _∋_ _**H**_ in [(] _[p]_ [)] _[8→]_ _**[H]**_ out [(] _[q]_ [)] _[∈]_


R _[|V|×][d]_ [out] _[×][n]_ _[q]_, can be defined as:



_**H**_ out [(] _[q]_ [)] [= IsoGCN] _[p][→][q]_ [(] _**[H]**_ in [(] _[p]_ [)] [) := EquivariantPointwiseMLP]



_q−p_
P _**G**_
!# $



_⊗_ _**H**_ in [(] _[p]_ [)]



"



_._



(3.42)


If _p_ = 0, we regard _**G**_ _⊗_ _**H**_ [(0)] as _**G**_ _∗_ _**H**_ [(0)] . If _p_ = _q_, one can add the residual


connection (He et al., 2016) in Equation 3.42. If _p > q_,



_**H**_ out [(] _[q]_ [)] [= IsoGCN] _[p][→][q]_ [(] _**[H]**_ in [(] _[p]_ [)] [) := EquivariantPointwiseMLP]



_p−q_
P _**G**_
!# $



_⊙_ _**H**_ in [(] _[p]_ [)]



"



_._



(3.43)


In general, the nonlinear E( _n_ )-equivariant IsoGCN layer with the rank- _P_ min to rank
_P_ max
_P_ max input tensor field _**H**_ in [(] _[p]_ [)] out [can be defined]
o p _p_ = _P_ min [and the rank-] _[q]_ [ output tensor field] _**[ H]**_ [(] _[q]_ [)]


as:



(3.44)




_**H**_ out [(] _[q]_ [)] [=IsoGCN] _[·→][q]_



_P_ max
_**H**_ [(] _[p]_ [)]
in
o p _p_ = _P_ min



_,_




_**H**_ [(] _[q]_ [)]
:=EquivariantPointwiseMLP( in [) +] _**[ F]**_ [gather]



_P_ max
IsoGCN _p→q_ ( _**H**_ in [(] _[p]_ [)] [)]
o p _p_ = _P_ min



(3.45)


where _**F**_ gather denotes a function such as summation, product and concatenation in the


feature direction. One can see that this layer is similar to that in the TFN (Equation 2.50),


while there are no spherical harmonics and trainable message passing in the IsoGCN model.


To be exact, the output of the layer defined above is translation invariant. To out

put translation equivariant variables such as the vertex positions after deformation (which


change accordingly with the translation of the input graph), one can first define the ref

erence vertex position _**x**_ ref for each graph, then compute the translation invariant output


using equation 3.45, and finally, add _**x**_ ref to the output. For more detailed information on


IsoGCN modeling, see Section 3.3.5.




# Page 78

**54** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


3.3.4 I SO AM R EFINED FOR N UMERICAL A NALYSIS


The IsoAM _**G**_ is defined in a general form for the propositions to work with various


classes of graph. In this section, we concretize the concept of the IsoAM to apply an


IsoGCN to mesh-structured numerical analysis data. Here, a mesh is regarded as a graph


regarding the points in the mesh as vertices of the graph and assuming two vertices are


connected when they share the same element (cell), as seen in Figure 2.9.


3.3.4.1 D EFINITION OF D IFFERENTIAL I SO AM


As seesn in Section 2.2.4, the graph connectivities are closely related to spatial dif

ferentiation. Therefore, it is natural to construct a graph reflecting the structure of spatial


differentiation. Here, we define the _differential IsoAM_, a concrete instance of IsoAMs re

fined for numerical analysis.


The differential IsoAM _**G**_ [˜] _,_ _**G**_ [ˆ] _∈_ R _[|V|×|V|×][d]_ is defined as follows:


_G_ ˜ _ij_ ;; _k_ = ˆ _G_ _ij_ ;; _k_ _−_ _δ_ _ij_ Y _G_ ˆ _il_ ;; _k_ (3.46)


_l_


ˆ _**x**_ _j_ _−_ _**x**_ _i_
_G_ _ij_ ;;: = _**M**_ _i_ _[−]_ [1] (3.47)
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ [2] _[w]_ _[ij]_ _[A]_ _[ij]_ [(] _[m]_ [)]



_**M**_ _i_ =
Y


_l_



_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
(3.48)
_∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[w]_ _[il]_ _[A]_ _[il]_ [(] _[m]_ [)] _[,]_



where R _[|V|×|V|]_ _∋_ _**A**_ ( _m_ ) := min ( [Q] _[m]_ _k_ =1 _**[A]**_ _[k]_ _[,]_ [ 1)][ is an adjacency matrix up to] _[ m]_ [ hops and]


_w_ _ij_ _∈_ R is an untrainable weight between the _i_ th and _j_ th vertices that is determined depend

ing on the tasks [2] . Although one could define _w_ _ij_ as a function of the distance _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_,


_w_ _ij_ was kept constant with respect to the distance required to maintain the simplicity of the


model with fewer hyperparameters.


By regarding


_**T**_ _ijkl_ = _δ_ _il_ _δ_ _jk_ _**M**_ _i_ _[−]_ [1] _w_ _ij_ _**A**_ _ij_ ( _m_ ) _/∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ [2] (3.49)


2 _**M**_ _i_ is invertible when the number of independent vectors in _{_ _**x**_ _l_ _−_ _**x**_ _i_ _}_ _l_ is greater than or equal to the
space dimension _n_, which is true for common meshes, e.g., a solid mesh in 3D Euclidean space.




# Page 79

3.3. Method **55**


in equation 3.8, one can see that _**G**_ [ˆ] is qualified as an IsoAM. Because a linear combination

of IsoAMs is also an IsoAM, _**G**_ [˜] is an IsoAM. Thus, they provide translation invariance and

orthogonal transformation equivariance. _**G**_ [˜] can be obtained only from the mesh geometry


information, thus can be computed in the preprocessing step.


Here, _**G**_ [˜] is designed such that it corresponds to the gradient operator model used in the


LSMPS method(Tamai & Koshizuka, 2014) (Equation 2.113, while we added _A_ _ij_ ( _m_ ) fac
tor to work on graphs. As presented in Table 3.1, _**G**_ [˜] is closely related to many differential


operators, such as the gradient, divergence, Laplacian, Jacobian, and Hessian. Therefore,


the considered IsoAM plays an essential role in constructing neural network models that


are capable of learning differential equations. In the following sections, we discuss the con
nection between the IsoAM for numerical analysis _**G**_ [˜] and the differential operators such as


the gradient, divergence, the Laplacian, the Jacobian, and the Hessian operators.


Table 3.1: Correspondence between the differential operators and the expressions using the


IsoAM _**G**_ [˜] .


**Differential operator** **Expression**


˜
Gradient _**G**_ _∗_ _**H**_ [(0)]


Divergence _**G**_ ˜ _⊙_ _**H**_ [(1)]


Laplacian _**G**_ ˜ _⊙_ _**GH**_ ˜ [(0)]


Jacobian _**G**_ ˜ _⊗_ _**H**_ [(1)]


˜ ˜
Hessian _**G**_ _⊗_ _**G**_ _∗_ _**H**_ [(0)]


3.3.4.2 P ARTIAL D ERIVATIVE


First let us consider a partial derivative model of a rank-0 discrete tensor field _**H**_ [(0)] at



the _i_ th vertex and _g_ th feature regarding the _k_ th axis _∂_ _**H**_ [(0)] _/∂x_ _k_



_i_ ; _g_ ; _[∈]_ [R][ (] _[k][ ∈{]_ [1] _[, . . ., n][}]_ [)][.]



Recalling the gradient model of the LSMPS method (Equation 2.113),



_∂_ _**H**_ (0)
 _∂x_ _k_







:= _**M**_ _[−]_ [1]
_i_ Y
_i_ ; _g_ ;



_j_



_H_ _j_ [(0)] ; _g_ ; _[−]_ _[H]_ _i_ [(0)] ; _g_ ; _x_ _jk_ _−_ _x_ _ik_
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[w]_ _[ij]_ _[A]_ _[ij]_ [(] _[m]_ [)]



ˆ

= Y _G_ _ijk_ ( _H_ _j_ [(0)] ; _g_ ; _[−]_ _[H]_ _i_ [(0)] ; _g_ ; [)] _[.]_ (3.50)

_j_




# Page 80

**56** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


3.3.4.3 G RADIENT


_**G**_ ˜ is similar to a graph Laplacian matrix based on ˆ _**G**_ ; however, surprizingly, ˜ _**G**_ _∗_ _**H**_ [(0)]


can be interpreted as the gradient within the Euclidean space. Let _∇_ _**H**_ [(0)] _∈_ R _[|V|×][f]_ _[×][d]_ be


an approximation of the gradient of _**H**_ [(0)] . Using Equation 3.50, the gradient model can be


expressed as follows:



_∇_ _**H**_ [(0)]



_i_ ; _g_ ; _k_ [=] _[ ∂H]_ _∂x_ _i_ [(0)] _k_ ; _g_ ; (3.51)

= _G_ [ˆ] _ijk_ ( _H_ _j_ [(0)] ; _g_ ; _[−]_ _[H]_ _i_ [(0)] ; _g_ ; [)] _[.]_ (3.52)



Using this gradient model, we can confirm that ( _**G**_ [˜] _∗_ _**H**_ [(0)] ) _i_ ; _g_ ; _k_ = ( _∇_ _**H**_ [(0)] ) _i_ ; _glk_ because



˜
_**G**_ _∗_ _**H**_ [(0)] [F]
E



_i_ ; _g_ ; _k_ [=] Y _G_ ˜ _ij_ ;; _k_ _H_ _j_ [(0)] ; _g_ ; (3.53)

_j_



=
Y



( _G_ [ˆ] _ij_ ;; _k_ _−_ _δ_ _ij_ Y
_j_ _l_



ˆ
_G_ _il_ ;; _k_ ) _H_ _j_ [(0)] ; _g_ ;

_l_



ˆ
_G_ _ij_ ;; _k_ _H_ _j_ [(0)] ; _g_ ; _[−]_ Y
_j_ _j,l_


ˆ
_G_ _ij_ ;; _k_ _H_ _j_ [(0)] ; _g_ ; _[−]_ Y
_j_ _l_


ˆ
_G_ _ij_ ;; _k_ _H_ _j_ [(0)] ; _g_ ; _[−]_ Y
_j_ _j_



=
Y



_δ_ _ij_ _G_ [ˆ] _il_ ;; _k_ _H_ _j_ [(0)] ; _g_ ;

_j,l_



=
Y



ˆ
_G_ _il_ ;; _k_ _H_ _i_ [(0)] ; _g_ ;

_l_



=
Y



ˆ
_G_ _ij_ ;; _k_ _H_ _i_ [(0)] ; _g_ ; (∵ Change the dummy index _l →_ _j_ )

_j_



ˆ

= Y _G_ _ij_ ;; _k_ ( _H_ _j_ [(0)] ; _g_ ; _[−]_ _[H]_ _i_ [(0)] ; _g_ ; [)]

_j_



= _∇_ _**H**_ [(0)]



_i_ ; _g_ ; _k_ _[.]_ (3.54)



Therefore, _**G**_ [˜] _∗_ can be interpreted as the gradient operator within a Euclidean space.


3.3.4.4 D IVERGENCE


We show that _**G**_ [˜] _⊙_ _**H**_ [(1)] corresponds to the divergence. Using Equation 3.50, the


divergence model _∇·_ _**H**_ [(1)] _∈_ R _[|V|×][f]_ is expressed as follows:



(3.55)

, _i_ ; _g_ ;



_∇·_ _**H**_ [(1)]



_i_ ; _g_ ; [=]



+Y _k_



_∂_ _**H**_ [(1)]


_∂x_ _k_




# Page 81

3.3. Method **57**


ˆ

= Y _G_ _ij_ ;; _k_ ( _H_ _j_ [(1)] ; _g_ ; _k_ _[−]_ _[H]_ _i_ [(1)] ; _g_ ; _k_ [)] _[.]_ (3.56)

_j,k_



Then, _**G**_ [˜] _⊙_ _**H**_ [(1)] is



_**G**_ ˜ _⊙_ _**H**_ [(1)] [F]
E



_i_ ; _g_ ; [=] Y _G_ ˜ _ij_ ;; _k_ _H_ _j_ [(1)] ; _g_ ; _k_

_j,k_



"



=
Y

_j,k_


=
Y



_G_ ˆ _ij_ ;; _k_ _−_ _δ_ _ij_ Y _G_ ˆ _il_ ;; _k_
! _l_



ˆ

Y _G_ _il_ ;; _k_ _H_ _i_ [(1)] ; _g_ ; _k_

_l,k_



_H_ [(1)]
_j_ ; _g_ ; _k_



ˆ

Y _G_ _ij_ ;; _k_ _H_ _j_ [(1)] ; _g_ ; _k_ _[−]_ Y

_j,k_ _l,k_



ˆ

= Y _G_ _ij_ ;; _k_ ( _H_ _j_ [(1)] ; _g_ ; _k_ _[−]_ _[H]_ _i_ [(1)] ; _g_ ; _k_ [)] (∵ Change the dummy index _l →_ _j_ )

_j,k_



= _∇·_ _**H**_ [(1)]



_i_ ; _g_ ; _[.]_ (3.57)



3.3.4.5 L APLACIAN O PERATOR


We prove that _**G**_ [˜] _⊙_ _**G**_ [˜] corresponds to the Laplacian operator within a Euclidean space.


Using Equation 3.50, the Laplacian model _∇· ∇_ _**H**_ [(0)] _∈_ R _[|V|×][f]_ can be expressed as


follows:



 _i_



 _i_ ; _g_ ;



_∂_ _∂_ _**H**_
 _∂x_ _k_ _∂x_ _k_



_∇· ∇_ _**H**_ [(0)]



_i_ ; _g_ ; [:=] Y

_k_



_∂_ _**H**_
_j_ ; _g_ ; _−_ _∂x_ _k_



 _i_ ; _g_ ;



,



ˆ

= Y _G_ _ij_ ;; _k_

_j,k_


ˆ

= Y _G_ _ij_ ;; _k_

_j,k_



_∂_ _**H**_


_∂x_ _k_

,







#Y _l_



ˆ
_G_ _jl_ ;; _k_ ( _H_ _l_ [(0)] ; _g_ ; _[−]_ _[H]_ _j_ [(0)] ; _g_ ; [)] _[ −]_ Y

_l_ _l_



ˆ
_G_ _il_ ;; _k_ ( _H_ _l_ [(0)] ; _g_ ; _[−]_ _[H]_ _i_ [(0)] ; _g_ ; [)]

_l_



$



ˆ ˆ

= Y _G_ _ij_ ;; _k_ ( ˆ _G_ _jl_ ;; _k_ _−_ _G_ _il_ ;; _k_ )( _H_ _l_ [(0)] ; _g_ ; _[−]_ _[H]_ _j_ [(0)] ; _g_ ; [)] _[.]_ (3.58)

_j,k,l_



Then, ( _**G**_ [˜] _⊙_ _**G**_ [˜] ) _**H**_ [(0)] is


(( _**G**_ [˜] _⊙_ _**G**_ [˜] ) _**H**_ [(0)] ) _i_ ; _g_ ; = Y _G_ ˜ _ij_ ;; _k_ ˜ _G_ _jl_ ;; _k_ _H_ _l_ [(0)] ; _g_ ;

_j,k,l_




# Page 82

**58** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network



_G_ ˆ _jl_ ;; _k_ _−_ _δ_ _jl_ Y _G_ ˆ _jn_ ;; _k_
" ! _n_



"



=
Y

_j,k,l_


=
Y



_G_ ˆ _ij_ ;; _k_ _−_ _δ_ _ij_ Y _G_ ˆ _im_ ;; _k_
! _m_



ˆ

Y _G_ _ij_ ;; _k_ ˆ _G_ _jn_ ;; _k_ _H_ _j_ [(0)] ; _g_ ;

_j,k,n_



_H_ [(0)]
_l_ ; _g_ ;



ˆ

Y _G_ _ij_ ;; _k_ ˆ _G_ _jl_ ;; _k_ _H_ _l_ [(0)] ; _g_ ; _[−]_ Y

_j,k,l_ _j,k,n_



ˆ

Y _G_ _im_ ;; _k_ ˆ _G_ _il_ ;; _k_ _H_ _l_ [(0)] ; _g_ ; [+] Y

_k,l,m_ _k,m,n_



_−_
Y



ˆ

Y _G_ _im_ ;; _k_ ˆ _G_ _in_ ;; _k_ _H_ _i_ [(0)] ; _g_ ;

_k,m,n_



ˆ

Y _G_ _ij_ ;; _k_ ˆ _G_ _jl_ ;; _k_ _H_ _l_ [(0)] ; _g_ ; _[−]_ Y

_j,k,l_ _j,k,n_



=
Y



ˆ

Y _G_ _ij_ ;; _k_ ˆ _G_ _jn_ ;; _k_ _H_ _j_ [(0)] ; _g_ ;

_j,k,n_



ˆ

Y _G_ _ij_ ;; _k_ ˆ _G_ _il_ ;; _k_ _H_ _l_ [(0)] ; _g_ ; [+] Y

_k,l,j_ _k,j,n_



_−_
Y



ˆ

Y _G_ _ij_ ;; _k_ ˆ _G_ _in_ ;; _k_ _H_ _i_ [(0)] ; _g_ ;

_k,j,n_



(∵ Change the dummy index _m →_ _j_ for the third and fourth terms)


ˆ ˆ

= Y _G_ _ij_ ;; _k_ ( ˆ _G_ _jl_ ;; _k_ _−_ _G_ _il_ ;; _k_ )( _H_ _l_ [(0)] ; _g_ ; _[−]_ _[H]_ _j_ [(0)] ; _g_ ; [)]

_j,k,l_


(∵ Change the dummy index _n →_ _l_ for the second and fourth terms)



= _∇_ [2] _**H**_ [(0)]



_i_ ; _g_ ; _[.]_ (3.59)



3.3.4.6 J ACOBIAN AND H ESSIAN O PERATORS


Considering a similar discussion, we can show the following dependencies. For the


Jacobian model, _∇⊗_ _**H**_ [(1)] _∈_ R _[|V|×][f]_ _[×][d][×][d]_,



(3.60)

_i_ ; _g_ ; _k_



_∇⊗_ _**H**_ [(1)]



_∂_ _**H**_ (1)
_i_ ; _g_ ; _kl_ [=] _∂x_ _l_







ˆ

= Y _G_ _ij_ ;; _l_ ( _H_ _j_ [(1)] ; _g_ ; _k_ _[−]_ _[H]_ _i_ [(1)] ; _g_ ; _k_ [)] (3.61)

_j_



= ( _**G**_ [˜] _⊗_ _**H**_ [(1)] ) _i_ ; _g_ ; _lk_ _._ (3.62)


For the Hessian model, _∇⊗∇_ _**H**_ [(0)] _∈_ R _[|V|×][f]_ _[×][d][×][d]_,



_∂_
_**H**_ [(0)]
_∂x_ _l_ 



(3.63)

_i_ ; _g_ ;



_∇⊗∇_ _**H**_ [(0)]



_∂_
_i_ ; _g_ ; _kl_ [=] _∂x_ _k_




# Page 83

3.3. Method **59**


ˆ

= Y _G_ _ij_ ;; _k_ [ ˆ _G_ _jm_ ;; _l_ ( _H_ _m_ [(0)] ; _g_ ; _[−]_ _[H]_ _l_ [(0)] ; _g_ ; [)] _[ −]_ _[G]_ [ˆ] _[im]_ [;;] _[l]_ [(] _[H]_ _m_ [(0)] ; _g_ ; _[−]_ _[H]_ _i_ [(0)] ; _g_ ; [)]] (3.64)

_j,m_



= ( _**G**_ [˜] _⊗_ _**G**_ [˜] ) _∗_ _**H**_ [(0)] [j]
i


3.3.5 I SO GCN M ODELING D ETAILS



(3.65)
_i_ ; _g_ ; _kl_ _[.]_



To achieve E( _n_ )- invariance and equivariance, there are several rules to follow. Here,


we describe the desired focus when constructing an IsoGCN model. In this section, a rank

_p_ tensor denotes a tensor the rank of which is _p ≥_ 1 and _σ_ denotes a nonlinear activation


function. _**W**_ is a trainable weight matrix and _**b**_ is a trainable bias.


3.3.5.1 A CTIVATION AND B IAS


As the nonlinear activation function is not E( _n_ )-equivariant, nonlinear activation to


rank- _p_ tensors cannot be applied, while one can apply any activation to rank-0 tensors. In


addition, adding bias is also not E( _n_ )-equivariant, so one cannot add bias when performing


an affine transformation to rank- _p_ tensors. Again, one can add bias to rank-0 tensors.


Thus, for instance, if one converts from rank-0 tensors _**H**_ [(0)] to rank-1 tensors using


IsoAM _**G**_, _**G**_ _∗_ _σ_ ( _**H**_ [(0)] _**W**_ + _**b**_ ) and ( _**G**_ _∗_ _σ_ ( _**H**_ [(0)] )) _**W**_ are E( _n_ )-equivariant functions,

however ( _**G**_ _∗_ _**H**_ [(0)] ) _**W**_ + _**b**_ and _σ_  ( _**G**_ _∗_ _σ_ ( _**H**_ [(0)] )) _**W**_  are not due to the bias and the


nonlinear activation, respectively. Likewise, regarding a conversion from rank-1 tensors


_**H**_ [(1)] to rank-0 tensors, _σ_  ( _**G**_ _⊙_ _**H**_ [(1)] ) _**W**_ + _**b**_  and _σ_  _**G**_ _⊙_ ( _**H**_ [(1)] _**W**_ )  are E( _n_ )-invariant

functions; however, _**G**_ _⊙_ ( _**H**_ [(1)] _**W**_ + _**b**_ ) and ( _**G**_ _⊙_ _σ_ ( _**H**_ [(1)] )) _**W**_ + _**b**_ are not.


To convert rank- _p_ tensors to rank- _q_ tensors ( _q ≥_ 1), one can apply neither bias nor non

linear activation. To add nonlinearity to such a conversion, we can multiply the converted


rank-0 tensors _σ_ (( [O] _[p]_ _**G**_ _⊙_ _**H**_ [(] _[p]_ [)] ) _**W**_ + _**b**_ ) with the input tensors _**H**_ [(] _[p]_ [)] or the output tensors


_**H**_ [(] _[q]_ [)] .


3.3.5.2 P REPROCESSING OF I NPUT F EATURE


Similarly to the discussion regarding the biases, we have to take care of the prepro

cessing of rank- _p_ tensors to retain E( _n_ )-invariance because adding a constant array and


component-wise scaling could distort the tensors, resulting in broken E( _n_ )-equivariance.




# Page 84

**60** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


For instance, _**H**_ [(] _[p]_ [)] _/_ Std all  _**H**_ [(] _[p]_ [)] [] is a valid transformation to retain E( _n_ )-equivariance,

assuming Std all  _**H**_ [(] _[p]_ [)] [] _∈_ R is a standard deviation of all components of _**H**_ [(] _[p]_ [)] . However,

conversions such as _**H**_ [(] _[p]_ [)] _/_ Std component  _**H**_ [(] _[p]_ [)] [] and _**H**_ [(] _[p]_ [)] _−_ Mean  _**H**_ [(] _[p]_ [)] [] are not E( _n_ )
equivariant, assuming that Std component  _**H**_ [(] _[p]_ [)] [] _∈_ R _[d]_ _[p]_ is a component-wise standard de

viation.


3.3.5.3 S CALING


Because the differential IsoAM _**G**_ [˜] corresponds to the differential operator, the scale of

the output after operations regarding _D_ [˜] can be huge. Thus, we rescale _**G**_ [˜] using the scaling

1 _/_ 2
factor Mean sample _,i_ ( _G_ [˜] [2] _ii_ ;;1 [+ ˜] _[G]_ [2] _ii_ ;;2 [+ ˜] _[G]_ [2] _ii_ ;;3 [)], where Mean sample _,i_ denotes the mean over
i j

the samples and vertices.


3.3.5.4 T ENSOR R ANK


Although we defined IsoGCN _p→q_ in Equations 3.42 and 3.43, there are other ways to


model function converting from rank- _p_ discrete tensor field to rank- _q_ discrete tensor field.


For instance, in the case of _p_ = 2 and _q_ = 3, one may also define as:


_**H**_ out [(3)] [= EquivariantPointwiseMLP] _**G**_ _⊗_ _**G**_ _⊙_ _**G**_ _⊗_ _**H**_ in [(2)] _,_ (3.66)
 


or


_**H**_ out [(3)] [= IsoGCN] [4] _[→]_ [3] _[◦]_ [IsoGCN] [3] _[→]_ [4] _[◦]_ [IsoGCN] [2] _[→]_ [3] [(] _**[H]**_ in [(2)] [)] _[.]_ (3.67)


One guideline is to consider PDEs of interest when using the differential IsoAM, as done in


the numerical experiments (Section 3.4). In the other case, generally, tensor rank should not


be dropped unless necessary. Namely, transformation of the tensor rank 2 _→_ 3 _→_ 4 _→_ 3


is more preferable compared to that of 2 _→_ 1 _→_ 0 _→_ 1 _→_ 2 _→_ 3 to constract the IsoGCN


model which converts a rank-2 discrete tensor field to a rank-3 discrete tensor field.


3.3.5.5 I MPLEMENTATION


Because an adjacency matrix _**A**_ is usually a sparse matrix for a regular mesh, _**A**_ ( _m_ )


in equation 3.47 is also a sparse matrix for a sufficiently small _m_ . Thus, we can leverage




# Page 85

3.4. Numerical Experiments **61**


sparse matrix multiplication in the IsoGCN computation. This is one major reason why


IsoGCNs can compute rapidly. If the multiplication (tensor product or contraction) of


IsoAMs must be computed multiple times the associative property of the IsoAM can be


utilized.


For instance, it is apparent that



_k_
P _**G**_
# $



_∗_ _**H**_ [(0)] = _**G**_ _⊗_ ( _**G**_ _⊗_ _. . ._ ( _**G**_ _∗_ _**H**_ [(0)] )) _._ (3.68)



Assuming that the number of nonzero elements in _**A**_ ( _m_ ) equals _n_ and _**H**_ [(0)] _∈_ R _[|V|×][f]_, then


the computational complexity of the right-hand side is _O_ ( _n|V|fn_ _[k]_ ). This is an exponential


order regarding the spatial dimension _n_ . However, _n_ and _k_ are usually small numbers (typi

cally _n_ = 3 and _k ≤_ 4). Therefore one can compute an IsoGCN layer with a realistic spatial


dimension _n_ and tensor rank _k_ fast and memory efficiently. In our implementation, both a


sparse matrix operation and associative property are utilized to realize fast computation.


3.4 N UMERICAL E XPERIMENTS


To test the applicability of the proposed model, we composed the following two


datasets:


1. a differential operator dataset of grid meshes; and


2. an anisotropic nonlinear heat equation dataset of meshes generated from CAD data.


In this section, we discuss our machine learning model, the definition of the problem, and


the results for each dataset.


Using _**G**_ [˜] defined in Section 3.3.4, we constructed a neural network model considering


an encode-process-decode configuration (Battaglia et al., 2018). The encoder and decoder


were comprised of component-wise MLPs and tensor operations. For each task, we tested


_m_ = 2 _,_ 5 in Equation 3.47 to investigate the effect of the number of hops considered.




# Page 86

**62** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


In addition to the GCN (Kipf & Welling, 2017), we chose GIN (Xu et al., 2018),


SGCN (Wu et al., 2019), Cluster-GCN (Chiang et al., 2019), and GCNII (Chen et al.,


2020) as GCN variant baseline models.


For the equivariant models, we chose the TFN (Thomas et al., 2018) and SE(3)

Transformer (Fuchs et al., 2020) as the baseline. We implemented these models using


PyTorch 1.6.0 (Paszke et al., 2019) and PyTorch Geometric 1.6.1 (Fey & Lenssen, 2019).


For both the TFN and SE(3)-Transformer, we used implementation of Fuchs et al. (2020) [3]


because the computation of the TFN is considerably faster than the original implemen

tation, as claimed in Fuchs et al. (2020). For each experiment, we minimized the mean


squared loss using the Adam optimizer (Kingma & Ba, 2014). The corresponding imple

mentation and the dataset will be made available online.


3.4.1 D IFFERENTIAL O PERATOR D ATASET


3.4.1.1 T ASK D EFINITION


To demonstrate the expressive power of IsoGCNs, we created a dataset to learn the


differential operators. We first generated a pseudo-2D grid mesh randomly with only one


cell in the _Z_ direction and 10 to 100 cells in the _X_ and _Y_ directions. We then generated


scalar fields on the grid meshes and analytically calculated the gradient, Laplacian, and


Hessian fields. We generated 100 samples for each train, validation, and test dataset.


For simplicity, we set _w_ _ij_ = 1 in Equation 3.47 for all ( _i, j_ ) _∈E_ . To compare the


performance with the GCN models, we simply replaced an IsoGCN layer with a GCN or


its variant layers while keeping the number of hops _m_ the same to enable a fair comparison.


We adjusted the hyperparameters for the equivariant models to ensure that the number of


parameters in each was almost the same as that in the IsoGCN model.


We conducted the experiments using the following settings:


1. inputting the scalar field _φ_ and predicting the gradient field _∇φ_ (rank-0 _→_ rank-1


tensor);


3 [https://github.com/FabianFuchsML/se3-transformer-public](https://github.com/FabianFuchsML/se3-transformer-public)




# Page 87

3.4. Numerical Experiments **63**


2. inputting the scalar field _φ_ and predicting the Hessian field _∇⊗∇φ_ (rank-0 _→_


rank-2 tensor);


3. inputting the gradient field _∇φ_ and predicting the Laplacian field _∇· ∇φ_ (rank-1


_→_ rank-0 tensor); and


4. inputting the gradient field _∇φ_ and predicting the Hessian field _∇⊗∇φ_ (rank-1 _→_


rank-2 tensor).


3.4.1.2 M ODEL A RCHITECTURES



( _a_ )


( _b_ )


( _c_ )


( _d_ )

















































ブロック図の主要コンポーネントは「∇φ」「IsoGCN」「MLP」「∇²φ」です。信号の入出力関係は、∇φからLinear([1, 64], [Identity])を出力し、その出力からMLP([64,64],[tanh,tanh,Identity])に送り、MLPの出力はIsoGCn([6,6],[Identity])に入力され、再びMLPを経過した信号から∇₂φに送られ、最終的に∇φに戻る仕組みです。

























フローチャートの開始は「∇φ」から始まり、主な分岐は「MLP」と「IsoGCN G⊙−」で、処理の流れは「Linear [1,64] [Identity] → IsoGCN/G⊙− → MLP/tanh/tanh/Identity → Linear [64,1] → ∇φ ∘ ∘」と進みます。

























Encoder



Process



Decoder



Figure 3.2: The IsoGCN models used for (a) the scalar field to the gradient field, (b) the


scalar field to the Hessian field, (c) the gradient field to the Laplacian field, (d) the gradient


field to the Hessian field of the gradient operator dataset. Gray boxes are trainable com

ponents. In each trainable cell, we put the number of units in each layer along with the


activation functions used. _∗⃝_ denotes the multiplication in the feature direction.




# Page 88

**64** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


Figure 3.2 represents the IsoGCN model used for the differential operator dataset. We


used the tanh activation function as a nonlinear activation function because we expect


the target temperature field to be smooth. Therefore, we avoid using non-differentiable


activation functions such as the rectified linear unit (ReLU) (Nair & Hinton, 2010). For


GCN and its variants, we simply replaced the IsoGCN layers with the corresponding ones.


We stacked _m_ (= 2 _,_ 5) layers for GCN, GIN, GCNII, and Cluster-GCN. We used an _m_


hop adjacency matrix for SGCN.


For the TFN and SE(3)-Transformer, we set the hyperparameters to have almost the


same number of parameters as in the IsoGCN model. The settings of the hyperparameters


are shown in Table 3.2.


Table 3.2: Summary of the hyperparameter setting for both the TFN and


SE(3)-Transformer. For the parameters not in the table, we used the de

[fault setting in the implementation of https://github.com/FabianFuchsML/](https://github.com/FabianFuchsML/se3-transformer-public)


[se3-transformer-public.](https://github.com/FabianFuchsML/se3-transformer-public)


**0** _**→**_ **1** **0** _**→**_ **2** **1** _**→**_ **0** **1** _**→**_ **2**


# hidden layers 1 1 1 1


# NL layers in the self-interaction 1 1 1 1


# channels 24 20 24 24


# maximum rank of the hidden layers 1 2 1 2


# nodes in the radial function 16 8 16 22


3.4.1.3 R ESULTS


Figure 3.3 and Table 3.3 present a visualization and comparison of predictive perfor

mance, respectively. The results show that an IsoGCN outperforms other GCN models for


all settings. This is because the IsoGCN model has information on the relative position of


the adjacency vertices, and thus understands the direction of the gradient, whereas the other


GCN models cannot distinguish where the adjacencies are, making it nearly impossible to


predict the gradient directions.




# Page 89

ヒートマップの軸は縦横の格子線で構成され、緑色から黄色、橙色、赤色に色が変化しています。高域集中領域は左上隅に黄色と橙色が混在する部分、右下隅に赤色が集中的に分布しています。目立つパターンは、左下隅の黄色と赤色の混合区域が特に目立っています。

ヒートマップの軸は横軸と縦軸で、データの分布を示します。高濃度の領域は黄色・橙色に、低濃度は青色・緑色に表示されます。目立つパターンは、色の変化や形状の一致が特徴的です。

ヒートマップの軸は横軸と縦軸です。高域集中領域は緑・黄・橙色で、低域は青色です。目立つパターンは、左上角の緑黄橙色域と右下角の紫白色域が特徴的です。

主要ノード：Cluster-GCN
クラスタ：SE(3)-Tr
強い接続：網膜状接続（網膜様接続）、星状接通（星様接通）、放射状接線（放射様接線）、網状接合（網様接合）



3.4. Numerical Experiments **65**



ヒートマップの軸は「gradient Magnitude（梯度の大きさ）」で、0.0e+00から1.5e-01の範囲を示しています。色は赤から緑に変化し、高値域（0.1程度）は赤色で、低値領域は青色です。右上角の赤色部分が最大値の集中領域で、左下角の青色部分は最小値区域です。

ヒートマップの軸は横軸と縦軸です。高域集中領域は黄色・橙色、低域は緑・青です。目立つパターンは、左の図では不規則な緑色斑点、中央と右の団円状の色調変化が見られます。

図はベクトル場の分布を示しています。矢印の大きさは場の強度を表し、右上に斜めの矢印が特徴的で、左下の領域では矢量が逆方向に方向づけられ、強度が弱いことがわかります。

縦軸は「difference-gradient Magnitude（差分勾配の大きさ）」を示し、横軸には「gr（不明）」が記載されています。色条は正の値（赤色）から負の值（青色）へと変化し、最大値5.0e-02（0.05）を示しています。全体的に正の傾向が見られ、最大差分は右端の赤色部分に位置しています。

左の図は「r-GCN」で生成されたベクトル場を示しています。矢印の大きさは場の強さを表し、右上に指向する傾向が特徴的で、中央に集中的な強度が見られ、周囲には弱い矢量が分布しています。

ヒートマップの横軸は「difference-gradient Magnitude（差分勾配の大きさ）」を示し、右側の色条はこの値の範囲を示しています。上部のヒートmapでは、緑色と黄色の領域が目立っており、これらの色域内では勾配が大きいため、高集中領域に該当します。下部のIsoGCN（Ours）ヒートmapsでは、赤色と橙色の領域も目立っていますが、勾配はそれほど大きくないため、低集中領域と見なされています。

Figure 3.3: (Top) the gradient field and (bottom) the error vector between the prediction


and the ground truth of a test data sample. The error vectors are exaggerated by a factor of


2 for clear visualization.


Adding the vertex positions to the input feature to other GCN models exhibited a perfor

mance improvement, however as the vertex position is not a translation invariant feature, it


could degrade the predictive performance of the models. Thus, we did not input _**x**_ as a ver

tex feature to the IsoGCN model or other equivariant models to retain their E( _n_ )- invariant


and equivariant natures.


IsoGCNs perform competitively against other equivariant models with shorter predic
tion time as shown in Table 3.4. As mentioned in Section 3.3.4, _**G**_ [˜] corresponds to the


gradient operator, which is now confirmed in practice. Therefore, it can be found out the


proposed model has a strong expressive power to express differential regarding space with


less computation resources compared to the TFN and SE(3)-Transformer.




# Page 90

**66** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


Table 3.3: Summary of the test losses (mean squared error _±_ the standard error of the


mean in the original scale) of the differential operator dataset: 0 _→_ 1 (the scalar field to the


gradient field), 0 _→_ 2 (the scalar field to the Hessian field), 1 _→_ 0 (the gradient field to the


Laplacian field), and 1 _→_ 2 (the gradient field to the Hessian field). Here, if “ _**x**_ ” is “Yes”,


_**x**_ is also in the input feature.


**Loss of 0** _**→**_ **1** **Loss of 0** _**→**_ **2** **Loss of 1** _**→**_ **0** **Loss of 1** _**→**_ **2**
**Method** **# hops** _**x**_
_×_ 10 _[−]_ [5] _×_ 10 _[−]_ [6] _×_ 10 _[−]_ [6] _×_ 10 _[−]_ [6]


2 No 151.19 _±_ 0.53 49.10 _±_ 0.36 542.52 _±_ 2.14 59.65 _±_ 0.46


2 Yes 147.10 _±_ 0.51 47.56 _±_ 0.35 463.79 _±_ 2.08 50.73 _±_ 0.40

GIN

5 No 151.18 _±_ 0.53 48.99 _±_ 0.36 542.54 _±_ 2.14 59.64 _±_ 0.46


5 Yes 147.07 _±_ 0.51 47.35 _±_ 0.35 404.92 _±_ 1.74 46.18 _±_ 0.39


2 No 151.18 _±_ 0.53 43.08 _±_ 0.31 542.74 _±_ 2.14 59.65 _±_ 0.46


2 Yes 151.14 _±_ 0.53 40.72 _±_ 0.29 194.65 _±_ 1.00 45.43 _±_ 0.36

GCNII

5 No 151.11 _±_ 0.53 32.85 _±_ 0.23 542.65 _±_ 2.14 59.66 _±_ 0.46


5 Yes 151.13 _±_ 0.53 31.87 _±_ 0.22 280.61 _±_ 1.30 39.38 _±_ 0.34


2 No 151.17 _±_ 0.53 50.26 _±_ 0.38 542.90 _±_ 2.14 59.65 _±_ 0.46


2 Yes 151.12 _±_ 0.53 49.96 _±_ 0.37 353.29 _±_ 1.49 59.61 _±_ 0.46

SGCN

5 No 151.12 _±_ 0.53 55.02 _±_ 0.42 542.73 _±_ 2.14 59.64 _±_ 0.46


5 Yes 151.16 _±_ 0.53 55.08 _±_ 0.42 127.21 _±_ 0.63 56.97 _±_ 0.44


2 No 151.23 _±_ 0.53 49.59 _±_ 0.37 542.54 _±_ 2.14 59.64 _±_ 0.46


2 Yes 151.14 _±_ 0.53 47.91 _±_ 0.35 542.68 _±_ 2.14 59.60 _±_ 0.46

GCN

5 No 151.18 _±_ 0.53 50.58 _±_ 0.38 542.53 _±_ 2.14 59.64 _±_ 0.46


5 Yes 151.14 _±_ 0.53 48.50 _±_ 0.35 542.30 _±_ 2.14 25.37 _±_ 0.28


2 No 151.19 _±_ 0.53 33.39 _±_ 0.24 542.54 _±_ 2.14 59.66 _±_ 0.46


2 Yes 147.23 _±_ 0.51 32.29 _±_ 0.24 167.73 _±_ 0.83 17.72 _±_ 0.17

Cluster-GCN

5 No 151.15 _±_ 0.53 28.79 _±_ 0.21 542.51 _±_ 2.14 59.66 _±_ 0.46


5 Yes 146.91 _±_ 0.51 26.60 _±_ 0.19 185.21 _±_ 0.99 18.18 _±_ 0.20


2 No 2.47 _±_ 0.02 OOM 26.69 _±_ 0.24 OOM
TFN

5 No OOM OOM OOM OOM


2 No **1.79** _±_ 0.02 **3.50** _±_ 0.04 **2.52** _±_ 0.02 OOM
SE(3)-Trans.

5 No 2.12 _±_ 0.02 OOM 7.66 _±_ 0.05 OOM


2 No 2.67 _±_ 0.02 6.37 _±_ 0.07 7.18 _±_ 0.06 **1.44** _±_ 0.02
**IsoGCN** (Ours)

5 No 14.19 _±_ 0.10 21.72 _±_ 0.25 34.09 _±_ 0.19 8.32 _±_ 0.09




# Page 91

3.4. Numerical Experiments **67**


Table 3.4: Summary of the prediction time on the test dataset. 0 _→_ 1 corresponds to the


scalar field to the gradient field, and 0 _→_ 2 corresponds to the scalar field to the Hessian


field. Each computation was run on the same GPU (NVIDIA Tesla V100 with 32 GiB


memory). OOM denotes the out-of-memory of the GPU.


**0** _**→**_ **1** **0** _**→**_ **2**


**Method** **# parameters** **Inference time [s]** **# parameters** **Inference time [s]**


TFN 5264 3.8 5220 OOM


SE(3)-Trans. 5392 4.0 5265 9.2


**IsoGCN** (Ours) 4816 0.4 4816 0.7




# Page 92

**68** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


3.4.2 A NISOTROPIC N ONLINEAR H EAT E QUATION D ATASET


3.4.2.1 T ASK D EFINITION


To apply the proposed model to a real problem, we adopted the anisotropic nonlinear


heat equation. We considered the task of predicting the time evolution of the temperature


field based on the initial temperature field, material property, and mesh geometry infor

mation as inputs. We randomly selected 82 CAD shapes from the first 200 shapes of the


ABC dataset (Koch et al., 2019), generate first-order tetrahedral meshes using a mesh gen

erator program, Gmsh (Geuzaine & Remacle, 2009), randomly set the initial temperature


and anisotropic thermal conductivity, and finally conducted a finite element analysis (FEA)


using the FEA program FrontISTR [4] (Morita et al., 2016; Ihara et al., 2017).


For this task, we set


_w_ _ij_ = _V_ _j_ [effective] _/V_ _i_ [effective] _,_ (3.69)


where _V_ _i_ [effective] denotes the effective volume of the _i_ th vertex (Equation 3.74.) Similarly to


the differential operator dataset, we tested the number of hops _m_ = 2 _,_ 5. However because


we put four IsoAM operations in one model, the number of hops visible from the model is


8 ( _m_ = 2) or 20 ( _m_ = 5). As is the case with the differential operator dataset, we replaced


an IsoGCN layer accordingly for GCN or its variant models.


In the case of _k_ = 2, we reduced the number of parameters for each of the baseline


equivariant models to fewer than the IsoGCN model because they exceeded the memory of


the GPU (NVIDIA Tesla V100 with 32 GiB memory) with the same number of parameters.


In the case of _k_ = 5, neither the TFN nor the SE(3)-Transformer fits into the memory of the


GPU even with the number of parameters equal to 10. For more details about the dataset


and the model, see Section 3.4.2.


4 [https://github.com/FrontISTR/FrontISTR. We applied a private update to FrontISTR to](https://github.com/FrontISTR/FrontISTR)
deal with the anisotropic heat problem, which will be also made available online.




# Page 93

3.4. Numerical Experiments **69**


3.4.2.2 D ATASET


The purpose of the experiment was to solve the anisotropic nonlinear heat diffusion


under an adiabatic boundary condition. The governing equation is defined as follows:


Ω _⊂_ R [3] (3.70)


_∂T_ ( _t,_ _**x**_ )

= _∇·_ _**C**_ ( _T_ ( _t,_ _**x**_ )) _∇T_ ( _t,_ _**x**_ ) in Ω (3.71)
_∂t_


_T_ ( _t_ = 0 _,_ _**x**_ ) = _T_ 0 _._ 0 ( _**x**_ ) in Ω (3.72)


_∇T_ ( _t,_ _**x**_ ) _|_ _**x**_ = _**x**_ _b_ _·_ _**n**_ ( _**x**_ _b_ ) = 0 on _∂_ Ω _,_ (3.73)


where _T_ is the temperature field, _T_ 0 _._ 0 is the initial temperature field, _**C**_ _∈_ R _[d][×][d]_ is an


anisotropic diffusion tensor and _**n**_ ( _**x**_ _b_ ) is the normal vector at _**x**_ _b_ _∈_ _∂_ Ω. The Neumann


boundary condition expressed in Equation 3.73 corresponds to the adiabatic condition.


Here, _**C**_ depends on temperature thus the equation is nonlinear. We randomly generate


_**C**_ ( _T_ = _−_ 1) for it to be a positive semidefinite symmetric tensor with eigenvalues varying


from 0.0 to 0.02. Then, we defined the linear temperature dependency the slope of which


is _−_ _**C**_ ( _T_ = _−_ 1) _/_ 4. The function of the anisotropic diffusion tensor is uniform for each


sample.


The task is defined to predict the temperature field at _t_ = 0 _._ 2 _,_ 0 _._ 4 _,_ 0 _._ 6 _,_ 1 _._ 0


( _T_ 0 _._ 2 _, T_ 0 _._ 4 _, T_ 0 _._ 6 _, T_ 0 _._ 8 _, T_ 1 _._ 0 ) from the given initial temperature field _T_ 0 _._ 9, material property,


and mesh geometry. However, the performance is evaluated only with _T_ 1 _._ 0 to focus on


the predictive performance. We inserted other output features to stabilize the trainings.


Accordingly, the diffusion number of this problem is _**C**_ ∆ _t/_ (∆ _x_ ) [2] _≃_ 10 _._ 0 [4] assuming


∆ _x ≃_ 10 _._ 0 _[−]_ [3] .


Figure 3.4 represents the process of generating the dataset. We generated up to 9 FEA


results for each CAD shape. To avoid data leakage in terms of the CAD shapes, we first


split them into training, validation, and test datasets, and then applied the following process.


Using one CAD shape, we generated up to three meshes using clscale (a control pa

rameter of the mesh characteristic lengths) = 0.20, 0.25, and 0.30. To facilitate the training


process, we scaled the meshes to fit into a cube with an edge length equal to 1.




# Page 94

**70** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


Using one mesh, we generated three initial conditions randomly using a Fourier series


of the 2nd to 10th orders. We then applied an FEA to each initial condition and material


property determined randomly as described above. We applied an implicit method to solve


time evolutions and a direct method to solve the linear equations. The FEA time step ∆ _t_


was set to 0.01.


During this process, some of the meshes or FEA results may not have been available


due to excessive computation time or non-convergence. Therefore, the size of the dataset


was not exactly equal to the number multiplied by 9. Finally, we obtained 439 FEA results


for the training dataset, 143 FEA results for the validation dataset, and 140 FEA results for



図はCAD（Computer-Aided Design）で作成された試験データセットの機械図を示し、上部の半円形と下部の矩形状が互いに接合する構造を主な要素とし、灰色と白色の塗り分けで内部構造を示しています。

この図は、CAD（Computer-Aided Design，コンピュータアシスタント設計）からFEA（Finite Element Analysis，フinit element解析）へのプロセスを示しています。左側はCADで作成された曲面形状の図示と、その図示を細かく分割した「mesh（マッシュ）」を示します。右側は、初期条件と材料特性を設定した後、FEAによる温度分布の結果を示した図です。図の下に温度の範囲（-1.0e+00 ～ 1.0E+00）を示し、色の変化は温度の高低を表しています。左から右へと進むと、meshの粒度（clscale）が0.30から0.20に減少し、FEA結果の温度分布の精度が向上する様子が示されています。





画像は機械構造の変化を示す図です。左から右に進むと、構造の形状が徐々に変化し、中央の図では「clscale = 0.30」という値が示されています。右端の図は表面の温度分布を表す彩色図で、緑色は高温、黄色は中温、灰色は低温を示しています。

画像は物理的性質の変化を示す3D図示で、左側の図形から右側に移動する方向に性質が変化していることを示しています。背景色の変化は性質の高低を表し、右側の形状は左側の状態から変化した状態を示しています。

画像は材料特性の変化を示すブロック図で、灰色の立方体から彩色表面が変化し、上向きの矢印で「Material property（材料特性）」を示す。右側の彩色表面は材料特性が変化した状態を表しています。

画像は物体の形状変化を示すプロセスを表しています。最初に灰色の立方体状物体が示され、次にその物体の表面に彩色マップが追加され、最後に物体の形状が変化した彩色表面が示されています。彩色マップは物体表面の特性を表し、色の変化は表面の特性の変化を反映しています。

図は物体の形状を示す3D図と、同一物体の表面温度分布を示す彩色曲面図を示し、左図の「clscale = 0.25」が右図の温度分布に影響する関係を示しています。左図から右図への矢印は、物体の形状から表面温度分布への変換を表しています。

画像は流体シミュレーションの結果を示す3D図で、左から右に進むと流体の温度分布が変化する様子を示しています。色の変化は温度の高低を表し、右側の図では上部が高温（赤色）に、下部が低温（青色）に分布しています。

図は機械構造の変形過程を示しています。左側の灰色構造体から右側の彩色曲面構造体へと変形が進行し、色の変化は応力の分布を表しています。右側の構造体は左側の状態に比べて形状が変化しています。

この画像は、物体の形状変形を示す技術的な図です。左の図は原始の形状を表し、右の図ではその形状が変形した状態を示しています。色の変化は変形の程度を示すもので、左から右に進むにつれて変形が進行しています。

図は機械構造のスケーリング関係を示す図で、左側の図は「clscale = 0.20」の状態を表し、右側の彩色曲面図は同一スケーラビリティ条件下での形状変化を示しています。

Figure 3.4: The process of generating the dataset. A smaller clscale parameter generates


smaller meshes.




# Page 95

3.4. Numerical Experiments **71**


3.4.2.3 I NPUT AND O UTPUT F EATURES


To express the geometry information, we extracted the effective volume of the _i_ th vertex


_V_ _i_ [effective] and the mean volume of the _i_ th vertex _V_ _i_ [mean], which are defined as follows:



_V_ _i_ [effective] = Y

_e∈N_ _i_ _[e]_



1
(3.74)
4 _[V]_ _[e]_



_V_ _i_ [mean] =



Q _e_ _|N_ _∈Ni_ _[e]_ _i_ _[e]_ _[|]_ _[V]_ _[e]_ _,_ (3.75)



where _N_ _i_ _[e]_ [is the set of elements, including the] _[ i]_ [th vertex.]


For GCN or its variant models, we tested several combinations of input vertex features


_T_ 0 _._ 0, _**C**_, _V_ [effective], _V_ [mean], and _**x**_ (Table 3.6). For the IsoGCN model, inputs were _T_ 0 _._ 0,


_V_ [effective], _V_ [mean], and _**C**_ . Since we construct define the discrete tensor field for each tensor


rank, we have




















_**H**_ [(0)]
in [=]


_**H**_ [(2)]
in [=]



































_**C**_


_**C**_


...


_**C**_



_T_ 0 _._ 0 ( _**x**_ 1 ) _V_ [effective] ( _**x**_ 1 ) _V_ mean ( _**x**_ 1 )


_T_ 0 _._ 0 ( _**x**_ 2 ) _V_ [effective] ( _**x**_ 2 ) _V_ mean ( _**x**_ 2 )


... ... ...



_∈_ R _[|V|×]_ [3] _[×][n]_ [0] (3.76)



_T_ 0 _._ 0 ( _**x**_ _|V|_ ) _V_ [effective] ( _**x**_ _|V|_ ) _V_ mean ( _**x**_ _|V|_ )





















































_|V|_ rows _∈_ R _[|V|×]_ [1] _[×][n]_ [2] _,_ (3.77)




# Page 96

**72** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


for input discrete tensor fields and



_∈_ R _[|V|×]_ [5] _[×][n]_ [0]


(3.78)




















_**H**_ out [(0)] [=]




















_T_ 0 _._ 2 ( _**x**_ 1 ) _T_ 0 _._ 4 ( _**x**_ 1 ) _T_ 0 _._ 6 ( _**x**_ 1 ) _T_ 0 _._ 8 ( _**x**_ 1 ) _T_ 1 _._ 0 ( _**x**_ 1 )


_T_ 0 _._ 2 ( _**x**_ 2 ) _T_ 0 _._ 4 ( _**x**_ 2 ) _T_ 0 _._ 6 ( _**x**_ 2 ) _T_ 0 _._ 8 ( _**x**_ 2 ) _T_ 1 _._ 0 ( _**x**_ 2 )


... ... ... ... ...



_T_ 0 _._ 2 ( _**x**_ _|V|_ ) _T_ 0 _._ 4 ( _**x**_ _|V|_ ) _T_ 0 _._ 6 ( _**x**_ _|V|_ ) _T_ 0 _._ 8 ( _**x**_ _|V|_ ) _T_ 1 _._ 0 ( _**x**_ _|V|_ )



for the output discrete tensor field in the present task.


3.4.2.4 M ODEL A RCHITECTURES



フローチャートの開始は「T₀.₀」から始まり、終了は「C」へと進みます。主な分岐は「MLP」と「IsoGCN」で、MLPは「Identity」「tanh」を含む多層パーソナルニューラルネットワークを経て「Linear」に到達し、「Identity」を出力する処理が主な流れです。











図はMLP（多層パーソナルニューラルネットワーク）のブロック図を示しています。MLPの入力層は512個、隠れ層は2層で、各層の活性化関数はtanhで、最後の層はIdentity（線形）を含んでいます。出力はT₀.₂からT₁.₀までの5個の値になります。









































Propagation 1 Propagation 2


Encoder Process Decoder



Figure 3.5: The IsoGCN model used for the anisotropic nonlinear heat equation dataset.


Gray boxes are trainable components. In each trainable cell, we put the number of units in


each layer along with the activation functions used. Below the unit numbers, the activation


function used for each layer is also shown. _∗⃝_ denotes the multiplication in the feature


direction, _⊙_ denotes the contraction, and _⊕_ denotes the addition in the feature direction.


Figure 3.5 represents the IsoGCN model used for the anisotropic nonlinear heat equa

tion dataset. We adopted the encode-process-decode configuration (Battaglia et al., 2018)


to leverage the expressive power of neural networks. The encoder embeds the input fea

tures to a higher dimensional space, 512 dimension in the present case. By increasing the




# Page 97

3.4. Numerical Experiments **73**


dimension of the encoded space, one can expect that the expressive power increases. The


decoder takes the embedded features and outputs features in the desired dimension.


The process part contains two propagation blocks. Although the propagation block


looks complicated, one can see it corresponds to the explicit Euler method (Equation 2.58):


_T_ ( _t_ + ∆ _t,_ _**x**_ ) _≈_ _T_ ( _t,_ _**x**_ ) + _∇·_ _**C**_ ( _T_ ( _t,_ _**x**_ )) _∇T_ ( _t,_ _**x**_ )∆ _t,_ (3.79)


because one propagation block is expressed as


Propagation _i_ ( _**H**_ [(0)] _,_ _**H**_ [(2)] ) = _**H**_ [(0)] + _**G**_ [˜] _⊙_ _**H**_ [(2)] _⊙_ MLP( _**H**_ [(0)] ) _**G**_ [˜] _∗_ _**H**_ [(0)] _,_ (3.80)


where _**H**_ [(0)] and _**H**_ [(2)] denotes the rank-0 and rank-2 tensor inputs to the considered prop

agation block ( _i_ = 1 _,_ 2). Thus, one propagation block proceeds time ∆ _t_ because of the


relationship to the Euler method. By stacking this propagation block _r_ times, we can make


time evolution by _r_ ∆ _t_, making it possible to predict the state after the long time. How

ever, increasing _r_ may cause longer computation time. Therefore, we keep _r_ = 2 for the


experiment to retain computational efficiency.


For the nonlinear activation function, we used tanh because we expect the target tem

perature field to be smooth. Therefore, we avoid using non-differentiable activation func

tions such as the rectified linear unit (ReLU) (Nair & Hinton, 2010).


For GCN and its variants, we simply replaced the IsoGCN layers with the correspond

ing ones. We stacked _m_ (= 2 _,_ 5) layers for GCN, GIN, GCNII, and Cluster-GCN. We used


an _m_ hop adjacency matrix for SGCN.


For the TFN and SE(3)-Transformer, we set the hyperparameters to as many parameters


as possible that would fit on the GPU because the TFN and SE(3)-Transformer with almost


the same number of parameters as in IsoGCN did not fit on the GPU we used (NVIDIA


Tesla V100 with 32 GiB memory). The settings of the hyperparameters are shown in


Table 3.5.




# Page 98

**74** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


Table 3.5: Summary of the hyperparameter setting for both the TFN and SE(3)

Transformer. For the parameters not written in the table, we used the de

[fault setting in the implementation of https://github.com/FabianFuchsML/](https://github.com/FabianFuchsML/se3-transformer-public)


[se3-transformer-public.](https://github.com/FabianFuchsML/se3-transformer-public)


# hidden layers 1


# NL layers in the self-interaction 1


# channels 16


# maximum rank of the hidden layers 2


# nodes in the radial function 32


3.4.2.5 R ESULTS


Figure 3.6 and Table 3.6 present the results of the qualitative and quantitative compar

isons for the test dataset. The IsoGCN demonstrably outperforms all other baseline models.


Moreover, owing to the computationally efficient E( _n_ )-invariant nature of IsoGCNs, it also


achieved a high prediction performance for the meshes that had a significantly larger graph


than those considered in the training dataset. The IsoGCN can scale up to 1M vertices,


which is practical and is considerably greater than that reported in Sanchez-Gonzalez et al.


(2020). Therefore, we conclude that IsoGCN models can be trained on relatively smaller


meshes [5] to save the training time and then used to apply the inference to larger meshes


without observing significant performance deterioration.


Table 3.7 reports the preprocessing and inference computation time using the equivari

ant models with _m_ = 2 as the number of hops and FEA using FrontISTR 5.0.0. We varied


the time step (∆ _t_ = 1 _._ 0 _,_ 0 _._ 5) for the FEA computation to compute the _t_ = 1 _._ 0 time evo

lution thus, resulting in different computation times and errors compared to an FEA with


∆ _t_ = 0 _._ 01, which was considered as the ground truth. Clearly, the IsoGCN is 3- to 5- times


faster than the FEA with the same level of accuracy, while other equivariant models have


almost the same speed as FrontISTR with ∆ _t_ = 0 _._ 5.


The results show that the inclusion of _**x**_ in the input features of the baseline models did


not improve the performance. In addition, if _**x**_ is included in the input features, a loss of the


5 However, it should also be sufficiently large to express sample shapes and fields.




# Page 99

図面上に「Ground truth」と書かれた2つの円筒状物体が示されています。物体表面に網状の格子が描かれており、色は緑、黄、橙、緑の順に変化しています。物体の上部に矩形の穴が開いています。

等高線/等値線図は、特定の物理量（例：温度、圧力）の分布を表します。軸は物理量の単位を示し、等高線上の値は同一物理量を示します。高低の等価線は高値と低値の区別を表し、重要な領域は等価線上で物理量が急激に変化する部分を指します。

図面上に「Ground truth」と書かれた彩色曲面が示され、その下に灰色の曲面が描かれており、両者の関係を示しています。地上の真の状態（Ground truth）を示す彩色曲面と、その状態を推定した灰色曲面が対比されています。



3.4. Numerical Experiments **75**

等高線/等値線図は、特定の物理量（例：温度、圧力）の分布を表します。軸は物理量の単位を示し、等高線上の値は同一物理量を示します。高低の等価線は高値と低値の区別を表し、重要な領域は等価線上で物理量が急激に変化する部分を指します。

ヒートマップの軸は「TEMPERATURE（温度）」です。高温度域は赤色、低温度域が青色に表れています。中央の矩形区域内は温度が最も高いため、赤色が強調され、周囲は青色で低温度を示しています。


SGCN SE(3) Trans. IsoGCN (Ours)



図面上に「SGCN」と「SE(3) Tra」の名称が示され、両方の図は相似した円筒状物体を示しています。左の図（SGCN）は青色と茶色の色調で構成され、右の図「(SE(3)) Tra」は右半分が茶色、左半分が青色に色調が異なります。背景には「and truth」の文字が表示されています。

画像は3種類の柱状物体を示しており、左から「CN」「SE(3) Trans」「IsoGCN (CN)」と名称が付けられています。各物体は網状の表面構造を有し、中央に矩形孔が開いています。物体の色は主に青色と橙色の混合色で構成され、色の分布は物体の形状や孔の位置に応じて変化しています。

ヒートマップの軸は「Inference - Ground Truth」で、色は推定値と真値の差異を示します。高濃度の赤色領域は推測が高値に近い場所を示し、低濃度（青色）は低値を推測している場所です。中央に集中的な青色領域が真值と推定の差が最小であることを示しています。

Figure 3.6: (Top) the temperature field of the ground truth and inference results and (bot

tom) the error between the prediction and the ground truth of a test data sample. The error


is exaggerated by a factor of 2 for clear visualization.


generalization capacity for larger shapes compared to the training dataset may result as it


extrapolates. The proposed model achieved the best performance compared to the baseline


models considered. Therefore, we concluded that the essential features regarding the mesh

shapes are included in _**G**_ [˜] .


Besides, IsoGCN can scale up to meshes with 1M vertices as shown in Figure 3.7.


The result is surprizing because we trained relatively smaller meshes with several thousand


vertices. Since IsoGCN successfully includes the information of the PDE, it can show such


a high generalizability.




# Page 100

**76** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network



ヒートマップの軸は「TEMPERATURE（温度）」で、色は温度の高低を示します。高温域は赤色、低温域は青色です。図中央に「IsoGCN（Ours）」と「Ground Truth（FEA）」の名称が表示され、図の右下に拡大した部分が注目点です。

ヒートマップの軸は「温度」で、色は温度の高低を示します。高温度域は赤・橙色、低域は緑・青色です。中央の「Ground Truth (FEA)」と右の「IsoGCN (Ours)」のヒートグラフに、温度分布のパターンが見られます。



ヒートマップの軸は「色の深浅」を示します。高域は赤色、低域は青色です。中心部に緑色が集まり、周囲に黄色と赤色が分布しています。右上角に「IsoGCN (Ours)」と「Ground Truth (FEA)」のラベルがあります。

ヒートマップの軸は左から右に進む方向に設定されています。左側のサンプルでは、緑色と黄色の領域が密集しており、右側のIsoGCN推論結果では、赤色と橙色の高集中領域が見られ、両者のパターンが異なることが示されています。

ヒートマップの軸は左上から右下に進む方向に示されています。高域集中領域は黄色から赤色に移行し、低域は青色から緑色へと移行しています。右上角に「Training samples」の黒い点が存在し、その周囲の色は明るめの黄色と緑です。右側には「IsoGCN inference result」と書かれた白色の文字と、右上に「Figure 3.7: Comparison between (left) samples in the training, computed through FEA, and (right) IsoGCN inferenc...」と書かれている白色のテキストがあります。

ヒートマップの軸は横軸と縦軸です。高域集中領域は黄色・橙色に、低域は緑・青色に分布しています。右上角に目立つ赤色斑点が特徴的です。

field for a mesh, which is much larger than these in the training dataset.




# Page 101

3.4. Numerical Experiments **77**


Table 3.6: Summary of the test losses (mean squared error _±_ the standard error of the mean


in the original scale) of the anisotropic nonlinear heat dataset. Here, if “ _**x**_ ” is “Yes”, _**x**_ is


also in the input feature. OOM denotes the out-of-memory on the applied GPU (32 GiB).


**Loss**
**Method** **# hops** _**x**_
_×_ 10 _[−]_ [3]


2 No 16.921 _±_ 0.040


2 Yes 18.483 _±_ 0.025

GIN

5 No 22.961 _±_ 0.056


5 Yes 17.637 _±_ 0.046


2 No 10.427 _±_ 0.028


2 Yes 11.610 _±_ 0.032

GCN

5 No 12.139 _±_ 0.031


5 Yes 11.404 _±_ 0.032


2 No 9.595 _±_ 0.026


2 Yes 9.789 _±_ 0.028

GCNII

5 No 8.377 _±_ 0.024


5 Yes 9.172 _±_ 0.028


2 No 7.266 _±_ 0.021


2 Yes 8.532 _±_ 0.023

Cluster-GCN

5 No 8.680 _±_ 0.024


5 Yes 10.712 _±_ 0.030


2 No 7.317 _±_ 0.021


2 Yes 9.083 _±_ 0.026

SGCN

5 No 6.426 _±_ 0.018


5 Yes 6.519 _±_ 0.020


2 No 15.661 _±_ 0.019
TFN

5 No OOM


2 No 14.164 _±_ 0.018
SE(3)-Trans.

5 No OOM


2 No 4.674 _±_ 0.014
**IsoGCN** (Ours)

5 No **2.470** _±_ 0.008




# Page 102

**78** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network


Table 3.7: Comparison of computation time. To generate the test data, we sampled CAD


data from the test dataset and then generated the mesh for the graph to expand while re

taining the element volume at almost the same size. The initial temperature field and the


material properties are set randomly using the same methodology as the dataset sample


generation. For a fair comparison, each computation was run on the same CPU (Intel Xeon


E5-2695 v2@2.40GHz) using one core, and we excluded file I/O time from the measured


time. OOM denotes the out-of-memory (500 GiB).


_**|V|**_ **= 21** _**,**_ **289** _**|V|**_ **= 155** _**,**_ **019** _**|V|**_ **= 1** _**,**_ **011** _**,**_ **301**


**Loss** **Loss** **Loss**
**Method** **Time [s]** **Time [s]** **Time [s]**
_×_ 10 _[−]_ [4] _×_ 10 _[−]_ [4] _×_ 10 _[−]_ [4]


FrontISTR (∆ _t_ = 1 _._ 0) 10.9 16.7 6.1 181.7 2.9 1656.5


FrontISTR (∆ _t_ = 0 _._ 5) 0.8 30.5 0.4 288.0 0.2 2884.2


TFN 77.9 46.1 30.1 400.9 OOM OOM


SE(3)-Transformer 111.4 31.2 80.3 271.1 OOM OOM


**IsoGCN** (Ours) 8.1 **7.4** 4.9 **84.1** 3.9 **648.4**




# Page 103

3.5. Conclusion **79**


3.5 C ONCLUSION


In this chapter, we introduced the GCN-based E( _n_ )- invariant and equivariant mod

els called IsoGCN. We discussed the differential IsoAM, an isometric adjacency matrix


(IsoAM) for numerical analysis, that was closely related to the essential differential opera

tors. The experiment results confirmed that the proposed model leveraged the spatial struc

tures and can deal with large-scale graphs. The computation time of the IsoGCN model is


significantly shorter than the FEA, which other equivariant models cannot achieve. There

fore, IsoGCN must be the first choice to learn physical simulations because of its compu

tational efficiency as well as E( _n_ )- invariance and equivariance. Our demonstrations were


conducted on the mesh structured dataset based on the FEA results. However, we expect


IsoGCNs to be applied to various domains, such as object detection, molecular property


prediction, and physical simulations using particles.




# Page 104

**80** 3. IsoGCN: E( _n_ )-Equivariant Graph Convolutional Network




# Page 105

# **Chapter 4** **Physics-Embedded Neural Network:** **Boundary Condition and Implicit** **Method**

4.1 I NTRODUCTION


In Chapter 3, we introduced IsoGCN, a lightweight E( _n_ )-equivariant graph neural net

work. It can:


   - handle an arbitrary mesh thanks to the generalizability of GNN;


   - reflect symmetries regarding E( _n_ ) transformation that exists in physical phenom

ena; and


   - predict faster than conventional numerical analysis methods and complex GNNs


based on linear message passing scheme.


However, we still miss the following keys to constructing general PDE solvers:


   - **Treatment of mixed boundary conditions** : Mixed boundary condition contains


Dirichlet and Neumann boundary conditions in disjoint boundary regions, as ex

pressed in Equations 2.54 and 2.55. The IsoGCN model demonstrated in Sec

tion 3.4.2 considers only adiabatic boundary conditions corresponding to the ho

81




# Page 106

**82** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


mogeneous Neumann boundary condition (Equation 3.73). Therefore, we must


provide a provable way to handle mixed boundary conditions.


   - **An implicit manner for time evolution** : In Section 3.4.2, we constructed IsoGCN


models based on the explicit Euler method (Equation 3.80). It can consider interac

tions between vertices _k_ hop away by stacking _k_ IsoGCN layers. However, global


interaction may sometimes occur as in incompressible flow phenomena, where the


speed of sound is regarded as infinity. These global interactions require IsoGCN


layers stacked more than the number of vertices _|V|_, which may result in huge


computation time. Therefore, we must incorporate implicit time evolution that can


consider global interaction.


   - **Demonstration in various PDEs** : We demonstrated IsoGCN’s expressibility using


the heat equation in Section 3.4.2. However, there are many PDEs in addition to the


heat equation. Thus, we must show the model can learn various phenomena, such


as the advection-diffusion and incompressible flow problems.


Thus, we introduce _physics-embedded neural networks_ (PENNs), a machine learning


framework to address these issues by embedding physics in the models. We build our model


based on IsoGCN to reflect physical symmetry and realize fast prediction. Furthermore, we


construct a method to consider mixed boundary conditions. Finally, we reconsider a way


to stack GNNs based on a nonlinear solver, which naturally introduces the global pooling


to GNNs as the global interaction with high interpretability. In numerical experiments, we


demonstrate that our treatment of Neumann boundary conditions improves the predictive


performance of the model, and our method can fulfill Dirichlet boundary conditions with


no error. Our method also achieves state-of-the-art performance compared to a classical,


well-optimized numerical solver and a baseline machine learning model in speed-accuracy


trade-off.


Figure 4.1 shows the overview of the proposed model. Our main contributions are


summarized as follows:


   - We construct models to satisfy mixed boundary conditions: the _boundary encoder_,


_Dirichlet layer_, _pseudoinverse decoder_, and _NeumannIsoGCN_ (NIsoGCN). The




# Page 107

4.2. Related Prior Work **83**


considered models show provable fulfillment of boundary conditions, while exist

ing models cannot.


- We propose _neural nonlinear solvers_, which realize global connections to stably


predict the state after a long time.


- We demonstrate that the proposed model shows state-of-the-art performance in


speed-accuracy trade-off, and all the proposed components are compatible with


E( _n_ )-equivariance.



画像はDirichlet層とNeumannIsoGCNを組み合わせたE(n)-対称グラフニューラルネットワークの仕組みを示しています。グラフの境界条件を考慮するEncoderとBoundary Encoderを経て、Neumann境界条件をエンコードし、Pseudoinverse Decoderを通じて境界条件を再現するプロセスが描かれています。





Dirichlet boundary

condition









boundary condition Input feature boundary condition Encoded feature Output feature



Figure 4.1: Overview of the proposed method. On decoding input features, we apply


boundary encoders to boundary conditions. Thereafter, we apply a nonlinear solver con

sisting of an E( _n_ )-equivariant graph neural network in the encoded space. Here, we apply


encoded boundary conditions for each iteration of the nonlinear solver. After the solver


stops, we apply the pseudoinverse decoder to satisfy Dirichlet boundary conditions.


4.2 R ELATED P RIOR W ORK


We review machine learning models used to solve PDEs called neural PDE solvers,


typically formulated as _**u**_ ( _t_ _n_ +1 _,_ _**x**_ _i_ ) _≈F_ NN ( _**u**_ )( _t_ _n_ _,_ _**x**_ _i_ ) for ( _t_ _n_ _,_ _**x**_ _i_ ) _∈{t_ 0 _, t_ 1 _, . . . } ×_ Ω,


where _F_ NN is a machine learning model.


4.2.1 P HYSICS -I NFORMED N EURAL N ETWORK (PINN)


Raissi et al. (2019) made a pioneering work combining PDE information and neural


networks, called PINNs, by adding loss to monitor how much the output satisfies the equa

tions. PINNs can be used to solve forward and inverse problems and extract physical




# Page 108

**84** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


states from measurements (Pang et al., 2019; Mao et al., 2020; Cai et al., 2021). However,


PINNs’ outputs should be functions of space because PINNs rely on automatic differentia

tion to obtain loss regarding PDEs. This design constraint significantly limits the model’s


generalization ability because the solution of a PDE could be entirely different when the


shape of the domain or boundary condition changes. Besides, the loss reflecting PDEs helps


models learn physics at training time; however, prediction by PINN models can be out of


physics because of lacking PDE information inside the model. Therefore, these methods


are not applicable in building models that are generalizable over shape and boundary con

dition variations. As seen in Section 4.3, our model contains PDE information inside and


does not take absolute positions of vertices, thus resulting in high generalizability (See


Figure 4.16).


4.2.2 G RAPH N EURAL N ETWORK B ASED PDE S OLVER


As discussed in Sections 2.2.2, 2.2.4, and 3.2.3, one can regard a mesh as a graph and


various existing studies demonstrated that GNNs can learn physical phenomena, as seen


in Alet et al. (2019); Chang & Cheng (2020); Pfaff et al. (2021). Then, Brandstetter et al.


(2022) advanced these works by suggesting temporal bundling and pushforward trick for


efficient and stable prediction. Their method could also consider boundary conditions by


feeding them to the models as inputs. Here, one could expect the model to learn to satisfy


boundary conditions approximately, while there is no guarantee to fulfill hard constraints


such as Dirichlet conditions. In contrast, our model ensures the satisfaction of boundary


conditions. Besides, most GNNs use local connections with a fixed number of message


passings, which lacks consideration of global interaction. We suggest an effective way to


incorporate a global connection with GNN through the neural nonlinear solver.


4.3 M ETHOD


We present our model architecture. Following the study done in Section 3.4, we adopt


the encode-process-decode architecture, proposed by Battaglia et al. (2018), which has


been applied successfully in various previous works, e.g., Pfaff et al. (2021); Brandstetter


et al. (2022). Our key concept is to encode input features, including information on bound

ary conditions, apply a GNN-based nonlinear solver loop reflecting boundary conditions




# Page 109

4.3. Method **85**


in the encoded space, then decode carefully to satisfy boundary conditions in the output


space. In this section, we continue to use the discrete tensor field (Equation 3.5) expressed


as:




















_**H**_ =




















_**h**_ 1


_**h**_ 2


...


_**h**_
_|V|_



_,_ (4.1)



while we do not write the tensor rank explicitly unless needed.


4.3.1 D IRICHLET B OUNDARY M ODEL


As demonstrated theoretically and experimentally in literature (Hornik, 1991; Cybenko,


1992; Nakkiran et al., 2021), the expressive power of neural networks comes from encoding


in a higher-dimensional space, where the corresponding boundary conditions are not trivial.


However, if there are no boundary condition treatments in layers inside the processor, which


resides in the encoded space, the trajectory of the solution can be far from the one with


boundary conditions. Therefore, boundary condition treatments in an encoded space are


essential for obtaining reliable neural PDE solvers that fulfill boundary conditions.


4.3.1.1 B OUNDARY E NCODER


To ensure the same encoded space between variables and boundary conditions, we use


the same encoder for variables and the corresponding Dirichlet boundary conditions, which


we term the _boundary encoder_, as follows:


_**h**_ _i_ = _**f**_ encode ( _**u**_ _i_ ) in Ω (4.2)


ˆ
_**h**_ _i_ = _**f**_ encode (ˆ _**u**_ _i_ ) on _∂_ Ω Dirichlet _,_ (4.3)


where ˆ _**u**_ _i_ is the value of the Dirichlet boundary condition at _**x**_ _i_ _∈_ _∂_ Ω Dirichlet .




# Page 110

**86** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.3.1.2 D IRICHLET L AYER


One can easily apply Dirichlet boundary conditions in the aforementioned encoded


space using the _Dirichlet layer_ defined as:



DirichletLayer( _**h**_ _i_ ) =





_**h**_ _i_ _,_ _**x**_ _i_ _/∈_ _∂_ Ω Dirichlet
ˆ (4.4)



 _**h**_ _i_ _,_ _**x**_ _i_ _∈_ _∂_ Ω Dirichlet _._



This process is necessary to return to the state respecting the boundary conditions after


some operations in the processor, which might violate the conditions.


4.3.1.3 P SEUDOINVERSE D ECODER


After the processor layers, we decode the hidden features using functions satisfying:


_**f**_ decode _◦_ _**f**_ encode (ˆ _**u**_ _i_ ) = ˆ _**u**_ _i_ on _∂_ Ω Dirichlet _._ (4.5)


This condition ensures that the encoded boundary conditions correspond to the ones in the


original physical space. Demanding that Equation 4.5 holds for arbitrary ˆ _**u**_ ; we obtain:


_**f**_ decode _◦_ _**f**_ encode = Id _**u**_ _,_ (4.6)


where Id _**u**_ denotes the identity map from the space of _**u**_ to the same space. By applying


_**f**_ encode [+] [, a left inverse function of the encoder, we have:]


_**f**_ decode = _**f**_ encode [+] _[,]_ (4.7)


which we call the _pseudoinverse decoder_ . It is pseudoinverse because _**f**_ encode, in particular


encoding in a higher-dimensional space, may not be invertible. Therefore, we construct


_**f**_ encode [+] [using pseudoinverse matrices.]


We can construct the pseudoinverse decoders for a wide range of neural network archi

tectures. For instance, the pseudoinverse decoder for an MLP with one hidden layer


_**h**_ = _**f**_ ( _**x**_ ) = _σ_ 2 ( _**W**_ 2 _σ_ 1 ( _**W**_ 1 _**x**_ + _**b**_ 1 ) + _**b**_ 2 ) (4.8)




# Page 111

can be constructed as:



4.3. Method **87**


_**f**_ [+] ( _**h**_ ) = _**W**_ 1 [+] _[σ]_ 1 _[−]_ [1]  _**W**_ 2 [+] _[σ]_ 2 _[−]_ [1] [(] _**[h]**_ [)] _[ −]_ _**[b]**_ [2]  _−_ _**b**_ 1 _,_ (4.9)



where _**W**_ [+] is the pseudoinverse matrix of _**W**_, satisfying _**W**_ [+] _**W**_ = _**I**_, and _σ_ is an invertible


activation function whose Dom( _σ_ ) = Im( _σ_ ) = R. We can confirm that _**f**_ [+] is in fact the


pseudoinverse of _**f**_ as:


_**f**_ [+] _◦_ _**f**_ ( _**x**_ ) = _**W**_ 1 [+] _[σ]_ 1 _[−]_ [1]  _**W**_ 2 [+] _[σ]_ 2 _[−]_ [1] [(] _[σ]_ [2] [(] _**[W]**_ [2] _[σ]_ [1] [(] _**[W]**_ [1] _**[x]**_ [ +] _**[ b]**_ [1] [) +] _**[ b]**_ [2] [))] _[ −]_ _**[b]**_ [2]  _−_ _**b**_ 1


= _**W**_ 1 [+] _[σ]_ 1 _[−]_ [1]  _**W**_ 2 [+] _**[W]**_ [2] _[σ]_ [1] [(] _**[W]**_ [1] _**[x]**_ [ +] _**[ b]**_ [1] [) +] _**[ b]**_ [2] _[−]_ _**[b]**_ [2]  _−_ _**b**_ 1


= _**W**_ 1 [+] _[σ]_ 1 _[−]_ [1] [(] _[σ]_ [1] [(] _**[W]**_ [1] _**[x]**_ [ +] _**[ b]**_ [1] [))] _[ −]_ _**[b]**_ [1]


= _**W**_ 1 [+] _**[W]**_ [1] _**[x]**_ [ +] _**[ b]**_ [1] _[−]_ _**[b]**_ [1]


= _**x**_ _._ (4.10)


For the activation function, we may choose LeakyReLU



(4.11)
_ax_ ( _x <_ 0) _,_



LeakyReLU( _x_ ) =








_x_ ( _x ≥_ 0)



_ax_ ( _x <_ 0)





where set _a_ = 0 _._ 5 because an extreme value of _a_ (e.g., 0.01) could lead to an extreme


value of gradient for the inverse function. In addition, one may choose activation functions


whose Im( _σ_ ) _̸_ = R, such as tanh. However, in that case, we must ensure that the input


value to the pseudoinverse decoder is in Im( _σ_ ) (in case of tanh, it is ( _−_ 1 _,_ 1)); otherwise,


the computation would be invalid.


4.3.2 N EUMANN B OUNDARY M ODEL


Matsunaga et al. (2020) proposed a wall boundary model to deal with Neumann bound

ary conditions for the LSMPS method (Tamai & Koshizuka, 2014) (Section 2.2.4.3), a


framework to solve PDEs using particles. The LSMPS method is the origin of the IsoGCN’s


gradient operator, so one can imagine that the wall boundary model may introduce a so

phisticated treatment of Neumann boundary conditions into IsoGCN. We modified the wall




# Page 112

**88** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


boundary model to adapt to the situation where the vertices are on the Neumann boundary,


which differs from the situation of particle simulations.


4.3.2.1 D EFINITION OF N EUMANN I SO GCN (NI SO GCN)


Our formulation of IsoGCN with Neumann boundary conditions, which is termed _Neu-_


_mannIsoGCN_ (NIsoGCN), is expressed as:


NIsoGCN 0 _→_ 1 ( _**H**_ [(0)] )



$"



_j∈N_ _i_



:= EquivariantPointwiseMLP



!



_**M**_ _i−_ 1
#Y _j∈N_ _i_



_**h**_ [(0)] _j_ _−_ _**h**_ [(0)] _j_ _**x**_ _j_ _−_ _**x**_ _i_
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _[w]_ _[ij]_ [ +] _[ w]_ _[i]_ _**[n]**_ _[i]_ _**[g]**_ [ˆ] _[i]_



_**M**_ _i_ :=
Y

_l∈N_ _i_



(4.12)


_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
(4.13)
_∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[w]_ _[ij]_ [ +] _[ w]_ _[i]_ _**[n]**_ _[i]_ _[ ⊗]_ _**[n]**_ _[i]_ _[,]_



where ˆ _**g**_ _i_ is the encoded value of the Neumann boundary condition at _**x**_ _i_ and _w_ _i_ _>_ 0 is


an untrainable parameter to control the strength of the Neumann constraint. As _w_ _i_ _→∞_,


the model strictly satisfies the given Neumann condition in the direction _**n**_ _i_, while the


directional derivatives in the direction of ( _**x**_ _j_ _−_ _**x**_ _i_ ) tend to be relatively neglected. Thus,


we keep the value of _w_ _i_ moderate to consider derivatives in both _**n**_ and _**x**_ directions. In


particular, we set _w_ _i_ = 10 _._ 0, assuming that around ten vertices may virtually exist ”outside”


the boundary on a flat surface in a 3D space.


NIsoGCN is a straightforward generalization of the original IsoGCN by letting _**n**_ _i_ = **0**


when _**x**_ _i_ _/∈_ _∂_ Ω Neumann . This model can also be generalized to vectors or higher rank


tensors, similarly to the original IsoGCN’s construction. Therefore, NIsoGCN can express


any spatial differential operator, constituting _D_ in PDEs.


4.3.2.2 D ERIVATION OF NI SO GCN


Matsunaga et al. (2020) derived a gradient model that can treat the Neumann boundary


condition with an arbitrary convergence rate with regard to spatial resolution. Here, we


derive our gradient model, i.e., NIsoGCN, in a different way to simplify the discussion


because we only need the first-order approximation for fast computation.




# Page 113

4.3. Method **89**


Before deriving NIsoGCN, we review introductory linear algebra using simple norma
tion. Using a orthonormal basis _**e**_ _j_ _∈_ R _[d]_ _**e**_ _j_ _·_ _**e**_ _k_ = _δ_ _jk_ _nj_ =1 [, one can decompose a vector]


_**v**_ _∈_ R _[n]_ using:


_**v**_ = Y ( _**v**_ _·_ _**e**_ _j_ ) _**e**_ _j_ _._ (4.14)

_j_


Now, consider replacing the basis _{_ _**e**_ _j_ _∈_ R _[n]_ _}_ _[n]_ _j_ =1 [with a set of vectors] _**[ B]**_ [ =] _[ {]_ _**[b]**_ _[j]_ _[∈]_

R _[n]_ _}_ _[n]_ _j_ =1 _[′]_ [, called a] _[ frame]_ [, that spans the space but is not necessarily independent (thus,] _[ n]_ _[′]_ _[ ≥]_


_n_ ). Using the frame, one can assume _**v**_ is decomposed as:


_**v**_ = Y ( _**v**_ _·_ _**b**_ _j_ ) _**Ab**_ _j_ _,_ (4.15)

_j_


where _**A**_ _∈_ R _[n][×][n]_ is a matrix that corrects the ”overcount” that may occur using the frame


(for instance, consider expanding (1 _,_ 0) _[⊤]_ with the frame _{_ (1 _,_ 0) _[⊤]_ _,_ ( _−_ 1 _,_ 0) _[⊤]_ _,_ (0 _,_ 1) _[⊤]_ _}_ ). A

set _{_ _**Ab**_ _j_ _}_ _[d]_ _j_ =0 _[′]_ [is called a] _[ dual frame]_ [ for] _**[ B]**_ [. Recalling Equation 2.122, we can find the]


concrete form of _**A**_ considering:


_**v**_ = _**A**_ Y ( _**v**_ _·_ _**b**_ _j_ ) _**b**_ _j_

_j_

= _**A**_ Y ( _**b**_ _j_ _⊗_ _**b**_ _j_ ) _**v**_ _._ (4.16)

_j_


Requiring that Equation 4.16 holds for any _**v**_ _∈_ R _[d]_, one can conclude _**A**_ = [Q] _j_ [(] _**[b]**_ _[j]_ _[ ⊗]_ _**[b]**_ _[j]_ [)] _[−]_ [1] [.]


Then, we obtain



_−_ 1
Y ( _**v**_ _·_ _**b**_ _j_ ) _**b**_ _j_ _._ (4.17)
$ _j_



_**v**_ =



_**b**_ _l_ _⊗_ _**b**_ _l_

#Y _l_



For more details on frames, see, e.g., Han et al. (2007).


Now, we can derive NIsoGCN at the _i_ th vertex on the Neumann boundary, by letting



_**x**_ _j_ _−_ _**x**_ _i_
_**B**_ = _√_ ~~_w_~~ _ij_
 _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_



_∪{_ _[√]_ ~~_w_~~ _i_ _**n**_ _i_ _}._ (4.18)

 _j∈N_ _i_




# Page 114

**90** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


In addition, we assume the approximated gradient of a scalar field _u_ at the _i_ th vertex, _⟨∇u⟩_ _i_,


satisfies the following conditions:


_**x**_ _j_ _−_ _**x**_ _i_ _u_ _j_ _−_ _u_ _i_
_⟨∇u⟩_ _i_ _·_ _[√]_ ~~_w_~~ _ij_ ( _j ∈N_ _i_ ) (4.19)
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_ [=] _[ √]_ ~~_[w]_~~ _[ij]_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_


_⟨∇u⟩_ _i_ _·_ _[√]_ ~~_w_~~ _i_ ~~_**n**_~~ _i_ = _[√]_ ~~_w_~~ _i_ _g_ ˆ _i_ _._ (4.20)


Equation 4.19 is a natural assumption because we expect the directional derivative in the


direction of ( _**x**_ _j_ _k_ _−_ _**x**_ _i_ ) _/∥_ _**x**_ _j_ _k_ _−_ _**x**_ _i_ _∥_ should correspond to the slope of _u_ in the same direction.


Equation 4.20 is the Neumann boundary condition, which we want to satisfy. Finally,


by substituting Equations 4.18, 4.19, and 4.20 into Equation 4.17, we obtain the gradient


model considering the Neumann boundry consition as:



#Y _l∈N_ _i_



$ _−_ 1



_⟨u⟩_ _i_ =



_l∈N_ _i_



_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
_√_ ~~_w_~~ _il_
_∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗√]_ ~~_[w]_~~ _[il]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_



+ _[√]_ ~~_w_~~ _i_ _g_ ˆ _i_ _√_ ~~_w_~~ _i_ _**n**_ _i_




$



_×_



#Y _j_



_u_ _j_ _−_ _u_ _i_ _**x**_ _j_ _−_ _**x**_ _i_
_√_ ~~_w_~~ _ij_ _√_ ~~_w_~~ _ij_
 _**x**_ _j_ _−_ _**x**_ _i_ _∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_



$ _−_ 1



=



_**x**_ _l_ _−_ _**x**_ _i_ _**x**_ _l_ _−_ _**x**_ _i_
_w_ _il_

#Y _l∈N_ _i_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_ _[⊗]_ _∥_ _**x**_ _l_ _−_ _**x**_ _i_ _∥_



$



_**x**_ _j_ _−_ _**x**_ _i_
_∥_ _**x**_ _j_ _−_ _**x**_ _i_ _∥_



+ _w_ _i_ _g_ ˆ _i_ _**n**_ _i_




_×_



#Y _j_



_u_ _j_ _−_ _u_ _i_
_w_ _ij_
 _**x**_ _j_ _−_ _**x**_ _i_



_._ (4.21)



If we apply the gradient model to a encoded features, we obtain the gradient model in the


NIsoGCN layer, i.e., Equation 4.12. Similar to the Dirichlet encoder and pseudoinverse


decoder, we could define the specific encoder and decoder for the Neumann boundary


condition. However, this is not included in the contributions of our work because it does


not improve the performance of our model, which may be because the Neumann boundary


condition is a soft constraint in contrast to the Dirichlet one and expressive power seems


more important than that inductive bias.




# Page 115

4.3. Method **91**


4.3.2.3 G ENERALIZATION OF NI SO GCN


To apply NIsoGCN to _**H**_ [(] _[p]_ [)], a rank _p_ discrete tensor field ( _p ≥_ 1), one can recursively


define the operation as:



NIsoGCN _p−_ 1 _→p_ ( _**H**_ :;:;1 [(] _[p]_ [)] _..._ [)]

NIsoGCN _p−_ 1 _→p_ ( _**H**_ :;:;2 [(] _[p]_ [)] _..._ [)]

NIsoGCN _p−_ 1 _→p_ ( _**H**_ :;:;3 [(] _[p]_ [)] _..._ [)]





 (4.22)
 _[,]_



NIsoGCN _p→p_ +1 ( _**H**_ [(] _[p]_ [)] ) :=











where _**H**_ :;:; [(] _[p]_ [)] _i..._ _[∈]_ [R] _[|V|×][d]_ [feature] _[×][n]_ _[p][−]_ [1] [ is the] _[ i]_ [th component of] _**[ H]**_ [(] _[p]_ [)] [ regarding the first spatial]


index, resulting in the rank ( _p_ _−_ 1) discrete tensor field. In case of a three-dimensional rank


one discrete tensor field _**H**_ [(1)], it can be formulated as:



_∂_ _**H**_ [(1)] _∂_ _**H**_ [(1)] _∂_ _**H**_ [(1)]
:;:;1 _[/∂x]_ :;:;1 _[/∂y]_ :;:;1 _[/∂z]_
E F E F E F

_∂_ _**H**_ [(1)] _∂_ _**H**_ [(1)] _∂_ _**H**_ [(1)]
:;:;2 _[/∂x]_ :;:;2 _[/∂y]_ :;:;2 _[/∂z]_
E F E F E F

_∂_ _**H**_ [(1)] _∂_ _**H**_ [(1)] _∂_ _**H**_ [(1)]
:;:;3 _[/∂x]_ :;:;3 _[/∂y]_ :;:;3 _[/∂z]_
E F E F E F






 (4.23)













NIsoGCN 1 _→_ 2 ( _**H**_ [(1)] ) :=


_≈_


















NIsoGCN 0 _→_ 1 ( _**H**_ :;:;1 [(1)] [)]

NIsoGCN 0 _→_ 1 ( _**H**_ :;:;2 [(1)] [)]

NIsoGCN 0 _→_ 1 ( _**H**_ :;:;3 [(1)] [)]



= _∇⊗_ _**H**_ [(1)] _,_ (4.24)


which corresponds to the Jacobian tensor field of _**H**_ [(1)] . Similarly, NIsoGCN to decrease


tensor rank can be defined as:


NIsoGCN _p→p−_ 1 ( _**H**_ [(] _[p]_ [)] ) :=NIsoGCN _p−_ 1 _→p_ ( _**H**_ :;:;1 [(] _[p]_ [)] _..._ [)]

+ NIsoGCN _p−_ 1 _→p_ ( _**H**_ :;:;2 [(] _[p]_ [)] _..._ [)]

+ NIsoGCN _p−_ 1 _→p_ ( _**H**_ :;:;3 [(] _[p]_ [)] _..._ [)] _[.]_ (4.25)


As discussed in Section 3.3.4.1, IsoGCNs (NIsoGCNs) correspond to spatial differen

tial operators. Because NIsoGCN contains a learnable neural network (Equation 4.12),


the component learns to predict the derivative of the corresponding tensor rank in an en



# Page 116

**92** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


coded space. This feature of NIsoGCNs enables us to construct machine learning models


corresponding to PDE in the encoded space.


4.3.3 N EURAL N ONLINEAR S OLVER


4.3.3.1 I MPLICIT E ULER M ETHOD IN E NCODED S PACE


As reviewed in Section 2.2.1, one can regard solving PDEs as optimization. To con

struct a neural PDE solver using the implicit Euler method in a high-dimensional encoded


space, we first define the residual and the nonlinear problem in the encoded space based on


Equation 2.63 as:


_**R**_ NIsoGCN ( _**H**_ _[′]_ ) := _**H**_ _[′]_ _−_ _**H**_ ( _t_ ) _−D_ NIsoGCN ( _**H**_ _[′]_ )∆ _t_ (4.26)


Solve _[′]_ _**H**_ _**[R]**_ [NIsoGCN] [(] _**[H]**_ _[′]_ [) =] **[0]** _[,]_ (4.27)


where _**H**_ ( _t_ ) and _**H**_ _[′]_ are discrete tensor fields, and _D_ NIsoGCN is an E( _n_ )-equivariant GNN


reflecting the structure of _D_ using differential operators provided by NIsoGCN (See Sec

tion 4.4 for the concrete examples of _D_ NIsoGCN ). Equation 4.27 corresponds to solving a


PDE in a high-dimensional encoded space, where we can utilize the expressibility of neural


networks.


One may consider solving Equation 4.27 by using the Newton–Raphson method. How

ever, it may consume huge memory because we embed the input feature into a high

dimensional space, resulting in a large matrix to solve. In addition, we must use GPUs


to accelerate the training of models, which makes memory limitation more strict. Fur

thermore, solving linear systems makes the computation graph extremely long, leading to


unstable backpropagation. There are various existing studies to challenge this type of prob

lem, e.g., Neural ODE (Chen et al., 2018) and implicit GNN (Gu et al., 2020). Besides,


adopting limited-memory quasi-Newton methods (e.g., Liu & Nocedal (1989)) might be in

teresting as they are supposed to facilitate incorporating global interactions. Nevertheless,


we applied the gradient descent method in this research for simplicity and computational


efficiency. Based on Equation 2.70, gradient descent in the encoded space can be expressed




# Page 117

as:



4.3. Method **93**


_**H**_ [[0]] := _**H**_ ( _t_ ) (4.28)


_**H**_ [[] _[i]_ [+1]] := _**H**_ [[] _[i]_ []] _−_ _α_ [[] _[i]_ []] _**R**_ NIsoGCN ( _**H**_ [[] _[i]_ []] ) _i >_ 0 _,_ (4.29)



where _**H**_ [[] _[i]_ []] denotes the approximated solution at _i_ th step of the iterative nonlinear solver


(as in Section 2.2.3), not a rank- _i_ discrete tensor field.


4.3.3.2 B ARZILAI –B ORWEIN M ETHOD FOR N EURAL N ONLINEAR S OLVER


As discussed in Section 2.2.3.3, _α_ [[] _[i]_ []] are determined by the line search, requiring addi

tional computational resource. However, using a small constant value of _α_ results in the


explicit Euler method, which corresponds to simply stacking the GNN layers. Therefore,


we adopt the Barzilai–Borwein method (Barzilai & Borwein, 1988) to approximate _α_ [[] _[i]_ []] in


Equation 4.29. In our case, by applying Equation 2.81, the step size _α_ [[] _[i]_ []] of gradient descent


is approximated as:



_α_ [[] _[i]_ []] _≈_ _α_ [[] _[i]_ []]
BB [:=]



 _**H**_ [[] _[i]_ []] _−_ _**H**_ [[] _[i][−]_ [1]] [] _·_  _**R**_ NIsoGCN ( _**H**_ [[] _[i]_ []] ) _−_ _**R**_ NIsoGCN ( _**H**_ [[] _[i][−]_ [1]] ) 

_._ (4.30)
_∥_ _**R**_ NIsoGCN ( _**H**_ [[] _[i]_ []] ) _−_ _**R**_ NIsoGCN ( _**H**_ [[] _[i][−]_ [1]] ) _∥_ [2]



Here, _·_ denotes the inner product between two discrete tensor fields with the same shape,


i.e.:


_**H**_ [(] _[p]_ [)] _·_ _**G**_ [(] _[p]_ [)] = Y _H_ _i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_ _G_ _i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_ _∈_ R _,_ (4.31)

_igk_ 1 _k_ 2 _...k_ _p_


for rank- _p_ discrete tensor fields _**H**_ [(] _[p]_ [)] and _**G**_ [(] _[p]_ [)] . Besides, _∥_ _**H**_ _∥_ [2] := _**H**_ _·_ _**H**_ . The inner


product used here corresponds to that for rank- _p_ continuous tensor fields, _⟨_ _**h**_ _,_ _**g**_ _⟩_ (where


_**h**_ _,_ _**g**_ : Ω _→_ R _[d]_ [feature] _[×][n]_ _[p]_ ), because:


_⟨_ _**h**_ _,_ _**g**_ _⟩_ = _**h**_ ( _**x**_ ) _·_ _**g**_ ( _**x**_ ) _d_ Ω( _**x**_ ) (4.32)

[ Ω

_≈_ Y _**h**_ ( _**x**_ _i_ ) _·_ _**g**_ ( _**x**_ _i_ ) _V_ _i_ (4.33)


_i_

= Y _H_ _i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_ _G_ _i_ ; _g_ ; _k_ 1 _k_ 2 _...k_ _p_ _V_ _i_ [effective] _,_ (4.34)

_igk_ 1 _k_ 2 _...k_ _p_




# Page 118

**94** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


wherer _V_ _i_ [effective] denotes the effective volume of the _i_ th vertex (Equation 3.74). One must


note that _α_ BB defined here is E( _n_ )-invariant because it is computed using the contraction


between tensors. Therefore, the gradient descent update:


_**H**_ [[] _[i]_ [+1]] := _**H**_ [[] _[i]_ []] _−_ _α_ BB [[] _[i]_ []] _**[R]**_ [NIsoGCN] [(] _**[H]**_ [[] _[i]_ []] [)] (4.35)


is E( _n_ )-equivariant.


In addition, one can see that computing _α_ BB [[] _[i]_ []] [corresponds to global pooling because the]


inner product is taken all over the mesh (graph). With that view, one can find similarities


between Equation 4.35 and deep sets (Zaheer et al., 2017). A deep set layer is expressed


as:


DeepSet( _**H**_ ) := _σ_  _λ_ _**H**_ + _γ_ **1** _|V|_ GlobalPooling( _**H**_ )  _,_ (4.36)


where _λ_ and _γ_ are trainable parameters, GlobalPooling : R _[|V|×][d]_ [feature] _[×][n]_ _[p]_ _→_ R [1] _[×][d]_ [feature] _[×][n]_ _[p]_


denotes an operation that aggregates all information in a graph, such as max, mean, and


sum, and **1** = (1 _,_ 1 _, . . .,_ 1) _[T]_ _∈_ R _[|V|×]_ [1] . Deep set is a successful method to learn point cloud


data and has a strong background regarding permutation equivariance. However, E( _n_ )

equivariance is not considered in their model. Our gradient descent update (Equation 4.35)


successfully incorporate the strength of the deep set model with E( _n_ )-equivariance and


interpretability in terms of the implicit Euler method.


4.3.3.3 F ORMULATION OF N EURAL N ONLINEAR S OLVER


Our aim is to use Equation 4.35, approximating the nonlinear differential operator


_D_ in Equation 2.60 with NIsoGCN. By doing this, we expect the processor, the core of


the encode-decode-processor Architecture, to consider both local and global information,


which may have an advantage over simply stacking GNNs corresponding to the explicit


method as discussed in Section 2.2.2. Combinations of solvers and neural networks are


already suggested in, e.g., NeuralODE (Chen et al., 2018). The novelty of our study is the


extension of existing methods for solving PDEs with spatial structure and the incorporation


of global pooling into the solver in an E( _n_ )-equivariant way, enabling us to capture global


interaction, which we refer to as the _neural nonlinear solver_ .




# Page 119

4.4. Numerical Experiments **95**


Finally, the update from the state at the _i_ th iteration _**H**_ [[] _[i]_ []] to the ( _i_ + 1)th in the neural


nonlinear solver is expressed as:


_**H**_ [[] _[i]_ [+1]] = DirichletLayer  _**H**_ [[] _[i]_ []] _−_ _α_ BB [[] _[i]_ []]  _**H**_ [[] _[i]_ []] _−_ _**H**_ [[0]] _−D_ NIsoGCN ( _**H**_ [[] _[i]_ []] )∆ _t_  [] _,_ (4.37)


where _**H**_ [[0]] is the encoded _**U**_ ( _t_ ). Here, Equation 4.37 enforces hidden features to satisfy


the encoded PDE, including boundary conditions, motivating us to call our model _physics-_


_embedded neural networks_ because it embeds physics (PDEs) in the model rather than in


the loss.


4.4 N UMERICAL E XPERIMENTS


Using numerical experiments, we demonstrate the proposed model’s validity, express

ibility, and computational efficiency. We use three types of datasets:


1. the gradient dataset to verify the correctness of NIsoGCN; and


2. the advection-diffusion dataset to demonstrate capacity of the model for various


PDE parameters; and


3. the incompressible flow dataset to demonstrate the speed and accuracy of the model.


We also present ablation study results to corroborate the effectiveness of the proposed


method. The implementation of our model is based on the original IsoGCN’s code. [1] Our


implementation is available online. [2]


4.4.1 G RADIENT D ATASET


As done in Section 3.4.1, we conducted experiments to predict the gradient field from


a given scalar field to verify the expressive power of NIsoGCN.


4.4.1.1 T AKS D EFINITION


We generated cuboid-shaped meshes randomly with 10 to 20 cells in the _X_, _Y_, and _Z_


directions. We then generated random scalar fields over these meshes using polynomials of


1 [https://github.com/yellowshippo/isogcn-iclr2021, Apache License 2.0.](https://github.com/yellowshippo/isogcn-iclr2021)
2 [https://github.com/yellowshippo/penn-neurips2022, Apache License 2.0.](https://github.com/yellowshippo/penn-neurips2022)




# Page 120

**96** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


degree 10 and computed their gradient fields analytically. Our training, validation, and test


datasets consisted of 100 samples.


4.4.1.2 M ODEL A RCHITECTURE


Figure 4.2 shows the architectures we used for the gradient dataset. The dataset is up

loaded online. [3] We followed the instruction of Horie et al. (2021) (in particular, Appendix


D.1 of their paper) to make the features and models equivariant. To facilitate a fair compar

ison, we made input information for both models equivalent, except for _**M**_ _[−]_ [1] in Equation


Equation 4.13, which is a part of our novelty. For both models, we used Adam (Kingma &


Ba, 2014) as an optimizer with the default setting. Training for both models took around


ten minutes using one GPU (NVIDIA A100 for NVLink 40GiB HBM2). Figure 4.2 shows


model architectures used for the experiment.



(a)



(b)








|, gˆ|Col2|n|Col4|
|---|---|---|---|
|||||
|MLP<br>2, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|MLP<br>2, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|MLP<br>2, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|MLP<br>2, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|
|||||
|IsoGCN<br>16, 16<br>Identity|IsoGCN<br>16, 16<br>Identity|IsoGCN<br>16, 16<br>Identity|IsoGCN<br>16, 16<br>Identity|
|||||
|Concatenation|Concatenation|Concatenation|Concatenation|
|||||
|MLP<br>17, 1<br>Identity|MLP<br>17, 1<br>Identity|MLP<br>17, 1<br>Identity|MLP<br>17, 1<br>Identity|
|||||
|_r _|_r _|_r _|_r _|


|Col1|Col2|M −1|Col4|
|---|---|---|---|
|||||
|MLP<br>1, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|MLP<br>1, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|MLP<br>1, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|MLP<br>1, 8, 16, 16<br>LeakyReLU, LeakyReLU, Identity|
|||||
|NIsoGCN<br>16, 16<br>Identity|NIsoGCN<br>16, 16<br>Identity|NIsoGCN<br>16, 16<br>Identity|NIsoGCN<br>16, 16<br>Identity|
|||||
|MLP<br>1, 16<br>Identity|MLP<br>1, 16<br>Identity|MLP<br>1, 16<br>Identity|MLP<br>1, 16<br>Identity|
|||||
|_r _|_r _|_r _|_r _|



Figure 4.2: Architecture used for (a) original IsoGCN and (b) NIsoGCN training. In each


trainable cell, we put the number of units in each layer along with the activation functions


used.


3 [https://savanna.ritc.jp/˜horiem/penn_neurips2022/data/grad/grad_data.](https://savanna.ritc.jp/~horiem/penn_neurips2022/data/grad/grad_data.tar.gz)

[tar.gz](https://savanna.ritc.jp/~horiem/penn_neurips2022/data/grad/grad_data.tar.gz)




# Page 121

4.4. Numerical Experiments **97**


4.4.1.3 R ESULTS


Table 4.1 and Figure 4.3 show that the proposed NIsoGCN improves gradient predic

tion, especially near the boundary, showing that our model successfully considers Neumann


boundary conditions.


Table 4.1: MSE loss ( _±_ the standard error of the mean) on test dataset of gradient predic

tion. ˆ _g_ Neumann is the loss computed only on the boundary where the Neuman condition is


set.


Method _∇φ_ ( _×_ 10 _[−]_ [3] ) _g_ ˆ Neumann ( _×_ 10 _[−]_ [3] )


Original IsoGCN 192 _._ 72 _±_ 1 _._ 69 1390 _._ 95 _±_ 7 _._ 93


**NIsoGCN** (Ours) 6 _._ 70 _±_ 0 _._ 15 3 _._ 52 _±_ 0 _._ 02

立方体内部の矢量場を示した図で、立方体の各辺に平行な矢量が存在し、各矢量の大きさは同じであることが特徴的です。矢量は立方体全体に均一に分布しており、向きも一致しています。

図は3D直方体の内部を示しています。矢印は直方体内に均一に分布し、各点の矢印の向きと大きさは一致しています。これにより、直立方体内のベクトル場が均一であることが示されています。

立方体内部の矢量場を示した図で、矢印の向きは立方体の各面の法線方向に一致し、大きさは立方体内の位置に応じて変化しています。立方体中央付近では矢量の大きさが最大で、四角形の四辺に近づくと矢量が徐々に弱まります。

等高線/等値線図は、3D物体の表面の高低を表す図法です。軸は水平方向（x軸）と垂直方向（y軸）、値は表面の高さを示します。等高線上の高低は、表面の傾斜度を反映し、重要な領域（例：最大値や最小値の所在）を示すために、高低の区別が重要です。

画像は立方体の立体図示で、灰色の平面が立方体の面を示しています。立方体の各辺は白色の線で描かれており、平面と立方体の接点は灰色の平面と白色の線の交点で示されています。右側には色調の色板が表示されており、色板の色は灰色から白い順番に変化しています。


Ground truth Original IsoGCN NIsoGCN

ヒートマップの軸は「Gradient magnitude（梯度の大きさ）」で、0.0e+00から4.00e00の範囲を示しています。高集中領域は右上 quadrant（赤色）に位置し、低濃度領域は左下 quadrant（青色）です。中央に「1.5」の値が目立たず、周囲は「0.5」と「2.0」の間で均一に分布しています。

このグラフは「Difference of gradient magnitude（勾配のmagnitudeの差）」を表しています。縦軸は0から3.0e+00（30）までの値を示し、横軸には変数名がありません。色の深浅は勾配magnitudeの大小を反映し、最大値30に近い深紫色が目立つピークを示しています。全体の傾向は右上に右肩上がりで、最大差30が右端に位置しています。


Figure 4.3: Gradient field (top) and the magnitude of error between the predicted gradient


and the ground truth (bottom) of a test data sample, sliced on the center of the mesh.




# Page 122

**98** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.4.2 A DVECTION -D IFFUSION D ATASET


To test the generalization ability of PENNs regarding PDE’s parameters and time series,


we run an experiment with the advection-diffusion dataset.


4.4.2.1 T ASK D EFINITION


The governing equation regarding the temperature field _T_ used for the experiment is


expressed as:





 ( _t,_ _**x**_ ) _∈_ (0 _,_ 1) _×_ Ω (4.38)
 _[· ∇][T]_ [ +] _[ D][∇· ∇][T]_



_∂T_

_∂t_ [=] _[ −][c]_











1


0


0



_T_ ( _t_ = 0 _,_ _**x**_ ) = 0 _**x**_ _∈_ Ω (4.39)


_T_ = _T_ [ˆ] ( _t,_ _**x**_ ) _∈_ _∂_ Ω Dirichlet (4.40)


_∇T ·_ _**n**_ = 0 ( _t,_ _**x**_ ) _∈_ _∂_ Ω Neumann _,_ (4.41)


where _c ∈_ R is the magnitude of a known velocity field, and _D ∈_ R is the diffusion


coefficient. We set Ω= _{_ _**x**_ _∈_ R [3] _|_ 0 _< x_ 1 _<_ 1 _∧_ 0 _< x_ 2 _<_ 1 _∧_ 0 _< x_ 3 _<_ 0 _._ 01 _}_,


_∂_ Ω Dirichlet = _{_ _**x**_ _∈_ _∂_ Ω _| x_ 1 = 0 _}_ and _∂_ Ω Neumann = _∂_ Ω _\ ∂_ Ω Dirichlet .


4.4.2.2 D ATASET


We varied _c_ and _D_ from 0.0 to 1.0, eliminating the condition _c_ = _D_ = 0 _._ 0 because

nothing drives the phenomena, and and varied _T_ [ˆ] from 0.1 to 1.0 with ∆ _t_ = 10 _[−]_ [3] We


generated fine meshes, ran numerical analysis with a classical solver, OpenFOAM, [4] and


interpolated the obtained temperature fields onto coarser meshes so that we can obtain


high-quality ground truth data. We split the generated data into training, validation, and


test dataset containing 960, 120, and 120 samples. The dataset is uploaded online. [5]


4 [https://www.openfoam.com/](https://www.openfoam.com/)
5 [https://savanna.ritc.jp/˜horiem/penn_neurips2022/data/ad/ad_](https://savanna.ritc.jp/~horiem/penn_neurips2022/data/ad/ad_preprocessed.tar.gz)

[preprocessed.tar.gz](https://savanna.ritc.jp/~horiem/penn_neurips2022/data/ad/ad_preprocessed.tar.gz)




# Page 123

4.4. Numerical Experiments **99**


4.4.2.3 M ODEL A RCHITECTURE


The strategy to construct PENN for the advection-diffusion dataset is consistent with


one for the incompressible flow dataset (see Section 4.4.3.3). The input features of the


model are:


   - _T_ ( _t_ = 0 _._ 0): The initial temperature field


   - _T_ [ˆ] : The Dirichlet boundary condition for the temperature field


   - ( _c,_ 0 _,_ 0) _[⊤]_ : The velocity field


   - _c_ : The magnitude of the velocity


   - _D_ : The diffusion coefficient


   - _e_ _[−]_ [0] _[.]_ [5] _[d]_ _, e_ _[−]_ [1] _[.]_ [0] _[d]_ _, e_ _[−]_ [2] _[.]_ [0] _[d]_ : Features computed from _d_, the distance from the Dirichlet


boundary


and the output features are:


   - _T_ ( _t_ = 0 _._ 25): The temperature field at _t_ = 0 _._ 25


   - _T_ ( _t_ = 0 _._ 50): The temperature field at _t_ = 0 _._ 50


   - _T_ ( _t_ = 0 _._ 75): The temperature field at _t_ = 0 _._ 75


   - _T_ ( _t_ = 1 _._ 00): The temperature field at _t_ = 1 _._ 00


The encoded governing equation is expressed as:


_**H**_ _T_ ( _t_ + ∆ _t_ ) = _**H**_ _T_ ( _t_ ) + _D_ NIsoGCN;A   - D ( _**H**_ _T_ ) ( _t_ + ∆ _t_ ) (4.42)


_D_ NIsoGCN;A  - D ( _**H**_ _T_ ) : = _−_ _**H**_ _**c**_ _·_ NIsoGCN 0 _→_ 1 ( _**H**_ _T_ ) + _**H**_ _D_ NIsoGCN 0 _→_ 1 _→_ 0 ( _**H**_ _T_ ) _,_


(4.43)


where encoded discrete tensor fields corresponds to the following:


   - _**H**_ _T_ : Encoded rank-0 discrete tensor field of _T_


   - _**H**_ _D_ : Encoded rank-0 discrete tensor field of _c_, _D_, _e_ _[−]_ [0] _[.]_ [5] _[d]_, _e_ _[−]_ [1] _[.]_ [0] _[d]_, and _e_ _[−]_ [2] _[.]_ [0] _[d]_




# Page 124

**100** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


   - _**H**_ _**c**_ : Encoded rank-1 discrete tensor field of _**c**_


The corresponding neural nonlinear solver is:


_**H**_ _T_ [[] _[i]_ [+1]] = _**H**_ _T_ [[] _[i]_ []] _[−]_ _[α]_ BB [[] _[i]_ []] _**H**_ _T_ [[] _[i]_ []] _[−]_ _**[H]**_ _T_ [[0]] _[−D]_ [NIsoGCN;A] [-] [D] [(] _**[H]**_ _T_ [[] _[i]_ []] [)∆] _[t]_ _,_ (4.44)
i j


Because the task is to predict time series data, we adopt autoregressive architecture for


the nonlinear neural solver, i.e., input the output of the solver of the previous step (which


is in the encoded space) to predict the encoded feature of the next step (see Figure 4.4).


Figures 4.5 and 4.6 present the detailed architecture of the PENN model for the advection

diffusion dataset experiment.


To confirm the PENN’s effectiveness, we ran the ablation study on the following set

tings:


(A) Without encoded boundary: In the nonlinear loop, we decode features to apply


boundary conditions to fulfill Dirichlet conditions in the original physical space


(B) Without boundary condition in the neural nonlinear solver: We removed the Dirich

let layer in the nonlinear loop. Instead, we added the Dirichlet layer after the (non

pseudoinverse) decoder.


(C) Without neural nonlinear solver: We removed the nonlinear solver from the model


and used the explicit time-stepping instead


(D) Without boundary condition input: We removed the boundary condition from input


features


(E) Without Dirichlet layer: We removed the Dirichlet layer. Instead, we let the model


learn to satisfy boundary conditions during training.


(F) Without pseudoinverse decoder: We removed the pseudoinverse decoder and used


simple MLPs for decoders.


(G) Without pseudoinverse decoder with Dirichlet boundary layer after decoding: Same


as above, but with Dirichlet layer after decoding.




# Page 125

4.4. Numerical Experiments **101**


The training is performed for up to ten hours using the Adam optimizer for each setting.


|T(t = 0.00)|Col2|
|---|---|
|Encoding||






|T95S+aPn34vy8f/cNCzw=<ltexi>H (t = 0.00)<br>T|Col2|
|---|---|
|||
|||



フローチャートの開始は「Neural Nonlinear Solver」で、終了は「T(t = 1.00)」です。主要な分岐は、各時間ステップ（t = 0.25、0.50など）で「H_T(t)」を計算し、それから「Decoding」を経て「T」を推定する処理です。















Figure 4.4: The concept of the neural nonlinear solver for time series data with autoregres

sive architecture. The solver’s output is fed to the same solver to obtain the state at the next


time step (bold red arrow). Please note that this architecture can be applied to arbitrary


time series lengths.




# Page 126

**102** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method



_T_ ( _t_ = 0 _._ 00) _T_ ˆ ( _c,_ 0 _,_ 0) _[>]_










|T(t = 0.00)|Col2|
|---|---|
|||


|Tˆ|Col2|
|---|---|
|||


|c NPK879/fyDGprM=<latexi>D e−0.5d e−1.0d e−2.0d|Col2|
|---|---|
|||
















|(c, 0, 0)>|Col2|
|---|---|
|||
|MLP<br>1, 64, 64<br>tanh, Identity|MLP<br>1, 64, 64<br>tanh, Identity|
|||









|MLP *1 MLP MLP<br>BoundaryEncoder<br>1, 16, 64 1, 64, 64 5, 64, 64<br>(Weight share with *1)<br>LeakyReLU, Identity tanh, Identity tanh, Identity<br>H[0 ](t = 0.00)<br>H[0 ](t) T<br>T<br>H T[i] b9X/uf1t6P+vjVNqTpsrzgwA7LE<laexi>Hˆ T H c H D<br>Neural Nonlinear Solver<br>H[i+1]<br>T<br>After 8 iterations<br>Dirichlet Layer|MLP<br>5, 64, 64<br>tanh, Identity|Col3|
|---|---|---|
|BoundaryEncoder<br>(Weight share with *1)<br>Neural Nonlinear Solver<br>After 8 iterations<br>MLP<br>1, 16, 64<br>LeakyReLU, Identity<br>*1<br>MLP<br>1, 64, 64<br>tanh, Identity<br>MLP<br>5, 64, 64<br>tanh, Identity<br>Dirichlet Layer<br>**_H_**[_i_]<br>_T_<br>**_H_**[_i_+1]<br>_T_<br>**_H_**[0]<br>_T_ (_t_ = 0_._00)<br>**_H_**[0]<br>_T_ (_t_)<br> ˆ<br>**_H_**_T_<br>**_Hc_**<br>**_H_**_D_|||
||||


画像には「Pseudoinverse decoder（Weight share with *1）」というブロックが示されており、その下に「T(t = 0.25)」「T(t=0.50)」「T(=0.75)」と「T(=1.00)」という数値が並んでいます。この図は、Pseudoinverseデコーダの入力信号「T(t)」の値を示している様子です。

Figure 4.5: The overview of the PENN architecture for the advection-diffusion dataset.


Gray boxes with continuous (dotted) lines are trainable (untrainable) components. Arrows


with dotted lines correspond to the loop. In each trainable cell, we put the number of units


in each layer along with the activation functions used. The bold red arrow corresponds to


the one in Figure 4.4.




# Page 127

フローチャートの開始は「H_T」から始まり、主要な分岐は「MLP」と「Dirichlet Layer」です。処理の流れは、MLPを経過した後は「NIsoGCN_0→1→0」に進み、DIRICHLET LAYERを通じて「H_c」と「H_D」に分岐し、それらを加算し、最後に「Calculate Eq (4.30)」へと繋がります。



4.4. Numerical Experiments **103**















_−_ NIsoGCN 0 _!_ 1 ( _**H**_ _T_ [)]







_−_ _**H**_ _**c**_ _·_ NIsoGCN 0 _!_ 1 ( _**H**_ _T_ [[] _[i]_ []] [)]















_T_ [[] _[i]_ []] [) =:] _[ D]_ [NIsoGCN;A] _[−]_ [D] [(] _**[H]**_ _T_ [[] _[i]_ []]



_T_ [)]

























Figure 4.6: The overview of the PENN architecture for the advection-diffusion dataset.


Gray boxes with continuous (dotted) lines are trainable (untrainable) components. In each


trainable cell, we put the number of units in each layer along with the activation functions


used.




# Page 128

**104** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.4.2.4 R ESULTS


Table 4.2 presents the results of the ablation study. We found that the PENN model with


all the proposed components achieved the best performance, showing that all the compo

nents we introduced contributed to performance. Because the boundary condition applied


is relatively simple compared to the incompressible flow dataset (Section 4.4.3), the con

figuration without the Dirichlet layer (Model (E)) showed the second best performance;


however, the fulfillment of the Dirichlet condition of that model is not rigorous.


Figures 4.7, 4.8, and 4.9 show the visual comparison of the prediction with the PENN


model against the ground truth. As seen in the figures, one can see that our model is


capable of predicting time series under various boundary conditions and PDE parameters,


e.g., pure advection (Figure 4.7), pure diffusion (Figure 4.8), and mixed advection and


diffusion (Figure 4.9).


Table 4.2: MSE loss ( _±_ the standard error of the mean) on test dataset of the advection

diffusion dataset.


ˆ
Method _T_ ( _×_ 10 _[−]_ [4] ) _T_ Dirichlet ( _×_ 10 _[−]_ [4] )


(A) Without encoded boundary 54 _._ 191 _±_ 6 _._ 36 0 _._ 0000 _±_ 0 _._ 0000


(B) Without boundary condition
390 _._ 828 _±_ 24 _._ 58 0 _._ 0000 _±_ 0 _._ 0000
in the neural nonlinear solver


(C) Without neural nonlinear solver 6 _._ 630 _±_ 1 _._ 21 0 _._ 0000 _±_ 0 _._ 0000


(D) Without boundary condition input 465 _._ 492 _±_ 26 _._ 47 868 _._ 7009 _±_ 15 _._ 5447


(E) Without Dirichlet layer 2 _._ 860 _±_ 2 _._ 46 1 _._ 1703 _±_ 0 _._ 0328


(F) Without pseudoinverse decoder 44 _._ 947 _±_ 6 _._ 00 9 _._ 7130 _±_ 0 _._ 1201


(G) Without pseudoinverse decoder
4 _._ 907 _±_ 4 _._ 87 0 _._ 0000 _±_ 0 _._ 0000
with Dirichlet layer after decoding


**PENN** **1** _**.**_ **795** _±_ 1 _._ 33 0 _._ 0000 _±_ 0 _._ 0000




# Page 129

4.4. Numerical Experiments **105**

ヒートマップの横軸は「t = 0.25」を示し、縦軸には格子線が描かれています。左側に緑色の領域が現れ、右側には深蓝色の区域が広がっています。緑の領域は左端に集中し、右端まで延びています。右側の深蓝色区域は左側の緑域と対比し、左端から右端にかけて均一に分布しています。

ヒートマップの軸は縦軸と横軸で、緑色から青色に色が薄くなる方向を示す。高域集中領域は左上隅に位置し、低域は右下隅に分布。右上隅には明るい青色の帯状パターンが目立つ。

ヒートマップの横軸は「t = 0.50」を示しています。左側は緑色で、右側は深蓝色で、境界線が明確に区別されています。緑の領域は左側に広がり、深蓝色は右側に集中しています。この配置から、左側の緑が右側の深蓝色へと徐々に変化している様子が示されています。

ヒートマップの軸は横軸と縦軸で、緑色と青色が高域、赤色が低域を示します。右上角に緑と青の領域が広がり、左下角に青と赤の領域があります。中央に青色と赤色の境界が明確に分かれています。

ヒートマップの横軸は「t = 0.75」を示し、縦軸には格子線が描かれています。左半分は緑色で、右半分が青色です。青色の領域は右端に位置し、左端から右端まで一定の範囲に延びています。この分布から、右端の青色領域が高値の集中領域であることが推測されます。

ヒートマップの軸は横軸と縦軸で、左から右、上から下に位置づけられています。高値域は緑色、中間値は青色、低値領域は黄色と赤色に分かれています。右端と上端に赤色が広がり、左端と下端に青色が集まっています。右上隅に黄色の区域が目立っています。

ヒートマップの横軸は「Temperature（温度）」を示しています。左側の図では、温度が0.0から1.0の範囲で緑色が広がり、右側では緑が薄く、右端に薄い青色の領域が現れています。右図は左図と同様に温度軸を示し、緑の分布と右端の青色領域が一致しています。

ヒートマップの横軸は「Temperature（温度）」です。左から右へ温度が上昇します。右端に「1.0」と刻まれ、左端には「0.0」と刻まれています。

高域（緑色）と低域（青色・深青色）が明確に区別され、右端の高域が目立っています。左端の低域は薄い青色で、中央から右に広がる青色域が特徴的です。


Figure 4.7: Visual comparison on a test sample between (left) ground truth obtained from


OpenFOAM computation with fine spatial-temporal resolution and (right) prediction by

PENN. Here, _c_ = 0 _._ 9, _D_ = 0 _._ 0, and _T_ [ˆ] = 0 _._ 4.




# Page 130

**106** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method

ヒートマップの横軸は「t = 0.25」を示し、縦軸には格子線が描かれています。左側は緑色で、右側は深蓝色に色が変化しています。左から右へと色が深く濃くなる様子が目立っています。

ヒートマップの軸は横軸と縦軸で、緑色から深蓝色に色が変化しています。高域集中領域は左上隅と右下隅に位置し、低域は中央から右上に分布しています。右上隅に「2023」の数字が目立っています。

ヒートマップの横軸は「t = 0.50」を示し、縦軸には格子線が描かれています。左側の緑色領域は低値域で、右側の深蓝色領域は高値区域に集中しています。中央の青色領域が中間値を示しています。全体的に左から右へ値が上昇する傾向が見られます。

ヒートマップの軸は横軸と縦軸で、緑色から青色に色が深くなるように配置されています。高値域は右上隅に集中的に分布し、左下隅には低値領域が広がっています。中央部分には目立たない平坦な区域が存在します。

ヒートマップの横軸は「t = 0.75」を示し、縦軸には緑色から青色、再到深蓝色の色段階が存在します。左端（緑）から右端（深blue）に移動する過程で、色の濃度が徐々に低下し、右端に集中的に深蓝色が広がっています。この様子は、時間tが0から1に近づくにつれて、特定の領域（右端）に熱量（濃度）が高まっていくことを示しています。

ヒートマップの軸は横軸と縦軸で、緑色から青色に色が深まる順序で数字を示しています。高値域は右上 quadrant（右上隅）に集中的に、左下 quadrant（左下隅）は低値領域に分布しています。中央部分は色が薄く、値の変動が見られません。

ヒートマップの横軸は「温度」を示し、縦軸には時間（t = 1.00）を表します。左側の緑色領域は温度が低く、右側の深蓝色領域は高温域です。左から右へ温度が徐々に上昇する傾向が見られます。

ヒートマップの軸は「Temperature（温度）」で、0.0から1.0の範囲を示しています。高温度域（緑色）は右上隅に集中的に分布し、左下隅（低温度域）は青色で広がっています。中央部分（茶色）が中程度の温度を示し、周囲の色差が目立たない状況です。


Figure 4.8: Visual comparison on a test sample between (left) ground truth obtained from


OpenFOAM computation with fine spatial-temporal resolution and (right) prediction by

PENN. Here, _c_ = 0 _._ 0, _D_ = 0 _._ 4, and _T_ [ˆ] = 0 _._ 3.




# Page 131

4.4. Numerical Experiments **107**

ヒートマップの横軸は「t = 0.25」を示し、縦軸に格子線が配置されています。左から右に色が変化し、赤色から黄色、緑色、青色、深蓝色へと移動します。右端の深蓝色領域が最も高値域に集中し、左端の赤色領域が最低値領域に集中しています。中央の青色領域は中間値を示す位置に位置しています。

ヒートマップの軸は縦と横の格子線で構成され、左上から右下への色の変化を示しています。高値域は右上隅から左下隅にかけて、右上部が最も高めで、左下部が低めに分布しています。左上隅と右下隅は深蓝色で、中央部分は緑色から黄色色に色段階的に変化しています。

ヒートマップの横軸は「t = 0.50」を示し、縦軸には格子線が配置されています。左端から右端にかけて、赤色から青緑色に色が変化し、色の深浅に応じて値の高低が示されています。右端の色が最も深く、左端が最も浅く、この色の変化に従って高値域と低値域能見分けることができます。

ヒートマップの軸は横軸と縦軸で、色の深浅が値の大小を示します。高値域は赤色・橙色に集中し、低温域は青色・緑色に集まります。右上角の赤色区域が最高値領域で、左下角の青色領域が最低値区域に位置しています。

ヒートマップの横軸は「t = 0.75」を示し、縦軸には格子線が配置されています。左端から右端にかけて、赤色から緑色に色が変化しています。右端の緑地帯が最も高値域に集中し、左端の赤色地帶が低値領域に位置しています。中央から右にかけての橙黄色帯は中間値を示しています。

ヒートマップの軸は横軸と縦軸で、緑色から赤色に色が変化します。高値域は右上隅に集まり、左下隅が低値領域です。中央に黄色の帯が現れ、その周囲に緑と赤の色が交互に分布しています。

ヒートマップの横軸は「温度」を示し、縦軸には「t = 1.00」が記載されています。色の濃度は温度の高低を反映し、左から右へ温度が上昇する傾向が見られます。右端の色が最も鮮やかで、温度の高い領域が示されています。

ヒートマップの軸は「Temperature（温度）」で、0.0から1.0の範囲を示しています。高温度域は右端の黄色から橙色に移行し、左端の赤色に近い黄色域が低温度域です。中央の橙色帯は温度の変化が緩やかに現れています。


Figure 4.9: Visual comparison on a test sample between (left) ground truth obtained from


OpenFOAM computation with fine spatial-temporal resolution and (right) prediction by

PENN. Here, _c_ = 0 _._ 6, _D_ = 0 _._ 3, and _T_ [ˆ] = 0 _._ 8.




# Page 132

**108** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.4.3 I NCOMPRESSIBLE F LOW D ATASET


We tested the expressive power our model by learning incompressible flow in complex


shapes.


4.4.3.1 T ASK D EFINITION


The incompressible Navier–Stokes equations, the governing equations of incompress

ible flow, are expressed as:



_∂_ _**u**_



( _t,_ _**x**_ ) _∈_ (0 _, T_ ) _×_ Ω (4.45)
Re _[∇· ∇]_ _**[u]**_ _[ −∇][p]_



_∂_ _**u**_ [1]

_∂t_ [=] _[ −]_ [(] _**[u]**_ _[ · ∇]_ [)] _**[u]**_ [ +]



_**u**_ = ˆ _**u**_ ( _t,_ _**x**_ ) _∈_ _∂_ Ω [(] Dirichlet _**[u]**_ [)] (4.46)
 _∇_ _**u**_ + ( _∇_ _**u**_ ) _[T]_ [] _**n**_ = **0** ( _t,_ _**x**_ ) _∈_ _∂_ Ω [(] Neumann _**[u]**_ [)] _[.]_ (4.47)


We also consider the following incompressible condition:


_∇·_ _**u**_ = 0 ( _t,_ _**x**_ ) _∈_ (0 _, T_ ) _×_ Ω _,_ (4.48)


which may be problematic when solving these equations numerically. Therefore, it is com

mon to divide the equations into two: one to obtain pressure and one to compute velocity.


There are many methods to make such a division; for instance, the fractional step method


derives the Poisson equation for pressure as follows:


_∇· ∇p_ ( _t_ + ∆ _t,_ _**x**_ ) = [1] (4.49)

∆ _t_ [(] _[∇·]_ [ ˜] _**[u]**_ [)(] _[t,]_ _**[ x]**_ [)] _[,]_


where


˜
_**u**_ = _**u**_ _−_ ∆ _t_ _**u**_ _· ∇_ _**u**_ _−_ [1] (4.50)
 Re _[∇· ∇]_ _**[u]**_ 


is called the intermediate velocity. Once we solve the equation, we can compute the time


evolution of velocity as follows:


_**u**_ ( _t_ + ∆ _t,_ _**x**_ ) = ˜ _**u**_ ( _t,_ _**x**_ ) _−_ ∆ _t∇p_ ( _t_ + ∆ _t,_ _**x**_ ) _._ (4.51)




# Page 133

4.4. Numerical Experiments **109**


Because the fractional step method requires solving the Poisson equation for pressure,


we also need the boundary conditions for pressure as well:


_p_ = 0 ( _t,_ _**x**_ ) _∈_ _∂_ Ω [(] Dirichlet _[p]_ [)] (4.52)


_∇p ·_ _**n**_ = 0 ( _t,_ _**x**_ ) _∈_ _∂_ Ω [(] Neumann _[p]_ [)] _[.]_ (4.53)


Our machine learning task is also based on the same assumption: motivating pressure pre

diction in addition to velocity with boundary conditions of both. The task was to predict


flow velocity and pressure fields at _t_ = 4 _._ 0 using information available before numerical


analysis, e.g., initial conditions and the geometries of the meshes.


4.4.3.2 D ATASET


To generate the dataset, we first generated pseudo-2D shapes, with one cell in the Z


direction, by changing design parameters, starting from three template shapes. Thereafter,


we performed numerical analysis using OpenFOAM [6] with ∆ _t_ = 10 _[−]_ [3], and the initial


conditions were the solutions of potential flow, which can be computed quickly and stably


using the classical solver. The linear solvers used were generalized geometric-algebraic


multi-grid for _p_ and the smooth solver with the Gauss–Siedel smoother for _**u**_ .


To confirm the expressive power of the proposed model, we used coarse input meshes


for machine learning models. We generated these coarse meshes by setting cell sizes


roughly four times larger than the original numerical analysis. We obtained ground truth


variables using interpolation. Training, validation, and test datasets consisted of 203, 25,


and 25 samples, respectively. We generated the dataset by randomly rotating and translat

ing test samples to monitor the generalization ability of machine learning models.


We generated numerical analysis results using various shapes of the computational do

main, starting from three template shapes and changing their design parameters as shown


in Figure 4.10. For each design parameter, we varied from 0 to 1.0 with a step size of 0.1,


yielding 11 shapes for type A and 121 shapes for type B and C. The boundary conditions


were set as shown in Figures 4.11 and 4.12. These design and boundary conditions were


6 [https://www.openfoam.com/](https://www.openfoam.com/)




# Page 134

**110** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


chosen to have the characteristic length of 1.0 and flow speed of 1.0. The viscosity was set


to 10 _[−]_ [3], resulting in Reynolds number Re _∼_ 10 [3] .


The linear solvers used were generalized geometric-algebraic multi-grid for _p_ and the


smooth solver with the Gauss–Siedel smoother for _**u**_ . Numerical analysis to generate each


sample took up to one hour using CPU one core (Intel Xeon CPU E5-2695 v2@2.40GHz).


The dataset is uploaded online. [7]



画像はIntel Xeon CPU E5-2695 v2 @ 2.60GHzの単一コアの動作を示すブロック図です。図面上に灰色の矩形が示され、各矩形には「a1」や「b2」という文字が記載され、矩形の左右方向に青い矢印が示されています。矩形の高さは1.0と示されています。

画像は3つのブロックA、B、Cを示しています。各ブロックは縦1.0、横1.0の長方形で、AとBには水平方向の矢印a1、b1、b2が存在し、Cには垂直方向の矢巻きが示されています。

図Bと図Cは灰色の図形を基にし、図Bには「b1」と「b2」、図Cには「c1」と「c2」の単位が示されています。両図には上下の矢印と左右の矢印が存在し、矢印の方向と単位は図の左下の座標系に従って示されています。





図Bと図Cは、1.0の高さの灰色矩形を基準に、図Bでは「b1」方向に右向きの青色矢印、図Cでは「c1」方向と「c2」方向に各1.0長さの青色右向き矢印を示す。左下に座標軸「x」「y」「z」を示した。









Figure 4.10: Three template shapes used to generate the dataset. _a_ 1, _b_ 1, _b_ 2, _c_ 1, and _c_ 2 are


the design parameters.


7 [https://savanna.ritc.jp/˜horiem/penn_neurips2022/data/fluid/fluid_](https://savanna.ritc.jp/~horiem/penn_neurips2022/data/fluid/fluid_data.tar.gz.parta[a-e])

[data.tar.gz.parta[a-e]](https://savanna.ritc.jp/~horiem/penn_neurips2022/data/fluid/fluid_data.tar.gz.parta[a-e])




# Page 135

4.4. Numerical Experiments **111**



画像は流体の境界条件を示す図で、図Aと図Bの境界面上に「u = 0」を示し、境界面上の法線方向に「[∇u + (∇u)ᵀ] n = 0」という条件を示しています。図AはL型の境界面、図Bは矩形の境界面を表しています。









画像は3種類の形状（A、B、C）を示し、各形状の境界面上に「∇u + (∇u)ᵀn = 0」という式が書かれている。形状Aは矩形で、形状BはT字型で、形状Cは長方形で、境界面上の「n」は法線方向を示している。

図Bと図Cは、灰色背景の図形を基にした図示で、図Bは「u = 0」の条件を満たす図形で「[∇u + (∇u)ᵀn = 0]」の式が示されています。図Cも同様の条件と式が示され、左下に座標軸の図示が存在します。

図面上に灰色の図形が表示され、図形の周囲に橙色の線が描かれており、各図形に「u = 0」の文字が書かれています。右側には「[∇u + (∇u)ᵀ]n = 0」という式が示されています。左下には「u = (1, 0, 0)ᵀ」の文字と、X、Y、Z軸を示した座標系の図が描かれています。

































and dotted lines correspond to Dirichlet and Neumann boundaries.



図面上に灰色の図形が示されており、図形の周囲には「∇p・n = 0」と「p = 0」の文字が書かれています。この図形は流体力学の境界条件を表しており、周囲の法線方向（n）と流体の速度勾配（∇p）の内積がゼロになることを示しています。





図Aは単純な図形を示し、図Bと図Cは同じ図形の2種類を示しています。各図の右側に「p = 0」の文字が表示され、左側に「∇p・n = 0」という式が示されています。

図Bと図Cは、灰色背景の図形で囲まれた領域を示し、図Bの図域の右端に「p = 0」の文字が表示され、図Cの左端に同様の文字が示されています。図の左下隅には、X軸とY軸を表す矢印が描かれています。





図面上に灰色の図形が示され、図形の周囲に赤い虚線が描かれており「p = 0」と「∇p・n = 0」の条件が記載されています。左下に座標軸（x、y、z）の矢印が示されています。この図は「p」に関する条件を用いてデータセットを生成するための主な要素と関係を示しています。

and dotted lines correspond to Dirichlet and Neumann boundaries.




# Page 136

**112** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.4.3.3 M ACHINE L EARNING M ODELS


We constructed the PENN model corresponding to the incompressible Navier–Stokes


equation. In particular, we adopted the fractional step method, where the pressure field was


also obtained as a PDE solution along with the velocity field. We encoded each feature in a


4, 8, or 16-dimensional space. After features were encoded, we applied a neural nonlinear


solver containing NIsoGCNs and Dirichlet layers, reflecting the fractional step method


(See Equations 4.50 and 4.51). Inside the nonlinear solver’s loop, we had a subloop that


solved the Poisson equation for pressure, which also reflected the considered PDE (See


Equation 4.49). We looped the solver for pressure five times and four or eight times for


velocity. After these loops stopped, we decoded the hidden features to obtain predictions


for velocity and pressure, using the corresponding pseudoinverse decoders.


For the state-of-the-art baseline model, we selected MP-PDE (Brandstetter et al., 2022)


as it also provides a way to deal with boundary conditions. We used the authors’ code [8]


with minimum modification to adapt to the task. We tested various time window sizes such


as 2, 4, 10, and 20, where one step corresponds to time step size ∆ _t_ = 0 _._ 1. With changes


in time window size, we changed the number of hops considered in one operation of the


GNN of the baseline to have almost the same number of hops visible from the model when


predicting the state at _t_ = 4 _._ 0. The numbers of hidden features, 32, 64, and 128, were


tested. All models were trained for up to 24 hours using one GPU (NVIDIA A100 for


NVLink 40GiB HBM2).


The strategy to construct PENN for the incompressible flow dataset is the following:


   - Consider the encoded version of the governing equation


   - Apply the neural nonlinear solver containing the Dirichlet layer and the NIsoGCN


to the encoded equation


   - Decode the hidden feature using the pseudoinverse decoder.


Reflecting the fractional step method, we build PENN using spatial differential operators


provided by NIsoGCN. We use a simple linear encoder for the velocity and the associated


Dirichlet boundary conditions. For pressure and its Dirichlet constraint, we use a simple


8 [https://github.com/brandstetter-johannes/MP-Neural-PDE-Solvers](https://github.com/brandstetter-johannes/MP-Neural-PDE-Solvers)




# Page 137

4.4. Numerical Experiments **113**


MLP with one hidden layer. We encode each feature in a 16-dimensional space. After fea

tures are encoded, we apply a neural nonlinear solver containing NIsoGCNs and Dirichlet


layers, reflecting the fractional step method (Equations 4.50 and 4.51).


The encoded equations are expressed as:


[NIsoGCN 1 _→_ 0 _◦_ NIsoGCN 0 _→_ 1 ( _**H**_ _p_ )]( _t_ + ∆ _t,_ _**x**_ )



= [1]

∆ _t_



NIsoGCN 1 _→_ 0 _**H**_ ˜ _**u**_ ( _t,_ _**x**_ ) (4.54)
i  j



_**H**_ ˜ _**u**_ := _**H**_ _**u**_ _−_ ∆ _t_ _**H**_ _**u**_ _·_ NIsoGCN 1 _→_ 2 ( _**H**_ _**u**_ )


_−_ [1]

(4.55)
Re [NIsoGCN] [2] _[→]_ [1] _[ ◦]_ [NIsoGCN] [1] _[→]_ [2] [ (] _**[H]**_ _**[u]**_ [)] 

_**H**_ _**u**_ ( _t_ + ∆ _t,_ _**x**_ ) = _**H**_ [˜] _**u**_ ( _t,_ _**x**_ ) _−_ ∆ _t_ NIsoGCN 0 _→_ 1 ( _**H**_ _p_ ) ( _t_ + ∆ _t,_ _**x**_ ) _,_ (4.56)


where _**H**_ _**u**_ is the encoded rank-1 discrete tensor field of _**u**_ and _**H**_ _p_ is the encoded rank-0


discrete tensor field of _p_ . Note that these equations correspond to Equations 4.49, 4.50,


and 4.51, by regarding IsoGCNs as spatial derivative operators. The corresponding neural


nonlinear solvers are expressed as:


_**H**_ _**u**_ [[] _[i]_ [+1]] = _**H**_ _**u**_ [[] _[i]_ []] _[−]_ _[α]_ BB [[] _[i]_ []]  _**H**_ _**u**_ [[] _[i]_ [)]] _[−]_ _**[H]**_ _**u**_ [(0)] _[−D]_ [NIsoGCN;NS]  _**H**_ _**u**_ [[] _[i]_ [)]] _[,]_ _**[ H]**_ _p_ [[] _[i]_ [+1]]  ∆ _t_  (4.57)


_D_ NIsoGCN;NS  _**H**_ _**u**_ [[] _[i]_ []] _[,]_ _**[ H]**_ _p_ [[] _[i]_ [+1]]  := _**H**_ _**u**_ [[] _[i]_ []] _[·]_ [ NIsoGCN] [1] _[→]_ [2]  _**H**_ _**u**_ [[] _[i]_ []] 




for _**H**_ _**u**_ and



_−_ [1] _**H**_ [[] _[i]_ []]

 _**u**_ 
Re [NIsoGCN] [2] _[→]_ [1] _[ ◦]_ [NIsoGCN] [1] _[→]_ [2]

+ NIsoGCN  _**H**_ _p_ [[] _[i]_ [+1]]  [] _,_ (4.58)


_**H**_ _p_ [[] _[i]_ [;] _[j]_ [+1]] = _**H**_ _p_ [[] _[i]_ [;] _[j]_ []] _−_ _α_ BB [[] _[i]_ [;] _[j]_ []] _[D]_ [NIsoGCN;pressure] [(] _**[H]**_ _p_ [[] _[i]_ [;] _[j]_ []] ) (4.59)



1
_D_ _**H**_ [[] _[i]_ [;] _[j]_ []] : = _**H**_ [(;] _[,j]_ [)]
NIsoGCN;pressure  _p_  ∆ _t_ [NIsoGCN] [1] _[→]_ [0] _[ ◦]_ [NIsoGCN] [0] _[→]_ [1]  _p_ 




ˆ

_−_ [1] _**h**_ [[] _**u**_ _[i]_ []] _,_ (4.60)

∆ _t_ [NIsoGCN] [1] _[→]_ [0]   []




# Page 138

**114** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


for _**H**_ _p_, where _**H**_ _**u**_ [[0]] [=] _**[ H]**_ _**u**_ [(] _[t]_ [)][,] _**[ H]**_ _p_ [[0;0]] = _**H**_ _p_ ( _t_ ), and _**H**_ _p_ [[] _[i]_ [;0]] = _**H**_ _p_ [[] _[i]_ []] [. Figures 4.13, 4.14, and]


4.15 present the PENN model architecture used for the incompressible flow dataset.


The input features of the model are:


   - _**u**_ ( _t_ = 0 _._ 0): The initial velocity field, the solulsion of potential flow


  - ˆ _**u**_ : The Dirichlet boundary condition for velocity


   - _p_ ( _t_ = 0 _._ 0): The initial pressure field


   - ˆ _p_ : The Dirichlet boundary condition for pressure


   - _e_ _[−]_ [0] _[.]_ [5] _[d]_ _, e_ _[−]_ [1] _[.]_ [0] _[d]_ _, e_ _[−]_ [2] _[.]_ [0] _[d]_ : Features computed from _d_, the distance from the wall bound

ary condition


and the output features are:


   - _**u**_ ( _t_ = 4 _._ 0): The velocity field at _t_ = 4 _._ 0


   - _p_ ( _t_ = 4 _._ 0): The pressure field at _t_ = 4 _._ 0


As seen in Figure 4.14, we have a subloop that solves the Poisson equation for pressure


in the nonlinear solver’s loop for velocity. We looped the solver for pressure five times and


eight times for velocity. After these loops stopped, we decoded the hidden features to obtain


predictions for velocity and pressure, using the corresponding pseudoinverse decoders.


To facilitate the smoothness of pressure and velocity fields, we apply GCN layers cor

responding to numerical viscosity in the standard numerical analysis method. Here, please


note that the PENN model consists of components that accept arbitrary input lengths, e.g.,


pointwise MLPs, deep sets, and NIsoGCNs. Thanks to the model’s flexibility, we can apply


the same model to arbitrary meshes similar to other GNNs.


4.4.3.4 T RAINING D ETAILS


Because the neural nonlinear solver applies the same layers many times during the loop,


the model behaved somehow similar to recurrent neural networks during training, which


could cause instability. To avoid such unwanted behavior, we simply retried training by


reducing the learning rate of the Adam optimizer by a factor of 0.5. We found our way of




# Page 139

4.4. Numerical Experiments **115**



ブロック図の主要コンポーネントは、MLP（多層パーソナルニューラルネットワーク）、境界エンコーダ（Boundary Encoder）、IsogCN（Isotropic Graph Convolutional Network）、ディリクレ層（Dirichlet Layer）、擬逆解碼器（Pseudoinverse decoder）で構成されています。信号の入出力関係は、入力信号u(t=0.0)とû(t)をMLP1（1, 16）で処理し、出力信号H[u]^[0]とĤ[u]^[i]を生成します。同様にp(t)とp̃(t)=e^{-0.5d}e^{-1.0d}-e^{-2.0}dの信号もMLP2（1、8、16）、Boundary Encoder（Weight share with *2）を経過し、H[p]^[[0]]とH^{\hat{p}}_p^[i+1]を出力します。これらの信号は、Neural Nonlinear Solverに送り込まれ、8回の iteration 后にH[u]^{\hat{i+1}}とH[p]^{\tilde{i}}が生成されます。次に、各信号はディリクリッド層を通じて再処理会され、最後にU(t=4.0)=u(t)、P(t)=p(t)=U(t)の形式で出力されます。



ブロック図の上部に「u(t = 0.0)」という入力信号があり、この信号はMLP（多層パーセプトロン）に送られます。MLPの入力層は1個で、出力層には16個のニューラル要素が存在し、この層は「Identity」（単純な線形変換）として機能します。





ブロック図の上部に「\(\hat{u}\)」という信号が入力され、その信号は「BoundaryEncoder（Weight share with *1）」というコンポーネントに送られる。BoundaryEncoderはこの信号を処理し、出力する関係が示されています。






























|H[0]<br>u|Col2|
|---|---|
|||


|Col1|Col2|
|---|---|
|||



























Figure 4.13: The overview of the PENN architecture for the incompressible flow dataset.


Gray boxes with continuous (dotted) lines are trainable (untrainable) components. Arrows


with dotted lines correspond to the loop. In each trainable cell, we put the number of units


in each layer along with the activation functions used.


training useful compared to using the learning rate schedule because sometimes the loss


value of PENN can be extremely high, resulting in difficulty to reach convergence with


a lower learning rate after such an explosion. Therefore, we applied early stopping and


restarted training using a lower learning rate from the epoch with the best validation loss.


Our initial learning rate was 5 _._ 0 _×_ 10 _[−]_ [4], and we restarted the training twice, which


was done automatically, within the 24-hour training period of PENN. For the ablation


study, we used the same setting for all models. For PENN and ablation models, we used


Adam (Kingma & Ba, 2014) as an optimizer. For MP-PDE solvers, we used the default


setting written in the paper and the code.




# Page 140

**116** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method



ブロック図の主要コンポーネントは、多層パーソナルニューラルネットワーク（MLP）、ディリクレ層（DirichletLayer）、NISoGCN（Neural Isotropic Spatial Graph Convolutional Network）、ガウシアンカーネル（GCN）などです。信号の入出力関係は、入力層から出力層へと進む際、各層間で「Multiplcation（乗算）」「Concatenation（接合）」「Addition（加算）」などの演算が行われ、最終的に「Neural Nonlinear Solver for Pressure Poisson Equation（圧力ポアソン方程式のニュートラル非線形解法器）」に到達します。
















|Col1|Col2|Col3|
|---|---|---|
||||





























































































































Figure 4.14: The neural nonlinear solver for velocity. Gray boxes with continuous (dot

ted) lines are trainable (untrainable) components. Arrows with dotted lines correspond to


the loop. In each trainable cell, we put the number of units in each layer along with the


activation functions used.




# Page 141

4.4. Numerical Experiments **117**








|H[i;j]<br>p|Col2|
|---|---|
|||


|Hˆ<br>p|Col2|
|---|---|
|||


|Dirichlet Layer|Col2|
|---|---|
|||


|NIsoGCN<br>0→1→0<br>16, 16, 16<br>tanh, Identity|Col2|
|---|---|
||_r · r_**_H_**[_i_<br>_p_|


|1 r :· H˜[i]<br>∆t u|Col2|
|---|---|
|||

















:= _−D_ NIsoGCN;pressure ( _**H**_ _p_ [[] _[i]_ [;] _[j]_ []] )


|Addition|Col2|
|---|---|
||_−_<br>✓<br>_r · r_**_H_**[_i_;_j_]<br>_p_<br>_−_1<br>∆_tr ·_ ˆ<br>**_H_**[_i_]<br>**_u_**<br>◆<br>:=_ −D_|







_p_ )






|Calculate Eq (9)|Col2|
|---|---|
||**_H_**[_i_;_j_]<br>_p_<br>_−↵_[_i_;_j_]<br>BB _D_NIsoGCN;pressure(**_H_**|







Figure 4.15: The neural nonlinear solver for pressure. Gray boxes with continuous (dotted)


lines are trainable (untrainable) components. In each trainable cell, we put the number of


units in each layer along with the activation functions used.




# Page 142

**118** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.4.3.5 R ESULTS


Table 4.3 and Figure 4.16 show the comparison between MP-PDE and PENN. The pre

dictive performances of both models are at almost the same level when evaluated on the


original test dataset. The results show the great expressive power of the MP-PDE model


because we kept most settings at default as much as possible and applied no task-specific


tuning. However, when evaluating them on the transformed dataset, the predictive perfor

mance of MP-PDE significantly degrades. Nevertheless, PENN shows the same loss value


up to the numerical error, confirming our proposed components are compatible with E( _n_ )

equivariance. In addition, PENN exhibits no error on the Dirichlet boundaries, showing


that our treatment of Dirichlet boundary conditions is rigorous.


Figure 4.17 shows the speed-accuracy trade-off for OpenFOAM, MP-PDE, and PENN.


We varied mesh cell size, the time step size, linear sover settings for OpenFOAM to have


different computation speeds and accuracy. The proposed model achieved the best perfor

mance in speed-accuracy trade-off between all the tested methods under fair comparison


conditions.


Table 4.3: MSE loss ( _±_ the standard error of the mean) on test dataset of incompressible


flow. If ”Trans.” is ”Yes,” it means evaluation is done on randomly rotated and transformed


test dataset. ˆ _·_ Dirichlet is the loss computed only on the boundary where the Dirichlet condi

tion is set for each _**u**_ and _p_ . MP-PDE’s results are based on the time window size equaling


40 as it showed the best performance in the tested MP-PDEs. For complete results, see


Table 4.5.


_**u**_ _p_ _**u**_ ˆ Dirichlet _p_ ˆ Dirichlet
Method Trans.
( _×_ 10 _[−]_ [4] ) ( _×_ 10 _[−]_ [3] ) ( _×_ 10 _[−]_ [4] ) ( _×_ 10 _[−]_ [3] )


MP-PDE No **1** _**.**_ **30** _±_ 0 _._ 01 1 _._ 32 _±_ 0 _._ 01 0 _._ 45 _±_ 0 _._ 01 0 _._ 28 _±_ 0 _._ 02

TW = 20

Yes 1953 _._ 62 _±_ 7 _._ 62 281 _._ 86 _±_ 0 _._ 78 924 _._ 73 _±_ 6 _._ 14 202 _._ 97 _±_ 3 _._ 81


No 4 _._ 36 _±_ 0 _._ 03 **1** _**.**_ **17** _±_ 0 _._ 01 **0** _**.**_ **00** _±_ 0 _._ 00 **0** _**.**_ **00** _±_ 0 _._ 00
**PENN** (Ours)

Yes **4** _**.**_ **36** _±_ 0 _._ 03 **1** _**.**_ **17** _±_ 0 _._ 01 **0** _**.**_ **00** _±_ 0 _._ 00 **0** _**.**_ **00** _±_ 0 _._ 00




# Page 143

4.4. Numerical Experiments **119**

ヒートマップの軸は横軸と縦軸で、温度の高低を示します。高温度域は赤色・橙色に、低温域は青色・緑色に分布します。中央に星形の高温度区域が見られ、周囲に低温度域が広がっています。

ヒートマップの軸は横軸と縦軸で、温度の高低を示します。高温度域は赤色・橙色で集中的に、低温域は青色・緑色で分布します。中央に明るい色域が現れ、周囲は明るさの変化が見られます。

ヒートマップの横軸は「時間」を示し、縦軸には「温度」が刻まれています。高温域（赤・橙色）は上部中央に広がり、低温域（青・緑）は下部に集まります。右側の色条は1.0から1.5e+00の温度範囲を示しています。

ヒートマップの軸はX、Y、Zで表され、X軸が右方向、Y軸上方、Z軸下方を示します。高域は赤色で、低域は青色です。中央に黄色と緑色が混在し、周囲に赤色と青色が広がっているため、中心部が高域、周辺が低域のパターンが見られます。

ヒートマップの軸は縦軸と横軸です。高域集中領域は右上部に位置し、低域は左下部に分布しています。中央に目立つ赤色区域が特徴的です。

図は流体の速度場を示しています。矢印の方向は速度の方向を示し、大きさは流速の大きさを示します。特徴的な領域は、矢印が密集した部分で流速が速いことがわかります。

ヒートマップの軸はZ軸とX軸です。高域は緑色、低域は黄色と赤色に分かれ、中心部に青色の高域が集中しています。右上角と左下角に黄色と青色が混在する区域が目立っています。

ヒートマップの軸は横軸と縦軸で、温度の高低を示します。高温度域は緑色、低温度域が黄色から赤色に移行します。各図の中央に藍色の点が目立っており、これが最も高温の集中領域です。右下の図では赤色域が拡大し、中央の藍色点の周囲に赤色が広がっている様子が目立ちます。

ヒートマップの横軸は「1.0e+00」から「0.2」まで、色の深浅が値の大小を示します。各図形の中央に深緑・青色の斑点が現れ、周囲は黄色・橙色に広がり、右上角に赤色の高値域が存在します。


Ground truth MP-PDE (TW=20) PENN (Ours)

ヒートマップの軸は「Velocity magnitude（速度の大きさ）」で、0から1.5e+00（150）までの値を示します。紫色から青緑色に色が変化し、紫色部分は速度が最大（約15）で、色が浅くなるほど速度が減少します。右上角の紫色区域が速度の高集中領域で、左下角の青色区域は速度の低集中領域です。

ヒートマップの軸は「Pressure（圧力）」で、範囲は-1.0e+00（-100）から10.0（10）です。紫色から黄色に色が変化し、紫色は高圧（正の圧）を示し、黄色は低圧を示します。中央に黄色が集中的に分布し、周辺に紫色が広がっています。

ヒートマップの軸はX、Y、Zです。高域は緑・青色、低域は黄色・橙色に分かれ、中央に深青色の高域が現れ、上下に橙色の低域が広がっています。

ヒートマップの軸は横軸と縦軸です。高域集中領域は中部に位置し、低域は上部と下部に分布します。右上角と左下角に目立つ赤色区域が特徴的です。

ヒートマップの軸は「Pressure（圧力）」です。高圧域は黄色・橙色に、中低域は緑・黄緑に、低域（負圧）は青・深青に分布します。中央に深青色の圧低域が目立っています。


Figure 4.16: Comparison of the velocity field (top two rows) and the pressure field (bottom


two rows) without (first and third rows) and with (second and fourth rows) random rotation


and translation. PENN prediction is consistent under rotation and translation due to the


E( _n_ )-equivariance nature of the model, while MP-PDE’s predictive performance degrades


under transformations.




# Page 144

**120** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


10 [3]


10 [2]


10 [1]



このグラフは流体シミュレーションの結果を示しています。横軸は時間（秒）を示し、縦軸には流体の速度（m/s）を表しています。各色の図形は異なるシミュレータ（PENN、MP-PDE、OpenFOAMなど）の出力値を示しており、緑色の「PENN（Ours）」が右下に急激に下落し、紫色の「MP・PDE」が中間でピークを上げて右下方に傾斜します。右上に分布した赤色の三角形は「MP·PDE（Trans.）」の結果で、右上隅に集中的に分布しています。全体而言、PENNの結果は右下方で最大値が現れ、MP・MPDEは中央から右下方へと速度が低下し、MP·MPDE（Transformed）は右上方に分布する傾向が見られます。



10 [0]

10 _[−]_ [4] 10 _[−]_ [3] 10 _[−]_ [2] 10 _[−]_ [1] 10 [0]


Total MSE


Figure 4.17: Comparison of computation time and total MSE loss ( _**u**_ and _p_ ) on the test


dataset (with and without transformation) between OpenFOAM, MP-PDE, and PENN. The


error bar represents the standard error of the mean. All computation was done using one


core of Intel Xeon CPU E5-2695 v2@2.40GHz. Data used to plot this figure are shown in


Tables 4.6, 4.7, and 4.8.




# Page 145

4.4. Numerical Experiments **121**


4.4.3.6 A BLATION S TUDY R ESULTS


Similar to the advection-diffusion dataset case, we validate the effectiveness of our


model through an ablation study on the following settings:


(A) Without encoded boundary: In the nonlinear loop, we decode features to apply


boundary conditions to fulfill Dirichlet conditions in the original physical space


(B) Without boundary condition in the neural nonlinear solver: We removed the Dirich

let layer in the nonlinear loop. Instead, we added the Dirichlet layer after the (non

pseudoinverse) decoder.


(C) Without neural nonlinear solver: We removed the nonlinear solver from the model


and used the explicit time-stepping instead


(D) Without boundary condition input: We removed the boundary condition from input


features


(E) Without Dirichlet layer: We removed the Dirichlet layer. Instead, we let the model


learn to satisfy boundary conditions during training.


(F) Without pseudoinverse decoder: We removed the pseudoinverse decoder and used


simple MLPs for decoders.


(G) Without pseudoinverse decoder with Dirichlet boundary layer after decoding: Same


as above, but with Dirichlet layer after decoding.


Table 4.4 presents the results of the ablation study. Comparison between models with


and without the proposed components shows that the proposed components, i.e., the bound

ary encoder, Dirichlet layer, pseudoinverse decoder, and neural nonlinear solver, signifi

cantly improve the models. The neural nonlinear solver in the encoded space turned out


to have the biggest impact on the performance, while the Dirichlet layer ensured reliable


models that strictly respect Dirichlet boundary conditions.


Comparison with Model (A) shows that the nonlinear loop in the encoded space is in

evitable for machine learning. This result is quite convincing because if the loop is made in




# Page 146

**122** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


the original space, the advantage of the expressive power of the neural networks cannot be


leveraged. Comparison with Model (C) confirms that the concept of the solver is effective


compared to simply stacking GNNs, corresponding to the explicit method.


If the boundary condition input is excluded (Model (D)), the performance degrades in


line with Brandstetter et al. (2022). That model also has an error on the Dirichlet bound

aries. Model (E) shows a similar result, improving performance using the information of


the boundary conditions. If the pseudoinverse decoder is excluded (Model (F)), the out

put may not satisfy the Dirichlet boundary conditions as well. Besides, the decoder has


more effect than expected because PENN is better than Model (G). Both models satisfy


the Dirichlet boundary condition, while PENN has significant improvement. This may be


because the pseudoinverse decoder facilitates the spatial continuity of the outputs in addi

tion to the fulfillment of the Dirichlet boundary condition. In other words, using a simple


decoder and the Dirichlet layer after that may cause spatial discontinuity of outputs. Visual


comparison of part of the ablation study is shown in Figure 4.18.


Table 4.4: Ablation study on the incompressible flow dataset. The value represents MSE


loss ( _±_ standard error of the mean) on the test dataset. ”Divergent” means the implicit


solver does not converge and the loss gets extreme value ( _∼_ 10 [14] ).


_**u**_ _p_ _**u**_ ˆ Dirichlet _p_ ˆ Dirichlet
Method
( _×_ 10 _[−]_ [4] ) ( _×_ 10 _[−]_ [3] ) ( _×_ 10 _[−]_ [4] ) ( _×_ 10 _[−]_ [3] )


Without encoded boundary Divergent Divergent Divergent Divergent


Without boundary condition
65 _._ 10 _±_ 0 _._ 38 21 _._ 70 _±_ 0 _._ 09 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00
in the neural nonlinear solver


Without neural nonlinear solver 31 _._ 03 _±_ 0 _._ 19 9 _._ 81 _±_ 0 _._ 04 **0** _**.**_ **00** _±_ 0 _._ 00 **0** _**.**_ **00** _±_ 0 _._ 00


Without boundary condition input 20 _._ 08 _±_ 0 _._ 21 3 _._ 61 _±_ 0 _._ 02 59 _._ 60 _±_ 0 _._ 89 1 _._ 43 _±_ 0 _._ 05


Without Dirichlet layer 8 _._ 22 _±_ 0 _._ 07 1 _._ 41 _±_ 0 _._ 01 18 _._ 20 _±_ 0 _._ 28 0 _._ 38 _±_ 0 _._ 01


Without pseudoinverse decoder 8 _._ 91 _±_ 0 _._ 06 2 _._ 36 _±_ 0 _._ 02 1 _._ 97 _±_ 0 _._ 06 **0** _**.**_ **00** _±_ 0 _._ 00


Without pseudoinverse decoder
6 _._ 65 _±_ 0 _._ 05 1 _._ 71 _±_ 0 _._ 01 **0** _**.**_ **00** _±_ 0 _._ 00 **0** _**.**_ **00** _±_ 0 _._ 00
with Dirichlet layer after decoding


**PENN** **4** _**.**_ **36** _±_ 0 _._ 03 **1** _**.**_ **17** _±_ 0 _._ 01 **0** _**.**_ **00** _±_ 0 _._ 00 **0** _**.**_ **00** _±_ 0 _._ 00




# Page 147

4.4. Numerical Experiments **123**

ヒートマップの軸は横軸と縦軸です。高域は赤色、低域は青色で表示されます。左図の(i)は水平に広がり、右図(ii)は中央に集中的に高域が見られます。右側の図は縦方向に分布し、中央に青色の点が目立っています。

ヒートマップの軸は横軸と縦軸で、温度の高低を示します。高集中領域は赤・橙色、低領域は緑・青色です。目立つパターンは、左上角・右下角に高温域が集中し、中央に低温域が現れ、周囲に緑色が広がる状態です。

ヒートマップの軸は横軸と縦軸です。高域は赤色、低域は青色で表示されます。各図の中央に明確な赤色斑点が現れ、周囲に青色が広がっている様子が目立っています。

ヒートマップの軸は横軸と縦軸です。高集中領域は赤・橙色域で、低領域は緑・青色域です。目立つパターンは、左上・右下・左下・右上に分布し、中央に集中的な青色区域が見られます。

ヒートマップの軸は横軸と縦軸です。高域は赤色、低域は青色で表示されます。各図の中央に目立つ赤色斑点が見られます。

ヒートマップの軸は横軸と縦軸です。高域集中領域は赤・橙色域で、低域は緑・青色域です。目立つパターンは、縦方向に高域域が広がり、横方向に低域域の中心が移動する様子です。

ヒートマップの軸は「u magnitude（uの大きさ）」です。高集中領域は赤・橙色域で、低集中域は緑・青色域です。右上角に「(iv)」と「(iii)」のラベルがあります。

ヒートマップの軸は「u」と「p」で、色域は1から1.5e+00（1.2）と-1.0e-00到0.8（0.4）の範囲です。高集中領域は左上角の赤色域と右下角の緑色域で、低集中は中央の青色域です。右上角と左下角に明確なパターンが見られます。


Figure 4.18: Visual comparison of the ablation study of (i) ground truth, (ii) the model


without the neural nonlinear solver (Model (C)), (iii) the model without pseudoinverse


decoder with Dirichlet layer after decoding (Model (G)), and (iv) PENN. It can be observed


that PENN improves the prediction smoothness, especially for the velocity field.




# Page 148

**124** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


4.4.3.7 D ETAILED R ESULTS


Table 4.5 presents the detailed results of the comparison between MP-PDE and PENN.


Interestingly, the performance of MP-PDE gets better as the time window size increases.


Therefore, our future direction may be to incorporate MP-PDE’s temporal bundling and


pushforward trick into PENN to enable us to predict the state after a far longer time than


we do in the present work.


Tables 4.6 and 4.7 show the speed and accuracy of the machine learning models tested.


PENN models show excellent performance with a lot smaller number of parameters com

pared to MP-PDE models. It is achieved due to efficient parameter sharing in the proposed


model, e.g., the same weights are used repeatedly in the neural nonlinear encoder. Also, as


pointed out in Ravanbakhsh et al. (2017), there is a strong connection between parameter


sharing and equivariance. PENN has equivariance in, e.g., permutation, time translation,


and E( _n_ ) through parameter sharing, which is in line with them.


Table 4.8 presents the speed and accuracy with various settings of OpenFOAM to seek


a speed-accuracy tradeoff. We tested three configurations of linear solvers:


   - Generalized geometric-algebraic multi-grid (GAMG) for _p_ and the smooth solver


for _**u**_


   - Generalized geometric-algebraic multi-grid (GAMG) for both _p_ and _**u**_


   - The smooth solver for _p_ and _**u**_


In addition, we tested different resolutions for space and time by changing:


   - The number of divisions per unit length: 22.5, 45.0, 90.0


   - Time step size: 0.001, 0.005, 0.010, 0.050


Ground truth is computed using the number of divisions per unit length of 90.0 and time


step size of 0.001; thus, this combination is eliminated from the comparison because the


MSE error is underestimated (in particular, zero).




# Page 149

4.4. Numerical Experiments **125**


Table 4.5: MSE loss ( _±_ the standard error of the mean) on test dataset of incompressible


flow. If ”Trans.” is ”Yes”, it means evaluation on randomly rotated and transformed test


dataset. _n_ denotes the number of hidden features, _r_ denotes the number of iterations in the


neural nonlinear solver used in PENN models, and TW denotes the time window size used


in MP-PDE models.


_**u**_ _p_ _**u**_ ˆ Dirichlet _p_ ˆ Dirichlet
Method Trans.
( _×_ 10 _[−]_ [4] ) ( _×_ 10 _[−]_ [3] ) ( _×_ 10 _[−]_ [4] ) ( _×_ 10 _[−]_ [3] )
PENN No 4 _._ 36 _±_ 0 _._ 03 1 _._ 17 _±_ 0 _._ 01 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

_n_ = 16 _, r_ = 8 Yes 4 _._ 36 _±_ 0 _._ 03 1 _._ 17 _±_ 0 _._ 01 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00
PENN No 29 _._ 09 _±_ 0 _._ 17 11 _._ 35 _±_ 0 _._ 04 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

_n_ = 16 _, r_ = 4 Yes 29 _._ 09 _±_ 0 _._ 17 11 _._ 35 _±_ 0 _._ 04 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00
PENN No 177 _._ 42 _±_ 0 _._ 93 35 _._ 70 _±_ 0 _._ 12 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

_n_ = 8 _, r_ = 8 Yes 177 _._ 42 _±_ 0 _._ 93 35 _._ 70 _±_ 0 _._ 12 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00
PENN No 26 _._ 82 _±_ 0 _._ 16 7 _._ 86 _±_ 0 _._ 03 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

_n_ = 8 _, r_ = 4 Yes 26 _._ 82 _±_ 0 _._ 16 7 _._ 86 _±_ 0 _._ 03 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00
PENN No 92 _._ 80 _±_ 0 _._ 52 31 _._ 47 _±_ 0 _._ 13 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

_n_ = 4 _, r_ = 8 Yes 92 _._ 80 _±_ 0 _._ 52 31 _._ 47 _±_ 0 _._ 13 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

PENN No 120 _._ 35 _±_ 0 _._ 65 35 _._ 53 _±_ 0 _._ 12 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00

_n_ = 4 _, r_ = 4 Yes 120 _._ 35 _±_ 0 _._ 65 35 _._ 53 _±_ 0 _._ 12 0 _._ 00 _±_ 0 _._ 00 0 _._ 00 _±_ 0 _._ 00
MP-PDE No 1 _._ 30 _±_ 0 _._ 01 1 _._ 32 _±_ 0 _._ 01 0 _._ 45 _±_ 0 _._ 01 0 _._ 28 _±_ 0 _._ 02

_n_ = 128 _,_ TW = 20 Yes 1953 _._ 62 _±_ 7 _._ 62 281 _._ 86 _±_ 0 _._ 78 924 _._ 73 _±_ 6 _._ 14 202 _._ 97 _±_ 3 _._ 81
MP-PDE No 12 _._ 08 _±_ 0 _._ 11 6 _._ 49 _±_ 0 _._ 03 1 _._ 36 _±_ 0 _._ 01 2 _._ 57 _±_ 0 _._ 05

_n_ = 128 _,_ TW = 10 Yes 1468 _._ 12 _±_ 5 _._ 75 192 _._ 97 _±_ 0 _._ 57 767 _._ 17 _±_ 4 _._ 36 51 _._ 87 _±_ 1 _._ 07
MP-PDE No 32 _._ 07 _±_ 0 _._ 33 6 _._ 22 _±_ 0 _._ 05 0 _._ 85 _±_ 0 _._ 01 0 _._ 92 _±_ 0 _._ 03

_n_ = 128 _,_ TW = 4 Yes 2068 _._ 99 _±_ 8 _._ 30 180 _._ 54 _±_ 0 _._ 57 284 _._ 72 _±_ 1 _._ 69 59 _._ 21 _±_ 1 _._ 32
MP-PDE No 58 _._ 88 _±_ 0 _._ 60 9 _._ 62 _±_ 0 _._ 07 1 _._ 02 _±_ 0 _._ 02 2 _._ 83 _±_ 0 _._ 10

_n_ = 128 _,_ TW = 2 Yes 1853 _._ 27 _±_ 7 _._ 89 219 _._ 59 _±_ 0 _._ 53 965 _._ 90 _±_ 28 _._ 61 358 _._ 53 _±_ 2 _._ 13

MP-PDE No 6 _._ 09 _±_ 0 _._ 05 5 _._ 39 _±_ 0 _._ 03 1 _._ 65 _±_ 0 _._ 02 2 _._ 16 _±_ 0 _._ 08

_n_ = 64 _,_ TW = 20 Yes 1969 _._ 34 _±_ 7 _._ 50 388 _._ 54 _±_ 1 _._ 12 720 _._ 35 _±_ 5 _._ 15 218 _._ 06 _±_ 8 _._ 01
MP-PDE No 38 _._ 54 _±_ 0 _._ 32 31 _._ 33 _±_ 0 _._ 09 2 _._ 04 _±_ 0 _._ 02 5 _._ 87 _±_ 0 _._ 09

_n_ = 64 _,_ TW = 10 Yes 2738 _._ 84 _±_ 9 _._ 37 171 _._ 32 _±_ 0 _._ 60 417 _._ 57 _±_ 2 _._ 49 28 _._ 34 _±_ 0 _._ 92
MP-PDE No 125 _._ 09 _±_ 1 _._ 11 21 _._ 93 _±_ 0 _._ 09 2 _._ 27 _±_ 0 _._ 03 5 _._ 92 _±_ 0 _._ 16

_n_ = 64 _,_ TW = 2 Yes 1402 _._ 01 _±_ 6 _._ 03 435 _._ 75 _±_ 2 _._ 41 384 _._ 30 _±_ 4 _._ 13 57 _._ 26 _±_ 1 _._ 90
MP-PDE No 32 _._ 46 _±_ 0 _._ 24 17 _._ 40 _±_ 0 _._ 07 5 _._ 92 _±_ 0 _._ 05 5 _._ 94 _±_ 0 _._ 17

_n_ = 32 _,_ TW = 20 Yes 2201 _._ 16 _±_ 7 _._ 59 351 _._ 66 _±_ 0 _._ 82 429 _._ 30 _±_ 3 _._ 27 562 _._ 16 _±_ 11 _._ 62
MP-PDE No 115 _._ 30 _±_ 1 _._ 01 34 _._ 97 _±_ 0 _._ 15 10 _._ 26 _±_ 0 _._ 09 6 _._ 84 _±_ 0 _._ 14

_n_ = 32 _,_ TW = 10 Yes 2824 _._ 76 _±_ 8 _._ 60 496 _._ 33 _±_ 1 _._ 33 2276 _._ 11 _±_ 10 _._ 57 488 _._ 50 _±_ 5 _._ 01
MP-PDE No 272 _._ 73 _±_ 2 _._ 07 94 _._ 27 _±_ 0 _._ 45 11 _._ 50 _±_ 0 _._ 12 35 _._ 76 _±_ 0 _._ 29

_n_ = 32 _,_ TW = 4 Yes 1973 _._ 35 _±_ 8 _._ 29 554 _._ 69 _±_ 4 _._ 26 647 _._ 31 _±_ 7 _._ 40 157 _._ 85 _±_ 8 _._ 41
MP-PDE No 794 _._ 90 _±_ 4 _._ 68 82 _._ 61 _±_ 0 _._ 40 50 _._ 23 _±_ 0 _._ 91 31 _._ 41 _±_ 1 _._ 88

_n_ = 32 _,_ TW = 2 Yes 3240 _._ 69 _±_ 21 _._ 91 443 _._ 10 _±_ 2 _._ 56 2885 _._ 30 _±_ 41 _._ 17 562 _._ 08 _±_ 19 _._ 28




# Page 150

**126** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method


Table 4.6: MSE loss ( _±_ the standard error of the mean) of PENN models on test dataset of


incompressible flow.


# hidden # iteration in Total MSE
# parameter Total time [s]
feature the neural nonlinear solver ( _×_ 10 _[−]_ [3] )


16 8 8,432 1 _._ 61 _±_ 0 _._ 01 5 _._ 33 _±_ 0 _._ 13


16 4 8,432 14 _._ 26 _±_ 0 _._ 03 2 _._ 52 _±_ 0 _._ 06


8 8 2,100 53 _._ 44 _±_ 0 _._ 11 3 _._ 54 _±_ 0 _._ 08


8 4 2,100 10 _._ 54 _±_ 0 _._ 03 2 _._ 16 _±_ 0 _._ 04


4 8 596 40 _._ 75 _±_ 0 _._ 10 2 _._ 86 _±_ 0 _._ 06


4 4 596 47 _._ 57 _±_ 0 _._ 10 1 _._ 35 _±_ 0 _._ 04


Table 4.7: MSE loss ( _±_ the standard error of the mean) of MP-PDE models on test dataset


of incompressible flow.


# hidden Total MSE Total MSE (Trans.)
Time window size # parameter Total time [s]
feature ( _×_ 10 _[−]_ [3] ) ( _×_ 10 _[−]_ [3] )


128 20 709,316 1 _._ 45 _±_ 0 _._ 01 477 _._ 23 _±_ 0 _._ 77 51 _._ 61 _±_ 1 _._ 41


128 10 673,484 7 _._ 70 _±_ 0 _._ 02 339 _._ 78 _±_ 0 _._ 57 94 _._ 01 _±_ 2 _._ 66


128 4 651,972 9 _._ 43 _±_ 0 _._ 04 387 _._ 44 _±_ 0 _._ 71 137 _._ 32 _±_ 3 _._ 91


128 2 644,548 15 _._ 51 _±_ 0 _._ 07 404 _._ 92 _±_ 0 _._ 67 57 _._ 28 _±_ 1 _._ 91


64 20 204,004 6 _._ 00 _±_ 0 _._ 02 585 _._ 48 _±_ 0 _._ 95 13 _._ 62 _±_ 0 _._ 38


64 10 185,356 35 _._ 19 _±_ 0 _._ 07 445 _._ 20 _±_ 0 _._ 79 23 _._ 73 _±_ 0 _._ 67


64 2 174,740 34 _._ 44 _±_ 0 _._ 10 575 _._ 95 _±_ 1 _._ 76 32 _._ 61 _±_ 1 _._ 02


32 20 63,964 20 _._ 64 _±_ 0 _._ 05 571 _._ 77 _±_ 0 _._ 79 7 _._ 64 _±_ 0 _._ 24


32 10 55,348 46 _._ 50 _±_ 0 _._ 13 778 _._ 80 _±_ 1 _._ 12 12 _._ 93 _±_ 0 _._ 39


32 4 49,948 121 _._ 55 _±_ 0 _._ 35 752 _._ 03 _±_ 3 _._ 07 13 _._ 99 _±_ 0 _._ 41


32 2 47,924 162 _._ 10 _±_ 0 _._ 44 767 _._ 17 _±_ 2 _._ 38 4 _._ 55 _±_ 0 _._ 13




# Page 151

4.4. Numerical Experiments **127**


Table 4.8: MSE loss ( _±_ the standard error of the mean) of OpenFOAM computations on


test dataset of incompressible flow.


# division
Solver for _**u**_ Solver for _p_ ∆ _t_ Total MSE ( _×_ 10 _[−]_ [3] ) Total time [s]
per unit length

GAMG Smooth 22.5 0.050 Divergent Divergent
GAMG Smooth 22.5 0.010 6 _._ 09 _±_ 0 _._ 02 6 _._ 08 _±_ 0 _._ 17

GAMG Smooth 22.5 0.005 6 _._ 04 _±_ 0 _._ 02 11 _._ 57 _±_ 0 _._ 32

GAMG Smooth 22.5 0.001 4 _._ 80 _±_ 0 _._ 02 51 _._ 43 _±_ 1 _._ 39

GAMG Smooth 45.0 0.050 Divergent Divergent
GAMG Smooth 45.0 0.010 0 _._ 46 _±_ 0 _._ 00 25 _._ 12 _±_ 0 _._ 81

GAMG Smooth 45.0 0.005 0 _._ 78 _±_ 0 _._ 00 46 _._ 71 _±_ 1 _._ 53

GAMG Smooth 45.0 0.001 1 _._ 04 _±_ 0 _._ 00 201 _._ 11 _±_ 6 _._ 29

GAMG Smooth 90.0 0.050 Divergent Divergent
GAMG Smooth 90.0 0.010 Divergent Divergent
GAMG Smooth 90.0 0.005 0 _._ 15 _±_ 0 _._ 00 231 _._ 18 _±_ 10 _._ 38

GAMG GAMG 22.5 0.050 Divergent Divergent
GAMG GAMG 22.5 0.010 6 _._ 05 _±_ 0 _._ 02 6 _._ 41 _±_ 0 _._ 18

GAMG GAMG 22.5 0.005 6 _._ 00 _±_ 0 _._ 02 12 _._ 21 _±_ 0 _._ 34

GAMG GAMG 22.5 0.001 4 _._ 80 _±_ 0 _._ 02 55 _._ 51 _±_ 1 _._ 52

GAMG GAMG 45.0 0.050 Divergent Divergent
GAMG GAMG 45.0 0.010 0 _._ 46 _±_ 0 _._ 00 26 _._ 00 _±_ 0 _._ 85

GAMG GAMG 45.0 0.005 0 _._ 77 _±_ 0 _._ 00 48 _._ 78 _±_ 1 _._ 57

GAMG GAMG 45.0 0.001 1 _._ 03 _±_ 0 _._ 00 214 _._ 29 _±_ 6 _._ 62

GAMG GAMG 90.0 0.050 Divergent Divergent
GAMG GAMG 90.0 0.010 Divergent Divergent
GAMG GAMG 90.0 0.005 0 _._ 14 _±_ 0 _._ 00 238 _._ 94 _±_ 10 _._ 70

Smooth Smooth 22.5 0.050 Divergent Divergent
Smooth Smooth 22.5 0.010 5 _._ 59 _±_ 0 _._ 02 85 _._ 50 _±_ 3 _._ 05

Smooth Smooth 22.5 0.005 5 _._ 41 _±_ 0 _._ 02 164 _._ 36 _±_ 7 _._ 57

Smooth Smooth 22.5 0.001 4 _._ 19 _±_ 0 _._ 02 765 _._ 50 _±_ 29 _._ 65

Smooth Smooth 45.0 0.050 Divergent Divergent
Smooth Smooth 45.0 0.010 51 _._ 10 _±_ 0 _._ 05 426 _._ 07 _±_ 22 _._ 51

Smooth Smooth 45.0 0.005 2 _._ 09 _±_ 0 _._ 00 824 _._ 71 _±_ 39 _._ 90

Smooth Smooth 45.0 0.001 1 _._ 12 _±_ 0 _._ 00 3960 _._ 88 _±_ 151 _._ 93

Smooth Smooth 90.0 0.050 Divergent Divergent
Smooth Smooth 90.0 0.010 Divergent Divergent
Smooth Smooth 90.0 0.005 4493 _._ 78 _±_ 1 _._ 88 3566 _._ 05 _±_ 183 _._ 75




# Page 152

**128** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method



このグラフは、'PENN (Ours)'と'MP-PDE'のデータを比較する scatter plot です。横軸と縦軸は具体的な変数が示されていないため、具体的な意味は不明ですが、両者の関連性を視覚的に示しています。右上 quadrant に 'PENN' のデータ点が集中的に存在し、左下 quadrant には 'MP-PDE's データ点が分布しています。これにより、右上に配置された点が右下に移動する傾向が見られ、相関関係が示唆されます。具体的なピークや増減の詳細は、軸の単位や範囲が不明瞭なため推測できません。



Figure 4.19: The relationship between the relative MSE of the velocity _**u**_ and inlet velocity.


4.4.3.8 E VALUATION OF O UT - OF -D ISTRIBUTION G ENERALIZATION


We evaluated the out-of-distribution generalizability of PENN and MP-PDE. The mod

els with the best accuracy for each method are used for evaluation. The PENN model has


16 hidden features and eight iterations in the neural nonlinear solver, and the MP-PDE


model has 128 hidden features and a time window size of 20.


First, we tested generalizability for Reynolds numbers. We varied Reynolds numbers


from 500 to 2,000 by changing inlet velocity _u_ inlet from 0.5 to 2.0, while it was 1.0 for the


training dataset. Figures 4.19 and 4.20 show the generalizability regarding inlet velocities,


and Figure 4.21 shows the visualization of velocity fields with inlet velocities of 2.0 and 0.5


for each method. For evaluation, we used relative MSE because the magnitude of features


may differ drastically with inlet velocity change.


From these figures, one can see that PENN has better accuracy in the lower Reynolds


number range while almost no difference in the higher Reynolds numbers. That may be


because PENN can deal with boundary conditions rigorously, and training data may contain


subdomains where the Reynolds number is small locally.


Then, generalizability regarding shapes is evaluated. We generated ground truth data


with the same procedure as that to generate the training dataset, except that the analy

sis domains used here are larger. Figures 4.22, 4.23, and Table 4.9 present the evaluation




# Page 153

4.4. Numerical Experiments **129**





このグラフでは、MP-PDE（紅色の×）とPENN（青色の点）のデータを比較しています。横軸は未知の変数を示し、縦軸には値の大小が示されています。PENNのデータは左から右に右肩上がりの傾向を示していますが、MP-DPEは右肩下がりに傾向しており、両者には相関関係が見られません。



Figure 4.20: The relationship between the relative MSE of the pressure _p_ and inlet velocity.

ヒートマップの軸は「u_inlet = 2.0」と「v_inlet」です。高域（黄色・橙色）は流速の急激な変化を示し、低域（青・緑）は安定した流速を表します。中央の赤色区域は流体の集積が最も集中的で、周囲の流速変化が顕著です。

ヒートマップの軸は横軸と縦軸で、温度の高低を示します。高温度域は黄色・橙色、低温度域が青・緑です。各図形の中央に目立つ赤色斑点が特徴的で、周囲の温度分布を示しています。

図は流体の速度ベクトル場を示しています。右上部で速度が最大（赤色）で、左下部で最小（青色）に分布し、中央で急激に変化する特徴的な領域が見られます。

ヒートマップの軸は「u_inlet」で、値は2.0と0.5に分かれています。高域（黄色・橙色）と低域（青色・緑色）が明確に区別され、両方の値で「Ground truth」と「MI」の図が示されています。低域では「MI」との関連が強調され、高域では両者間の関係が検証される様子が見られます。

ヒートマップの軸は「MP-PDE」と「PEN」です。高集中領域はMP-PDENの右上、PENの左下にあります。目立つパターンは、MP-PENの右下に黄色の広範囲が見られます。

ヒートマップの軸は「u magnitude（uの大きさ）」です。高集中領域は黄色・橙色域で、低集中域は青色域です。右上角に「PENN (Ours)」と「DE」が示されています。


Figure 4.21: The visualization of velocity fields with inlet velocities _u_ inlet of 2.0 and 0.5.


results. Here, we did not observe strong generalizability, such as what was observed in Sec

tion 3.4.2. That may be because the global feature introduced by the neural nonlinear solver


highly depends on the size of the analysis domain, resulting in relatively poor generaliza

tion ability regarding the analysis domain size. The performance degradation is more sig

nificant for pressure field prediction than the velocity because it may have stronger global


interactions through the pressure Poisson equation, which is a static problem introducing


global interaction.



折れ線グラフでは、横軸が時間や条件を示し、縦軸に値を表します。変化の傾向は、上昇・下降するかを示しており、ピークは最大値の位置を示します。増減は、値が高くなるか低くなるかを表し、グラフ全体の形状に反映されます。


# Page 154

ヒートマップの軸は「uのmagnitude（uの大きさ）」で、色は0.0e+00から2.00e00の範囲を示します。上部の「Ground truth（真の値）」は、黄色から赤色にかけて高値域に集中的に分布し、青色から緑色へと低値領域に移行しています。下部のMP-PDEは、緑から黄緑にかけて中程度の高值域に集中し、紫色から青緑へと極端な値の低域に移動しています。前者は真の分布を反映し、後者は物理的制約に従った近似値を示しています。

ヒートマップの軸は「uのmagnitude（uの大きさ）」です。高集中領域は、MP-PDEとPENN（Ours）の上部に黄色・橙色域が広がっている部分で、低領域は下部に青・緑域が集中的に分布している部分です。目立つパターンは、PENNの右端に黄色域が突出している点が特徴的です。

MP-PDEとPENNの速度場を視覚化した図です。MP-PDENの矢印は右上方に指向し、中部で最大の大きさを示しています。PENNでは矢印が右下方に偏向し、左中部で最も大きさが大きい特徴的な領域が見られます。

4.5 C ONCLUSION


We have presented an E( _n_ )-equivariant, GNN-based neural PDE solver, PENN, which


can fulfill boundary conditions required for reliable predictions. The model has superiority


in embedding the information of PDEs (physics) in the model and speed-accuracy trade

off. Therefore, our model can be a useful standard for realizing reliable, fast, and accurate


GNN-based PDE solvers.


Table 4.9: MSE loss ( _±_ the standard error of the mean) on the dataset with larger samples.


ˆ
_g_ Neumann is the loss computed only on the boundary where the Neuman condition is set.


Method _**u**_ ( _×_ 10 _[−]_ [3] ) _p_ ( _×_ 10 _[−]_ [2] )
MP-PDE 10 _._ 335 _±_ 0 _._ 033 **4** _**.**_ **002** _±_ 0 _._ 005

**PENN** (Ours) **4** _**.**_ **132** _±_ 0 _._ 009 9 _._ 621 _±_ 0 _._ 009




# Page 155

ヒートマップの軸は「pressure（圧力）」です。高圧域は赤色で、低圧領域は青色です。中央に緑色の領域が見られ、周囲には赤色と青色の区域が分布しています。右上角に「MP-PDE」のラベルがあり、左上角には「Ground truth」と書かれています。

ヒートマップの軸は「pressure（圧力）」です。高圧域は赤色で、低圧領域は青色です。中央に緑色の領域が見られ、周囲には赤色と青色の区域が分布しています。右上角に「MP-PDE」のラベルがあり、左上角には「Ground truth」と書かれています。

ヒートマップの軸は「pressure（圧力）」です。高圧域（赤・橙色）は「Ground truth（真の値）」の右端に集中的に分布し、中低圧（緑・黄色）は中央に広がり、低圦域（青・紫色）は左端に集中しています。右端の真値と左端の予測値（MP-PDE、PENN）の境界線が明確に示されています。

ヒートマップの軸は「pressure（圧力）」です。高圧域（赤・橙色）は「Ground truth（真の値）」の右端に集中的に分布し、中低圧（緑・黄色）は中央に広がり、低圦域（青・紫色）は左端に集中しています。右端の真値と左端の予測値（MP-PDE、PENN）の境界線が明確に示されています。

ヒートマップの軸は「pressure」（圧力）で、範囲は-0.5から-9.0e-01（約-9%）です。高圧域は黄色・橙色に、低域は緑・青色に分布し、中央に深青色の集中的な低圧領域が見られます。

Although the property of our model is preferable, it also limits the applicable domain

ヒートマップの軸は「pressure（圧力）」です。MP-PDEとPENN（Ours）の図では、高圧域（赤・橙色）と低圴域（緑・青色）が明確に区別され、図中央に緑色の集中領域が見られ、周囲に橙色・赤色の領域が広がっている様子が示されています。

ヒートマップの軸は「pressure（圧力）」です。MP-PDEとPENN（Ours）の図では、高圧域（赤・橙色）と低圴域（緑・青色）が明確に区別され、図中央に緑色の集中領域が見られ、周囲に橙色・赤色の領域が広がっている様子が示されています。


of the model because we need to be familiar with the concrete form of the PDE of interest

r sample
e appli
r sampl
e applic
3.1.7.5.1.2.3.4.5.6.7.8.9.10.11.12.13.14.15.16.17.18.19.20.21.22.23.24.25.26.27.28.29.30.31.32.33.34.35.36.37.38.39.40.41.42.43.44.45.46.47.48.49.50.51.52.53.54.55.56.57.58.59.60.61.62.63.64.65.66.67.68.69.70.71.72.73.74.75.76.77.78.79.80.81.82.83.84.85.86.87.88.89.90.91.92.93.94.95.96.97.98.99..100..101..102..103..104..105..106..107..108..109..110..111..112..113..114..115..116..117..118..119..120..121..122..123..124..125..126..127..128..129..130..131..132..133..134..135..136..137..138..139..140..141..142..143..144..145..146..147..148..149..150..151..152..153..154..155..156..157..158..159..160..161..162..163..164..165..166..167..168..169..170..171..172..173..174..175..176..177..178..179..180..181..182..183..184..185..186..187..188..189..190..191..192..193..194..195..196..197..198..199..200..201..202..203..204..205..206..207..208..209..210..211..212..213..214..215..216..217..218..219..220..221..222..223..224..225..226..227..228..229..230..231..232..233..234..235..236..237..238..239..240..241..242..243..244..245..246..247..248..249..250..251..252..253..254..255..256..257..258..259..260..261..262..263..264..265..266..267..268..269..270..271..272..273..274..275..276..277..278..279..280..281..282..283..284..285..286..287..288..289..290..291..292..293..294..295..296..297..298..299..300..301..302..303..304..305..306..307..308..309..310..311..312..313..314..315..316..317..318..319..320..321..322..323..324..325..326..327..328..329..330..331..332..333..334..335..336..337..338..339..340..341..342..343..344..345..346..347..348..349..350..351..352..353..354..355..356..357..358..359..360..361..362..363..364..365..366..367..368..369..370..371..372..373..374..375..376..377..378..379..380..381..382..383..384..385..386..387..388..389..390..391..392..393..394..395..396..397..398..399..400..401..402..403..404..405..406..407..408..409..410..411..412..413..414..415..416..417..418..419..420..421..422..423..424..425..426..427..428..429..430..431..432..433..434..435..436..437..438..439..440..441..442..443..444..445..446..447..448..449..450..451..452..453..454..455..456..457..458..459..460..461..462..463..464..465..466..467..468..469..470..471..472..473..474..475..476..477..478..479..480..481..482..483..484..485..486..487..488..489..490..491..492..493..494..495..496..497..498..499..500..501..502..503..504..505..506..507..508..509..510..511..512..513..514..515..516..517..518..519..520..521..52


to construct the effective PENN model. For instance, the proposed model cannot exploit


its potential to solve inverse problems where explicit forms of the governing PDE are not


available for such tasks. Therefore, combining PINNs and PENNs could be the next direc

tion of the research community.




# Page 156

**132** 4. Physics-Embedded Neural Network: Boundary Condition and Implicit Method




# Page 157

# **Chapter 5** **Conclusion**

The main contribution of this dissertation is the development of a general neural PDE


solvers that are:


   - E( _n_ )-equivariant thanks to the use of an IsoGCN (Chapter 3); and


   - capable of handling mixed boundary conditions and global interactions by applying


the implicit Euler method (Chapter 4).


Through numerical experiments, we demonstrated that our model is capable of accurately


predicting heat phenomena on a mesh that is significantly larger than that used in the train

ing phase (Section 3.4). Our approach was also successful in handling various boundary


conditions and PDE parameters, in addition to the global interactions that occur in incom

pressible flow phenomena (Section 4.4). Hereunder, we revisit the objectives outlined in


Chapter 1 and evaluate how they were addressed, indicating any existing limitations and


suggesting potential avenues for future work.


**Flexibility to treat arbitrary meshes based on GNNs** In this dissertation, we highlight


the flexibility of GNNs in treating arbitrary meshes. Additionally, GNNs offer other desir

able characteristics, such as permutation equivariance (Section 3.3) and a generalizability


coming from locally-connected nature (Section 3.4). Permutation equivariance is crucial


because a mesh can be indexed in various ways, each corresponding to a permutation of in

dices. The locally-connected nature of GNNs allows for successful predictions on meshes


133




# Page 158

**134** 5. Conclusion


larger than those used during training, as demonstrated in Section 3.4. However, due to


that feature, GNNs may struggle to capture global interactions that occur in fields such as


incompressible flow, steady-state analysis, and structural analysis, which will be discussed


in a subsequent work.


**E(** _**n**_ **)-equivariance to reflect physical symmetries** Chapter 3 introduced the IsoGCN


model, a GNN with E(n)-equivariance capable of learning mesh-discretized physical phe

nomena from a relatively small dataset. We confirmed that PENN models also have E(n)

equivariance (Section 4.4), which means that their added capability to handle boundary


conditions and implicit time evolution is also E(n)-equivariant. However, physical phe

nomena have other symmetries, such as that with respect to unit changes corresponding


to scaling. In particular, some PDEs do not change under scaling as long as certain di

mensionless quantities, such as the Reynolds number, remain constant. In contrast, our


current model depend on scaling because we use volume features to improve predictive


performance. Therefore, a possible future direction could be developing a machine learn

ing model that is, not only permutation- and E(n)-, but also scaling-equivariant. Moreover,


incorporating the conservation property could also lead to more stable and accurate predic

tions.


**Computational efficiency to realize faster predictions than with conventional nu-**


**merical analysis methods** The computational efficiency of the IsoGCN model is due


to its linear message passing and utilization of the sparse structure of mesh-like graphs


(Section 3.3). Additionally, PENN models achieve fast and stable predictions using the


Barzilai–Borwein method, a simplified nonlinear solver for implicit time evolution (Sec

tion 4.3). However, the speedup observed in numerical experiments is of two to five times,


rather than an order of magnitude (Sections 3.4 and 4.4). This might be because we utilized


detailed meshes with a large amount of information. To improve computation speed, a pos

sible future direction would be to reduce the number of degrees of freedom in the input


mesh.


**Accurate consideration of boundary conditions** In Chapter 4, we presented a frame

work for dealing with mixed boundary conditions. Our approach rigorously handles Dirich



# Page 159

**135**


let boundary conditions, but there is room for improvement in satisfying Neumann bound

ary conditions, which is currently done with a certain degree of error. This may be due


to the discretization error inherent in the chosen spatial differential model. To address this


issue, we may consider using higher-order approximations of LSMPS differential operators


or exploring alternative formalizations. For instance, the weak formulation used in methods


such as FEM and FVM might be more accurate in treating Neumann boundary conditions.


**Stable prediction over long time steps by accounting for global interactions** The


PENN model achieves stable predictions for long-term states due to its use of the implicit


Euler method, as described in Chapter 4. However, to reduce the computational cost, we


were forced to introduce considerable approximations in the implicit formulation, which


may compromise its benefits. In fact, as shown in Section 4.4.3.8, such approximations


may limit the generalizability of the analysis domain size. To resolve this, we could con

sider using the quasi-Newton method instead of gradient descent to more accurately solve


the implicit equation. Another option may be to use the multigrid method, where the mesh


is coarsened within the solver to increase the physical distances visible by the one-hop


operation. Additionally, we may also explore the application of the all-to-all connectivity


used in the Transformer model (Vaswani et al., 2017).


Despite its limitations, the method proposed in this study lays a solid foundation for


the development of practical neural PDE solvers, possessing some desired features, such


as the ability to handle arbitrary shapes and boundary conditions. Thus, our work may


be a crucial step towards achieving efficient, accurate, and versatile PDE solvers that can


contribute to the further advancement of the productivity of human societies.




# Page 160

**136** 5. Conclusion




# Page 161

# **Bibliography**

Eman Ahmed, Alexandre Saint, Abd El Rahman Shabayek, Kseniya Cherenkova, Rig Das,


Gleb Gusev, Djamila Aouada, and Bjorn Ottersten. A Survey on Deep Learning Ad

vances on Different 3D Data Representations. _arXiv preprint arXiv:1808.01462_, 2018.


Ferran Alet, Adarsh Keshav Jeewajee, Maria Bauza Villalonga, Alberto Rodriguez, Tomas


Lozano-Perez, and Leslie Kaelbling. Graph Element Networks: Adaptive, Structured


Computation and Memory. In _International Conference on Machine Learning_, 2019.


Jonathan Barzilai and Jonathan M Borwein. Two-Point Step Size Gradient Methods. _IMA_


_Journal of Numerical Analysis_, 8(1):141–148, 1988.


Igor I Baskin, Vladimir A Palyulin, and Nikolai S Zefirov. A Neural Device for Searching


Direct Correlations Between Structures and Properties of Chemical Compounds. _Journal_


_of Chemical Information and Computer Sciences_, 37(4):715–721, 1997.


Peter W Battaglia, Jessica B Hamrick, Victor Bapst, Alvaro Sanchez-Gonzalez, Vinicius


Zambaldi, Mateusz Malinowski, Andrea Tacchetti, David Raposo, Adam Santoro, Ryan


Faulkner, et al. Relational Inductive Biases, Deep Learning, and Graph Networks. _arXiv_


_preprint arXiv:1806.01261_, 2018.


Christopher M Bishop. _Pattern Recognition and Machine Learning_ . Springer, 2006.


Johannes Brandstetter, Daniel E. Worrall, and Max Welling. Message Passing Neural PDE


Solvers. In _International Conference on Learning Representations_ [, 2022. URL https:](https://openreview.net/forum?id=vSix3HPYKSU)


[//openreview.net/forum?id=vSix3HPYKSU.](https://openreview.net/forum?id=vSix3HPYKSU)


137




# Page 162

**138** BIBLIOGRAPHY


Shengze Cai, Zhicheng Wang, Frederik Fuest, Young Jin Jeon, Callum Gray, and


George Em Karniadakis. Flow Over an Espresso Cup: Inferring 3-D Velocity and


Pressure Fields from Tomographic Background Oriented Schlieren via Physics-Informed


Neural Networks. _Journal of Fluid Mechanics_, 915, 2021.


Kai-Hung Chang and Chin-Yi Cheng. Learning to Simulate and Design for Structural


Engineering. _arXiv preprint arXiv:2003.09103_, 2020.


Ming Chen, Zhewei Wei, Zengfeng Huang, Bolin Ding, and Yaliang Li. Simple and Deep


Graph Convolutional Networks. _arXiv preprint arXiv:2007.02133_, 2020.


Ricky TQ Chen, Yulia Rubanova, Jesse Bettencourt, and David K Duvenaud. Neural Or

dinary Differential Equations. _Advances in Neural Information Processing Systems_, 31,


2018.


Wei-Lin Chiang, Xuanqing Liu, Si Si, Yang Li, Samy Bengio, and Cho-Jui Hsieh. Cluster

GCN: An Efficient Algorithm for Training Deep and Large Graph Convolutional Net

works. In _Proceedings of the 25th ACM SIGKDD International Conference on Knowl-_


_edge Discovery & Data Mining_, pp. 257–266, 2019.


Taco Cohen and Max Welling. Group Equivariant Convolutional Networks. In _Interna-_


_tional Conference on Machine Learning_, pp. 2990–2999, 2016.


Taco S Cohen, Mario Geiger, Jonas K¨ohler, and Max Welling. Spherical CNNs. In _Inter-_


_national Conference on Learning Representations_, 2018.


Taco S Cohen, Maurice Weiler, Berkay Kicanaoglu, and Max Welling. Gauge Equivariant


Convolutional Networks and the Icosahedral CNN. _International Conference on Ma-_


_chine Learning_, 2019.


George Cybenko. Approximation by Superpositions of a Sigmoidal Function. _Mathematics_


_of Control, Signals and Systems_, 5(4):455, 1992.


Xiaowen Dong, Dorina Thanou, Laura Toni, Michael Bronstein, and Pascal Frossard.


Graph Signal Processing for Machine Learning: A Review and New Perspectives. _IEEE_


_Signal Processing Magazine_, 37(6):117–127, 2020.




# Page 163

Bibliography **139**


Nadav Dym and Haggai Maron. On the Universality of Rotation Equivariant Point Cloud


Networks. _arXiv preprint arXiv:2010.02449_, 2020.


Wenqi Fan, Yao Ma, Qing Li, Yuan He, Eric Zhao, Jiliang Tang, and Dawei Yin. Graph


Neural Networks for Social Recommendation. In _The World Wide Web Conference_, pp.


417–426, 2019.


Matthias Fey and Jan E. Lenssen. Fast Graph Representation Learning with PyTorch Geo

metric. In _ICLR Workshop on Representation Learning on Graphs and Manifolds_, 2019.


Matthias Fey, Jan Eric Lenssen, Frank Weichert, and Heinrich M¨uller. SplineCNN: Fast


Geometric Deep Learning with Continuous B-Spline Kernels. In _Proceedings of the_


_IEEE Conference on Computer Vision and Pattern Recognition_, pp. 869–877, 2018.


Fabian Fuchs, Daniel Worrall, Volker Fischer, and Max Welling. SE(3)-Transformers:


3D Roto-Translation Equivariant Attention Networks. _Advances in Neural Information_


_Processing Systems_, 33, 2020.


Christophe Geuzaine and Jean-Franc¸ois Remacle. Gmsh: a Three-Dimensional Finite El

ement Mesh Generator with Built-in Pre- and Post-Processing Facilities. _International_


_Journal for Numerical Methods in Engineering_, 79(11):1309–1331, 2009.


Justin Gilmer, Samuel S Schoenholz, Patrick F Riley, Oriol Vinyals, and George E Dahl.


Neural Message Passing for Quantum Chemistry. In _International Conference on Ma-_


_chine Learning_, pp. 1263–1272. JMLR. org, 2017.


Marco Gori, Gabriele Monfardini, and Franco Scarselli. A New Model for Learning in


Graph Domains. In _Proceedings. 2005 IEEE International Joint Conference on Neural_


_Networks, 2005._, volume 2, pp. 729–734. IEEE, 2005.


Fangda Gu, Heng Chang, Wenwu Zhu, Somayeh Sojoudi, and Laurent El Ghaoui. Im

plicit Graph Neural Networks. _Advances in Neural Information Processing Systems_, 33:


11984–11995, 2020.


Deguang Han, Keri Kornelson, Eric Weber, and David Larson. _Frames for Undergraduates_,


volume 40. American Mathematical Soc., 2007.




# Page 164

**140** BIBLIOGRAPHY


Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep Residual Learning for


Image Recognition. In _Proceedings of the IEEE Conference on Computer Vision and_


_Pattern Recognition_, pp. 770–778, 2016.


Masanobu Horie and Naoto Mitsume. Physics-Embedded Neural Networks: Graph Neural


PDE Solvers with Mixed Boundary Conditions. In Alice H. Oh, Alekh Agarwal, Danielle


Belgrave, and Kyunghyun Cho (eds.), _Advances in Neural Information Processing Sys-_


_tems_ [, 2022. URL https://openreview.net/forum?id=B3TOg-YCtzo.](https://openreview.net/forum?id=B3TOg-YCtzo)


Masanobu Horie, Naoki Morita, Toshiaki Hishinuma, Yu Ihara, and Naoto Mitsume.


Isometric Transformation Invariant and Equivariant Graph Convolutional Networks.


In _International Conference on Learning Representations_, 2021. [URL https://](https://openreview.net/forum?id=FX0vR39SJ5q)


[openreview.net/forum?id=FX0vR39SJ5q.](https://openreview.net/forum?id=FX0vR39SJ5q)


Kurt Hornik. Approximation Capabilities of Multilayer Feedforward Networks. _Neural_


_Networks_, 4(2):251–257, 1991.


Yurie A Ignatieff. Foundations of Rational Continuum Mechanics. In _The Mathematical_


_World of Walter Noll_, pp. 107–125. Springer, 1996.


Yu Ihara, Gaku Hashimoto, and Hiroshi Okuda. Web-Based Integrated Cloud CAE Plat

form for Large-Scale Finite Element Analysis. _Mechanical Engineering Letters_, 3:17–


00520, 2017.


Diederik P Kingma and Jimmy Ba. Adam: A method for Stochastic Optimization. _arXiv_


_preprint arXiv:1412.6980_, 2014.


Thomas N Kipf and Max Welling. Semi-Supervised Classification with Graph Convolu

tional Networks. In _International Conference on Learning Representations_, 2017. URL


[https://openreview.net/forum?id=SJU4ayYgl.](https://openreview.net/forum?id=SJU4ayYgl)


Johannes Klicpera, Janek Groß, and Stephan G¨unnemann. Directional Message Passing


for Molecular Graphs. In _International Conference on Learning Representations_, 2020.


Sebastian Koch, Albert Matveev, Zhongshi Jiang, Francis Williams, Alexey Artemov,


Evgeny Burnaev, Marc Alexa, Denis Zorin, and Daniele Panozzo. ABC: A Big CAD




# Page 165

Bibliography **141**


Model Dataset for Geometric Deep Learning. In _The IEEE Conference on Computer_


_Vision and Pattern Recognition (CVPR)_, June 2019.


Risi Kondor. N-body Networks: a Covariant Hierarchical Neural Network Architecture for


Learning Atomic Potentials. _arXiv preprint arXiv:1803.01588_, 2018.


Alex Krizhevsky, Geoffrey Hinton, et al. Learning Multiple Layers of Features from Tiny


Images. 2009.


Julia Ling, Andrew Kurzawski, and Jeremy Templeton. Reynolds Averaged Turbulence


Modelling using Deep Neural Networks with Embedded Invariance. _Journal of Fluid_


_Mechanics_, 807:155–166, 2016.


Dong C Liu and Jorge Nocedal. On the Limited Memory BFGS Method for Large Scale


Optimization. _Mathematical Programming_, 45(1):503–528, 1989.


David G Luenberger, Yinyu Ye, et al. _Linear and Nonlinear Programming_, volume 2.


Springer, 1984.


Zhiping Mao, Ameya D Jagtap, and George Em Karniadakis. Physics-Informed Neural


Networks for High-Speed Flows. _Computer Methods in Applied Mechanics and Engi-_


_neering_, 360:112789, 2020.


Haggai Maron, Heli Ben-Hamu, Nadav Shamir, and Yaron Lipman. Invariant and Equiv

ariant Graph Networks. _arXiv preprint arXiv:1812.09902_, 2018.


Takuya Matsunaga, Axel S¨odersten, Kazuya Shibata, and Seiichi Koshizuka. Improved


Treatment of Wall Boundary Conditions for a Particle Method with Consistent Spatial


Discretization. _Computer Methods in Applied Mechanics and Engineering_, 358:112624,


2020.


Federico Monti, Davide Boscaini, Jonathan Masci, Emanuele Rodola, Jan Svoboda, and


Michael M Bronstein. Geometric Deep Learning on Graphs and Manifolds using Mix

ture Model CNNs. In _Proceedings of the IEEE Conference on Computer Vision and_


_Pattern Recognition_, pp. 5115–5124, 2017.




# Page 166

**142** BIBLIOGRAPHY


Naoki Morita, Kazuo Yonekura, Ichiro Yasuzumi, Mitsuyoshi Tsunori, Gaku Hashimoto,


and Hiroshi Okuda. Development of 3 _×_ 3 DOF Blocking Structural Elements to En

hance the Computational Intensity of Iterative Linear Solver. _Mechanical Engineering_


_Letters_, 2:16–00082, 2016.


Vinod Nair and Geoffrey E Hinton. Rectified Linear Units Improve Restricted Boltzmann


Machines. In _International Conference on Machine Learning_, pp. 807–814, 2010.


Preetum Nakkiran, Gal Kaplun, Yamini Bansal, Tristan Yang, Boaz Barak, and Ilya


Sutskever. Deep Double Descent: Where Bigger Models and More Data Hurt. _Jour-_


_nal of Statistical Mechanics: Theory and Experiment_, 2021(12):124003, 2021.


Antonio Ortega, Pascal Frossard, Jelena Kovaˇcevi´c, Jos´e MF Moura, and Pierre Van

dergheynst. Graph Signal Processing: Overview, Challenges, and Applications. _Pro-_


_ceedings of the IEEE_, 106(5):808–828, 2018.


Guofei Pang, Lu Lu, and George Em Karniadakis. fPINNs: Fractional Physics-Informed


Neural Networks. _SIAM Journal on Scientific Computing_, 41(4):A2603–A2626, 2019.


Adam Paszke, Sam Gross, Francisco Massa, Adam Lerer, James Bradbury, Gregory


Chanan, Trevor Killeen, Zeming Lin, Natalia Gimelshein, Luca Antiga, Alban Des

maison, Andreas Kopf, Edward Yang, Zachary DeVito, Martin Raison, Alykhan Te

jani, Sasank Chilamkurthy, Benoit Steiner, Lu Fang, Junjie Bai, and Soumith Chintala.


PyTorch: An Imperative Style, High-Performance Deep Learning Library. In H. Wal

lach, H. Larochelle, A. Beygelzimer, F. d'Alch´e-Buc, E. Fox, and R. Garnett (eds.), _Ad-_


_vances in Neural Information Processing Systems_, pp. 8024–8035. Curran Associates,


Inc., 2019.


Tobias Pfaff, Meire Fortunato, Alvaro Sanchez-Gonzalez, and Peter Battaglia. Learn

ing Mesh-Based Simulation with Graph Networks. In _International Conference on_


_Learning Representations_ [, 2021. URL https://openreview.net/forum?id=](https://openreview.net/forum?id=roNqYL0_XP)


[roNqYL0_XP.](https://openreview.net/forum?id=roNqYL0_XP)


Maziar Raissi, Paris Perdikaris, and George E Karniadakis. Physics-Informed Neural Net

works: A Deep Learning Framework for Solving Forward and Inverse Problems Involv



# Page 167

Bibliography **143**


ing Nonlinear Partial Differential Equations. _Journal of Computational Physics_, 378:


686–707, 2019.


Siamak Ravanbakhsh, Jeff Schneider, and Barnab´as P´oczos. Equivariance Through


Parameter-Sharing. In Doina Precup and Yee Whye Teh (eds.), _International Confer-_


_ence on Machine Learning_, volume 70 of _Proceedings of Machine Learning Research_,


pp. 2892–2901. PMLR, 06–11 Aug 2017. [URL https://proceedings.mlr.](https://proceedings.mlr.press/v70/ravanbakhsh17a.html)


[press/v70/ravanbakhsh17a.html.](https://proceedings.mlr.press/v70/ravanbakhsh17a.html)


Alvaro Sanchez-Gonzalez, Nicolas Heess, Jost Tobias Springenberg, Josh Merel, Martin


Riedmiller, Raia Hadsell, and Peter Battaglia. Graph Networks as Learnable Physics


Engines for Inference and Control. _arXiv preprint arXiv:1806.01242_, 2018.


Alvaro Sanchez-Gonzalez, Victor Bapst, Kyle Cranmer, and Peter Battaglia. Hamiltonian


Graph Networks with ODE Integrators. _arXiv preprint arXiv:1909.12790_, 2019.


Alvaro Sanchez-Gonzalez, Jonathan Godwin, Tobias Pfaff, Rex Ying, Jure Leskovec, and


Peter W Battaglia. Learning to Simulate Complex Physics with Graph Networks. _arXiv_


_preprint arXiv:2002.09405_, 2020.


Franco Scarselli, Marco Gori, Ah Chung Tsoi, Markus Hagenbuchner, and Gabriele Mon

fardini. The Graph Neural Network Model. _IEEE Transactions on Neural Networks_, 20


(1):61–80, 2008.


Alessandro Sperduti and Antonina Starita. Supervised Neural Networks for the Classifica

tion of Structures. _IEEE Transactions on Neural Networks_, 8(3):714–735, 1997.


Tasuku Tamai and Seiichi Koshizuka. Least Squares Moving Particle Semi-Implicit


Method. _Computational Particle Mechanics_, 1(3):277–305, 2014.


Nathaniel Thomas, Tess Smidt, Steven Kearnes, Lusann Yang, Li Li, Kai Kohlhoff, and


Patrick Riley. Tensor Field Networks: Rotation-and Translation-Equivariant Neural Net

works for 3d Point Clouds. _arXiv preprint arXiv:1802.08219_, 2018.


Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N


Gomez, Łukasz Kaiser, and Illia Polosukhin. Attention is All You Need. _Advances_


_in Neural Information Processing Systems_, 30, 2017.




# Page 168

**144** BIBLIOGRAPHY


Rui Wang, Robin Walters, and Rose Yu. Incorporating Symmetry into Deep Dynamics


Models for Improved Generalization. In _International Conference on Learning Repre-_


_sentations_ [, 2021. URL https://openreview.net/forum?id=wta_8Hx2KD.](https://openreview.net/forum?id=wta_8Hx2KD)


Maurice Weiler, Mario Geiger, Max Welling, Wouter Boomsma, and Taco S Cohen. 3d


Steerable CNNs: Learning Rotationally Equivariant Features in Volumetric Data. In


_Advances in Neural Information Processing Systems_, pp. 10381–10392, 2018.


Felix Wu, Amauri Souza, Tianyi Zhang, Christopher Fifty, Tao Yu, and Kilian Weinberger.


Simplifying Graph Convolutional Networks. In _International Conference on Machine_


_Learning_, pp. 6861–6871. PMLR, 2019.


Keyulu Xu, Weihua Hu, Jure Leskovec, and Stefanie Jegelka. How Powerful are Graph


Neural Networks? _arXiv preprint arXiv:1810.00826_, 2018.


Jiaxuan You, Rex Ying, and Jure Leskovec. Position-Aware Graph Neural Networks. _arXiv_


_preprint arXiv:1906.04817_, 2019.


Manzil Zaheer, Satwik Kottur, Siamak Ravanbakhsh, Barnabas Poczos, Russ R Salakhut

dinov, and Alexander J Smola. Deep Sets. _Advances in Neural Information Processing_


_Systems_, 30, 2017.




# Page 169

# **Index**

E( _n_ )-equivariant pointwise MLP, 52


activation function, 12


adjacency matrix, 10


bias, 12


boundary encoder, 85


contraction, 47


convolution, 47


degree matrix, 10


Dirichlet boundary condition, 22


Dirichlet layer, 86


discrete tensor field, 42, 43


edge feature, 12


equivariance, 18


Euclidean group, 18


explicit Euler method, 23


FDM, 29


FEM, 32


frame, 89


dual frame, 89


GCN, 15


general linear group, 17


GNN, 9



gradient descent, 26


graph, 9


directed graph, 9


undirected graph, 9


graph Laplacian matrix, 10


group, 17


group action, 17


implicit Euler method, 23


invariance, 18


IsoAM, 44


differential IsoAM, 54


IsoGCN, 40, 53


NIsoGCN, 88


Kronecker delta, 20


LSMPS method, 36


mesh, 23


MLP, 12


MPNN, 14


Neumann boundary condition, 22


Newton–Raphson method, 25


orthogonal group, 17


PDE, 21


145




# Page 170

**146** INDEX


PENN, 82


permutaion, 10


pointwise MLP, 13


pseudoinverse decoder, 86


quasi-Newton method, 25


symmetric group, 18


vertex feature, 12


weight matrix, 12


