# WhatsApp Stack Unified MCP Server (Google Antigravity)

Servidor **Model Context Protocol (FastMCP)** unificado para controlar y automatizar chatbots de WhatsApp en un entorno VPS con **Evolution API Go**, **Typebot** y **Chatwoot**.

## 🛠️ Herramientas Incluidas (Tools)

### 1. Diagnóstico y Salud
* `check_stack_health`: Verifica la disponibilidad y conectividad hacia Evolution API Go, Typebot y Chatwoot.

### 2. Gestión de WhatsApp (Evolution API Go)
* `evolution_create_instance`: Crea una instancia de WhatsApp y genera el código QR / pairing code.
* `evolution_get_instance_status`: Consulta el estado de la conexión (`open`, `connecting`, `close`).
* `evolution_get_qr_code`: Obtiene el código QR actualizado en Base64 para reconectar la sesión si expiró.
* `evolution_send_text_message`: Envía mensajes de texto simulando escritura humana (`delay`). Soporta endpoint nativo Go (`/send/text`) y fallback v2.
* `evolution_send_media_message`: Envía documentos (PDFs, catálogos), imágenes, audios o videos.

### 3. Motor Conversacional (Typebot)
* `evolution_link_typebot`: Vincula un bot de Typebot a tu WhatsApp con parámetros anti-baneo (`debounceTime: 8`, `delayMessage: 1500`, `stopBotFromMe: true`).
* `typebot_change_session_status`: Pausa (`paused`), reanuda (`opened`) o cierra (`closed`) la sesión del bot para un contacto cuando interviene un asesor humano.

### 4. Atención al Cliente y Handoff Humano (Chatwoot)
* `evolution_link_chatwoot`: Vincula WhatsApp a una bandeja compartida de Chatwoot.
* `chatwoot_list_conversations`: Lista los chats pendientes de atención humana.
* `chatwoot_send_reply`: Envía respuestas desde el asesor humano directamente al chat de WhatsApp.

## 🚀 Configuración en Google Antigravity
Añade a tu archivo `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "whatsapp-stack-mcp": {
      "command": "python",
      "args": ["ruta/al/mcp-server/server.py"],
      "env": {
        "EVOLUTION_API_URL": "https://api.tudominio.com",
        "EVOLUTION_API_KEY": "TuClave",
        "TYPEBOT_VIEWER_URL": "https://bot.tudominio.com",
        "CHATWOOT_API_URL": "https://chat.tudominio.com",
        "CHATWOOT_API_TOKEN": "TuToken",
        "CHATWOOT_ACCOUNT_ID": "1"
      }
    }
  }
}
```
