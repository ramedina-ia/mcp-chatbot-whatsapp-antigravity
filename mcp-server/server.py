"""
Unified WhatsApp Stack MCP Server
=================================
Model Context Protocol (MCP) server for managing:
1. Evolution API (WhatsApp Gateway & Multi-Device Baileys)
2. Typebot (Conversational Chatbot Builder & Session Manager)
3. Chatwoot (Customer Support Shared Inbox & Human Handoff)

Author: Antigravity AI
Version: 1.0.0 (October 2026)
"""

import os
import sys
import json
import logging
from typing import Optional, Dict, Any
import requests
from mcp.server.fastmcp import FastMCP

# Setup basic logging to stderr (stdio is reserved for MCP JSON-RPC protocol)
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("whatsapp-stack-mcp")

# Initialize FastMCP Server
mcp = FastMCP("whatsapp-stack-mcp")

# Helper to load .env if present
def load_env_file():
    # Check current dir or parent project dir
    candidates = [
        os.path.join(os.path.dirname(__file__), ".env"),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    ]
    for env_path in candidates:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            val = v.strip().strip('"').strip("'")
                            # If unset or placeholder, take from .env
                            if os.environ.get(k.strip()) in [None, "", "tu_token_chatwoot"]:
                                os.environ[k.strip()] = val
            except Exception as e:
                logger.warning(f"Error loading .env file: {e}")

load_env_file()

def get_env_var(name: str, default: Optional[str] = None) -> str:
    val = os.environ.get(name, default)
    if not val:
        raise ValueError(f"Falta la variable de entorno obligatoria: {name}. Por favor configúrala en el archivo .env o en mcp_config.json.")
    return val.rstrip("/")

# ==============================================================================
# 1. HEALTH & CONNECTIVITY CHECK
# ==============================================================================
@mcp.tool()
def check_stack_health() -> str:
    """Verifica el estado de conexión y disponibilidad de los servicios del VPS (Evolution API, Typebot y Chatwoot)."""
    evo_url = os.environ.get("EVOLUTION_API_URL")
    evo_key = os.environ.get("EVOLUTION_API_KEY")
    typebot_url = os.environ.get("TYPEBOT_VIEWER_URL")
    chatwoot_url = os.environ.get("CHATWOOT_API_URL")

    results = []

    # Check Evolution API
    if evo_url and evo_key:
        try:
            r = requests.get(f"{evo_url.rstrip('/')}/instance/fetchInstances", headers={"apikey": evo_key}, timeout=5)
            if r.status_code == 200:
                instances = r.json()
                results.append(f" Evolution API ({evo_url}): OK (Conectado, {len(instances)} instancias detectadas)")
            else:
                results.append(f" Evolution API ({evo_url}): Error HTTP {r.status_code}")
        except Exception as e:
            results.append(f"❌ Evolution API ({evo_url}): Inaccesible ({e})")
    else:
        results.append("⚠️ Evolution API: No configurado (falta EVOLUTION_API_URL o EVOLUTION_API_KEY)")

    # Check Typebot
    if typebot_url:
        try:
            r = requests.get(f"{typebot_url.rstrip('/')}/api/health", timeout=5)
            if r.status_code in [200, 404]: # Typebot responds ok or not found on root
                results.append(f" Typebot ({typebot_url}): OK (Servicio en línea)")
            else:
                results.append(f" Typebot ({typebot_url}): HTTP {r.status_code}")
        except Exception as e:
            results.append(f"❌ Typebot ({typebot_url}): Inaccesible ({e})")
    else:
        results.append("⚠️ Typebot: No configurado (falta TYPEBOT_VIEWER_URL)")

    # Check Chatwoot
    if chatwoot_url:
        try:
            r = requests.get(f"{chatwoot_url.rstrip('/')}/api", timeout=5)
            results.append(f" Chatwoot ({chatwoot_url}): OK (Servicio en línea, status {r.status_code})")
        except Exception as e:
            results.append(f"❌ Chatwoot ({chatwoot_url}): Inaccesible ({e})")
    else:
        results.append("⚠️ Chatwoot: No configurado (falta CHATWOOT_API_URL)")

    return "\n".join(results)

