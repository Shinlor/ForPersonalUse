#!/bin/bash
# ================================
# UFW 安装与配置脚本
# ================================
# 检查 root 权限
if [[ $EUID -ne 0 ]]; then
    echo "请以 root 权限运行此脚本"
    exit 1
fi
echo "=============================="
echo " UFW 安装与配置脚本"
echo "=============================="

# 安装 ufw
echo "[1/5] 检查并安装 ufw..."
if command -v ufw &>/dev/null; then
    echo "ufw 已安装，跳过安装步骤"
else
    apt-get update -y
    apt-get install ufw -y
    echo "ufw 安装完成"
fi

# 锁定 ufw 防止被其他脚本卸载
echo "[2/5] 锁定 ufw 防止被自动卸载..."
apt-mark hold ufw
echo "ufw 已锁定"

# 开启 IP 转发
echo "[3/5] 开启 IP 转发..."
sed -i 's|#*net/ipv4/ip_forward=1|net/ipv4/ip_forward=1|' /etc/ufw/sysctl.conf
grep -q "^net/ipv4/ip_forward=1" /etc/ufw/sysctl.conf || echo "net/ipv4/ip_forward=1" >> /etc/ufw/sysctl.conf
echo "IP 转发已开启"

# 重置并设置默认策略
echo "[4/5] 重置 ufw 规则并设置默认策略..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# 写入 NAT 规则到 before.rules（reset 之后写入，避免被覆盖）
BEFORE_RULES="/etc/ufw/before.rules"
sed -i '1s|^|*nat\n:PREROUTING ACCEPT [0:0]\n-A PREROUTING -p udp -m udp --dport 2001:2999 -j DNAT --to-destination :1030\n-A PREROUTING -p udp -m udp --dport 3001:3999 -j DNAT --to-destination :1040\nCOMMIT\n\n|' "$BEFORE_RULES"
echo "NAT 规则已写入"

# 配置放行规则
echo "[5/5] 配置放行端口规则..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw allow 985
ufw allow 1010
ufw allow 1020
ufw allow 1030
ufw allow 1040
ufw allow 1050
ufw allow 1060
ufw allow 1070
ufw allow 5000
ufw allow 5001
ufw allow 5050
ufw allow 5858
ufw allow 2000:3000/tcp
ufw allow 2000:3000/udp
ufw allow 2001:2999/udp
ufw allow 3001:3999/udp

# 启用 ufw
ufw --force enable

echo ""
echo "=============================="
echo " 配置完成，当前规则如下："
echo "=============================="
ufw status verbose

# 验证 NAT 规则
echo ""
echo "=============================="
echo " NAT 转发规则验证："
echo "=============================="
iptables -t nat -L PREROUTING -n --line-numbers
