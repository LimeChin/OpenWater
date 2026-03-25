#!/bin/bash

# Water API 快速部署脚本
# 使用方法: bash deploy.sh [faka|oneapi|all]
# 示例: bash deploy.sh faka  (仅部署发卡程序)
#      bash deploy.sh all    (部署所有)

# ============ 配置信息 ============
SERVER_IP="144.202.121.4"
SERVER_USER="root"
SERVER_PASSWORD="5_XuT*ZGC_3m(F?J"
PROJECT_PATH="/opt/one-api"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============ 函数定义 ============

# 打印成功信息
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印错误信息
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# 打印提示信息
print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# 检查 sshpass 是否安装
check_sshpass() {
    if ! command -v sshpass &> /dev/null; then
        print_error "sshpass 未安装，正在安装..."
        sudo apt-get update && sudo apt-get install -y sshpass
    fi
}

# 上传文件到服务器
upload_file() {
    local local_file=$1
    local remote_file=$2
    
    print_info "上传 $local_file 到 $remote_file..."
    sshpass -p "$SERVER_PASSWORD" scp -o StrictHostKeyChecking=no "$local_file" "$SERVER_USER@$SERVER_IP:$remote_file" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_success "上传成功"
        return 0
    else
        print_error "上传失败"
        return 1
    fi
}

# 执行远程命令
execute_remote() {
    local command=$1
    sshpass -p "$SERVER_PASSWORD" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$command" 2>/dev/null
}

# 部署发卡程序
deploy_faka() {
    print_info "开始部署发卡程序..."
    
    # 检查文件是否存在
    if [ ! -f "faka_app.py" ]; then
        print_error "faka_app.py 文件不存在"
        return 1
    fi
    
    # 上传文件
    upload_file "faka_app.py" "$PROJECT_PATH/faka_app.py"
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # 重启容器
    print_info "重启发卡程序容器..."
    execute_remote "cd $PROJECT_PATH && docker restart faka"
    
    if [ $? -eq 0 ]; then
        print_success "发卡程序部署完成"
        print_info "发卡页面地址: http://$SERVER_IP:3001"
        return 0
    else
        print_error "容器重启失败"
        return 1
    fi
}

# 部署 One-API
deploy_oneapi() {
    print_info "开始部署 One-API..."
    
    # 检查文件是否存在
    if [ ! -f "docker-compose.yml" ]; then
        print_error "docker-compose.yml 文件不存在"
        return 1
    fi
    
    # 上传文件
    upload_file "docker-compose.yml" "$PROJECT_PATH/docker-compose.yml"
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # 重启服务
    print_info "重启 One-API 服务..."
    execute_remote "cd $PROJECT_PATH && docker-compose up -d"
    
    if [ $? -eq 0 ]; then
        print_success "One-API 部署完成"
        print_info "One-API 地址: http://$SERVER_IP:3000"
        return 0
    else
        print_error "One-API 启动失败"
        return 1
    fi
}

# 部署所有
deploy_all() {
    print_info "开始完整部署..."
    
    deploy_faka
    if [ $? -ne 0 ]; then
        print_error "发卡程序部署失败，停止部署"
        return 1
    fi
    
    deploy_oneapi
    if [ $? -ne 0 ]; then
        print_error "One-API 部署失败"
        return 1
    fi
    
    print_success "完整部署完成！"
    print_info "One-API: http://$SERVER_IP:3000"
    print_info "发卡页面: http://$SERVER_IP:3001"
}

# 检查部署状态
check_status() {
    print_info "检查部署状态..."
    
    # 检查 One-API
    print_info "检查 One-API..."
    execute_remote "docker ps | grep one-api"
    if [ $? -eq 0 ]; then
        print_success "One-API 运行中"
    else
        print_error "One-API 未运行"
    fi
    
    # 检查发卡程序
    print_info "检查发卡程序..."
    execute_remote "docker ps | grep faka"
    if [ $? -eq 0 ]; then
        print_success "发卡程序运行中"
    else
        print_error "发卡程序未运行"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
Water API 快速部署脚本

使用方法:
  bash deploy.sh [命令]

命令:
  faka       仅部署发卡程序
  oneapi     仅部署 One-API
  all        部署所有（默认）
  status     检查部署状态
  help       显示帮助信息

示例:
  bash deploy.sh faka      # 仅部署发卡程序
  bash deploy.sh all       # 部署所有
  bash deploy.sh status    # 检查状态

配置信息:
  服务器: $SERVER_IP
  项目路径: $PROJECT_PATH

EOF
}

# ============ 主程序 ============

# 检查依赖
check_sshpass

# 获取命令参数
COMMAND=${1:-all}

case $COMMAND in
    faka)
        deploy_faka
        ;;
    oneapi)
        deploy_oneapi
        ;;
    all)
        deploy_all
        ;;
    status)
        check_status
        ;;
    help)
        show_help
        ;;
    *)
        print_error "未知命令: $COMMAND"
        show_help
        exit 1
        ;;
esac

exit $?
