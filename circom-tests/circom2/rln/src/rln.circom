pragma circom 2.0.0;

include "./rln-base.circom";

component main {public [x, epoch, rln_identifier ]} = RLN(15);
