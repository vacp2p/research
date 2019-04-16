package main

import "fmt"
import "log"
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
	log.Println("Merkle Root:" , mr)

	vt, err := t.VerifyTree()
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Verify Tree: ", vt)

	vc, err := t.VerifyContent(list[0])
	if err != nil {
		log.Fatal(err)
	}
	log.Println("Verify Content: ", vc)

	log.Println(t)

}