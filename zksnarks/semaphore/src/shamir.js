var secrets = require("secrets.js");

var key = secrets.random(512);

// 2/3 shared secret
var shares = secrets.share(key, 3, 2);

var comb1 = secrets.combine([shares[0]]);
var comb2 = secrets.combine([shares[0], shares[1]]);
var comb3 = secrets.combine([shares[1], shares[2]]);
assert((comb1 == key) == false);
assert((comb2 == key) == true);
assert((comb3 == key) == true);

// use external nullifier as seed
// XXX: this seed should be combined with private key too
var pwHex = secrets.str2hex("external nullifier 1");
var key2 = secrets.str2hex(pw);
// shares, combine, etc


