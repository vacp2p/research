package main

//import "context"
import (
	"github.com/ethereum/go-ethereum/swarm/pss"
	"context"
	"fmt"
	"os"
	"time"
 	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/node"
//import "github.com/ethereum/go-ethereum/log"
	"github.com/ethereum/go-ethereum/p2p"
//import "github.com/ethereum/go-ethereum/p2p/enode"
//import "github.com/ethereum/go-ethereum/rpc"
	"github.com/ethereum/go-ethereum/swarm"
//import "github.com/ethereum/go-ethereum/swarm/network"
	bzzapi "github.com/ethereum/go-ethereum/swarm/api"
)

// Lets do here
// Create two nodes, then what
// Or just one node with some port
// Then other node in separate process
// Can do node hosting separately as well
// Then just use that API

// So A sends to B, and B receives it
// Later also use Feeds to post to own so B can check/pull
// Coffee first brb

func newNode() (*node.Node, error) {
	// Create a node
	// TODO: Specify port and possibly data-dir
	// XXX: When do I use this?
	cfg := &node.DefaultConfig
	return node.New(cfg)
}

func newService() func(ctx *node.ServiceContext) (node.Service, error) {
	return func(ctx *node.ServiceContext) (node.Service, error) {
		// Generate keys
		// TODO: Load existing keys from file
		privKey, err := crypto.GenerateKey()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Unable to generate keys: %v\n", err)
			os.Exit(1)
		}

		// Create bzzconfig
		// TODO: Setup swarm port
		// XXX: What's difference between Privkey and EnodeKey in Init?
		bzzconfig := bzzapi.NewConfig()
		bzzconfig.Init(privKey, privKey)

		return swarm.NewSwarm(bzzconfig, nil)
	}
}

func main() {
	fmt.Printf("Hello PSS\n")

	args := os.Args[1:]
	// if len(args) != 2 {
	// 	fmt.Fprintf(os.Stderr, "Wrong number of arguments: %s, need two\n", args)
	// 	os.Exit(1)
	// }
	fmt.Println("args", args[0], args[1])

	// New node
	node, err := newNode()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Node failure: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Node: %v\n", node)

	// New Swarm service
	service := newService()
	// if err != nil {
	// 	fmt.Fprint(os.Stderr, "Unable to start swarm service: %v\n", err)
	// 	os.Exit(1)
	// }
	//	fmt.Printf("Swarm service: %x\n", service)

	// Register service
	err = node.Register(service)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to register swarm service: %v\n", err)
		os.Exit(1)
	}

	// Start the node
	err = node.Start()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to start node: %v\n", err)
		os.Exit(1)
	}

	// TODO: Add other peer

	// Get RPC Client
	client, err := node.Attach()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to attach to client: %v\n", err)
	}
	fmt.Printf("RPC Client %v\v", client)
	
	// Simpler, there should be a stdlib fn for waitHealthy anyway
	time.Sleep(time.Second)

	var nodeinfo p2p.NodeInfo
	err = client.Call(&nodeinfo, "admin_nodeInfo")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to get node info: %v\n", err)
	}

	var baseaddr string
	err = client.Call(&baseaddr, "pss_baseAddr")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to get base addr: %v\n", err)
	}
	fmt.Println("baseAddr", baseaddr)

	var pubkey string
	err = client.Call(&pubkey, "pss_getPublicKey")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to get pss public key: %v\n", err)
	}
	fmt.Println("PublicKey", pubkey)

	var topic string
	err = client.Call(&topic, "pss_stringToTopic", "foo")

	// XXX: Wrong pubkey
	receiver := pubkey
	err = client.Call(nil, "pss_sendAsym", receiver, topic, common.ToHex([]byte("Hello world")))

	msgC := make(chan pss.APIMsg)
	sub, err := client.Subscribe(context.Background(), "pss", msgC, "receive", topic, false, false)

	// XXX: Blocking, etc? Yeah, so run in bg or so
	in := <-msgC
	fmt.Println("Received message", string(in.Msg), "from", fmt.Sprintf("%x", in.Key))


	fmt.Printf("All operations successfully completed.\n")

	// Teardown
	sub.Unsubscribe()
	client.Close()
	node.Stop()
}

// TODO: Here at the moment. Need to make sure it reads nodekey wrt right data dir
// And then adjust ports. Then we should be able to run
// go run hello_pss.go alice and hello_pss.go bob, and then it should be able to send and recv
//
// Then also integrate feeds