"""
Test receivers endpoints
"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:5000"

print("\n" + "="*60)
print("TESTING RECEIVERS ENDPOINTS")
print("="*60 + "\n")

# Test 1: Get all receivers
print("1. Testing GET /receivers")
print("-" * 60)
response = requests.get(f"{BASE_URL}/receivers")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Success: {data.get('success')}")
print(f"Total receivers: {data.get('total')}")
if data.get('receivers'):
    print("\nReceivers:")
    for receiver in data['receivers']:
        print(f"  • {receiver['display_name']} ({receiver['username']}) - {receiver['email']}")
print()

# Test 2: Get specific receiver
print("2. Testing GET /receivers/rishabh")
print("-" * 60)
response = requests.get(f"{BASE_URL}/receivers/rishabh")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Success: {data.get('success')}")
if data.get('receiver'):
    receiver = data['receiver']
    print(f"Username: {receiver['username']}")
    print(f"Display Name: {receiver['display_name']}")
    print(f"Email: {receiver['email']}")
print()

# Test 3: Get non-existent receiver
print("3. Testing GET /receivers/nonexistent")
print("-" * 60)
response = requests.get(f"{BASE_URL}/receivers/nonexistent")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Success: {data.get('success')}")
print(f"Error: {data.get('error')}")
print()

# Test 4: Get receiver (dan)
print("4. Testing GET /receivers/dan")
print("-" * 60)
response = requests.get(f"{BASE_URL}/receivers/dan")
print(f"Status: {response.status_code}")
data = response.json()
print(f"Success: {data.get('success')}")
if data.get('receiver'):
    receiver = data['receiver']
    print(f"Display Name: {receiver['display_name']}")
    print(f"Email: {receiver['email']}")
print()

print("="*60)
print("✅ RECEIVERS TESTS COMPLETE")
print("="*60)
