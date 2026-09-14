#!/bin/bash
# Veronica WSL Network Fix - runs periodically to prevent DNS/Hyper-V issues
echo "[$(date)] Running WSL network fix..."

if [ ! -f /etc/resolv.conf ] || ! grep -q "1.1.1.1" /etc/resolv.conf; then
  echo "Resolv.conf missing or outdated - fixing..."
  sudo bash -c 'echo "nameserver 1.1.1.1" > /etc/resolv.conf && echo "nameserver 1.0.0.1" >> /etc/resolv.conf && echo "nameserver 8.8.8.8" >> /etc/resolv.conf'
  echo "DNS fixed."
else
  echo "DNS already correct."
fi

ping -c 1 8.8.8.8 > /dev/null 2>&1 && echo "Network reachable." || echo "Network still unreachable - check Hyper-V."

echo "[$(date)] Fix complete." >> /var/log/wsl-network-fix.log
echo "Log written to /var/log/wsl-network-fix.log"
