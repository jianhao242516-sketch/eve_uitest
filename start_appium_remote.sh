#!/bin/bash
# 启动 Appium 服务，监听所有网络接口（用于远程连接）

# 配置
APPIUM_PORT_START=4723
NUM_DEVICES=4  # 设备数量，根据实际情况修改

echo "🚀 启动 Appium 服务（支持远程连接）"
echo "📍 监听地址: 0.0.0.0"
echo "🔌 端口范围: ${APPIUM_PORT_START} - $((APPIUM_PORT_START + NUM_DEVICES - 1))"
echo ""

# 获取本机 IP 地址
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || hostname -I | awk '{print $1}')
fi

echo "💡 本机 IP 地址: ${LOCAL_IP}"
echo "📝 请在服务器配置中使用: appium_host=\"${LOCAL_IP}\""
echo ""

# 启动多个 Appium 实例
for i in $(seq 0 $((NUM_DEVICES - 1))); do
    PORT=$((APPIUM_PORT_START + i))
    echo "启动 Appium 实例 ${i}，端口: ${PORT}"
    appium --address 0.0.0.0 --port ${PORT} > /tmp/appium_${PORT}.log 2>&1 &
    echo "  PID: $!"
    echo "  日志: /tmp/appium_${PORT}.log"
    sleep 1
done

echo ""
echo "✅ Appium 服务已启动"
echo ""
echo "📋 检查服务状态:"
for i in $(seq 0 $((NUM_DEVICES - 1))); do
    PORT=$((APPIUM_PORT_START + i))
    sleep 1
    if curl -s http://localhost:${PORT}/status > /dev/null 2>&1; then
        echo "  ✅ 端口 ${PORT}: 运行中"
    else
        echo "  ❌ 端口 ${PORT}: 未响应"
    fi
done

echo ""
echo "🛑 停止服务: pkill -f appium"
echo "📖 查看日志: tail -f /tmp/appium_*.log"

