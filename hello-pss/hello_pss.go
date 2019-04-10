package main

import (
	"github.com/ethereum/go-ethereum/swarm/storage/feed/lookup"
	"github.com/ethereum/go-ethereum/swarm/pss"
	"context"
	"bufio"
	"fmt"
	"crypto/ecdsa"
	"os"
	"bytes"
	"time"
	"io/ioutil"
	"encoding/json"
	"github.com/ethereum/go-ethereum/log"
	"strconv"
	"github.com/ethereum/go-ethereum/common/hexutil"
	"github.com/ethereum/go-ethereum/p2p/nat"
	"github.com/ethereum/go-ethereum/common"
	"github.com/ethereum/go-ethereum/crypto"
	"github.com/ethereum/go-ethereum/node"
	"github.com/ethereum/go-ethereum/p2p"
	"github.com/ethereum/go-ethereum/swarm/storage/feed"
	"github.com/ethereum/go-ethereum/rpc"
	"github.com/ethereum/go-ethereum/swarm"
//	"github.com/ethereum/go-ethereum/swarm/network"
	bzzapi "github.com/ethereum/go-ethereum/swarm/api"
	feedsapi "github.com/ethereum/go-ethereum/swarm/api/client"

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
	} else if port == 9602 {
		cfg.P2P = getp2pConfig(":30402")
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

		// XXX: parsing logic should be same for pull from feed
		parsed := deserialize(string(in.Msg))

		//fmt.Println("Alice old:", string(in.Msg))
		// XXX Only one parent
		// TODO: Get all the parents here
		fmt.Println("Alice:", string(parsed.Text), "- parent0:", string(parsed.Parents[0]))

		//fmt.Println("\nReceived message", string(in.Msg), "from", fmt.Sprintf("%x", in.Key))
	}
}

// TODO: Error handling if fail
func postToFeed(client *rpc.Client, signer *feed.GenericSigner, receiver string, topic string, input string) {
	// For creating manifest, then posting, then finally getting

	// Create a new feed with user and topic.
	f := new(feed.Feed)
	f.User = signer.Address()
	f.Topic, _ = feed.NewTopic("bob", nil)
	query := feed.NewQueryLatest(f, lookup.NoClue)

	// XXX: Ok feeds seems fairly broken
	//httpClient := feedsapi.NewClient("https://swarm-gateways.net")

	// Cheating
	httpClient := feedsapi.NewClient("http://localhost:9602") // XXX 9600

	// local sender alice
	//httpClient := feedsapi.NewClient("http://localhost:9600")

	//XXX doesnt even work
	//httpClient := feedsapi.NewClient("https://swarm-gateways.net")

	// XXX: Post to multiple feeds?

	//fmt.Println("signer Address: ", f.User.Hex())

	request, err := httpClient.GetFeedRequest(query, "")
	if err != nil {
		fmt.Printf("Error retrieving feed status: %s", err.Error())
	}

	request.SetData([]byte(input))
	if err = request.Sign(signer); err != nil {
		fmt.Printf("Error signing feed update: %s", err.Error())
	}
	//fmt.Println("*** signed request", request)

	// manifest, err := httpClient.CreateFeedWithManifest(request)
	// if err != nil {
	// 	fmt.Printf("Error getting manifest: %s", manifest)
	// }
	// fmt.Println("MANIFEST:", manifest)
	
	// XXX: What do I want to do with feeds manifest?
	// 567f611190b2758fa625b3be14b2b9becf6f0e8887015b7c40d6cbe0e5fa14aa

	// Success: this works, also from 9601 Bob:
	//  curl 'http://localhost:9600/bzz-feed:/?user=0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259&name=bob'

	// XXX: Why do we need the second argument manifestAddressOrDomain?
	// It's already baked into httpClient and query.
	// Indeed:
	// > You only need to provide either manifestAddressOrDomain or Query to QueryFeed(). Set to "" or nil respectively.
	// response, err := httpClient.QueryFeed(query, "")
	// if err != nil {
	// 	fmt.Println("QueryFeed error", err)
	// }
	// buf := new(bytes.Buffer)
	// buf.ReadFrom(response)
	// feedStr := buf.String()
	// fmt.Println("Feed result: ", feedStr)


	// XXX Want to set level and time?
	// POST /bzz-feed:/?topic=<TOPIC>&user=<USER>&level=<LEVEL>&time=<TIME>&signature=<SIGNATURE>
 
	err = httpClient.UpdateFeed(request)
	if err != nil {
		fmt.Printf("Error updating feed: %s", err.Error())
	}
}

