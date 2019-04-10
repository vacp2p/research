package main

import (
	"github.com/ethereum/go-ethereum/swarm/pss"
	"context"
	"bufio"
	"fmt"
	"crypto/ecdsa"
	"os"
	"time"
	"io/ioutil"
	"github.com/ethereum/go-ethereum/log"
	"strconv"
	"github.com/ethereum/go-ethereum/common/hexutil"
	"github.com/ethereum/go-ethereum/p2p/nat"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/node"
	"github.com/ethereum/go-ethereum/p2p"
	"github.com/ethereum/go-ethereum/rpc"
	"github.com/ethereum/go-ethereum/swarm"
	bzzapi "github.com/ethereum/go-ethereum/swarm/api"
)

var (
	// logger
	Log = log.New("hello-pss", "*")
)

// TODO: Ensure node starts in light node so it doesn't eat up a lot of disk space

// XXX: Warning, this is bad design. Should use keystore for this.
func getHexPrivateKey() string {
	privateKey, err := crypto.GenerateKey()
	if err != nil {
		Log.Crit("can't generate private key", err)
	}
	privateKeyBytes := crypto.FromECDSA(privateKey)

	// Debugging and basic key operations
	//publicKey := privateKey.Public()
	//publicKeyECDSA, ok := publicKey.(*ecdsa.PublicKey)
	//if !ok {
	//	log.Crit("error casting public key to ECDSA", err)
	//}
	//publicKeyBytes := crypto.FromECDSAPub(publicKeyECDSA)
	//address := crypto.PubkeyToAddress(*publicKeyECDSA).Hex()
	//fmt.Println("Private Key: ", hexutil.Encode(privateKeyBytes))
	//fmt.Println("Public Key: ", hexutil.Encode(publicKeyBytes[4:]))
	//fmt.Println("Address: ", address)

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

	return privateKey
}

// XXX: This shouldn't be needed
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

	// XXX: 	cfg.P2P.ListenAddr = fmt.Sprintf(":%d", port), should work
	if port == 9600 {
		cfg.P2P = getp2pConfig(":30400")
	} else if port == 9601 {
		cfg.P2P = getp2pConfig(":30401")
	} else {
		log.Crit("Ports be fucked up", "yeah")
	}

	cfg.HTTPPort = port
	cfg.IPCPath = "bzz.ipc"
	//fmt.Printf("Current data directory is %s\n", cfg.DataDir)

	return node.New(cfg)
}

func listenForMessages(msgC chan pss.APIMsg) {
	for {
		in := <-msgC
		// XXX: Who is in.key really? want readable public key here
		// XXX: The UX is an illusion
		fmt.Println("Alice:", string(in.Msg))
		//fmt.Println("\nReceived message", string(in.Msg), "from", fmt.Sprintf("%x", in.Key))
	}
}

// XXX: Lame signature, should be may more compact
func runREPL(client *rpc.Client, receiver string, topic string) {
	fmt.Println("I am Alice, and I am ready to send messages.")
	fmt.Printf("> ")
	// Basic REPL functionality
	scanner := bufio.NewScanner(os.Stdin)	
	for scanner.Scan() {
		input := scanner.Text()
		//sendMessage(input)
		sendMessage(client, receiver, topic, input)
		fmt.Printf("> ")
	}
	if err := scanner.Err(); err != nil {
		fmt.Println("Unable to read input", err)
		os.Exit(1)
	}
}

