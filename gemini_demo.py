import json
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"

TEXTOES_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "sentimiento": types.Schema(
            type=types.Type.STRING,
            enum=["positivo", "negativo", "neutro"],
        ),
        "confianza": types.Schema(type=types.Type.STRING),
        "entidades": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "texto": types.Schema(type=types.Type.STRING),
                    "tipo": types.Schema(type=types.Type.STRING),
                },
                required=["texto", "tipo"],
            ),
        ),
        "justificacion": types.Schema(type=types.Type.STRING),
    },
    required=["sentimiento", "entidades"],
)

JSON_CONFIG = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=TEXTOES_SCHEMA,
    temperature=0.1,
)

TEXTOS = [
    ("es", "Me encanta la nueva interfaz del sistema, es súper intuitiva y rápida."),
    ("es", "El servicio técnico tardó tres días en responder y no solucionó el problema."),
    ("es", "La actualización se instalará esta noche a las 02:00 AM."),
    ("es", "No estoy seguro de si este cambio en la configuración nos beneficie a todos."),
    ("es", "Google lanzó una nueva herramienta de IA esta semana en California."),
    ("en", "The customer support team in London was amazingly helpful and fast!"),
    ("en", "This laptop gets extremely hot after only twenty minutes of use."),
    ("en", "The meeting with Microsoft was rescheduled for next Thursday."),
    ("en", "I'm feeling indifferent about the new design updates made by Apple."),
    ("en", "The delivery arrived two days late and the box was completely crushed."),
]

PROMPT = """Clasifica el sentimiento del siguiente texto y extrae sus entidades.

Texto ({lang}):
"{texto}"

Reglas:
- sentimiento: solo "positivo", "negativo" o "neutro".
- entidades: personas, organizaciones, lugares, productos, fechas, horas, cantidades.
- justificacion: una frase corta.
Responde SOLO con el JSON."""


def analizar_sentimiento(lang: str, texto: str) -> dict:
    prompt = PROMPT.format(lang="español" if lang == "es" else "inglés", texto=texto)
    respuesta = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=JSON_CONFIG,
    )
    return json.loads(respuesta.text)


def describir_imagen(ruta: str) -> str:
    imagen = Image.open(ruta)
    prompt = (
        "Describe detalladamente esta imagen en español: "
        "1) escena y elementos principales, 2) personas u objetos con su ubicación, "
        "3) colores, iluminación y ambiente, 4) texto visible si lo hay, "
        "5) contexto o interpretación general."
    )
    respuesta = client.models.generate_content(
        model=MODEL_NAME,
        contents=[imagen, prompt],
        config=types.GenerateContentConfig(temperature=0.4),
    )
    return respuesta.text


def main() -> None:
    print("=== PARTE 1: SENTIMIENTO Y ENTIDADES ===\n")
    resultados = []
    for lang, texto in TEXTOS:
        etiqueta = "ES" if lang == "es" else "EN"
        try:
            datos = analizar_sentimiento(lang, texto)
        except Exception as e:
            print(f"[!] Error en la API: {e}")
            time.sleep(5)
            continue

        entidades = ", ".join(
            f"{e.get('texto')} ({e.get('tipo')})" for e in datos.get("entidades", [])
        ) or "ninguna"

        resultados.append({"lang": lang, "texto": texto, **datos})
        print(f"[{etiqueta}] {texto}")
        print(f"    Sentimiento : {datos.get('sentimiento')}")
        print(f"    Entidades   : {entidades}")
        if datos.get("justificacion"):
            print(f"    Justificación: {datos['justificacion']}")
        print()
        time.sleep(1)

    with open("resultados_sentimiento.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    positivos = sum(1 for r in resultados if r.get("sentimiento") == "positivo")
    negativos = sum(1 for r in resultados if r.get("sentimiento") == "negativo")
    neutros = sum(1 for r in resultados if r.get("sentimiento") == "neutro")
    print(f"Resumen -> positivos: {positivos} | negativos: {negativos} | neutros: {neutros}")
    print("Guardado en resultados_sentimiento.json\n")

    print("=== PARTE 2: DESCRIPCIÓN MULTIMODAL (IMAGEN) ===\n")
    ruta_imagen = "foto.jpg"
    if os.path.exists(ruta_imagen):
        try:
            print(describir_imagen(ruta_imagen))
        except Exception as e:
            print(f"[!] Error procesando la imagen: {e}")
    else:
        print(f"Aviso: no se encontró '{ruta_imagen}' en esta carpeta.")


if __name__ == "__main__":
    main()
