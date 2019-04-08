package main

import "fmt"
import "os"
import "github.com/ethereum/go-ethereum/crypto"
import "github.com/ethereum/go-ethereum/node"
import "github.com/ethereum/go-ethereum/swarm"
import bzzapi "github.com/ethereum/go-ethereum/swarm/api"

// Lets do here
// Create two nodes, then what
// Or just one node with some port
// Then other node in separate process
// Can do node hosting separately as well
// Then just use that API

// So A sends to B, and B receives it
// Later also use Feeds to post to own so B can check/pull
// Coffee first brb

func NewService() (node.Service, error) {

	// Create a node
	// TODO: Specify port and possibly data-dir
	// XXX: When do I use this?
	// cfg := &node.DefaultConfig
	// node, err := node.New(cfg)
	// if err != nil {
	// 	 fmt.Fprintf(os.Stderr, "Node failure: %v\n", err)
	// 	 os.Exit(1)
	// 	//return nil, fmt.Errorf("Node failure: %v", err)
	// }
	// fmt.Printf("Node: %v\n", node)

	// Generate keys
	// TODO: Load existing keys from file
	privKey, err := crypto.GenerateKey()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to generate keys: %v\n", err)
		os.Exit(1)
	}
	//fmt.Printf("Privkey %v:\n", privKey)

	// Create bzzconfig
	// TODO: Setup swarm port
	// XXX: What's difference between Privkey and EnodeKey in Init?
	bzzconfig := bzzapi.NewConfig()
	bzzconfig.Init(privKey, privKey)

	return swarm.NewSwarm(bzzconfig, nil)
}

func main() {
	fmt.Printf("Hello PSS\n")

	service, err := NewService()
	if err != nil {
		fmt.Fprint(os.Stderr, "Unable to start swarm service:\n", err)
		os.Exit(1)
	}
	fmt.Printf("Swarm service: %v\n", service)

	
}