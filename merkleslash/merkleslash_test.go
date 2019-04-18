package main

import "testing"
import "github.com/cbergoon/merkletree"

func TestBasicGood(t *testing.T) {
	// Pre-compute expected tree
	var list []merkletree.Content
	list = append(list, TestContent{x: "1"})
	list = append(list, TestContent{x: "2"})
	list = append(list, TestContent{x: "3"})
	list = append(list, TestContent{x: "4"})
	mt, _ := merkletree.NewTree(list)
	trustedRoot := toHex(mt.MerkleRoot())

	// Local node setup, partial
	// Assume has access to trustedRoot
	var contents []merkletree.Content
	contents = append(contents, TestContent{x: "1"})
	contents = append(contents, TestContent{x: "2"})
	contents = append(contents, TestContent{x: "3"})

	// Byzantine case, currently sending nothing
	// TODO: Since haves is empty it should return full contents?
	// XXX: Doesn't make sense to have tree hardcoded in other code
	var haves []string
	untrustedPayloads := pull("good", trustedRoot, haves)
	content := TestContent{x: untrustedPayloads[0]}
	contents = append(contents, content)

	// XXX: is there no way to append to tree?
	untrusted := mt
	_ = untrusted.RebuildTreeWith(contents)
	untrustedRoot := toHex(untrusted.MerkleRoot())

	expect := (untrustedRoot == trustedRoot)
	if !expect {
        t.Errorf("Good basic: Untrusted root %s and trusted root %s should match", untrustedRoot, trustedRoot)
    }
}

func TestBasicByzantine(t *testing.T) {
	// Pre-compute expected tree
	var list []merkletree.Content
	list = append(list, TestContent{x: "1"})
	list = append(list, TestContent{x: "2"})
	list = append(list, TestContent{x: "3"})
	list = append(list, TestContent{x: "4"})
	mt, _ := merkletree.NewTree(list)
	trustedRoot := toHex(mt.MerkleRoot())

	// Local node setup, partial
	// Assume has access to trustedRoot
	var contents []merkletree.Content
	contents = append(contents, TestContent{x: "1"})
	contents = append(contents, TestContent{x: "2"})
	contents = append(contents, TestContent{x: "3"})

	// Byzantine case, currently sending nothing
	// TODO: Since haves is empty it should return full contents?
	// XXX: Doesn't make sense to have tree hardcoded in other code
	var haves []string
	untrustedPayloads := pull("byzantine", trustedRoot, haves)
	content := TestContent{x: untrustedPayloads[0]}
	contents = append(contents, content)

	// XXX: is there no way to append to tree?
	untrusted := mt
	_ = untrusted.RebuildTreeWith(contents)
	untrustedRoot := toHex(untrusted.MerkleRoot())

	expect := (untrustedRoot != trustedRoot)
	if !expect {
        t.Errorf("Byzantine basic: Untrusted root %s and trusted root %s shouldn't match", untrustedRoot, trustedRoot)
    }
}