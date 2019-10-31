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

// tree.update(index, value)
// tree.path(index)


// Hash values sanity check:
// Note that first argument to hash 'level' is ignored, has nothing to do with merkle hash.

// Default:
// zero_values:
// [ '0',
//   '20636625426020718969131298365984859231982649550971729229988535915544421356929',
//   '8234632431858659206959486870703726442454087730228411315786216865106603625166' ],

// > hash00 = hasher.hash(0, 0, 0).toString()
// '20636625426020718969131298365984859231982649550971729229988535915544421356929'

//     > hasher.hash(0, zero_hash, zero_hash)
// '8234632431858659206959486870703726442454087730228411315786216865106603625166'
// await tree.root() same


// Add 1 value:
//    > tree.update(1, '1')

//     > hash01 = hasher.hash(0, 0, 1).toString()
// '20817788844844400846305593449019051859483675600760331396756186604441020904869'

// // Err, they reversed?
//     > hasher.hash(0, hash00, hash01).toString()
// '11761812633131047631528311490954788291484058935864783081603456383187402910544'
//     > hasher.hash(0, hash01, hash00).toString()
// '11929234368174035070205246553665882981086741604867343533563248489540467991323'

// Why? Would expect: hash 0 = hash( hash 0-0 || hash 0-1 )
// Seems like it is on purpose, oh well: https://github.com/weijiekoh/semaphore-merkle-tree/blob/master/ts/merkletree.ts#L175
