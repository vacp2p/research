package main

import "testing"
import "log"
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

// Here's what I want to test:
// Full tree: C->A; C->B; B->h(3); B->h(4); h(4)->4
// Trusted root: C
// Get from untrusted root: A, h(3) ("small") and 4 ("big"). Through these pieces of data we can verify.
// What does this mean if you have or don't have e.g. A branch? (which can hide a lot of data)
// I guess this is difference between thin and full client.
// See: https://bitcoin.stackexchange.com/questions/50674/why-is-the-full-merkle-path-needed-to-verify-a-transaction
//
// Next question: how do we specify path? Index [0 1], etc.
// Lets try GetMerklePath
// Not clear exactly how it maps or changes as we rebuild tree but ok for now
// Now, how can we do partial rebuild here?
//
// As a client, I say I have A [x, y], h(3) [x, y]. And a trusted root hash.
// So I guess there are two ways the query can go: for a specific piece of data (how know?) and diff.
// Lets graph: https://notes.status.im/MLGgpdgqRzeyTqVWkl7gjg#

// Can use Whisper/mailservers as well for compatibility before Swarm Feeds ready, boom new topic

func printPath(mt merkletree.MerkleTree, item merkletree.Content, name string) {
	_, x, err := mt.GetMerklePath(item)
	log.Println("Path to", name, x)
	if err != nil {
		log.Fatal(err)
	}
}

// 4 nodes
// 2019/04/18 11:49:07 Path to 1 [1 1]
// 2019/04/18 11:49:07 Path to 2 [0 1]
// 2019/04/18 11:49:07 Path to 3 [1 0]
// 2019/04/18 11:49:07 Path to 4 [0 0]

// 5 nodes
// 2019/04/18 11:54:36 Path to 1 [1 1 1]
// 2019/04/18 11:54:36 Path to 2 [0 1 1]
// 2019/04/18 11:54:36 Path to 3 [1 0 1]
// 2019/04/18 11:54:36 Path to 4 [0 0 1]
// 2019/04/18 11:54:36 Path to 5 [1 1 0]

// XXX: Probably need a less naive implementation
// Yellow paper quote: 
// > The core of the trie, and its sole requirement in termsof the protocol specification,
// > is to provide a single value that identifies a given set of key-value pairs, which may be
// > either a 32-byte sequence or the empty byte sequence.
//
// So let's start there and happily rebuild





func TestPartialVerification(t *testing.T) {
	// Pre-compute expected tree

	// XXX: Have you heard of for loops
	var list []merkletree.Content
	item1 := TestContent{x: "1"}
	item2 := TestContent{x: "2"}
	item3 := TestContent{x: "3"}
	item4 := TestContent{x: "4"}
	item5 := TestContent{x: "5"}

	list = append(list, item1)
	list = append(list, item2)
	list = append(list, item3)
	list = append(list, item4)
	list = append(list, item5)

	mt, _ := merkletree.NewTree(list)
	//trustedRoot := toHex(mt.MerkleRoot())

	printPath(*mt, item1, "1")
	printPath(*mt, item2, "2")
	printPath(*mt, item3, "3")
	printPath(*mt, item4, "4")
	printPath(*mt, item5, "5")

	// print tree
	log.Print("TREE", mt.String())

	// // Local node setup, partial
	// // Assume has access to trustedRoot
	// var contents []merkletree.Content
	// contents = append(contents, TestContent{x: "1"})
	// contents = append(contents, TestContent{x: "2"})
	// contents = append(contents, TestContent{x: "3"})

	// // Byzantine case, currently sending nothing
	// // TODO: Since haves is empty it should return full contents?
	// // XXX: Doesn't make sense to have tree hardcoded in other code
	// var haves []string
	// untrustedPayloads := pull("good", trustedRoot, haves)
	// content := TestContent{x: untrustedPayloads[0]}
	// contents = append(contents, content)

	// // XXX: is there no way to append to tree?
	// untrusted := mt
	// _ = untrusted.RebuildTreeWith(contents)
	// untrustedRoot := toHex(untrusted.MerkleRoot())

	// expect := (untrustedRoot == trustedRoot)
	// if !expect {
    //     t.Errorf("Good basic: Untrusted root %s and trusted root %s should match", untrustedRoot, trustedRoot)
    // }
}