# RootReconstruct

Reconstruction program for tree root from root point data. Tree root structure can be reconstructed from point data. Root point data should be described in our oritinal data format shown as following.

X Y Z diameter PID dPID

The dat file is a text file. Here, X, Y, Z are x, y and z coordinate values. D is diameter. PID is ID number of the root point and dPID is the PID of the connection destination. The PID of center of stump point shoud be assigned 0. Line start with # will be processed as comment.

The dat formatted data file can be translated into the VTK or SWC formatted files for analyzing and visualization.

Execution <br>
$ python reconstruct.py input.dat output.dat --radius-ratio R --param-w W

Here, R is the ratio of the diameter of the target point to the point included in the connection candidate point.　W is a parameter for determining the priority ratio of the angle and the distance in determining the connection destination.

<b>Copyright</b><br>
GPR Research Group: Mizue Ohashi, Hidetoshi Ikeno, Kotaro Sekihara, Toko Tanikawa, Masako Dannoura, Keitaro Yamase, Chikage Todo, Takahiro Tomita, Yasuhiro Hirano 

<b>Reference</b> <br>
M. Ohashi, H. Ikeno, K. Sekihara, T. Tanikawa, M. Dannoura, K. Yamase, C. Todo, T. Tomita, Y. Hirano, Reconstruction of root systems in Cryptomeria japonica using root point coordinates and diamete, Planta, to be published.