# ==============================================================================
# 2. EVOLUTION API (WHATSAPP GATEWAY)
# ==============================================================================
@mcp.tool()
def evolution_create_instance(instance_name: str, qrcode: bool = True) -> str:
    """Crea una nueva instancia de WhatsApp en Evolution API y genera el código QR para escanear."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    url = f"{evo_url}/instance/create"
    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    payload = {
        "instanceName": instance_name,
        "token": instance_name,
        "qrcode": qrcode,
        "integration": "WHATSAPP-BAILEYS"
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code in [200, 201]:
            data = r.json()
            qrcode_data = data.get("qrcode", {})
            pairing_code = data.get("pairingCode")
            
            resp = [f" Instancia '{instance_name}' creada exitosamente en Evolution API."]
            if qrcode_data and isinstance(qrcode_data, dict):
                qr_base64 = qrcode_data.get("base64")
                if qr_base64:
                    resp.append(f"Código QR generado en Base64 (listo para escanear). Longitud: {len(qr_base64)} caracteres.")
            if pairing_code:
                resp.append(f"Código de emparejamiento numérico: {pairing_code}")
            return "\n".join(resp)
        else:
            return f"Error al crear instancia (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción de conexión al crear instancia: {e}"

@mcp.tool()
def evolution_get_instance_status(instance_name: str) -> str:
    """Obtiene el estado de conexión de una instancia de WhatsApp ('open', 'connecting', 'close')."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    url = f"{evo_url}/instance/connectionState/{instance_name}"
    headers = {"apikey": evo_key}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            state = data.get("instance", {}).get("state", "desconocido")
            return f"Estado de la instancia '{instance_name}': {state.upper()} (Datos completos: {json.dumps(data)})"
        return f"Error al consultar estado (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al consultar estado: {e}"

