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

func toHex(merkletree []byte) string {
	return hex.EncodeToString(merkletree)
}

func fromHex(merkletree string) []byte {
	res, err := hex.DecodeString(merkletree)
	if err != nil {
		log.Fatal(err)
	}
	return res
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

// TODO: see how this can be used: mt.GetMerklePath

func getTrustedRoot(location string, groupID string) string {
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
		diff = append(diff, "4")
	}
	return diff
}

func main() {
	fmt.Printf("Hello Merkleslash, see tests\n")
}