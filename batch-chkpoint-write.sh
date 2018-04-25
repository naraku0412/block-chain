#!/bin/bash

IP=$1
PORT=$2
[ -z "$IP" ] && IP="10.254.100.101"
[ -z "$PORT" ] && PORT="8080"
BATCH_SIZE=10
ID_PREFIX="ss"
FILE="./checkpoint.templ"

function generate_templ() {
  ID=$1
  DATE=$2
  TEMP=$3
  STATUS=$4
  FILE=$5
  [ -f "$FILE" ] && rm -f $FILE
  [ -e "$FILE" ] || touch $FILE
  cat > $FILE << EOF
{
  "id": "$ID",
  "temp": "$TEMP",
  "date": "$DATE",
  "status": "$STATUS"
}
EOF
}

DATE_PREFIX="2018-3"
STATUS_ARRAY[0]="Good"
STATUS_ARRAY[1]="Normal"
STATUS_ARRAY[2]="Excellent"
STATUS_ARRAY[3]="Happy"
STATUS_ARRAY[4]="Well"

for j in $(seq -s ' ' 1 31); do
  DATE="$DATE_PREFIX"-$j
  for i in $(seq -s ' ' 1 80); do
    ID="$ID_PREFIX"-"$i"
    TEMP=$[${RANDOM}%2+38].$[${RANDOM}%10]
    IDX=$[$RANDOM%${#STATUS_ARRAY[@]}]
    STATUS="${STATUS_ARRAY[$IDX]}"
    generate_templ $ID $DATE $TEMP $STATUS $FILE
    JSON=$(cat $FILE)
    #echo $JSON
    curl -X POST -H "Content-Type: application/json" -d "$JSON" "http://$IP:$PORT/checkpoints/new"
    if [ "$[$i%$BATCH_SIZE]" == "0" ]; then
      curl http://$IP:$PORT/mine  
    fi
  done
  curl http://$IP:$PORT/mine  
done
curl http://$IP:$PORT/mine  
[ -f "$FILE" ] && rm -f $FILE
