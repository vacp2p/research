# Notes

Bloom filter and probability of false positives


## Questions

### How big is an envelope?

`[ Expiry, TTL, Topic, Data, Nonce ]` 4+4+4+arb+8, where arb is data field as
factor of 256 bytes (minus salt?), according to EIP627. Can't find.

512 bytes seems like minimum, and 4 kB max. Let's assume 1 kB for now.

**Question: How big is an envelope in Status? Does it change?**

### How many envelopes over some time period for a full node?

Running `time ./shh_basic_client --mainnet --watch --post --port=30000`, connected to all full nodes with a full bloom filter we get incoming messages:

`WRN 2019-10-14 13:05:55+09:00 Message Ingress Stats                      tid=9527 added=6 allowed=58 disallowed=281 disallowedBloom=0 disallowedPow=281 disallowedSize=0 duplicate=27 invalid=23 noHandshake=0`

Note that pow is incorrect, so that's 281+58 ~ 330 envelopes in total per minute.

Assuming this is representative for whole network load, we get ~2k envelopes per
hour and ~50k envelopes per 24h. This corresponds to roughly ~2mb/h and
~50mb/day, assuming below is accurate.

Note that in https://discuss.status.im/t/performance-of-mailservers/1215 we see
1467846 envelopes for 30days, which is ~50k/day. While this was in May, this is
another data point.

### How many per topic?

`time ./shh_basic_client --mainnet --watch --post --port=30000 | grep topicStr > foo.log` with same settings as above for 1 minute:

`wc -l foo.log` 159 entries, so half of above. Not sure why.

```
cat foo.log | grep 5C6C9B56 | wc -l
159
```

All are from that weird topic. Hypothesis: no one was using Status during this
minute. Lets run again. Sent 4 messages from mobile, public and private chat
(1). Plus launched Status app so discovery topic. Indeed:

```
oskarth@localhost /home/oskarth/git/nim-eth/tests/p2p> wc -l foo.log
664 foo.log
```

```
oskarth@localhost /home/oskarth/git/nim-eth/tests/p2p> cat foo.log | grep 5C6C9B56 | wc -l
186
```

Constant at roughly x3 a second.

```
oskarth@localhost /home/oskarth/git/nim-eth/tests/p2p> cat foo.log | grep F8946AAC | wc -l
432
```

Discovery topic, um that's a lot! Does this imply duplicate?

```
oskarth@localhost /home/oskarth/git/nim-eth/tests/p2p> cat foo.log | grep 9C22FF5F | wc -l
36
```

```
oskarth@localhost /home/oskarth/git/nim-eth/tests/p2p> cat foo.log | grep CD423760 | wc -l
10
```

Not quite sure what to make of this, tbh.

Lets run again, just launch app (30s): It's all in either 5C6C9B56 topic
(mystery), 126 (for 30s), or discovery F8946AAC 911 (30s)!

The discovery topic is going crazy.

Hypothesis: a lot of duplicate envelopes getting through here.

### How many envelopes have already been received?

Checking hashes during 30s run. Also go to app and send one message. 159 total hashes and

`0102C0C42044FDCAC2D64CAF7EF35AA759BEA21703EE8BA7AEFFD176E2280089` 4

```
oskarth@localhost /home/oskarth/git/nim-eth/tests/p2p> cat foo.log | awk '{print $8}' | sort | uniq -c 
      1 
      8 hash=0002B6BA794DD457D55D67AD68BB8C49C98791AFEF466534FC97E28062F763FB
      8 hash=00637F3882A2EFEC89CF40249DC59FDC9A049B78D42EDB6E116B0D76BE0AA523
      4 hash=0102C0C42044FDCAC2D64CAF7EF35AA759BEA21703EE8BA7AEFFD176E2280089
     24 hash=2D567B7E97FA2510A1299EA84F140B19DA0B2012BE431845B433BA238A22282C
     22 hash=40D7D3BCC784CC9D663446A9DFB06D55533F80799261FDD30E30CC70853572CE
     21 hash=707DA8C56605C57C930CE910F2700E379C350C845B5DAE20A9F8A6DBA4F59B2B
     24 hash=AC8C3ABE198ABE3BF286E80E25B0CFF08B3573F42F61499FB258F519C1CF9F18
     24 hash=C4C3D64886ED31A387B7AE57C904D702AEE78036E9446B30E964A149134B0D56
     24 hash=D4A1D17641BD08E58589B120E7F8F399D23DA1AF1BA5BD3FED295CD852BC17DA
```

For how many connected nodes is this? WhisperNodes is 24, so assuming that's
duplication factor. Urf. But for Status nodes this should be lower?

### How does this behave with light users?

### How does this vary with Bloom filters?

Scalability trades off privacy vs traffic. I.e .false positives = privacy =
bandwidth.

Bloom size is 512-bits, and we have m topics, which leads to some p false
positive rate.

Assuming optimal number of hash functions, k = (m/n) ln2. Note that this is set
to 3 in Whisper afaict.

https://hur.st/bloomfilter/?n=1000&p=&m=512&k=3

Woaha, so at 512 bits, k=3 the probability of false positives is 1% at ~50
topics, ~10% at 100 topics and essentially 1 at 1000 topics.

Which makes sense, since the bloom would be full by then. Question: is this
actual items in filter or universe? This is for all that filter is being tested
to.

You need about 10 bits per element or 1 byte. So 50 topics checks out. Um...
sigh.

Accurate that this means 1% traffic overhead if you listen to 50 topics? How
many topics does a normal app listen to? It quickly explodes! Actually is this
accurate? Because if you get 100% it isn't 100% of traffic, it is _all_ traffic.

topicMatch vs bloomMatch.

ok, 3 main factors:

1 big topics
  - discover, then 5k one
    - what happens
2. duplicate messages
  - number of peers
  - mailservers
3. bloom filter
  - false positive
  - direct api call
4. disconnect bad peers

offline case dominating over online
