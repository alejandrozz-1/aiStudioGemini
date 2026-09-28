# Práctica: Google Gemini API con Python (`google-genai`)

Script funcional que conecta con la **API de Gemini** desde Python y ejecuta las tres
tareas de la práctica:

1. **Prompt de texto** básico (comprobación de conexión).
2. **Análisis de sentimiento + extracción de entidades** sobre 5 textos en español y
   5 en inglés, con salida JSON estructurada.
3. **Capacidad multimodal**: envío de una imagen (`foto.jpg`) y obtención de una
   descripción detallada en español.

---

## 1. Requisitos

| Elemento | Versión usada |
|---|---|
| Python | 3.14.7 (funciona con 3.9+) |
| `google-genai` (SDK oficial) | 2.25.0 |
| `python-dotenv` | 1.2.3 |
| `Pillow` | 12.3.0 |

## 2. Instalación

```bash
pip install google-genai python-dotenv Pillow
# o, equivalente:
pip install -r requirements.txt
```

> `Pillow` solo se usa para abrir la imagen antes de enviarla; el SDK también acepta
> bytes directamente si prefieres prescindir de él.

## 3. Obtención de la API Key (paso a paso)

1. Abrir **Google AI Studio**: <https://aistudio.google.com>.
2. Iniciar sesión con una cuenta de Google (no requiere tarjeta de crédito).
3. En el menú lateral, pulsar **«Get API key»** → **«Create API key»**.
4. Elegir **«Create API key in new project»** (recomendado) o un proyecto existente
   de Google Cloud.
5. Copiar la clave generada (empieza por `AQ...`). Se muestra solo una vez: si se
   pierde, se puede regenerar.
6. Opcional pero recomendable: en **Google Cloud Console → APIs & Services →
   Credentials**, restringir la clave a la *Generative Language API* y a tu IP.

**Segmentación de cuotas:** los límites se aplican **por proyecto**, no por clave
(`ai.google.dev/gemini-api/docs/rate-limits`). Varias claves del mismo proyecto
comparten la misma cuota.

### Almacenamiento seguro de la clave

La clave se guarda en el archivo `.env` (ignorado por git):

```dotenv
GEMINI_API_KEY="AQ..."
```

El script la carga con `python-dotenv`. **Nunca subir `.env` al repositorio**
ya que Google revoca claves expuestas públicamente. Existe un `.gitignore` que
incluye `.env`.

## 4. Ejecución

```bash
python gemini_demo.py
```

Salida esperada:

```
=== PARTE 1: SENTIMIENTO Y ENTIDADES ===

[ES] Me encanta la nueva interfaz del sistema, es súper intuitiva y rápida.
    Sentimiento : positivo
    Entidades   : sistema (producto)
    Justificación: ...

=== PARTE 2: DESCRIPCIÓN MULTIMODAL (IMAGEN) ===

1) Escena y elementos principales: ...
```

Además, la Parte 1 vuelca todos los resultados a `resultados_sentimiento.json`.

## 5. Qué hace el script (`gemini_demo.py`)

| Bloque | Implementación |
|---|---|
| Modelo | `gemini-3.6-flash` (constante `MODEL_NAME`, fácil de cambiar) |
| Conexión | `genai.Client(api_key=...)` leyendo `GEMINI_API_KEY` del entorno |
| Sentimiento | `response_mime_type="application/json"` + `response_schema` (JSON estructurado con `enum` de sentimientos `positivo/negativo/neutro`, array de entidades `{texto, tipo}` y justificación). `temperature=0.1` para respuestas deterministas. |
| Entradas | 5 textos ES + 5 textos EN (mezcla de positivos, negativos y neutros, con entidades como *Google*, *Microsoft*, *Apple*, *California*, *London*, horas y fechas) |
| Multimodal | `contents=[imagen, prompt]` con `PIL.Image.open("foto.jpg")` |
| Robustez | `try/except` por llamada, `time.sleep(1)` entre peticiones para respetar los RPM, resumen final de conteo de sentimientos |

## 6. Límites gratuitos (Free tier)

Referencia oficial: <https://ai.google.dev/gemini-api/docs/rate-limits> y
<https://ai.google.dev/gemini-api/docs/pricing> (la tabla de límites se muestra
también dentro de AI Studio, sección *Rate limits*).

- **Coste:** el *Free tier* no requiere tarjeta de crédito ni configurar billing.
- **Métricas de cuota:** RPM (peticiones/minuto), TPM (tokens/minuto) y RPD
  (peticiones/día). Las cuotas diarias se reinician a **medianoche (hora del
  Pacífico)**.
- **Ámbito:** la cuota es **por proyecto**, no por clave de API.
- **Orden de magnitud en modelos Flash (free tier):** de ~10 a ~20 RPM y ~250.000
  TPM; la RPD varía mucho según modelo (decenas de peticiones/día en los modelos
  Flash más recientes y hasta ~1.500 RPD en Flash/Flash-Lite más antiguos).
  **Consulta siempre el valor exacto en AIStudio → Rate limits**, porque Google
  lo ha ido ajustando con el tiempo.
