#!/bin/bash

IP=$1
PORT=$2
[ -z "$IP" ] && IP="10.254.100.101"
[ -z "$PORT" ] && PORT="8080"
BATCH_SIZE=10
ID_PREFIXi="ss"
FILE="./transaction.templ"

function generate_transaction() {
  ID=$1
  SRC=$2
  DST=$3
  FILE=$4
  [ -f "$FILE" ] && rm -f $FILE
  [ -e "$FILE" ] || touch $FILE
  cat > $FILE << EOF
{
  "id": "$ID",
  "src": "$SRC",
  "dst": "$DST"
}
EOF
}

SRC="pingshan-zone5"
DST="pingshan-zone6"
for i in $(seq -s ' ' 1 80); do
  ID="$ID_PREFIXi"-"$i"
  generate_transaction $ID $SRC $DST $FILE
  JSON=$(cat ./transaction.templ)
  curl -X POST -H "Content-Type: application/json" -d "$JSON" "http://$IP:$PORT/transactions_v1/new"
  if [ "$[$i%$BATCH_SIZE]" == "0" ]; then
    curl http://$IP:$PORT/mine  
  fi
done
curl http://$IP:$PORT/mine  
[ -f "$FILE" ] && rm -f $FILE