@mcp.tool()
def evolution_get_qr_code(instance_name: str) -> str:
    """Obtiene el código QR actualizado para vincular la app móvil de WhatsApp si la sesión expiró."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    url = f"{evo_url}/instance/connect/{instance_name}"
    headers = {"apikey": evo_key}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            base64_qr = data.get("base64")
            code = data.get("code")
            return json.dumps({
                "status": "success",
                "instance": instance_name,
                "has_base64": bool(base64_qr),
                "code": code,
                "raw_response": data
            }, indent=2)
        return f"Error al generar QR (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al conectar instancia: {e}"

@mcp.tool()
def evolution_send_text_message(instance_name: str, number: str, text: str, delay_ms: int = 1500) -> str:
    """Envía un mensaje de texto de WhatsApp a un número internacional (ej: '521XXXXXXXXXX' o '549XXXXXXXXXX') simulando escritura."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    # Limpiar formato de número
    clean_number = "".join(filter(str.isdigit, number))

    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    # 1. Intentar endpoint nativo de Evolution API Go (/send/text)
    go_url = f"{evo_url}/send/text"
    try:
        r_go = requests.post(go_url, headers=headers, json={"number": clean_number, "text": text, "delay": delay_ms}, timeout=10)
        if r_go.status_code in [200, 201]:
            return f"✅ Mensaje enviado exitosamente vía Evolution API Go a {clean_number}."
    except Exception:
        pass

    # 2. Fallback a endpoint de Evolution API v2 (/message/sendText/{instance_name})
    url = f"{evo_url}/message/sendText/{instance_name}"
    payload = {
        "number": clean_number,
        "text": text,
        "delay": delay_ms,
        "linkPreview": True
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code in [200, 201]:
            return f" Mensaje enviado exitosamente a {clean_number}. ID del mensaje: {r.json().get('key', {}).get('id')}"
        return f"Error al enviar mensaje (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al enviar mensaje: {e}"

@mcp.tool()
def evolution_send_media_message(instance_name: str, number: str, media_url: str, media_type: str, caption: str = "") -> str:
    """Envía un archivo multimedia (imagen, documento PDF, video o audio) por WhatsApp. media_type puede ser 'image', 'document', 'video', 'audio'."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    clean_number = "".join(filter(str.isdigit, number))

    url = f"{evo_url}/message/sendMedia/{instance_name}"
    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    payload = {
        "number": clean_number,
        "mediatype": media_type,
        "media": media_url,
        "caption": caption
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        if r.status_code in [200, 201]:
            return f" Archivo multimedia ({media_type}) enviado exitosamente a {clean_number}."
        return f"Error al enviar multimedia (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al enviar multimedia: {e}"

# ==============================================================================
# 3. TYPEBOT INTEGRATION (CONVERSATIONAL CHATBOT ENGINE)
# ==============================================================================
@mcp.tool()
def evolution_link_typebot(
    instance_name: str,
    typebot_slug: str,
    typebot_url: Optional[str] = None,
    trigger_type: str = "all",
    debounce_time: int = 8,
    delay_message: int = 1500,
    stop_bot_from_me: bool = True,
    keyword_finish: str = "#HUMANO"
) -> str:
    """Vincula un flujo de Typebot a una instancia de WhatsApp en Evolution API con parámetros anti-baneo y de simulación humana."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    target_typebot_url = typebot_url or os.environ.get("TYPEBOT_VIEWER_URL")
    if not target_typebot_url:
        raise ValueError("Debes proporcionar 'typebot_url' o definir la variable 'TYPEBOT_VIEWER_URL'.")

    target_typebot_url = target_typebot_url.rstrip("/")

    url = f"{evo_url}/typebot/create/{instance_name}"
    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    payload = {
        "enabled": True,
        "url": target_typebot_url,
        "typebot": typebot_slug,
        "triggerType": trigger_type,
        "triggerOperator": "none",
        "triggerValue": "",
        "expire": 0,
        "keywordFinish": keyword_finish,
        "delayMessage": delay_message,
        "unknownMessage": "No he comprendido tu respuesta.",
        "listeningFromMe": False,
        "stopBotFromMe": stop_bot_from_me,
        "keepOpen": True,
        "debounceTime": debounce_time
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code in [200, 201]:
            return (
                f" Typebot '{typebot_slug}' vinculado exitosamente a la instancia '{instance_name}'.\n"
                f"- URL Typebot: {target_typebot_url}\n"
                f"- Debounce Time: {debounce_time}s (evita spam de mensajes cortados)\n"
                f"- Delay Escritura: {delay_message}ms (simulación humana)\n"
                f"- Pausa si responde humano: {'Sí' if stop_bot_from_me else 'No'}\n"
                f"- Palabra clave de salida a asesor: '{keyword_finish}'"
            )
        return f"Error al vincular Typebot (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al vincular Typebot: {e}"

@mcp.tool()
def typebot_change_session_status(instance_name: str, remote_jid: str, status: str) -> str:
    """Cambia el estado de la sesión de Typebot para un usuario específico de WhatsApp ('opened', 'paused', 'closed'). Útil cuando un humano interviene."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    valid_statuses = ["opened", "paused", "closed"]
    if status.lower() not in valid_statuses:
        return f"Estado inválido. Debe ser uno de: {valid_statuses}"

    url = f"{evo_url}/typebot/changeStatus/{instance_name}"
    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    
    # Formatear JID si solo se pasó el número
    clean_jid = remote_jid if "@" in remote_jid else f"{''.join(filter(str.isdigit, remote_jid))}@s.whatsapp.net"

    payload = {
        "remoteJid": clean_jid,
        "status": status.lower()
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code == 200:
            return f" Sesión de Typebot para {clean_jid} cambiada a '{status.lower()}' con éxito."
        return f"Error al cambiar status (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al cambiar status de Typebot: {e}"

# ==============================================================================
# 4. CHATWOOT INTEGRATION (HUMAN HANDOFF & INBOX CRM)
# ==============================================================================
@mcp.tool()
def evolution_link_chatwoot(
    instance_name: str,
    account_id: str,
    token: str,
    chatwoot_url: Optional[str] = None,
    sign_msg: bool = True,
    reopen_conversation: bool = True
) -> str:
    """Vincula una instancia de WhatsApp a una bandeja de soporte compartida en Chatwoot para atención humana."""
    evo_url = get_env_var("EVOLUTION_API_URL")
    evo_key = get_env_var("EVOLUTION_API_KEY")

    target_chatwoot_url = chatwoot_url or os.environ.get("CHATWOOT_API_URL")
    if not target_chatwoot_url:
        raise ValueError("Debes proporcionar 'chatwoot_url' o definir la variable 'CHATWOOT_API_URL'.")

    target_chatwoot_url = target_chatwoot_url.rstrip("/")

    url = f"{evo_url}/chatwoot/create/{instance_name}"
    headers = {"apikey": evo_key, "Content-Type": "application/json"}
    payload = {
        "enabled": True,
        "account_id": account_id,
        "token": token,
        "url": target_chatwoot_url,
        "sign_msg": sign_msg,
        "reopen_conversation": reopen_conversation,
        "conversation_pending": False,
        "import_contacts": True,
        "import_messages": True,
        "days_limit_import": 3
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        if r.status_code in [200, 201]:
            return f" Chatwoot vinculado exitosamente a la instancia '{instance_name}' en {target_chatwoot_url} (Account ID: {account_id})."
        return f"Error al vincular Chatwoot (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al vincular Chatwoot: {e}"

@mcp.tool()
def chatwoot_list_conversations(status: str = "open") -> str:
    """Consulta la lista de conversaciones abiertas o pendientes en Chatwoot para atención de asesores."""
    chatwoot_url = get_env_var("CHATWOOT_API_URL")
    chatwoot_token = get_env_var("CHATWOOT_API_TOKEN")
    account_id = os.environ.get("CHATWOOT_ACCOUNT_ID", "1")

    url = f"{chatwoot_url}/api/v1/accounts/{account_id}/conversations?status={status}"
    headers = {"api_access_token": chatwoot_token}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            payload_data = data.get("data", {}).get("payload", [])
            summary = []
            for conv in payload_data[:10]: # primeros 10
                c_id = conv.get("id")
                contact = conv.get("meta", {}).get("sender", {}).get("name", "Desconocido")
                phone = conv.get("meta", {}).get("sender", {}).get("phone_number", "")
                unread = conv.get("unread_count", 0)
                summary.append(f"• ID: {c_id} | Contacto: {contact} ({phone}) | Sin leer: {unread}")
            return f"Total conversaciones ({status}): {len(payload_data)}\n" + ("\n".join(summary) if summary else "No hay conversaciones pendientes.")
        return f"Error al obtener conversaciones de Chatwoot (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al consultar Chatwoot: {e}"

@mcp.tool()
def chatwoot_send_reply(conversation_id: int, message: str) -> str:
    """Envía un mensaje de respuesta desde Chatwoot directamente al cliente de WhatsApp."""
    chatwoot_url = get_env_var("CHATWOOT_API_URL")
    chatwoot_token = get_env_var("CHATWOOT_API_TOKEN")
    account_id = os.environ.get("CHATWOOT_ACCOUNT_ID", "1")

    url = f"{chatwoot_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
    headers = {"api_access_token": chatwoot_token, "Content-Type": "application/json"}
    payload = {
        "content": message,
        "message_type": "outgoing",
        "private": False
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        if r.status_code in [200, 201]:
            return f" Respuesta enviada a la conversación ID {conversation_id} en Chatwoot."
        return f"Error al enviar respuesta en Chatwoot (HTTP {r.status_code}): {r.text}"
    except Exception as e:
        return f"Excepción al responder en Chatwoot: {e}"

# Entrypoint
if __name__ == "__main__":
    logger.info("Iniciando WhatsApp Stack Unified MCP Server sobre stdio...")
    mcp.run(transport="stdio")
