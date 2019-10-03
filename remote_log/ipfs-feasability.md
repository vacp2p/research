# IPFS as a remote log

Checking basic feasability and flow.

```
# Remote log over IPFS and IPNS
# Basic feasibility check

# 0. Run `ipfs daemon` in background

# 1. Upload first message to CAS
> cat foo
1 hello
> cat foo | ipfs add
added QmPvE58XgBFSAzQMWZ3abuSqfTeNV91hapa8gyAL18a9TP QmPvE58XgBFSAzQMWZ3abuSqfTeNV91hapa8gyAL18a9TP
 8 B / 8 B [==================================================================================================] 100.00%

# 2. Generate PKI namespace for a specific NS log
> ipfs key gen --type=rsa --size=2048 mykey
QmSWkQxeTY9wfCF3t7n26g7NDbTHYAVqdcevoQVXBQ5ybe
> ipfs key list -l
oskarth@localhost /home/oskarth> ipfs key list -l
QmTQMzSQhDW1FTDo328ds8mBeQDjvYqFTzvdyF4A9VWg9q self  
QmSWkQxeTY9wfCF3t7n26g7NDbTHYAVqdcevoQVXBQ5ybe mykey 

# 3. Update NS
# XXX: This command is quite slow
> ipfs name publish --key=mykey QmPvE58XgBFSAzQMWZ3abuSqfTeNV91hapa8gyAL18a9TP

# 4. Resolve NS and get message from CAS
> ipfs name resolve QmSWkQxeTY9wfCF3t7n26g7NDbTHYAVqdcevoQVXBQ5ybe
/ipfs/QmPvE58XgBFSAzQMWZ3abuSqfTeNV91hapa8gyAL18a9TP
> ipfs cat /ipfs/QmPvE58XgBFSAzQMWZ3abuSqfTeNV91hapa8gyAL18a9TP
1 hello

# 5. Upload new message to CAS
> cat bar | ipfs add
added QmYa4KRuvXvuTMxL57qKbRdkQBdLMeLevZ4a2emT4yByJJ QmYa4KRuvXvuTMxL57qKbRdkQBdLMeLevZ4a2emT4yByJJ
 5 B / 5 B [==================================================================================================] 100.00%

# 6. Update NS with new message
> ipfs name publish --key=mykey QmYa4KRuvXvuTMxL57qKbRdkQBdLMeLevZ4a2emT4yByJJ
Published to QmSWkQxeTY9wfCF3t7n26g7NDbTHYAVqdcevoQVXBQ5ybe: /ipfs/QmYa4KRuvXvuTMxL57qKbRdkQBdLMeLevZ4a2emT4yByJJ

# 7. Resolve NS and get second message
oskarth@localhost /home/oskarth> ipfs name resolve QmSWkQxeTY9wfCF3t7n26g7NDbTHYAVqdcevoQVXBQ5ybe
/ipfs/QmYa4KRuvXvuTMxL57qKbRdkQBdLMeLevZ4a2emT4yByJJ
oskarth@localhost /home/oskarth> ipfs cat /ipfs/QmYa4KRuvXvuTMxL57qKbRdkQBdLMeLevZ4a2emT4yByJJ
2 h1
```

## Notes

- Pin locally
- Pinning services for altruistic mode?
- Diff interface from Swarm Feeds with topic subspace vs new key for each
- Perf of name updated?
- Check resolution from other host