type message struct {
	Text string `json:"text"`
	Parents []string `json:"parents"`
}

// check sign logic bits version etc

// XXX: Lame signature, should be may more compact
func runREPL(client *rpc.Client, signer *feed.GenericSigner, receiver string, topic string) {
	fmt.Println("I am Alice, and I am ready to send messages.")

	fmt.Printf("> ")
	// Basic REPL functionality
	scanner := bufio.NewScanner(os.Stdin)	
	for scanner.Scan() {
		input := scanner.Text()
		//sendMessage(input)
		sendMessage(client, signer, receiver, topic, input)
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
//	for { }
//	fmt.Println("I am Bob or Charlie, and I can't speak right now.")

	fmt.Printf("> ")
	// Basic REPL functionality
	scanner := bufio.NewScanner(os.Stdin)	
	for scanner.Scan() {
		input := scanner.Text()
		fmt.Println("Echo", input)
		//sendMessage(input)
		//sendMessage(client, signer, receiver, topic, input)
		fmt.Printf("> ")
	}
	if err := scanner.Err(); err != nil {
		fmt.Println("Unable to read input", err)
		os.Exit(1)
	}
	// Ok maybe this is a bad idea?
}

// Get messages from feed
func pullMessages() {

	// Success: this works, also from 9601 Bob. Replicate with Go API
	//  curl 'http://localhost:9600/bzz-feed:/?user=0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259&name=bob'

	// Querying with local node
	// XXX Maybe this is a bad idea, what about gateway?

	/// Cheating
	httpClient := feedsapi.NewClient("http://localhost:9602") // XXX 9601 
	
	// local receiver bob
	//httpClient := feedsapi.NewClient("http://localhost:9601")

	// XXX: Probably not a great idea, but we need to make sure it is healthy etc
	//httpClient := feedsapi.NewClient("https://swarm-gateways.net")

	// Create a new feed with user and topic.
	f := new(feed.Feed)

	// Alice's dadress
	f.User = common.HexToAddress("0xBCa21d9c6031b1965a9e0233D9B905d2f10CA259")
	f.Topic, _ = feed.NewTopic("bob", nil)
	query := feed.NewQueryLatest(f, lookup.NoClue)

	// Look up feed results
	// XXX: Why do we need the second argument manifestAddressOrDomain?
	// It's already baked into httpClient and query.
	response, err := httpClient.QueryFeed(query, "")
	if err != nil {
		fmt.Println("QueryFeed error", err)
	}
	buf := new(bytes.Buffer)
	buf.ReadFrom(response)
	feedStr := buf.String()

	parsed := deserialize(feedStr)

	//fmt.Println("Feed result old: ", feedStr)
	fmt.Println("Feed result: ", parsed.Text, "- parent0:", parsed.Parents[0])

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

func addPeer(client *rpc.Client, enode string) {
//	fmt.Println("addPeer", enode)
 	var res bool
	err := client.Call(&res, "admin_addPeer", enode)
	if err != nil {
		fmt.Println("Lets also print unable to add peer here", err)
		log.Crit("Unable to add peer", err)
	}
//	fmt.Println("addPeer res", res)
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

	// XXX: Broke discovery or something so not connected to many peers, adding some manually as a hack
	// All have caps: ["bzz/8", "hive/8", "pss/2", "stream/8"] and came from standard swarm setup
	//static1 := "enode://058f55a4bfe3ef7c3718ac035cd0bc5ce7646d8acc95930036145a0bcb337eb7769b015cb404201e63e48b261962728554e03c2ffca0a80e857f2c8ad1df02f4@52.232.7.187:30400?discport=0"
	// static2 := "enode://a5d7168024c9992769cf380ffa559a64b4f39a29d468f579559863814eb0ae0ed689ac0871a3a2b4c78b03297485ec322d578281131ef5d5c09a4beb6200a97a@52.232.7.187:30442?discport=0"
	// static3 := "enode://1ffa7651094867d6486ce3ef46d27a052c2cb968b618346c6df7040322c7efc3337547ba85d4cbba32e8b31c42c867202554735c06d4c664b9afada2ed0c4b3c@52.232.7.187:30412?discport=0"

	// Ok, seems like there's an issue with hopCount being exceeded
	// Additionally, unable to geth attach to b receiver specifically
	// Let's try adding intermediate node
	// All it does is...run? Hm.

	// local third node - this has too much stuff in it
	//enodeC := "enode://a87e2c53089904ec916e5b0c06524fa5dbfd69dc31f5446e7937cd1cdbcc61ed6173d17474814a778129ea0ce8b0fdfc4d4b4e9845a82f00358aa548975f6eae@127.0.0.1:30399"

	enodeC := "enode://99c926eaa4276b79b255baaa8562ba124d7b7ecc81fc05e40679d4219ccbf01ec64f9068314cf20372e76d6dca4f02adf5db6570bc6774263fb1a2f7fc890bb6@127.0.0.1:30402"
	
	// open internet
	enodeD := "enode://99c926eaa4276b79b255baaa8562ba124d7b7ecc81fc05e40679d4219ccbf01ec64f9068314cf20372e76d6dca4f02adf5db6570bc6774263fb1a2f7fc890bb6@127.0.0.1:30402"

	// // Consider conditionally adding peers, get who is self.
	// if port == 9600 {
	// 	addPeer(client, enodeB)
	// 	} else if port == 9601 {
	// 		addPeer(client, enodeA)
	// 	}
	// addPeer(client, enodeC)

	addPeer(client, enodeA)
	addPeer(client, enodeB)
	addPeer(client, enodeC)
	addPeer(client, enodeD)

	// addPeer(client, static1)
	// addPeer(client, static2)
	// addPeer(client, static3)

	// // XXX: Eh
	// var res1 bool
	// err = client.Call(&res1, "admin_addPeer", enodeA)
	// if err != nil {
	// 	log.Crit("Unable to add peer", err)
	// }

	// var res2 bool
	// err = client.Call(&res2, "admin_addPeer", enodeB)
	// if err != nil {
	// 	log.Crit("Unable to add peer", err)
	// }
	//fmt.Println("*** added some peers probably ", res1, res2)
	// TODO: admin get peers here?

	// TODO: admin get peers ensure?

	// XXX: More robust health check here
	// Simpler, there should be a stdlib fn for waitHealthy anyway
	time.Sleep(time.Second * 3)

	// Hypothesis for why feed updates aren't spread - kademlia connectivity is bad
	// Test it by measuring it
	// HEALTH CHECK
	//func (k *Kademlia) GetHealthInfo(pp *PeerPot) *Health {
	//network.Kademlia
	// TODO check how do


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
	err = client.Call(&topic, "pss_stringToTopic", "bob")

	bobPubKey := "0x04cbd6b75038f2d1e4e8e2754ffadecaaa8d2fdbbb29311dc82a8e1880fce4576f86e3d87ab360bcdde1aaf9a01a2cf232be95684a1152a735ccb4200495e4145c"
	receiver := bobPubKey
	//fmt.Println("BobPublicKey PSS", bobPubKey)

	// XXX: I don't understand how baseAddr and public key interact
	// XXX: I also don't understand why you need to register public key
	err = client.Call(nil, "pss_setPeerPublicKey", bobPubKey, topic, bobBaseAddr)

	msgC := make(chan pss.APIMsg)
	// Nope, everyone gets to listen on that topic, also maybe it should be same?
	// Does it matter for feeds?
	// XXX: Let'ss try
	sub, err := client.Subscribe(context.Background(), "pss", msgC, "receive", topic, false, false)

	// Only Bob gets to listen
	// if port == 9601 {
	// 	sub, err := client.Subscribe(context.Background(), "pss", msgC, "receive", topic, false, false)
	// 	if err != nil {
	// 		fmt.Println("Error subscribing to topic", err)
	// 	}
	// 	defer sub.Unsubscribe()
	// }

	// XXX: Hack to make sure ready state
	time.Sleep(time.Second * 3)

	signer := feed.NewGenericSigner(privateKey)

	// XXX: Hacky
	// TODO: Replace with REPL-like functionality
	if port == 9600 {

		// NOTE: We assume here we are ready to actually send messages, so we REPL here
		// XXX: Only running REPL for Alice Sender for now
		runREPL(client, signer, receiver, topic)
	} else if port == 9601 {
		fmt.Println("I am Bob, and I am ready to receive messages")

		fmt.Println("First, let's see if we missed something while gone")
		pullMessages()
		fmt.Println("Alright, up to speed, let's listen in background")
		go listenForMessages(msgC)
		mockPassiveREPL()
	} else if port == 9602 {
		fmt.Println("I am Charlie, I'm just chilling here")
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
	//loglevel = log.LvlTrace //trace

	hf := log.LvlFilterHandler(loglevel, hs)
	h := log.CallerFileHandler(hf)
	log.Root().SetHandler(h)
}

// TODO: The swarm hash should match up with message ID
// How does this impact design?

// XXX: Ensure signature, also probably better with client as context but meh
func sendMessage(client *rpc.Client, signer *feed.GenericSigner, receiver string, topic string, input string) {
	//fmt.Println("Input:", input)

	// From input and parents, construct message
	// TODO: Hardcode parents now, later need to upload and keep track of
	msg := message{Text: input, Parents: []string{"foo", "bar"}}
	// XXX: Direct to byte and toHex?
	payload := serialize(msg)

	err := client.Call(nil, "pss_sendAsym", receiver, topic, common.ToHex([]byte(payload)))
	if err != nil {
		fmt.Println("Error sending message through RPC client", err)
		os.Exit(1)
	}

	// Also post to feed
	// XXX: Currently hardcoded to plaintext name, could be hash of two pubkeys e.g.
	// TODO: If any errors with this, show this

	// XXX payload fine?
	postToFeed(client, signer, receiver, topic, payload)
}

func serialize(msg message) string {
	//msg := &message{Text: "hi", Parents: []string{"foo", "bar"}}
	payload, err := json.Marshal(msg)
	if err != nil {
		fmt.Println("Unable to marshal into JSON", err)
		os.Exit(1)
	}
	strJSON := string(payload) 
	//fmt.Println("json payload", strJSON)
	return strJSON
}

func deserialize(strJSON string) message {
	msg := message{}
	json.Unmarshal([]byte(strJSON), &msg)
	// fmt.Println(msg2)
	return msg
}

func main() {
	fmt.Printf("Hello PSS\n")
	fmt.Printf("Setting up node and connecting to the network...\n")

	// Example
	// msg := message{Text: "hi", Parents: []string{"foo", "bar"}}
	// payload := serialize(msg)
	// parsed := deserialize(payload)
	// fmt.Println(parsed.Parents[0])

	// TODO: Then, integrate feed and update there too
	// Cool, here ATM.
	// Then we probably need some message deps
	// TODO: As Alice we want to do a basic Feed post
	// TODO: Then As Bob we want to do a basic Feed get pull, at startup or so
	// Possibly ability to toggle this
	// XXX: Actually how connected is this to the rest of the network? Who will store it?
	// Create feed first

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