func mockPassiveREPL() {
	// Poor Bob can only listen to messages, forever and ever
	// Until one day...when he snaps and quits with ctrl-D
	// Bob first shows loyalty, he never speaks, and then he exits
	// Allowing Bob to speak means he'll be less likely to exit
	for { }
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


func run(port int, privateKey *ecdsa.PrivateKey) {
	// New node
	node, err := newNode(port)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Node failure: %v\n", err)
		os.Exit(1)
	}
	//fmt.Printf("Node: %v\n", node)

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

	// Get RPC Client
	// ipcEndpoint
	client, err := node.Attach()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to attach to client: %v\n", err)
	}

	// TODO: Refactor to have this addpeer workaround in separate function
	// XXX: How to detect/derive this? Right now just grepping enode
	enodeA := "enode://395a074c059143a68473bcf7edb3bae72bc930cfef5c92399401cedd76c493014d29e75ed1833fe45a2c0e04f0e9f9c64bf029c9c0fb646aa23690e945d70193@127.0.0.1:30400"
	enodeB := "enode://f716c8cc7cc6674d8332ae1a3fb7f4776285095dc372c20a508e22e7d0a9c006b1626aab7b45802d99957b86bf1c0c14d9ba91df87528c735751e92dd96fa88f@127.0.0.1:30401"

	// XXX: Eh
	var res1 bool
	err = client.Call(&res1, "admin_addPeer", enodeA)
	if err != nil {
		log.Crit("Unable to add peer", err)
	}

	var res2 bool
	err = client.Call(&res2, "admin_addPeer", enodeB)
	if err != nil {
		log.Crit("Unable to add peer", err)
	}
	//fmt.Println("*** added some peers probably ", res1, res2)
	// TODO: admin get peers here?

	// XXX: More robust health check here
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
	//fmt.Println("baseAddr", baseaddr)

	var pubkey string
	err = client.Call(&pubkey, "pss_getPublicKey")
	if err != nil {
		fmt.Fprintf(os.Stderr, "Unable to get pss public key: %v\n", err)
	}
	//fmt.Println("PublicKey", pubkey)

	// XXX: Same with baseaddr
	// 0xd5ac92dd8f593ea7aabf5cfdb35d4d29d87316ffe3ae081750054168e147eb42
	bobBaseAddr := "0xb208b76c916d5eb84c118c0076b35828f0728a416537786f4515dd6608c4874d"
	//fmt.Println("BobbaseAddr PSS", bobBaseAddr)

	// XXX: This is separate from node generated key, so want to save this contacts or so
	// f(alice/bob.key, 9600/9601), not confirmed if it is stable if port changes
	// alice: 0x04c56131d8ded90e79b76b97f26e8fc032597886ff68ab6557f91c4bf1ae46eab94415c6df30bb6479cf40f811977bb2b237787f5b807d97191f7a994a558633e0
	// bob: 0x04cbd6b75038f2d1e4e8e2754ffadecaaa8d2fdbbb29311dc82a8e1880fce4576f86e3d87ab360bcdde1aaf9a01a2cf232be95684a1152a735ccb4200495e4145c

	var topic string
	err = client.Call(&topic, "pss_stringToTopic", "foo")

	bobPubKey := "0x04cbd6b75038f2d1e4e8e2754ffadecaaa8d2fdbbb29311dc82a8e1880fce4576f86e3d87ab360bcdde1aaf9a01a2cf232be95684a1152a735ccb4200495e4145c"
	receiver := bobPubKey
	//fmt.Println("BobPublicKey PSS", bobPubKey)

	// XXX: I don't understand how baseAddr and public key interact
	// XXX: I also don't understand why you need to register public key
	err = client.Call(nil, "pss_setPeerPublicKey", bobPubKey, topic, bobBaseAddr)

	msgC := make(chan pss.APIMsg)
	sub, err := client.Subscribe(context.Background(), "pss", msgC, "receive", topic, false, false)	

	// XXX: Hack to make sure ready state
	time.Sleep(time.Second * 3)



	// XXX: Hacky
	// TODO: Replace with REPL-like functionality
	if port == 9600 {

		// NOTE: We assume here we are ready to actually send messages, so we REPL here
		// XXX: Only running REPL for Alice Sender for now
		runREPL(client, receiver, topic)
	} else if port == 9601 {
		fmt.Println("I am Bob, and I am ready to receive messages")
		go listenForMessages(msgC)
		mockPassiveREPL()
	} else {
		fmt.Println("*** I don't know who you are")
		os.Exit(1)
	}

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
	loglevel = log.LvlDebug //trace
	hf := log.LvlFilterHandler(loglevel, hs)
	h := log.CallerFileHandler(hf)
	log.Root().SetHandler(h)
}

// XXX: Ensure signature, also probably better with client as context but meh
func sendMessage(client *rpc.Client, receiver string, topic string, input string) {
	//fmt.Println("Input:", input)
	err := client.Call(nil, "pss_sendAsym", receiver, topic, common.ToHex([]byte(input)))
	if err != nil {
		fmt.Println("Error sending message through RPC client", err)
		os.Exit(1)
	}
}

func main() {
	fmt.Printf("Hello PSS\n")
	fmt.Printf("Setting up node and connecting to the network...\n")

	// TODO: Then, integrate feed and update there too

	// TODO: Bad CLI design, use golang flags
	// TODO: Pull this out to separate parseArgs function
	args := os.Args[1:]
	if len(args) == 1 {
		if args[0] == "new" {
			// TODO: Use keystore or something more sane
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