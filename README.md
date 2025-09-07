# Aircrack-ng Advanced MCP Server

Servidor MCP (Model Context Protocol) avançado para automação de testes WiFi usando a suite Aircrack-ng. Desenvolvido para pentesting ético e auditoria de segurança wireless em ambientes controlados.

## AVISO LEGAL

⚠️ **APENAS PARA USO ÉTICO E AUTORIZADO**

Este projeto é destinado exclusivamente para:
- Pentesting autorizado
- Auditoria de segurança em redes próprias
- Pesquisa acadêmica com consentimento
- Treinamento em segurança cibernética

**NÃO use em redes que não sejam suas ou sem autorização explícita.**

## Características

- Interface MCP para ferramentas Aircrack-ng
- Scanning automatizado de redes WiFi
- Captura de handshakes WPA/WPA2
- Análise de redes WPS
- Ataques de desautenticação controlados
- Relatórios detalhados de auditoria
- Honeypot WiFi com captive portal
- Monitoramento em tempo real

## Pré-requisitos

### Sistema Operacional
- **Kali Linux** (recomendado)
- **Ubuntu/Debian** com repositórios de segurança
- **Arch Linux** com pacotes de pentesting

### Hardware
- Interface WiFi compatível com modo monitor
- Recomendado: Adaptador USB WiFi dedicado (ex: Alfa AWUS036ACS)

### Software Básico
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Pacotes essenciais
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
    git
```

## Instalação

### 1. Clonar o Repositório
```bash
git clone https://github.com/seu-usuario/aircrack-advanced-mcp.git
cd aircrack-advanced-mcp
```

### 2. Configurar Ambiente Python
```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências MCP
pip install mcp pydantic asyncio
```

### 3. Configurar Permissões sudo
```bash
# Adicionar permissões NOPASSWD para comandos aircrack
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/airmon-ng, /usr/bin/airodump-ng, /usr/bin/aireplay-ng, /usr/bin/reaver, /usr/bin/wash, /usr/bin/hostapd, /usr/bin/dnsmasq" | sudo tee /etc/sudoers.d/aircrack-mcp
```

### 4. Criar Estrutura de Diretórios
```bash
mkdir -p data/{captures,wordlists,hashcat}
touch data/authorization.txt
echo "Authorized for pentesting" > data/authorization.txt
```

### 5. Verificar Interface WiFi
```bash
# Listar interfaces disponíveis
iwconfig

# Verificar se suporta modo monitor
sudo airmon-ng
```

## Configuração no Claude.ai

### 1. Acessar Configurações MCP
1. Abrir [Claude.ai](https://claude.ai)
2. Ir em **Configurações** → **Recursos**
3. Clicar em **Conectar servidor MCP**

### 2. Configurar Servidor Local
```json
{
  "mcpServers": {
    "aircrack-advanced-mcp": {
      "command": "/caminho/para/venv/bin/python",
      "args": ["/caminho/para/aircrack_advanced_mcp_server.py"],
      "env": {
        "PENTEST_AUTH_FILE": "/caminho/para/data/authorization.txt",
        "PENTEST_CAPTURE_DIR": "/caminho/para/data/captures",
        "PENTEST_WORDLIST_DIR": "/caminho/para/data/wordlists"
      }
    }
  }
}
```

### 3. Arquivo de Configuração Alternativo
Criar `~/.config/claude-mcp/config.json`:
```json
{
  "aircrack-advanced-mcp": {
    "command": "python3",
    "args": ["aircrack_advanced_mcp_server.py"],
    "cwd": "/caminho/para/projeto"
  }
}
```

## Uso Básico

### 1. Iniciar o Servidor
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar servidor MCP
python3 aircrack_advanced_mcp_server.py
```

### 2. Comandos Disponíveis no Claude

#### Gerenciamento de Interface
```
airmon_start interface=wlan1
airmon_stop interface=wlan1mon
```

#### Scanning de Redes
```
airodump_scan interface=wlan1mon duration=15
airodump_scan interface=wlan1mon channel=6 duration=10
wash_scan interface=wlan1mon duration=30
```

#### Captura de Handshakes
```
airodump_target interface=wlan1mon bssid=XX:XX:XX:XX:XX:XX channel=6 duration=60
```

#### Ataques (Apenas em redes próprias)
```
aireplay_deauth interface=wlan1mon bssid=XX:XX:XX:XX:XX:XX count=5
reaver_attack interface=wlan1mon bssid=XX:XX:XX:XX:XX:XX channel=6
```

#### Análise de Capturas
```
aircrack_crack capture_file=/caminho/para/arquivo.cap
list_sessions
system_status
```

