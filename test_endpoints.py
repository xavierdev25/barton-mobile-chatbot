#!/usr/bin/env python3
"""
Script de prueba para verificar que los endpoints del chatbot funcionen correctamente
"""

import requests
import json

# URL base del servidor
BASE_URL = "https://barton-mobile-chatbot.onrender.com"

def test_health():
    """Prueba el endpoint de health check"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error en health check: {e}")
        return False

def test_nueva_sesion():
    """Prueba el endpoint de nueva sesión"""
    try:
        response = requests.post(f"{BASE_URL}/nueva-sesion")
        print(f"✅ Nueva sesión: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Session ID: {data.get('session_id')}")
            return data.get('session_id')
        return None
    except Exception as e:
        print(f"❌ Error en nueva sesión: {e}")
        return None

def test_chatbot(session_id):
    """Prueba el endpoint del chatbot"""
    try:
        payload = {
            "mensaje": "Hola, quiero información sobre matrícula",
            "session_id": session_id
        }
        response = requests.post(f"{BASE_URL}/chatbot-inteligente", json=payload)
        print(f"✅ Chatbot: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Mensaje: {data.get('mensaje', '')[:50]}...")
            return True
        else:
            print(f"   Error: {response.text}")
        return False
    except Exception as e:
        print(f"❌ Error en chatbot: {e}")
        return False

def main():
    """Ejecuta todas las pruebas"""
    print("🧪 Iniciando pruebas de endpoints...")
    print(f"🌐 URL base: {BASE_URL}")
    print("-" * 50)
    
    # Prueba 1: Health check
    health_ok = test_health()
    print()
    
    # Prueba 2: Nueva sesión
    session_id = test_nueva_sesion()
    print()
    
    # Prueba 3: Chatbot
    if session_id:
        chatbot_ok = test_chatbot(session_id)
    else:
        chatbot_ok = False
    print()
    
    # Resumen
    print("-" * 50)
    print("📊 Resumen de pruebas:")
    print(f"   Health check: {'✅ OK' if health_ok else '❌ FALLÓ'}")
    print(f"   Nueva sesión: {'✅ OK' if session_id else '❌ FALLÓ'}")
    print(f"   Chatbot: {'✅ OK' if chatbot_ok else '❌ FALLÓ'}")
    
    if health_ok and session_id and chatbot_ok:
        print("\n🎉 ¡Todas las pruebas pasaron! El servidor está funcionando correctamente.")
    else:
        print("\n⚠️  Algunas pruebas fallaron. Revisa la configuración del servidor.")

if __name__ == "__main__":
    main() 