#!/bin/bash

# 密钥生成工具
# 使用方法: ./generate_license.sh <数量> <有效期> <备注> <密码>

if [ $# -lt 4 ]; then
    echo "使用方法: ./generate_license.sh <数量> <有效期> <备注> <密码>"
    echo ""
    echo "参数说明:"
    echo "  数量:   要生成的密钥数量 (1-100)"
    echo "  有效期: -1=永久, 7=7天试用, 30=30天, 365=1年"
    echo "  备注:   客户名/渠道信息"
    echo "  密码:   管理员密码"
    echo ""
    echo "示例:"
    echo "  ./generate_license.sh 5 -1 \"VIP客户\" \"your_secret_password\""
    echo "  ./generate_license.sh 10 30 \"试用用户\" \"your_secret_password\""
    exit 1
fi

COUNT=$1
DAYS=$2
NOTE=$3
PASSWORD=$4

echo "正在生成 ${COUNT} 个密钥..."
echo ""

RESPONSE_FILE=$(mktemp)
cleanup() {
    rm -f "$RESPONSE_FILE"
}
trap cleanup EXIT

HTTP_CODE=$(curl -s -o "$RESPONSE_FILE" -w "%{http_code}" -X POST http://localhost:8000/admin/generate \
    -d "password=${PASSWORD}" \
    -d "count=${COUNT}" \
    -d "days=${DAYS}" \
    -d "note=${NOTE}")

if [ $? -ne 0 ]; then
    echo "请求失败：无法连接到本地服务，请确认服务已启动 (http://localhost:8000)。"
    exit 1
fi

if [ "$HTTP_CODE" != "200" ]; then
    echo "请求失败 (HTTP ${HTTP_CODE}). 返回内容:"
    sed -n '1,20p' "$RESPONSE_FILE"
    exit 1
fi

# 提取textarea中的内容（密钥）
KEYS=$(sed -n '/<textarea/,/<\/textarea>/p' "$RESPONSE_FILE" | sed 's/<textarea[^>]*>//g' | sed 's/<\/textarea>//g' | sed 's/&amp;/\&/g' | sed '/^$/d')
if [ -z "$KEYS" ]; then
    echo "未解析到密钥输出。请检查管理员密码或服务日志。"
    echo "返回内容:"
    sed -n '1,20p' "$RESPONSE_FILE"
    exit 1
fi

echo "$KEYS"

echo ""
echo "密钥生成完成！"
