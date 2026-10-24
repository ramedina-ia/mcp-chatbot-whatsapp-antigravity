import os
import re
import json
import time
import logging
import requests
from typing import Dict, Any, List
from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("intempo_bot")

app = FastAPI(title="In Tempo Eventos WhatsApp Bot")

# Environment & Config
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

PRIMARY_MODEL = os.getenv("NVIDIA_PRIMARY_MODEL", "minimaxai/minimax-m3.1-flash")
FALLBACK_MODEL_1 = os.getenv("NVIDIA_FALLBACK_MODEL_1", "deepseek-ai/deepseek-v4.1-flash")
FALLBACK_MODEL_2 = os.getenv("NVIDIA_FALLBACK_MODEL_2", "nvidia/nemotron-3.5-lightning-30b-a3b")

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://evolution_api:8080")
EVOLUTION_INSTANCE_TOKEN = os.getenv("EVOLUTION_INSTANCE_TOKEN", "")

CHATWOOT_URL = os.getenv("CHATWOOT_URL", "http://chatwoot_web:3000")
CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN", "")
CHATWOOT_ACCOUNT_ID = os.getenv("CHATWOOT_ACCOUNT_ID", "1")
CHATWOOT_INBOX_ID = int(os.getenv("CHATWOOT_INBOX_ID", "1"))

# In-memory session tracking
# phone -> list of messages [{"role": "user"|"assistant", "content": "..."}]
conversation_memory: Dict[str, List[Dict[str, Any]]] = {}
# Set of phones where handoff to human agent is active (bot silences itself)
handoff_active_sessions = set()

HANDOFF_KEYWORDS = [
    "catering", "banquete", "banquetes", "comida para", "comidas para",
    "papayera", "papayeras", "chirimia", "chirimía", "chirimias", "chirimías",
    "asesor", "humano", "persona", "agente", "comunicarme con alguien", "hablar con alguien"
]

