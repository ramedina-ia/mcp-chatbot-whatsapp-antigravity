# 🤖 WhatsApp AI Agent Stack + Google Antigravity MCP Server

> **Stack empresarial 100% Open-Source y Autoalojable ($0 en licencias):**  
> Agente de Inteligencia Artificial para WhatsApp con **Evolution API Go**, **Chatwoot**, **NVIDIA NIM (MiniMax / DeepSeek)** y un **Servidor MCP Unificado** para control directo desde **Google Antigravity**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![FastMCP](https://img.shields.io/badge/FastMCP-Google%20Antigravity-00F0FF)](https://modelcontextprotocol.io/)
[![Evolution Go](https://img.shields.io/badge/Evolution%20Go-Whatsmeow-00E676?logo=whatsapp&logoColor=white)](https://github.com/EvolutionAPI)
[![Chatwoot](https://img.shields.io/badge/Chatwoot-Handoff%20Humano-1F93FF)](https://www.chatwoot.com/)
[![NVIDIA NIM](https://img.shields.io/badge/NVIDIA%20NIM-MiniMax%20%7C%20DeepSeek-76B900?logo=nvidia&logoColor=white)](https://build.nvidia.com)

---

## 📑 Tabla de Contenidos
1. [¿Por qué este Stack?](#-por-qué-este-stack)
2. [Arquitectura del Sistema](#-arquitectura-del-sistema)
3. [Novedad Crítica: Migración a Evolution API Go](#-novedad-crítica-migración-a-evolution-api-go)
4. [Estructura del Repositorio](#-estructura-del-repositorio)
5. [Requisitos Previos](#-requisitos-previos)
6. [Instalación y Despliegue en VPS (Paso a Paso)](#-instalación-y-despliegue-en-vps-paso-a-paso)
7. [Configuración del Servidor MCP en Google Antigravity](#-configuración-del-servidor-mcp-en-google-antigravity)
8. [Variables de Entorno (.env)](#-variables-de-entorno-env)
9. [Protocolo Anti-Baneo de WhatsApp](#-protocolo-anti-baneo-de-whatsapp)
10. [Licencia y Créditos](#-licencia-y-créditos)

---

## 🚀 ¿Por qué este Stack?
Los chatbots tradicionales basados en árboles de decisión (como ManyChat o Botmaker) son costosos, rígidos y frustran a los clientes. Este proyecto implementa una solución de nivel corporativo que:
* **$0 en Licencias de Software:** Sin pagos mensuales por contactos; autoalojado en un VPS de $5-$10/mes (Vultr, Hostinger, DigitalOcean).
* **Agente Cognitivo Multimodelo (NVIDIA NIM):** Motor con `minimaxai/minimax-m3.1-flash` (ultra rápido, razonamiento en español nativo) y fallbacks automáticos a `deepseek-ai/deepseek-v4.1-flash` y `nvidia/nemotron-3.5-lightning`.
* **Cotizador Matemático en Tiempo Real:** Calcula productos, servicios, mobiliario y fletes geográficos específicos.
* **Handoff Humano Inteligente:** Cuando el cliente pide un asesor o cotizaciones especiales (catering, banquetes), el bot se silencia en memoria y transfiere la conversación en vivo a la bandeja de **Chatwoot**.
* **Centro de Mando MCP en Google Antigravity:** Diagnóstico de salud, creación de instancias, envío de mensajes y gestión de tickets ejecutados directamente desde prompts o agentes en el IDE.

---

## 🏗️ Arquitectura del Sistema

```
┌────────────────────────────────────────────────────────┐
│                   CLIENTE EN WHATSAPP                  │
└──────────────────────────┬─────────────────────────────┘
                           │ (Mensaje de texto / imagen)
                           ▼
┌────────────────────────────────────────────────────────┐
│        EVOLUTION API GO (Puerto 8080 - Golang)         │
│          Gateway nativo WhatsApp Web / Whatsmeow       │
└──────────────┬──────────────────────────┬──────────────┘
               │ (Webhook)                │ (Sync)
               ▼                          ▼
┌──────────────────────────────┐   ┌─────────────────────┐
│      FASTAPI AGENT BOT       │   │      CHATWOOT       │
│  Lógica de Negocio + Memoria │   │ Bandeja Asesores    │
│  Detección de Handoff Humano │   │ (Handoff en Vivo)   │
└──────────────┬───────────────┘   └─────────────────────┘
               │
               ▼
┌──────────────────────────────┐   ┌─────────────────────┐
│      NVIDIA NIM ENGINE       │   │  GOOGLE ANTIGRAVITY │
│   MiniMax M3.1 / DeepSeek    │   │ Servidor FastMCP    │
│    (Inferencia Gratuita)     │   │ whatsapp-stack-mcp  │
└──────────────────────────────┘   └─────────────────────┘
```

---

## ⚡ Novedad Crítica: Migración a Evolution API Go

En versiones previas se utilizaba Evolution API v2 (Node.js/Baileys). Este repositorio ha sido actualizado a **Evolution API Go (`evoapicloud/evolution-go:latest`)**:

| Característica | Evolution API v2 (Node.js) | Evolution API Go (Golang) |
| :--- | :---: | :---: |
| **Consumo de Memoria RAM** | ~500 MB - 800 MB | **~35 MB - 60 MB (90% menor)** |
| **Motor WhatsApp** | Baileys (Node.js) | **Whatsmeow (Golang puro)** |
| **Estabilidad de Sesión** | Desconexiones ocasionales | **Reconexión instantánea y persistente** |
| **Endpoint de Envío** | `/message/sendText/{instance}` | **`/send/text`** |
| **Rendimiento en VPS $5** | Límite ajustado de RAM | **Múltiples instancias fluidas** |

---

## 📂 Estructura del Repositorio

```
.
├── bot/
│   ├── bot.py                # Servidor FastAPI con lógica LLM y Handoff
│   ├── Dockerfile            # Contenedor Python 3.11
│   └── requirements.txt      # Dependencias del bot
├── mcp-server/
│   ├── server.py             # Servidor FastMCP para Google Antigravity
│   ├── test_tools.py         # Script de pruebas automáticas MCP
│   ├── requirements.txt      # Librerías FastMCP y Requests
│   ├── .env.example          # Plantilla de variables MCP
│   └── README.md             # Guía de configuración en Antigravity
├── docker-compose.yml        # Orquestador maestro de todos los servicios
├── .env.example              # Variables maestras del entorno
├── .gitignore                # Archivos ignorados por Git
└── README.md                 # Documentación maestra
```

---

## ⚙️ Instalación y Despliegue en VPS (Ubuntu 24.04 LTS)

### 1. Clonar el repositorio en tu servidor:
```bash
git clone https://github.com/ramedina-ia/mcp-chatbot-whatsapp-antigravity.git /opt/chatbot-stack
cd /opt/chatbot-stack
```

### 2. Configurar variables de entorno:
```bash
cp .env.example .env
nano .env
```
> Configura tus contraseñas seguras, dominios y la clave de NVIDIA NIM (`NVIDIA_API_KEY`).

### 3. Crear la red externa de Docker:
```bash
docker network create chatbot_network
```

### 4. Iniciar todos los servicios:
```bash
docker compose up -d --build
```

### 5. Configurar SSL en Nginx Proxy Manager:
Accede al panel web de Nginx Proxy Manager en el puerto `81` (`http://TU_IP:81`):
* Usuario por defecto: `admin@example.com`
* Contraseña por defecto: `changeme`
* Apunta tus dominios (`api.tudominio.com`, `chat.tudominio.com`, etc.) con certificados SSL Let's Encrypt gratuitos.

---

## 🛠️ Configuración del Servidor MCP en Google Antigravity

Para controlar todo el stack desde Google Antigravity:

1. Clona o copia la carpeta `mcp-server/` a tu entorno local o configúralo remotamente.
2. Añade la configuración a tu archivo `~/.gemini/config/mcp_config.json`:

```json
{
  "mcpServers": {
    "whatsapp-stack-mcp": {
      "command": "python",
      "args": ["/ruta/absoluta/a/mcp-server/server.py"],
      "env": {
        "EVOLUTION_API_URL": "https://api.tudominio.com",
        "EVOLUTION_API_KEY": "TuClaveMaestraApiEvolution2026",
        "TYPEBOT_VIEWER_URL": "https://bot.tudominio.com",
        "CHATWOOT_API_URL": "https://chat.tudominio.com",
        "CHATWOOT_API_TOKEN": "TuTokenDeChatwoot",
        "CHATWOOT_ACCOUNT_ID": "1"
      }
    }
  }
}
```

### Herramientas MCP Disponibles:
* `check_stack_health`: Diagnóstico integral de Evolution Go, Typebot y Chatwoot.
* `evolution_create_instance`: Crea instancias de WhatsApp y genera código QR.
* `evolution_get_instance_status`: Consulta el estado de conexión (`open`, `connecting`, `close`).
* `evolution_get_qr_code`: Devuelve el código QR en Base64 para reconectar la sesión.
* `evolution_send_text_message`: Envía mensajes con simulación humana anti-baneo.
* `chatwoot_list_conversations`: Inspecciona conversaciones abiertas y pendientes de asesor.
* `chatwoot_send_reply`: Responde directamente al chat de WhatsApp desde el IDE.

---

## 🛡️ Protocolo Anti-Baneo de WhatsApp
1. **Calentamiento de chip (Warm-up):** No envíes mensajes masivos los primeros 7 días con un número nuevo.
2. **Presencia Humana:** Evolution API Go simula el estado `composing` (escribiendo...) antes de enviar la respuesta.
3. **Debounce Time:** El bot espera entre 6 y 8 segundos para acumular mensajes antes de invocar al LLM, evitando respuestas fragmentadas.
4. **Handoff Humano:** Si el cliente muestra molestia, el bot se silencia en seco para que un humano resuelva la situación.

---

## 📄 Licencia
Este proyecto está bajo la Licencia **MIT**. Eres libre de usarlo, modificarlo y desplegarlo para tu empresa o clientes.

Creado con ❤️ por **Ramiro Medina** | [YouTube: @ramiromedina-ia](https://www.youtube.com/@ramiromedina-ia) · [Telegram Oficial](https://t.me/ramiromedina_ai0)
