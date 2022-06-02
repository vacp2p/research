pragma circom 2.0.0;

include "./nrln-base.circom";

component main {public [x, epoch, rln_identifier ]} = NRLN(15, 2);
