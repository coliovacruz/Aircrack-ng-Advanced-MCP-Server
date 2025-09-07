#!/usr/bin/env python3
"""
Aircrack-ng MCP Server - Versao Corrigida
Servidor MCP para automacao de testes WiFi com schemas corrigidos
APENAS PARA USO ETICO E AUTORIZADO
"""

import asyncio
import json
import subprocess
import tempfile
import os
import re
import time
import hashlib
from pathlib import Path
from typing import Any, Sequence, Dict, List, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource, LoggingLevel
)
from pydantic import AnyUrl
import mcp.types as types

# Configuracoes de seguranca e caminhos locais
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Configuracoes
AUTHORIZED_INTERFACES = []
MAX_SCAN_TIME = 300
MAX_CRACK_TIME = 3600

# Caminhos configuraveis via variaveis de ambiente
REQUIRED_AUTH_FILE = os.getenv("PENTEST_AUTH_FILE", str(DATA_DIR / "authorization.txt"))
CAPTURE_DIR = os.getenv("PENTEST_CAPTURE_DIR", str(DATA_DIR / "captures"))
WORDLIST_DIR = os.getenv("PENTEST_WORDLIST_DIR", str(DATA_DIR / "wordlists"))
HASHCAT_DIR = os.getenv("PENTEST_HASHCAT_DIR", str(DATA_DIR / "hashcat"))

