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
func getRoot(location string, groupID string) string {
	return "5f30cc80133b9394156e24b233f0c4be32b24e44bb3381f02c7ba52619d0febc"
}

// Pull gets difference between what you have and what you know you can have
// NOTE: This can happen from any untrusted location, as the integritry can be proven
// TODO: Should return a list of payloads
func pull(mr string, haves []string) []string {
	var diff []string
	diff = append(diff, "xxx")
	return diff
}

func main() {
	fmt.Printf("Hello Merkleslash\n")

	var list []merkletree.Content
	list = append(list, TestContent{x: "Hello"})
	list = append(list, TestContent{x: "Hi"})
	list = append(list, TestContent{x: "Hey"})
	list = append(list, TestContent{x: "Hola"})

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
	payloads := pull(newMR, emptyList)
	log.Println("Pulled payloads:", payloads)

	// TODO: Verify contents
}