#!/bin/bash
set -e

echo "========== 历史配对项目 - 生产环境部署 =========="

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "错误: 未安装 Docker，请先安装"
    exit 1
fi

# 检查 Docker Compose
if ! docker compose version &> /dev/null; then
    echo "错误: 未安装 Docker Compose，请先安装"
    exit 1
fi

# 检查 .env.production
if [ ! -f .env.production ]; then
    echo "错误: 未找到 .env.production 文件"
    echo "请复制 .env.production 并修改其中的密码和密钥"
    exit 1
fi

# 检查是否修改了默认密码
if grep -q "change_me" .env.production; then
    echo "警告: .env.production 中包含默认密码 'change_me'，请修改后再部署"
    read -p "是否继续？(y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 1
    fi
fi

# 构建前端
echo ""
echo ">>> 构建前端..."
if [ ! -d node_modules ]; then
    npm install
fi
npm run build

# 构建并启动容器
echo ""
echo ">>> 启动容器..."
docker compose -f docker-compose.prod.yml up -d --build

echo ""
echo "========== 部署完成 =========="
echo "访问 http://$(hostname -I | awk '{print $1}') 即可打开应用"
echo ""
echo "常用命令:"
echo "  查看日志:    docker compose -f docker-compose.prod.yml logs -f"
echo "  停止服务:    docker compose -f docker-compose.prod.yml down"
echo "  重启服务:    docker compose -f docker-compose.prod.yml restart"
echo "  查看状态:    docker compose -f docker-compose.prod.yml ps"
