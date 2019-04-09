package main

//import "context"
import (
	"github.com/ethereum/go-ethereum/swarm/pss"
	"context"
	"fmt"
	"crypto/ecdsa"
	"os"
	"time"
	"io/ioutil"
	"log"
	"strconv"
	"github.com/ethereum/go-ethereum/common/hexutil"
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

// Two different node processes
// So A sends to B, and B receives it
// Later also use Feeds to post to own so B can check/pull

// XXX: Warning, this is bad design. Should use keystore for this.
func getHexPrivateKey() string {
	privateKey, err := crypto.GenerateKey()
	if err != nil {
		log.Fatal(err)
	}
	privateKeyBytes := crypto.FromECDSA(privateKey)

	// Debugging, etc
	fmt.Println("Private Key: ", hexutil.Encode(privateKeyBytes))
	fmt.Println("Private Key alt: ", hexutil.Encode(privateKeyBytes)[2:])
	publicKey := privateKey.Public()
	publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	if !ok {
		log.Fatal("error casting public key to ECDSA")
	}
	publicKeyBytes := crypto.FromECDSAPub(publicKeyECDSA)
	fmt.Println("Public Key: ", hexutil.Encode(publicKeyBytes[4:]))
	address := crypto.PubkeyToAddress(*publicKeyECDSA).Hex()
	fmt.Println("Address: ", address)

	return hexutil.Encode(privateKeyBytes)
}

func getPrivateKeyFromFile(keyfile string) *ecdsa.PrivateKey {
	contents, err := ioutil.ReadFile(keyfile)
	if err != nil {
		log.Fatal("Unable to read keyfile", keyfile)
	}
	println(string(contents))
	privateKeyBytes, err := hexutil.Decode(string(contents))
	if err != nil {
		log.Fatal("Unable to get private key bytes")
	}
	privateKey, err := crypto.ToECDSA(privateKeyBytes)
	if err != nil {
		log.Fatal("Unable to get private key")
	}
	publicKey := privateKey.Public()
	publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	if !ok {
		log.Fatal("error casting public key to ECDSA")
	}
	publicKeyBytes := crypto.FromECDSAPub(publicKeyECDSA)
	address := crypto.PubkeyToAddress(*publicKeyECDSA).Hex()
	fmt.Println("Private Key: ", hexutil.Encode(privateKeyBytes))
	fmt.Println("Public Key: ", hexutil.Encode(publicKeyBytes[4:]))
	fmt.Println("Address: ", address)

	return privateKey
}

// Create a node
func newNode(port int) (*node.Node, error) {
	cfg := &node.DefaultConfig
	cfg.DataDir = fmt.Sprintf("%s%d", ".data_", port)
	cfg.HTTPPort = port
	fmt.Printf("Current data directory is %s\n", cfg.DataDir)

	return node.New(cfg)
}

// XXX: This is so sloppy, passing privatekey around
func newService(privKey *ecdsa.PrivateKey) func(ctx *node.ServiceContext) (node.Service, error) {
	return func(ctx *node.ServiceContext) (node.Service, error) {
		// Create bzzconfig
		// TODO: Setup swarm port
		// XXX: What's difference between Privkey and EnodeKey in Init?
		bzzconfig := bzzapi.NewConfig()
		bzzconfig.Init(privKey, privKey)

		return swarm.NewSwarm(bzzconfig, nil)
	}
}

// TODO: Ensure node starts in light node so it doesn't eat up a lot of disk space

func run(port int, privateKey *ecdsa.PrivateKey) {
	// New node
	node, err := newNode(port)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Node failure: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("Node: %v\n", node)

	// New Swarm service
	// XXX: Yuck privateKey
	service := newService(privateKey)
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

func main() {
	fmt.Printf("Hello PSS\n")

	// If 1 arg and it is new then generate new
	// If 2 args, first is keyfile second port

	/// XXX: Bad CLI design
	// TODO: Pull this out to separate parseArgs function
	args := os.Args[1:]
	if len(args) == 1 {
		if args[0] == "new" {
			// TODO: Use keystore or something
			privateKey := getHexPrivateKey()
			ioutil.WriteFile("new.key", []byte(privateKey), 0644)
			log.Fatal("Thanks for the fish, your private key is now insecurely stored in new.key")
		} else {
			log.Fatal("Unknown argument, please use 'new' or two arguments (keyfile and port)")
		}
	} else if len(args) == 2 {
		keyfile := args[0]
		portArg := args[1]
		// XXX error handling
		privateKey := getPrivateKeyFromFile(keyfile)
		port, err := strconv.Atoi(portArg)
		if err != nil {
			log.Fatal("Unable to parse port argument", portArg)
		}
		// Start engines
		run(port, privateKey)
	} else {
		log.Fatal("Wrong number of arguments, should be one (new) or two (keyfile and port)")
	}
}

// TODO: Here at the moment. Need to make sure it reads nodekey wrt right data dir
// And then adjust ports. Then we should be able to run
// go run hello_pss.go alice and hello_pss.go bob, and then it should be able to send and recv
//
// Then also integrate feeds