## Funcionalidades Avançadas

### Relatórios de Auditoria
O servidor gera automaticamente relatórios detalhados das redes detectadas, incluindo:
- Análise de segurança por canal
- Distribuição de fabricantes
- Redes vulneráveis (WPS habilitado)
- Recomendações de segurança
- Estatísticas de potência de sinal

### Integração com Hashcat
Suporte para análise avançada de handshakes capturados:
- Conversão automática para formato hashcat
- Testes de força bruta com wordlists
- Análise de padrões de senha

## Estrutura do Projeto

```
aircrack-advanced-mcp/
├── aircrack_advanced_mcp_server.py    # Servidor MCP principal
├── data/
│   ├── authorization.txt              # Arquivo de autorização
│   ├── captures/                      # Capturas .cap/.pcap
│   ├── wordlists/                     # Wordlists para cracking
│   └── hashcat/                       # Arquivos hashcat
├── venv/                              # Ambiente virtual Python
├── README.md                          # Este arquivo
├── LICENSE                            # Licença do projeto
└── requirements.txt                   # Dependências Python
```

## Troubleshooting

### Problema: Interface não entra em modo monitor
```bash
# Verificar se está sendo usada
sudo airmon-ng check kill

# Verificar driver
lsusb | grep -i wireless
dmesg | grep -i wifi
```

### Problema: Permissões sudo negadas
```bash
# Verificar se sudoers foi configurado corretamente
sudo visudo -f /etc/sudoers.d/aircrack-mcp

# Testar comando sudo específico
sudo -n airmon-ng

# Se falhar, reconfigurar permissões
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/airmon-ng, /usr/bin/airodump-ng, /usr/bin/aireplay-ng, /usr/bin/reaver, /usr/bin/wash, /usr/sbin/airmon-ng, /bin/timeout, /usr/bin/timeout" | sudo tee /etc/sudoers.d/aircrack-mcp
```

### Problema: MCP não conecta
```bash
# Verificar se servidor está rodando
python3 aircrack_advanced_mcp_server.py

# Verificar configuração do Claude.ai
# Caminho correto para venv/bin/python
# Args corretos para o script

# Verificar logs
tail -f data/captures/pentest_activity.log
```

### Problema: Timeout em comandos
```bash
# Verificar processos interferentes
ps aux | grep -E "(NetworkManager|wpa_supplicant)"

# Verificar interface
iwconfig wlan1

# Verificar se permissões sudo estão funcionando
sudo -n timeout 5 airodump-ng --help
```

### Problema: "Arquivo de autorização não encontrado"
```bash
# Verificar se arquivo existe
ls -la data/authorization.txt

# Criar arquivo se necessário
echo "Authorized for pentesting" > data/authorization.txt

# Verificar variável de ambiente
echo $PENTEST_AUTH_FILE
```

## Desenvolvimento

### Adicionar Nova Ferramenta
1. Adicionar tool em `handle_list_tools()`
2. Implementar lógica em `handle_call_tool()`
3. Atualizar documentação

### Exemplo de Nova Ferramenta
```python
Tool(
    name="nova_ferramenta",
    description="Descrição da ferramenta",
    inputSchema={
        "type": "object",
        "properties": {
            "parametro": {
                "type": "string",
                "description": "Descrição do parâmetro"
            }
        },
        "required": ["parametro"]
    }
)
```

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Segurança

### Práticas Recomendadas
- Execute apenas em ambiente isolado/controlado
- Use sempre VPN/proxy para testes
- Mantenha logs detalhados de atividades
- Respeite leis locais sobre segurança cibernética

### Responsabilidade
- O usuário é totalmente responsável pelo uso desta ferramenta
- Não nos responsabilizamos por uso inadequado ou ilegal
- Respeite sempre a privacidade e propriedade de terceiros

## Licença

MIT License - veja arquivo [LICENSE](LICENSE) para detalhes.

## Suporte

Para dúvidas, problemas ou contribuições:
- Abra uma **Issue** no GitHub
- Consulte a documentação do MCP: [Model Context Protocol](https://modelcontextprotocol.io/)
- Documentação Aircrack-ng: [Aircrack-ng Wiki](https://aircrack-ng.org/)

## Agradecimentos

- Equipe Aircrack-ng pelo conjunto de ferramentas
- Anthropic pelo protocolo MCP
- Comunidade de segurança cibernética

---

**Disclaimer**: Esta ferramenta é fornecida "como está" para fins educacionais e de pesquisa. Use com responsabilidade e sempre dentro da legalidade.