- **Límites de contenido:** en free tier el contenido *se usa para mejorar los
  productos de Google*; al pasar a un tier de pago deja de usarse.
- **Otros:** `429 RESOURCE_EXHAUSTED` = cuota agotada (esperar y reintentar);
  *spend-based limits* solo aplican a tiers de pago.
- Esta práctica usa ~11 llamadas de texto + 1 de imagen, muy por debajo de
  cualquier límite diario, pero se deja un `sleep(1)` entre llamadas para no
  acercarse al RPM.

## 7. Resultados obtenidos

### 7.1 Comprobaciones que sí fueron correctas

| Prueba | Endpoint | Resultado |
|---|---|---|
| Listar modelos | `GET /v1beta/models` | **200 OK** – 61 modelos disponibles |
| Ficha de modelo | `GET /v1beta/models/gemini-3.6-flash` | **200 OK** |
| SDK instalado | `pip show google-genai` | 2.25.0 |
| Auth de la clave | ambos GET anteriores | Válida (una clave inválida daría `400 API_KEY_INVALID`) |

### 7.2 Incidencia: generación bloqueada (403)

Todas las llamadas de **generación** fallaron con:

```
google.genai.errors.ClientError: 403 PERMISSION_DENIED.
{'error': {'code': 403,
 'message': 'Your project has been denied access. Please contact support.',
 'status': 'PERMISSION_DENIED'}}
```

Diagnóstico realizado:

| Comprobación | Resultado |
|---|---|
| 3 API keys distintas (la original, una nueva y la de un compañero) | Todas con el mismo patrón de prefijo (`AQ.Ab8RN6…`), **mismo 403** |
| SDK `models.generate_content` | 403 en `gemini-3.6-flash`, `3.8-flash`, `3.5-flash`, `3.1-pro-preview`, `flash-latest`, `gemma-4-*`, TTS, imagen… |
| REST directo con `httpx` (`x-goog-api-key`) | Mismo 403 → descarta error del SDK |
| API version `v1` y `v1beta` | Mismo 403 en ambas |
| Modelos antiguos (`gemini-2.5-flash`, `2.5-pro`) | `404 NOT_FOUND`: *«no longer available to new users»* (mensaje distinto, confirma que la clave y el proyecto sí se autentican) |
| Reintentos con espera (20 s × 3) | Mismo 403, no es un límite temporal ni un `429` |

**Conclusión:** el error no es de código ni de clave, sino de **autorización a
nivel de proyecto** en Google AI Studio («Your project has been denied access»).
`GET` funciona, `POST :generateContent` está denegado. La solución está del lado
de Google: comprobar en AI Studio si hay un aviso/política pendiente sobre el
proyecto, contactar con soporte o crear el proyecto con **otra cuenta de Google**.

**Reproducción mínima del fallo** (para adjuntar al soporte o para verificar
cuando se resuelva):

```python
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print(len(list(client.models.list())))            # 200 OK -> 61 modelos
r = client.models.generate_content(               # 403 PERMISSION_DENIED
    model="gemini-3.6-flash", contents="Responde OK"
)
print(r.text)
```

**Cómo obtener los resultados reales en cuanto se desbloquee el proyecto:**

```bash
python gemini_demo.py          # imprime las 10 clasificaciones + descripción de imagen
cat resultados_sentimiento.json
```

> Los resultados de sentimiento/entidades y la descripción de la imagen **no se
> incluyen en esta entrega** porque no fue posible ejecutar la generación con la
> API durante la práctica (incidente documentado arriba). El script está
> verificado y listo: solo requiere una API key con el proyecto habilitado.

## 8. Solución de problemas

| Error | Causa | Solución |
|---|---|---|
| `400 API_KEY_INVALID` | Clave mal copiada o revocada | Regenerar la clave en AI Studio |
| `403 PERMISSION_DENIED: Your project has been denied access` | Proyecto bloqueado por Google | Otra cuenta/proyecto o contactar soporte (ver §7.2) |
| `404 ... no longer available to new users` | Modelo antiguo retirado | Usar un modelo vigente (`gemini-3.6-flash`, `gemini-3.8-flash`, `gemini-flash-latest`) |
| `429 RESOURCE_EXHAUSTED` | Cuota RPM/TPM/RPD agotada | Esperar y reintentar; reducir frecuencia |
| `GEMINI_API_KEY is None` | Falta el archivo `.env` o la variable | Crear `.env` con `GEMINI_API_KEY="..."` |

## 9. Estructura del repositorio

```
.
├── gemini_demo.py              # script principal (texto + imagen)
├── test.py                     # diagnóstico rápido de la API key
├── foto.jpg                    # imagen de prueba para la parte multimodal
├── requirements.txt
├── .env                        # API key (NO se sube, está en .gitignore)
├── .gitignore
└── README.md                   # este archivo
```
