#!/bin/bash

# 等待 Elasticsearch 启动
until curl -u "elastic:${ELASTIC_PASSWORD}" -s http://es01:9200 >/dev/null; do
  echo "等待 Elasticsearch 启动..."
  sleep 5
done

echo "使用者: elastic:${ELASTIC_PASSWORD}"

# 创建 ragflow_reader 角色
ROLE_PAYLOAD='{
  "indices": [
    {
      "names": ["ragflow_*"],
      "privileges": ["read", "view_index_metadata", "read_cross_cluster"]
    }
  ]
}'

echo "创建角色: ragflow_reader"
curl -X POST "http://es01:9200/_security/role/ragflow_reader" \
-u "elastic:${ELASTIC_PASSWORD}" \
-H "Content-Type: application/json" \
-d "$ROLE_PAYLOAD"

# 创建用户账户
USER_PAYLOAD="{
  \"password\" : \"${KIBANA_PASSWORD}\",
  \"roles\" : [ \"kibana_admin\", \"kibana_system\", \"ragflow_reader\" ],
  \"full_name\" : \"${KIBANA_USER}\",
  \"email\" : \"${KIBANA_USER}@example.com\"
}"
echo "新用户账户: $USER_PAYLOAD"

# 创建新用户账户
curl -X POST "http://es01:9200/_security/user/${KIBANA_USER}" \
-u "elastic:${ELASTIC_PASSWORD}" \
-H "Content-Type: application/json" \
-d "$USER_PAYLOAD"

echo "新用户账户已创建"

exit 0