#!/bin/bash
# Aircrack-ng Advanced MCP Server - Setup Automático
# Script de instalação e configuração

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE} Aircrack-ng Advanced MCP Server${NC}"
echo -e "${BLUE} Instalação Automática${NC}"
echo -e "${BLUE}======================================${NC}"

# Verificar se está rodando como usuário normal (não root)
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}Este script deve ser executado como usuário normal, não como root.${NC}"
   echo -e "${YELLOW}Use: ./setup.sh${NC}"
   exit 1
fi

# Verificar distribuição
if ! command -v apt &> /dev/null; then
    echo -e "${RED}Este script requer uma distribuição baseada em Debian/Ubuntu${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/8] Atualizando sistema...${NC}"
sudo apt update && sudo apt upgrade -y

echo -e "${YELLOW}[2/8] Instalando dependências do sistema...${NC}"
sudo apt install -y \
    aircrack-ng \
    reaver \
    hashcat \
    hostapd \
    dnsmasq \
    apache2 \
    php \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wireless-tools \
    net-tools \
    iw \
    macchanger

echo -e "${YELLOW}[3/8] Criando ambiente virtual Python...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[4/8] Instalando dependências Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${YELLOW}[5/8] Configurando permissões sudo...${NC}"
SUDOERS_FILE="/etc/sudoers.d/aircrack-mcp"
sudo tee $SUDOERS_FILE > /dev/null << EOF
# Aircrack-ng MCP Server - Permissões sudo sem senha
$USER ALL=(ALL) NOPASSWD: /usr/bin/airmon-ng
$USER ALL=(ALL) NOPASSWD: /usr/sbin/airmon-ng
$USER ALL=(ALL) NOPASSWD: /usr/bin/airodump-ng
$USER ALL=(ALL) NOPASSWD: /usr/bin/aireplay-ng
$USER ALL=(ALL) NOPASSWD: /usr/bin/reaver
$USER ALL=(ALL) NOPASSWD: /usr/bin/wash
$USER ALL=(ALL) NOPASSWD: /bin/timeout
$USER ALL=(ALL) NOPASSWD: /usr/bin/timeout
EOF

echo -e "${GREEN}Permissões sudo configuradas em: $SUDOERS_FILE${NC}"

echo -e "${YELLOW}[6/8] Criando estrutura de diretórios...${NC}"
mkdir -p data/{captures,wordlists,hashcat}

# Criar arquivo de autorização
cat > data/authorization.txt << EOF
# Arquivo de Autorização - Aircrack-ng MCP Server
# Este arquivo autoriza o uso das ferramentas para pentesting ético
Authorized for penetration testing and security auditing
Generated on: $(date)
User: $USER
Hostname: $(hostname)
EOF

echo -e "${YELLOW}[7/8] Baixando wordlists básicas...${NC}"
# Wordlist pequena para testes
curl -s https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10-million-password-list-top-100.txt -o data/wordlists/top100.txt

# Verificar se rockyou.txt existe no sistema
if [[ -f /usr/share/wordlists/rockyou.txt ]]; then
    ln -sf /usr/share/wordlists/rockyou.txt data/wordlists/rockyou.txt
    echo -e "${GREEN}Wordlist rockyou.txt linkada${NC}"
elif [[ -f /usr/share/wordlists/rockyou.txt.gz ]]; then
    echo -e "${YELLOW}Descomprimindo rockyou.txt...${NC}"
    sudo gunzip /usr/share/wordlists/rockyou.txt.gz
    ln -sf /usr/share/wordlists/rockyou.txt data/wordlists/rockyou.txt
    echo -e "${GREEN}Wordlist rockyou.txt descomprimida e linkada${NC}"
fi

echo -e "${YELLOW}[8/8] Verificando instalação...${NC}"

# Verificar comandos principais
echo -e "${BLUE}Verificando ferramentas...${NC}"
for cmd in aircrack-ng reaver wash hostapd dnsmasq; do
    if command -v $cmd &> /dev/null; then
        echo -e "${GREEN}✓ $cmd encontrado${NC}"
    else
        echo -e "${RED}✗ $cmd não encontrado${NC}"
    fi
done

# Verificar Python
echo -e "${BLUE}Verificando Python...${NC}"
if source venv/bin/activate && python -c "import mcp, pydantic, asyncio" &> /dev/null; then
    echo -e "${GREEN}✓ Dependências Python OK${NC}"
else
    echo -e "${RED}✗ Problema com dependências Python${NC}"
fi

# Verificar interfaces WiFi
echo -e "${BLUE}Verificando interfaces WiFi...${NC}"
if iwconfig 2>/dev/null | grep -q "IEEE 802.11"; then
    echo -e "${GREEN}✓ Interface WiFi detectada${NC}"
    iwconfig 2>/dev/null | grep "IEEE 802.11" | awk '{print "  Interface:", $1}'
else
    echo -e "${YELLOW}⚠ Nenhuma interface WiFi detectada${NC}"
fi

# Verificar permissões sudo
echo -e "${BLUE}Verificando permissões sudo...${NC}"
if sudo -n airmon-ng 2>/dev/null | grep -q "usage"; then
    echo -e "${GREEN}✓ Permissões sudo OK${NC}"
else
    echo -e "${RED}✗ Problema com permissões sudo${NC}"
fi

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN} Instalação Concluída!${NC}"
echo -e "${GREEN}======================================${NC}"

echo -e "${BLUE}Próximos passos:${NC}"
echo -e "1. ${YELLOW}Ativar ambiente virtual:${NC}"
echo -e "   source venv/bin/activate"
echo -e ""
echo -e "2. ${YELLOW}Executar servidor MCP:${NC}"
echo -e "   python3 aircrack_advanced_mcp_server.py"
echo -e ""
echo -e "3. ${YELLOW}Configurar no Claude.ai:${NC}"
echo -e "   - Ir em Configurações → Recursos → Conectar servidor MCP"
echo -e "   - Usar caminho: $(pwd)/venv/bin/python"
echo -e "   - Args: [\"$(pwd)/aircrack_advanced_mcp_server.py\"]"
echo -e ""
echo -e "4. ${YELLOW}Verificar interface WiFi:${NC}"
echo -e "   iwconfig"
echo -e "   sudo airmon-ng"
echo -e ""
echo -e "${BLUE}Arquivos importantes:${NC}"
echo -e "• Servidor: ${YELLOW}aircrack_advanced_mcp_server.py${NC}"
echo -e "• Honeypot: ${YELLOW}honeypot_setup.sh${NC}"
echo -e "• Monitor: ${YELLOW}honeypot_monitor.py${NC}"
echo -e "• Dados: ${YELLOW}data/${NC}"
echo -e "• Logs: ${YELLOW}data/captures/${NC}"
echo -e ""
echo -e "${RED}LEMBRE-SE: Use apenas em redes próprias ou com autorização!${NC}"