SYSTEM_PROMPT = """Eres el asesor comercial y asistente virtual oficial de "In Tempo Eventos" en Medellín, Colombia.
Atiendes clientes por WhatsApp con un tono muy amable, cálido (estilo paisa profesional, cercano, educado y servicial).
Directamente responde al cliente en español con la información y cotización solicitada. NO incluyas razonamiento interno ni meta-comentarios en tu respuesta.

--- INFORMACIÓN DEL NEGOCIO ---
- Empresa: In Tempo Eventos (más de 12 años de trayectoria). "Eventos que inspiran historias".
- Sede física: Calle 77CC # 91-75, Robledo, Medellín, Colombia.
- Teléfono / WhatsApp oficial: 305 322 8123
- Correo: intempoeventos@gmail.com
- Sitio Web: https://www.intempoeventos.com/

--- CATÁLOGO DE MOBILIARIO Y DECORACIÓN ---
- Sillas Rimax (blancas sin brazos, cómodas y resistentes): $1.600 COP cada una.
- Mesas (plegables, capacidad para 8 personas): $12.000 COP cada una.
- Manteles blancos (base elegante): $10.000 COP cada uno.
- Sobremanteles (colores disponibles: rosados, dorados y 1 rojo): $6.000 COP cada uno.
- Arco en acero dorado para decoración: $40.000 COP.
- Bases cilíndricas decorativas (juego de 3 bases): $40.000 COP.

--- TARIFAS DE TRANSPORTE (Flete ida y vuelta: entrega y recogida) ---
- Robledo cercano (alrededor de 2 km²): $35.000 COP.
- Robledo perímetro extendido: $50.000 COP.
- Sectores cercanos (Doce de Octubre, Castilla, Calasanz, Los Colores): $60.000 COP.
- Sectores norte / sur (Niquía/Bello, El Poblado, Envigado, Itagüí, Sabaneta, La Estrella): $100.000 COP.
- Municipios retirados de Antioquia (Copacabana, Caldas, Rionegro, etc.): Valor a convenir según distancia, peajes y combustible.

--- REGLAS DE ENTREGA Y ALQUILER ---
1. Duración del alquiler: 24 horas (se entrega el día del evento en la mañana o en la tarde y se recoge al día siguiente).
2. Recargo por pisos: Si el evento es en un edificio o casa con MÁS DE 3 PISOS SIN ASCENSOR (piso 4 en adelante), se cobra un recargo de $20.000 COP por cargue y subida de escaleras. En pisos 1, 2 o 3, o con ascensor, no hay recargo ($0).

--- DEPÓSITO DE GARANTÍA (100% REEMBOLSABLE) ---
- Solo sillas (hasta 50 sillas): Depósito de $50.000 COP.
- Con mesas plegables (hasta 5 mesas): Depósito de $100.000 COP.
- Cantidades mayores: Se calcula de forma proporcional ($50.000 por cada bloque de 50 sillas adicionales y $100.000 por cada bloque de 5 mesas adicionales).
- El depósito se devuelve íntegro al recoger el mobiliario en buen estado.

--- SERVICIOS DE MINITECAS (Sonido, Luces, DJ Crossover, Animación) ---
(Precios netos para Medellín, Bello, Envigado, Sabaneta e Itagüí)
1. Miniteca Sencilla ($400.000 COP): 1.000W sonido, 4 luces audiorítmicas, PC +30.000 canciones, consola 6 canales, micrófono, DJ crossover por 5 horas.
2. Miniteca Básica ($600.000 COP): 1.200W sonido, 6 luces audiorítmicas, máquina de humo, consola 6 canales, micrófono, DJ crossover por 5 horas.
3. Miniteca Mediana ($800.000 COP): 2.400W sonido, 8 luces audiorítmicas, humo LED, hora loca (bombas chorizo o manillas neón), consola 6 canales, micrófono, DJ crossover por 5 horas.
4. Miniteca Premium ($1.000.000 COP): 2.800W sonido, estructura tipo arco 2x3m, 10 luces robotizadas, humo LED, DJ animador especialista, hora loca, consola 12 canales, micrófono, servicio por 5 horas.
5. Miniteca Profesional ($1.600.000 COP): 3.000W sonido, estructura en H tipo truss (aluminio), 12 luces robotizadas, pantalla LED 32" para karaoke, consola de mezcla + ecualización 12 canales, micrófono inalámbrico, DJ profesional + Animador, hora loca, servicio por 6 horas.

--- REGLAS DE ATENCIÓN Y COTIZACIÓN ---
1. Cuando un cliente cotice mobiliario, pídele amablemente los datos clave si no los ha dado:
   - Fecha del evento.
   - Lugar exacto / barrio del evento (para cotizar el transporte exacto).
   - Piso y si cuenta con ascensor.
   - Cantidades aproximadas de sillas, mesas y mantelería.
2. Presenta la cotización siempre con desglose claro y profesional:
   - Subtotal Mobiliario.
   - Costo de Transporte (entrega y recogida).
   - Recargo de piso (si aplica).
   - Valor Total del alquiler.
   - Depósito de garantía reembolsable.
3. Si el cliente acepta la cotización y desea reservar, infórmale que la reserva se realiza con:
   - Dirección exacta del evento.
   - Nombre completo del responsable.
   - 2 números telefónicos de contacto.
   - Correo electrónico.

--- SERVICIOS COMPLEJOS Y TRANSFERENCIA HUMANA (HANDOFF) ---
- Nota cultural: En Colombia, "papayera" o "chirimía" es una agrupación musical tradicional de instrumentos de viento y percusión que toca música festiva y alegre en vivo.
- Si el cliente pregunta por CATERING / BANQUETES / COMIDA, PAPAYERA / CHIRIMÍA (música en vivo), DECORACIÓN PERSONALIZADA INTEGRAL, o si solicita hablar con una persona/asesor:
  - Responde amablemente confirmando que estos servicios se coordinan de forma personalizada con un asesor comercial experto.
  - Informa que ya estás transfiriendo la conversación a un asesor humano.
  - Al final de tu respuesta agrega obligatoriamente la etiqueta oculta: [HANDOFF_HUMANO]
"""

