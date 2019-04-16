package main

import "fmt"
import "log"
import "encoding/hex"
import "crypto/sha256"
import "github.com/cbergoon/merkletree"

// Rough API

// eg swarm feeds, etc - any trusted point
// getRoot(method, groupID)

// list or merkle root and payment
// to untrusted node
// sync(root, [have], node) payment? 

//verify 
//slash
//court

// TODO: There should be a simple way to go from trustedMR and some partial content, and say whether
// (a) content is in MR with that trusted root (b) say if tree is complete

// Partial verification - illustration:
// C->A, C->B. B->h(3), B->h(4). C is trusted root hash that I have.
// From untrusted peer, I get data 4, h(3) and A, and can thus prove integrity, with partial fetch (4)

// define how untrusted nodes get in first place

// TestContent implements the Content interface provided by merkletree,
// it represents the content stored in the tree.
// NOTE: x can be a completely encrypted payload
type TestContent struct {
	x string
}

// CalculateHash hashes the value of a TestContent
func (t TestContent) CalculateHash() ([]byte, error) {
	h := sha256.New()
	if _, err := h.Write([]byte(t.x)); err != nil {
		return nil, err
	}

	return h.Sum(nil), nil
}

// Equals tests for equality of two Contents
func (t TestContent) Equals(other merkletree.Content) (bool, error) {
	return t.x == other.(TestContent).x, nil
}

// Get merkle root from trusted location
// TODO: Implement location/method logic and groupID dispatching, hardcoding for now

// NOTE: Built up from the following:
// var list []merkletree.Content
// list = append(list, TestContent{x: "Hello"})
// list = append(list, TestContent{x: "Hi"})
// list = append(list, TestContent{x: "Hey"})
// list = append(list, TestContent{x: "Hola"})
//
// t, err := merkletree.NewTree(list)
func getRoot(location string, groupID string) string {
	return "5f30cc80133b9394156e24b233f0c4be32b24e44bb3381f02c7ba52619d0febc"
}

// Pull gets difference between what you have and what you know you can have
// NOTE: This can happen from any untrusted location, as the integritry can be proven
// TODO: Should return a list of payloads
// XXX: For now, switch between good and bad case
func pull(location string, mr string, haves []string) []string {
	var diff []string
	// TODO: There's third case, not bad data but missing data
	// Also deal with multiple items
	if location == "byzantine" {
		diff = append(diff, "xxx")
	} else {
		diff = append(diff, "Hola")
	}
	return diff
}

func main() {
	fmt.Printf("Hello Merkleslash\n")

	var list []merkletree.Content
	list = append(list, TestContent{x: "Hello"})
	list = append(list, TestContent{x: "Hi"})
	list = append(list, TestContent{x: "Hey"})
	
	// XXX: Let's assume we don't have this part of the tree
	//list = append(list, TestContent{x: "Hola"})

	t, err := merkletree.NewTree(list)
	if err != nil {
		log.Fatal(err)
	}

	mr := t.MerkleRoot()
	mrHex := hex.EncodeToString(mr)
	log.Println("Merkle Root:" , mrHex)
	
	// mr2, err := hex.DecodeString(mrHex)
	// if err != nil {
	// 	log.Fatal(err)
	// }
	// log.Println("Merkle Root" , mr2)

	vt, err := t.VerifyTree()
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Verify Tree:", vt)

	vc, err := t.VerifyContent(list[0])
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Verify Content:", vc)

	//log.Println(t)

	// 1. Get trusted root
	newMR := getRoot("", "")
	log.Println("Trusted root:", newMR)

	// 2. Sync difference
	var emptyList []string

	// NOTE: Byzantine case
	location := "byzantine"
	payloads := pull(location, newMR, emptyList)
	//log.Println("Pulled payloads:", payloads)
	content := TestContent{x: payloads[0]}
	contents := list
	contents = append(contents, content)
	// Build up untrusted tree and compare it with contents
	untrusted := t
	// XXX: is there no way to append to tree?
	err = untrusted.RebuildTreeWith(contents)
	untrustedRoot := hex.EncodeToString(untrusted.MerkleRoot())
	log.Println("Untrusted root [Byzantine case]:", untrustedRoot)
	log.Println("Good data [Good case]?", untrustedRoot == newMR)

	// NOTE: Good case
	// TODO: partial case
	location2 := "good"
	payloads2 := pull(location2, newMR, emptyList)
	//log.Println("Pulled payloads:", payloads)
	content2 := TestContent{x: payloads2[0]}
	contents2 := list
	contents2 = append(contents2, content2)
	// Build up untrusted tree and compare it with contents
	untrusted2 := t
	// XXX: is there no way to append to tree?
	err = untrusted.RebuildTreeWith(contents)
	untrustedRoot2 := hex.EncodeToString(untrusted2.MerkleRoot())
	log.Println("Untrusted root [Good case]:", untrustedRoot2)
	log.Println("Good data [Good case]?", untrustedRoot2 == newMR)

}