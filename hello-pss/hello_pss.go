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
	//"log"
	"github.com/ethereum/go-ethereum/log"
	"strconv"
	"github.com/ethereum/go-ethereum/common/hexutil"
	"github.com/ethereum/go-ethereum/p2p/nat"
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

var (
	// logger
	Log = log.New("hello-pss", "*")
)

// XXX: Warning, this is bad design. Should use keystore for this.
func getHexPrivateKey() string {
	privateKey, err := crypto.GenerateKey()
	if err != nil {
		Log.Crit("can't generate private key", err)
	}
	privateKeyBytes := crypto.FromECDSA(privateKey)

	// Debugging, etc
	fmt.Println("Private Key: ", hexutil.Encode(privateKeyBytes))
	fmt.Println("Private Key alt: ", hexutil.Encode(privateKeyBytes)[2:])
	publicKey := privateKey.Public()
	publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	if !ok {
		log.Crit("error casting public key to ECDSA", err)
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
		log.Crit("Unable to read keyfile", keyfile)
	}
	println(string(contents))
	privateKeyBytes, err := hexutil.Decode(string(contents))
	if err != nil {
		log.Crit("Unable to get private key bytes", err)
	}
	privateKey, err := crypto.ToECDSA(privateKeyBytes)
	if err != nil {
		log.Crit("Unable to get private key", err)
	}
	publicKey := privateKey.Public()
	publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	if !ok {
		log.Crit("error casting public key to ECDSA", err)
	}
	publicKeyBytes := crypto.FromECDSAPub(publicKeyECDSA)
	address := crypto.PubkeyToAddress(*publicKeyECDSA).Hex()
	fmt.Println("Private Key: ", hexutil.Encode(privateKeyBytes))
	fmt.Println("Public Key: ", hexutil.Encode(publicKeyBytes[4:]))
	fmt.Println("Address: ", address)

	return privateKey
}

/////////////////////////////////////////////////////////////////////////////

//
func getp2pConfig(listenaddr string) p2p.Config {
	return p2p.Config{
			ListenAddr: listenaddr,
			MaxPeers:   25,
			NAT:        nat.Any(),
	}
}

// Create a node
func newNode(port int) (*node.Node, error) {
	cfg := &node.DefaultConfig
	cfg.DataDir = fmt.Sprintf("%s%d", ".data_", port)

	// XXX: Lol
	// XXX: 	cfg.P2P.ListenAddr = fmt.Sprintf(":%d", port), should work
	if port == 9600 {
		cfg.P2P = getp2pConfig(":30400")
	} else if port == 9601 {
		cfg.P2P = getp2pConfig(":30401")
	} else {
		log.Crit("Ports be fucked up", "yeah")
	}

	cfg.HTTPPort = port
	fmt.Printf("Current data directory is %s\n", cfg.DataDir)

	return node.New(cfg)
}