# Cria diretorios se nao existirem
for directory in [CAPTURE_DIR, WORDLIST_DIR, HASHCAT_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

server = Server("aircrack-advanced-mcp")

class AircrackManager:
    def __init__(self):
        self.active_processes = {}
        self.scan_results = {}
        self.session_id = int(time.time())
        self.ensure_directories()
    
    def ensure_directories(self):
        """Cria diretorios necessarios"""
        for directory in [CAPTURE_DIR, WORDLIST_DIR, HASHCAT_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def check_authorization(self, target_bssid=None):
        """Verifica se existe autorizacao para o teste"""
        if not os.path.exists(REQUIRED_AUTH_FILE):
            raise Exception("Arquivo de autorizacao nao encontrado")
        return True
    
    def log_activity(self, action: str, details: dict):
        """Log detalhado de atividades"""
        log_entry = {
            "timestamp": time.time(),
            "session": self.session_id,
            "action": action,
            "details": details
        }
        
        log_file = f"{CAPTURE_DIR}/pentest_activity.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    async def run_command(self, cmd: list, timeout: int = MAX_SCAN_TIME) -> dict:
        """Executa comando com timeout e captura de saida - versao melhorada"""
        try:
            self.log_activity("COMMAND_EXECUTION", {"cmd": " ".join(cmd)})
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                # Matar processo se timeout
                try:
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.returncode is None:
                        process.kill()
                except:
                    pass
                raise asyncio.TimeoutError(f"Comando excedeu timeout de {timeout}s")
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore'),
                "success": process.returncode == 0
            }
        except asyncio.TimeoutError:
            raise
        except Exception as e:
            raise Exception(f"Erro ao executar comando: {str(e)}")
    
    def get_session_filename(self, prefix: str, extension: str = "") -> str:
        """Gera nome de arquivo unico para a sessao"""
        timestamp = int(time.time())
        filename = f"{prefix}_{self.session_id}_{timestamp}"
        if extension:
            filename += f".{extension}"
        return os.path.join(CAPTURE_DIR, filename)

aircrack = AircrackManager()

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Lista as ferramentas disponiveis do Aircrack-ng com schemas corrigidos"""
    return [
        Tool(
            name="airmon_start",
            description="Coloca interface em modo monitor",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface de rede (ex: wlan0)"
                    }
                },
                "required": ["interface"]
            }
        ),
        Tool(
            name="airmon_stop",
            description="Remove interface do modo monitor",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface monitor (ex: wlan0mon)"
                    }
                },
                "required": ["interface"]
            }
        ),
        Tool(
            name="airodump_scan",
            description="Escaneia redes WiFi disponiveis",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface em modo monitor"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Canal especifico (opcional)"
                    },
                    "duration": {
                        "type": "string", 
                        "description": "Duracao do scan em segundos (padrao: 10)"
                    }
                },
                "required": ["interface"]
            }
        ),
        Tool(
            name="airodump_target",
            description="Captura dados de rede especifica",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface em modo monitor"
                    },
                    "bssid": {
                        "type": "string",
                        "description": "BSSID da rede alvo"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Canal da rede"
                    },
                    "duration": {
                        "type": "string",
                        "description": "Duracao da captura em segundos (padrao: 120)"
                    }
                },
                "required": ["interface", "bssid", "channel"]
            }
        ),
        Tool(
            name="aireplay_deauth",
            description="Executa ataque de desautenticacao",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface em modo monitor"
                    },
                    "bssid": {
                        "type": "string",
                        "description": "BSSID da rede alvo"
                    },
                    "client": {
                        "type": "string",
                        "description": "MAC do cliente (opcional para broadcast)"
                    },
                    "count": {
                        "type": "string",
                        "description": "Numero de pacotes (padrao: 10)"
                    }
                },
                "required": ["interface", "bssid"]
            }
        ),
        Tool(
            name="wash_scan",
            description="Escaneia redes com WPS habilitado",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface em modo monitor"
                    },
                    "duration": {
                        "type": "string",
                        "description": "Duracao do scan em segundos (padrao: 60)"
                    }
                },
                "required": ["interface"]
            }
        ),
        Tool(
            name="reaver_attack",
            description="Ataque WPS com Reaver (PIN brute force)",
            inputSchema={
                "type": "object",
                "properties": {
                    "interface": {
                        "type": "string",
                        "description": "Interface em modo monitor"
                    },
                    "bssid": {
                        "type": "string",
                        "description": "BSSID da rede alvo"
                    },
                    "channel": {
                        "type": "string",
                        "description": "Canal da rede"
                    },
                    "pixie_dust": {
                        "type": "string",
                        "description": "Usar ataque Pixie Dust (true/false)"
                    }
                },
                "required": ["interface", "bssid", "channel"]
            }
        ),
        Tool(
            name="aircrack_crack",
            description="Tenta quebrar senha WEP/WPA",
            inputSchema={
                "type": "object",
                "properties": {
                    "capture_file": {
                        "type": "string",
                        "description": "Arquivo de captura (.cap/.pcap)"
                    },
                    "wordlist": {
                        "type": "string",
                        "description": "Caminho para wordlist (opcional)"
                    },
                    "bssid": {
                        "type": "string",
                        "description": "BSSID da rede (opcional)"
                    }
                },
                "required": ["capture_file"]
            }
        ),
        Tool(
            name="list_sessions",
            description="Lista sessoes de captura ativas",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="system_status",
            description="Verifica status das ferramentas do sistema",
            inputSchema={
                "type": "object", 
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Executa as ferramentas do Aircrack-ng"""
    
    try:
        aircrack.check_authorization()
        
        if name == "airmon_start":
            interface = arguments["interface"]
            cmd = ["sudo", "airmon-ng", "start", interface]
            result = await aircrack.run_command(cmd, timeout=120)
            
            return [types.TextContent(
                type="text",
                text=f"Interface {interface} configurada em modo monitor:\n{result['stdout']}"
            )]
        
        elif name == "airmon_stop":
            interface = arguments["interface"]
            cmd = ["sudo", "airmon-ng", "stop", interface]
            result = await aircrack.run_command(cmd, timeout=120)
            
            return [types.TextContent(
                type="text",
                text=f"Modo monitor desabilitado para {interface}:\n{result['stdout']}"
            )]
        
        elif name == "airodump_scan":
            interface = arguments["interface"]
            duration = int(arguments.get("duration", "10"))
            channel = arguments.get("channel")
            
            try:
                # Usar timeout externo para garantir termino
                output_file = aircrack.get_session_filename("scan")
                
                cmd = ["sudo", "timeout", str(duration), "airodump-ng", "--write-interval", "1"]
                if channel:
                    cmd.extend(["-c", channel])
                cmd.extend(["-w", output_file, interface])
                
                aircrack.log_activity("AIRODUMP_SCAN", {
                    "interface": interface,
                    "duration": duration,
                    "channel": channel,
                    "cmd": " ".join(cmd)
                })
                
                result = await aircrack.run_command(cmd, timeout=duration + 8)
                
                # Tentar parse do arquivo CSV
                csv_file = output_file + "-01.csv"
                networks = []
                if os.path.exists(csv_file):
                    networks = parse_airodump_csv(csv_file)
                
                scan_result = f"Scan WiFi Completo ({duration}s)\n"
                scan_result += f"Interface: {interface}\n"
                scan_result += f"Canal: {channel if channel else 'Todos'}\n"
                scan_result += f"Redes detectadas: {len(networks)}\n\n"
                
                if networks:
                    scan_result += format_networks_simple(networks)
                else:
                    scan_result += "Nenhuma rede detectada ou erro no parse\n"
                    scan_result += f"Arquivo: {csv_file}\n"
                    scan_result += f"Saida: {result['stdout'][-200:] if result['stdout'] else 'Nenhuma'}"
                
                return [types.TextContent(type="text", text=scan_result)]
                
            except asyncio.TimeoutError:
                return [types.TextContent(
                    type="text",
                    text=f"Scan WiFi - Timeout apos {duration}s\n" +
                         f"Interface: {interface}\n" +
                         f"Sugestao: Reduza a duracao ou verifique a interface"
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=f"Erro no scan WiFi: {str(e)}\n" +
                         f"Interface: {interface}\n" +
                         f"Duracao: {duration}s"
                )]
        
        elif name == "wash_scan":
            interface = arguments["interface"]
            duration = int(arguments.get("duration", "60"))
            
            cmd = ["sudo", "timeout", str(duration), "wash", "-i", interface]
            result = await aircrack.run_command(cmd, timeout=duration + 10)
            
            return [types.TextContent(
                type="text",
                text=f"WPS Scan executado:\n{result['stdout']}"
            )]
        
        elif name == "airodump_target":
            interface = arguments["interface"]
            bssid = arguments["bssid"]
            channel = arguments["channel"]
            duration = int(arguments.get("duration", "120"))
            
            output_prefix = aircrack.get_session_filename(f"target_{bssid.replace(':', '')}")
            
            cmd = [
                "sudo", "timeout", str(duration), "airodump-ng",
                "-c", channel, "-d", bssid,
                "-w", output_prefix, interface
            ]
            
            result = await aircrack.run_command(cmd, timeout=duration + 10)
            
            return [types.TextContent(
                type="text",
                text=f"Captura da rede {bssid} completa\n{result['stdout'][-500:]}"
            )]
        
        elif name == "aireplay_deauth":
            interface = arguments["interface"]
            bssid = arguments["bssid"]
            client = arguments.get("client", "FF:FF:FF:FF:FF:FF")
            count = arguments.get("count", "10")
            
            cmd = [
                "sudo", "aireplay-ng", "-0", count,
                "-a", bssid, "-c", client, interface
            ]
            
            result = await aircrack.run_command(cmd, timeout=120)
            
            return [types.TextContent(
                type="text",
                text=f"Ataque de desautenticacao executado:\n{result['stdout']}"
            )]
        
        elif name == "reaver_attack":
            interface = arguments["interface"]
            bssid = arguments["bssid"]
            channel = arguments["channel"]
            pixie_dust = arguments.get("pixie_dust", "false").lower() == "true"
            
            output_file = aircrack.get_session_filename(f"reaver_{bssid.replace(':', '')}")
            
            cmd = ["sudo", "timeout", "300", "reaver", 
                   "-i", interface, "-b", bssid, "-c", channel,
                   "-d", "1", "-o", output_file]
            
            if pixie_dust:
                cmd.append("-K")  # Pixie Dust attack
            
            result = await aircrack.run_command(cmd, timeout=310)
            
            return [types.TextContent(
                type="text",
                text=f"Ataque Reaver executado contra {bssid}\n{result['stdout'][-500:]}"
            )]
        
        elif name == "aircrack_crack":
            capture_file = arguments["capture_file"]
            wordlist = arguments.get("wordlist")
            bssid = arguments.get("bssid")
            
            if not os.path.exists(capture_file):
                raise Exception(f"Arquivo nao encontrado: {capture_file}")
            
            cmd = ["aircrack-ng"]
            if wordlist and os.path.exists(wordlist):
                cmd.extend(["-w", wordlist])
            if bssid:
                cmd.extend(["-b", bssid])
            cmd.append(capture_file)
            
            result = await aircrack.run_command(cmd, timeout=1200)
            
            return [types.TextContent(
                type="text",
                text=f"Tentativa de quebra de senha:\n{result['stdout']}"
            )]
        
        elif name == "system_status":
            tools = ["aircrack-ng", "reaver", "wash", "hashcat", "bully"]
            status = "Status das Ferramentas WiFi:\n\n"
            
            for tool in tools:
                try:
                    result = await aircrack.run_command(["which", tool], timeout=5)
                    if result["success"]:
                        status += f"OK {tool}: {result['stdout'].strip()}\n"
                    else:
                        status += f"ERRO {tool}: Nao encontrado\n"
                except:
                    status += f"ERRO {tool}: Erro na verificacao\n"
            
            return [types.TextContent(type="text", text=status)]
        
        elif name == "list_sessions":
            sessions = "Arquivos da sessao atual:\n\n"
            try:
                session_files = []
                for filename in os.listdir(CAPTURE_DIR):
                    if str(aircrack.session_id) in filename:
                        filepath = os.path.join(CAPTURE_DIR, filename)
                        size = os.path.getsize(filepath)
                        sessions += f"ARQUIVO {filename} ({size:,} bytes)\n"
                
                if not session_files:
                    sessions += "Nenhum arquivo da sessao atual encontrado"
                    
            except Exception as e:
                sessions += f"Erro ao listar arquivos: {e}"
            
            return [types.TextContent(type="text", text=sessions)]
        
        else:
            return [types.TextContent(
                type="text",
                text=f"Ferramenta nao reconhecida: {name}"
            )]
    
    except Exception as e:
        aircrack.log_activity("ERROR", {"tool": name, "error": str(e)})
        return [types.TextContent(
            type="text",
            text=f"ERRO em {name}: {str(e)}"
        )]

def parse_airodump_csv(csv_file: str) -> list:
    """Parse simples da saida CSV do airodump-ng"""
    networks = []
    try:
        with open(csv_file, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('BSSID') and ',' in line:
                parts = line.split(',')
                if len(parts) >= 14:
                    try:
                        network = {
                            'bssid': parts[0].strip(),
                            'channel': parts[3].strip(),
                            'power': parts[8].strip(),
                            'privacy': parts[5].strip(),
                            'essid': parts[13].strip()
                        }
                        networks.append(network)
                    except:
                        continue
    except Exception as e:
        pass
    
    return networks

def format_networks_simple(networks: list) -> str:
    """Formata lista de redes de forma simples"""
    if not networks:
        return "Nenhuma rede encontrada"
    
    output = "\n"
    for net in networks[:10]:  # Limita a 10 redes
        output += f"REDE {net['essid']:<20} | {net['bssid']} | CH:{net['channel']:<3} | PWR:{net['power']:<4} | {net['privacy']}\n"
    
    if len(networks) > 10:
        output += f"\n... e mais {len(networks) - 10} redes"
    
    return output

async def main():
    """Funcao principal do servidor MCP"""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="aircrack-advanced-mcp",
                server_version="2.0.2",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )

if __name__ == "__main__":
    print("Aircrack-ng Advanced MCP Server")
    print("Ferramentas: Aircrack-ng, Reaver, Hashcat, HCX, Wifite")
    print("APENAS USO ETICO E AUTORIZADO")
    print("Iniciando servidor...")
    asyncio.run(main())