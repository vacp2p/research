# Preliminaries
In a Merkle Tree with the capacity of `n` leaves , one can compute the root of the tree by maintaining the root nodes of log(n) number of complete Merkle trees. 
We use this fact and define `F` to be an array of size log(n) holding the root of complete Merkle trees (all positioned on the left side of the tree) for levels `[0, d=log(n)+1]`. Each entry of `F` at position `i`  holds a pair `(index, H)` where H is the root of the complete subtree at level `i`, and  `index` indicates the index of the leaf node whose insertion resulted in `H`.
