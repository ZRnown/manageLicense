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

RESULT=$(curl -s -X POST http://localhost:8000/admin/generate \
    -d "password=${PASSWORD}" \
    -d "count=${COUNT}" \
    -d "days=${DAYS}" \
    -d "note=${NOTE}")

# 提取textarea中的内容（密钥）
echo "$RESULT" | sed -n '/<textarea/,/<\/textarea>/p' | sed 's/<textarea[^>]*>//g' | sed 's/<\/textarea>//g' | sed 's/&amp;/\&/g' | sed '/^$/d'

echo ""
echo "密钥生成完成！"
