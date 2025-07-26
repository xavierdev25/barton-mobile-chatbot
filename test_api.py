#!/usr/bin/env python3
"""
Script para probar la API del chatbot con saludos
"""

import requests
import json

def test_api_saludos():
    """Prueba la API con diferentes saludos"""
    print("=== PRUEBA DE LA API CON SALUDOS ===\n")
    
    # URL de la API
    url = "http://localhost:5000/chatbot"
    
    # Lista de saludos para probar
    saludos_prueba = [
        "Hola",
        "Buenos días",
        "Buenas tardes",
        "Buenas noches",
        "Qué tal",
        "Cómo estás",
        "Saludos"
    ]
    
    print("Probando saludos en la API:")
    print("-" * 50)
    
    for saludo in saludos_prueba:
        try:
            # Preparar la petición
            data = {"pregunta": saludo}
            headers = {"Content-Type": "application/json"}
            
            # Hacer la petición POST
            response = requests.post(url, json=data, headers=headers, timeout=5)
            
            if response.status_code == 200:
                respuesta = response.json()
                print(f"✓ '{saludo}' → {respuesta.get('respuesta', 'Sin respuesta')}")
            else:
                print(f"✗ '{saludo}' → Error HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"✗ '{saludo}' → Error: No se puede conectar al servidor. ¿Está ejecutándose la API?")
            break
        except Exception as e:
            print(f"✗ '{saludo}' → Error: {e}")
    
    print("\n" + "=" * 50)
    print("INSTRUCCIONES PARA PROBAR")
    print("=" * 50)
    print("Para probar la API completa:")
    print("1. Ejecuta: python api.py")
    print("2. En otra terminal, ejecuta: python test_api.py")
    print("3. O usa curl:")
    print("   curl -X POST http://localhost:5000/chatbot \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"pregunta\": \"Hola\"}'")

if __name__ == "__main__":
    test_api_saludos() 