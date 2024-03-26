#!/bin/bash
function send_message() {

	w_msg=$1
	w_msg="{\"msgtype\": \"text\", \"text\": {\"content\": \"$w_msg\"}, \"at\":{\"isAtAll\": true}}"
	# hook="https://oapi.dingtalk.com/robot/send?access_token=9f0bc978efebaa3a839be3ddd420f2946474b29961b45b5bad726e89102f6eb9"
  hook="https://oapi.dingtalk.com/robot/send?access_token=2780e3bcba1e1065d48535da6c3d9bca7f797622149acb14da723cfa8f4b12ad"
	curl -XPOST -s -L $hook -H "Content-Type: application/json" -H "charset:utf-8" -d "$w_msg"
}

curl --location 'http://127.0.0.1:8189/translate/' \
	--header 'Content-Type: application/json' \
	--data '{
      "id": 123,
      "engine": "google",
      "sourceLan": "auto",
      "targetLan": "en",
      "translateSource": "Bonjour le monde", "type": "html"
  }'

# if this command is successful, then the service is healthy
# else, send a message to the group
if [ $? -eq 0 ]; then
	echo "AI翻译正常"
else
	send_message "AI翻译崩溃"
fi
