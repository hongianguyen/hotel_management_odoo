#!/bin/bash

# Thông tin Server
SERVER_USER="root"
SERVER_IP="103.200.20.13"
REMOTE_PATH="~/odoo19_test/extra-addons/hotel_management_odoo"
CONTAINER_NAME="odoo19_test_odoo_1" # Tên chính xác bạn vừa tìm thấy
MODULE_NAME="hotel_management_odoo"          # Must match the folder name = module technical name

echo "🚀 Bước 1: Đồng bộ code lên VPS..."
# Đảm bảo thư mục tồn tại trên server
ssh $SERVER_USER@$SERVER_IP "mkdir -p $REMOTE_PATH"
# Sử dụng scp vì máy Windows thường không có rsync mặc định
scp -r ./* $SERVER_USER@$SERVER_IP:$REMOTE_PATH

echo "✅ Bước 2: Lệnh cho Odoo nâng cấp module..."
# Odoo 19 requires 'server' subcommand and long-form DB flags
ssh $SERVER_USER@$SERVER_IP "docker exec -u 0 $CONTAINER_NAME odoo server -d hotel_db -i $MODULE_NAME --db_host db --db_user odoo --db_password odoo_pwd --stop-after-init"
echo "✨ Hoàn tất! Kiểm tra tại: http://$SERVER_IP:8070"