// XXX: This is so sloppy, passing privatekey around
func newService(bzzdir string, bzzport int, privKey *ecdsa.PrivateKey) func(ctx *node.ServiceContext) (node.Service, error) {
	return func(ctx *node.ServiceContext) (node.Service, error) {
		// Create bzzconfig
		// TODO: Setup swarm port
		// XXX: What's difference between Privkey and EnodeKey in Init?
		bzzconfig := bzzapi.NewConfig()
		bzzconfig.Path = bzzdir
		bzzconfig.Port = fmt.Sprintf("%d", bzzport)
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
	service := newService(node.InstanceDir(), port, privateKey)
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

	// TODO: Add other peer?

	// Get RPC Client
	client, err := node.Attach()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to attach to client: %v\n", err)
	}
	// XXX: Not readable
	fmt.Printf("RPC Client %v\v", client)
	
	// Simpler, there should be a stdlib fn for waitHealthy anyway
	time.Sleep(time.Second * 3)

	// XXX: Not readable
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

	// XXX: Same with baseaddr
	// 0xd5ac92dd8f593ea7aabf5cfdb35d4d29d87316ffe3ae081750054168e147eb42
	bobBaseAddr := "0xb208b76c916d5eb84c118c0076b35828f0728a416537786f4515dd6608c4874d"
	fmt.Println("BobbaseAddr PSS", bobBaseAddr)

	// XXX: This is separate from node generated key, so want to save this contacts or so
	// f(alice/bob.key, 9600/9601), not confirmed if it is stable if port changes
	// alice: 0x04c56131d8ded90e79b76b97f26e8fc032597886ff68ab6557f91c4bf1ae46eab94415c6df30bb6479cf40f811977bb2b237787f5b807d97191f7a994a558633e0
	// bob: 0x04cbd6b75038f2d1e4e8e2754ffadecaaa8d2fdbbb29311dc82a8e1880fce4576f86e3d87ab360bcdde1aaf9a01a2cf232be95684a1152a735ccb4200495e4145c

	var topic string
	err = client.Call(&topic, "pss_stringToTopic", "foo")

	// Ok, now what?
	// XX: Also who is pubkey here

	// XXX: Wrong pubkey
	//receiver := pubkey
	bobPubKey := "0x04cbd6b75038f2d1e4e8e2754ffadecaaa8d2fdbbb29311dc82a8e1880fce4576f86e3d87ab360bcdde1aaf9a01a2cf232be95684a1152a735ccb4200495e4145c"
	receiver := bobPubKey
	fmt.Println("BobPublicKey PSS", bobPubKey)

	// XXX: I don't understand how baseAddr and public key interact
	// XXX: I also don't understand why you need to register public key
	err = client.Call(nil, "pss_setPeerPublicKey", bobPubKey, topic, bobBaseAddr)

	// XXX: Shouldn't it at least send a message to itself?
	// XXX: Add log stuff to see swarm state

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

func init() {
	// NOTE: taken from ethereum-samples
	hs := log.StreamHandler(os.Stderr, log.TerminalFormat(true))
	loglevel := log.LvlInfo
	// TODO: Setup flag and -v option
	// if *verbose {
	// 	loglevel = log.LvlTrace
	// }
	// XXX Trace for now
	loglevel = log.LvlTrace
	hf := log.LvlFilterHandler(loglevel, hs)
	h := log.CallerFileHandler(hf)
	log.Root().SetHandler(h)
}
 
func main() {
	fmt.Printf("Hello PSS\n")

	// If 1 arg and it is new then generate new
	// If 2 args, first is keyfile second port

	/// XXX: Bad CLI design
	// TODO: Use golang flags
	// TODO: Pull this out to separate parseArgs function
	args := os.Args[1:]
	if len(args) == 1 {
		if args[0] == "new" {
			// TODO: Use keystore or something
			privateKey := getHexPrivateKey()
			ioutil.WriteFile("new.key", []byte(privateKey), 0644)
			log.Crit("Thanks for the fish, your private key is now insecurely stored in new.key", args)
		} else {
			log.Crit("Unknown argument, please use 'new' or two arguments (keyfile and port)", args)
		}
	} else if len(args) == 2 {
		keyfile := args[0]
		portArg := args[1]
		// XXX error handling
		privateKey := getPrivateKeyFromFile(keyfile)
		port, err := strconv.Atoi(portArg)
		if err != nil {
			log.Crit("Unable to parse port argument", portArg)
		}
		// Start engines
		run(port, privateKey)
	} else {
		log.Crit("Wrong number of arguments, should be one (new) or two (keyfile and port)", args)
	}
}

// TODO: Here at the moment. Need to make sure it reads nodekey wrt right data dir DONE
// And then adjust ports DONE. Then we should be able to run
// go run hello_pss.go alice and hello_pss.go bob, and then it should be able to send and recv
//
// Then also integrate feeds


// XXX Ok the problem is https://github.com/ethereum/go-ethereum/blob/master/swarm/pss/pss.go#L766
// Which happens due to not being connected, so manually and possibly some local network stuff here
