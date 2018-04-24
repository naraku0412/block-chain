1 run
===
```console
docker run -it --rm --network host -v /data:/mnt block-chain /block-chain.py
```

2 add a new transaction 
===
```console
curl -X POST -H "Content-Type: application/json" -d '{
 "sender": "d4ee26eee15148ee92c6cd394edd974e",
 "recipient": "someone-other-address",
 "amount": 5
}' "http://localhost:6000/transactions/new"
```

3 mine
===
```console
curl http://localhost:6000/mine
```

4 register a node
===
```console
curl -X POST -H "Content-Type: application/json" -d '{
 "nodes": ["http://some-ip:some-port"]
}' "http://localhost:6000/transactions/new"
```

5 sync
===
```console
curl http://localhost:6000/nodes/resolve
```
