import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

print("\n===== DIAGNÓSTICO =====")
print("API KEY encontrada:", api_key is not None)

if api_key:
    print("Inicio clave:", api_key[:15])
    print("Longitud:", len(api_key))

client = genai.Client(api_key=api_key)

print("\nProbando LIST MODELS...")

try:
    modelos = list(client.models.list())
    print("OK")
    print("Total modelos:", len(modelos))
except Exception as e:
    print("ERROR LIST:", e)

print("\nProbando GENERATE_CONTENT...")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Responde únicamente OK"
    )
    print("OK")
    print(response.text)
except Exception as e:
    print("ERROR GENERATE:", e)