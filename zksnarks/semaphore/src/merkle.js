const SMT = require('semaphore-merkle-tree');

const storage = new SMT.storage.MemStorage();
const hasher = new SMT.hashers.MimcSpongeHasher();
const prefix = 'semaphore';
const default_value = '0';
const depth = 2;

const tree = new SMT.tree.MerkleTree(
    prefix,
    storage,
    hasher,
    depth,
    default_value,
);