def clean_llm_output(text: str) -> str:
    """Removes thinking tags or reasoning leaks from LLM responses."""
    if not text:
        return ""
    # Strip <think>...</think>
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip "Here's a thinking process: ... \n\n"
    if "Here's a thinking process:" in text:
        parts = text.split("Here's a thinking process:")
        last_part = parts[-1]
        lines = last_part.split("\n")
        filtered_lines = []
        started = False
        for line in lines:
            line_lower = line.lower()
            if any(greeting in line_lower for greeting in ["¡hola", "hola", "buenas", "buenos días", "estimado", "cordial", "**cotización"]):
                started = True
            if started:
                filtered_lines.append(line)
        if filtered_lines:
            text = "\n".join(filtered_lines)
    return text.strip()

def query_nvidia_llm(messages: List[Dict[str, Any]]) -> str:
    """Queries NVIDIA NIM with multi-tier fallback (Minimax Flash -> DeepSeek Flash -> Nemotron)."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }

    # 1. Primary Model: Minimax M3.1 Flash (ultra fast, high quality Spanish, reasoning separated)
    logger.info(f"Querying primary model: {PRIMARY_MODEL}...")
    try:
        payload_primary = {
            "model": PRIMARY_MODEL,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1200
        }
        r = requests.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers=headers,
            json=payload_primary,
            timeout=18
        )
        if r.status_code == 200:
            data = r.json()
            choice = data["choices"][0]["message"]
            content = choice.get("content")
            if content:
                cleaned = clean_llm_output(content)
                if cleaned:
                    logger.info(f"Primary model {PRIMARY_MODEL} responded successfully ({len(cleaned)} chars).")
                    return cleaned
    except Exception as e:
        logger.warning(f"Primary model {PRIMARY_MODEL} error/timeout: {e}. Trying fallback 1...")

    # 2. Fallback Model 1: DeepSeek v4.1 Flash with streaming
    logger.info(f"Querying fallback 1: {FALLBACK_MODEL_1} (streaming)...")
    try:
        payload_fallback1 = {
            "model": FALLBACK_MODEL_1,
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 1024,
            "stream": True
        }
        r = requests.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers={**headers, "Accept": "text/event-stream"},
            json=payload_fallback1,
            stream=True,
            timeout=15
        )
        if r.status_code == 200:
            full_text = []
            for line in r.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        chunk_str = decoded[6:].strip()
                        if chunk_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(chunk_str)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_text.append(content)
                        except Exception:
                            pass
            result = "".join(full_text).strip()
            if result:
                cleaned = clean_llm_output(result)
                logger.info(f"Fallback 1 {FALLBACK_MODEL_1} responded successfully ({len(cleaned)} chars).")
                return cleaned
    except Exception as e:
        logger.warning(f"Fallback 1 {FALLBACK_MODEL_1} error/timeout: {e}. Trying fallback 2...")

    # 3. Fallback Model 2: Nemotron 3.5 Lightning
    logger.info(f"Querying fallback 2: {FALLBACK_MODEL_2}...")
    try:
        payload_fallback2 = {
            "model": FALLBACK_MODEL_2,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1000
        }
        r = requests.post(
            f"{NVIDIA_BASE_URL}/chat/completions",
            headers=headers,
            json=payload_fallback2,
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            choice = data["choices"][0]["message"]
            content = choice.get("content") or choice.get("reasoning_content", "")
            if content:
                cleaned = clean_llm_output(content)
                logger.info(f"Fallback 2 {FALLBACK_MODEL_2} responded successfully ({len(cleaned)} chars).")
                return cleaned
    except Exception as e:
        logger.error(f"Fallback 2 {FALLBACK_MODEL_2} error: {e}")

    return "¡Hola! Gracias por comunicarte con In Tempo Eventos. En este momento estamos procesando tu solicitud, en un instante uno de nuestros asesores te atenderá personalmente."

def send_whatsapp_text(number: str, text: str):
    """Sends a text message back to WhatsApp via Evolution GO."""
    url = f"{EVOLUTION_API_URL}/send/text"
    headers = {
        "apikey": EVOLUTION_INSTANCE_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "number": number,
        "text": text
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(f"Evolution send result for {number}: status {r.status_code}")
    except Exception as e:
        logger.error(f"Error sending WhatsApp message to {number}: {e}")

def sync_to_chatwoot(phone: str, name: str, user_text: str, bot_text: str, is_handoff: bool, reason: str = ""):
    """Synchronizes customer conversation to Chatwoot for human supervision & handoff."""
    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }
    base = f"{CHATWOOT_URL}/api/v1/accounts/{CHATWOOT_ACCOUNT_ID}"

    try:
        # 1. Search or Create Contact
        contact_id = None
        r_search = requests.get(f"{base}/contacts/search?q={phone}", headers=headers, timeout=5)
        if r_search.status_code == 200 and r_search.json().get("payload"):
            contact_id = r_search.json()["payload"][0]["id"]
        else:
            c_payload = {
                "inbox_id": CHATWOOT_INBOX_ID,
                "name": name if name else f"Cliente {phone[-4:]}",
                "phone_number": f"+{phone}" if not phone.startswith("+") else phone
            }
            r_c = requests.post(f"{base}/contacts", headers=headers, json=c_payload, timeout=5)
            if r_c.status_code == 200:
                contact_id = r_c.json().get("payload", {}).get("contact", {}).get("id")

        if not contact_id:
            logger.warning(f"Could not find or create Chatwoot contact for {phone}")
            return

        # 2. Find or Create Conversation
        conv_id = None
        r_convs = requests.get(f"{base}/contacts/{contact_id}/conversations", headers=headers, timeout=5)
        if r_convs.status_code == 200 and r_convs.json().get("payload"):
            conv_id = r_convs.json()["payload"][0]["id"]
        else:
            conv_payload = {
                "inbox_id": CHATWOOT_INBOX_ID,
                "contact_id": contact_id,
                "status": "open"
            }
            r_create_conv = requests.post(f"{base}/conversations", headers=headers, json=conv_payload, timeout=5)
            if r_create_conv.status_code == 200:
                conv_id = r_create_conv.json().get("id")

        if not conv_id:
            logger.warning(f"Could not find or create Chatwoot conversation for {phone}")
            return

        # 3. Post User Message
        if user_text:
            requests.post(
                f"{base}/conversations/{conv_id}/messages",
                headers=headers,
                json={"content": user_text, "message_type": "incoming"},
                timeout=5
            )

        # 4. Post Bot Response
        if bot_text:
            requests.post(
                f"{base}/conversations/{conv_id}/messages",
                headers=headers,
                json={"content": bot_text, "message_type": "outgoing"},
                timeout=5
            )

        # 5. If Handoff, mark conversation with private note
        if is_handoff:
            note_reason = reason if reason else "El cliente solicita atención personalizada (catering, papayera o asesor humano)."
            requests.post(
                f"{base}/conversations/{conv_id}/messages",
                headers=headers,
                json={
                    "content": f"⚠️ [ALERTA DE TRANSFERENCIA HUMANA]\n{note_reason}\nEl bot se ha silenciado automáticamente para que puedas atender personalmente al cliente.",
                    "message_type": "activity",
                    "private": True
                },
                timeout=5
            )
            logger.info(f"Handoff note posted in Chatwoot conversation #{conv_id}")

    except Exception as e:
        logger.error(f"Error syncing with Chatwoot: {e}")

def process_incoming_message(data: Dict[str, Any]):
    """Background task to process incoming message and generate response."""
    try:
        info = data.get("Info", {})
        if not info:
            info = data.get("data", {}).get("Info", {})

        is_from_me = info.get("IsFromMe", False) or info.get("isFromMe", False)
        is_group = info.get("IsGroup", False) or info.get("isGroup", False)

        if is_from_me or is_group:
            # Ignore bot's own messages and group chats
            return

        sender_jid = info.get("Chat", "") or info.get("Sender", "") or info.get("chat", "")
        # Extract digits only
        phone_digits = "".join(filter(str.isdigit, sender_jid.split("@")[0]))
        if not phone_digits:
            return

        push_name = info.get("PushName", "") or info.get("pushName", "") or "Cliente"

        # Extract text content
        msg_obj = data.get("Message", {})
        if not msg_obj:
            msg_obj = data.get("data", {}).get("Message", {})

        text = ""
        if "conversation" in msg_obj:
            text = msg_obj["conversation"]
        elif "extendedTextMessage" in msg_obj:
            text = msg_obj["extendedTextMessage"].get("text", "")
        elif "imageMessage" in msg_obj:
            text = msg_obj["imageMessage"].get("caption", "Foto de referencia enviada por el cliente.")
            logger.info(f"Image received from {phone_digits} with caption: {text}")

        if not text:
            return

        logger.info(f"Received message from {push_name} ({phone_digits}): {text}")

        # Check if handoff is currently active for this phone
        if phone_digits in handoff_active_sessions:
            logger.info(f"Handoff is active for {phone_digits}. Bot remains silent.")
            # Still sync incoming user message to Chatwoot
            sync_to_chatwoot(phone_digits, push_name, text, "", is_handoff=False)
            return

        # Check for immediate keyword handoff trigger
        lower_text = text.lower()
        keyword_match = None
        for kw in HANDOFF_KEYWORDS:
            if kw in lower_text:
                keyword_match = kw
                break

        # Build conversation memory
        if phone_digits not in conversation_memory:
            conversation_memory[phone_digits] = []

        history = conversation_memory[phone_digits]
        history.append({"role": "user", "content": text})
        if len(history) > 8:
            history = history[-8:]
            conversation_memory[phone_digits] = history

        # Format messages for NVIDIA NIM
        messages_payload = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        # Query LLM
        bot_reply = query_nvidia_llm(messages_payload)

        # Check for handoff flag (from keyword or model output tag)
        is_handoff = False
        handoff_reason = ""

        if keyword_match:
            is_handoff = True
            handoff_reason = f"El mensaje del cliente contiene la palabra clave '{keyword_match}'."

        if "[HANDOFF_HUMANO]" in bot_reply:
            is_handoff = True
            bot_reply = bot_reply.replace("[HANDOFF_HUMANO]", "").strip()
            if not handoff_reason:
                handoff_reason = "El asistente inteligente detectó la necesidad de transferir a un asesor comercial."

        if is_handoff:
            handoff_active_sessions.add(phone_digits)
            logger.info(f"Activated human handoff for {phone_digits} (Reason: {handoff_reason})")

        # Save assistant reply to memory
        history.append({"role": "assistant", "content": bot_reply})

        # Send response via WhatsApp
        send_whatsapp_text(phone_digits, bot_reply)

        # Synchronize conversation to Chatwoot
        sync_to_chatwoot(phone_digits, push_name, text, bot_reply, is_handoff=is_handoff, reason=handoff_reason)

    except Exception as e:
        logger.error(f"Error in process_incoming_message: {e}", exc_info=True)

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """Receives webhook events from Evolution GO."""
    try:
        body = await request.json()
        background_tasks.add_task(process_incoming_message, body)
        return {"status": "received"}
    except Exception as e:
        logger.error(f"Error parsing webhook body: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/chatwoot-webhook")
async def chatwoot_webhook(request: Request):
    """Listens to Chatwoot conversation events (e.g. unmute bot when conversation resolved)."""
    try:
        body = await request.json()
        event = body.get("event")
        if event == "conversation_status_changed":
            status = body.get("status")
            if status == "resolved":
                # Find phone of conversation and unmute
                meta = body.get("meta", {})
                sender = meta.get("sender", {})
                phone = sender.get("phone_number", "")
                digits = "".join(filter(str.isdigit, phone))
                if digits in handoff_active_sessions:
                    handoff_active_sessions.remove(digits)
                    logger.info(f"Conversation resolved in Chatwoot. Bot unmuted for {digits}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error in chatwoot-webhook: {e}")
        return {"status": "error"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "In Tempo Eventos WhatsApp Bot",
        "primary_model": PRIMARY_MODEL,
        "fallback_model_1": FALLBACK_MODEL_1,
        "fallback_model_2": FALLBACK_MODEL_2,
        "active_handoffs": len(handoff_active_sessions)
    }

@app.post("/unmute/{phone}")
def unmute_phone(phone: str):
    digits = "".join(filter(str.isdigit, phone))
    if digits in handoff_active_sessions:
        handoff_active_sessions.remove(digits)
        return {"status": "unmuted", "phone": digits}
    return {"status": "not_muted", "phone": digits}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)
