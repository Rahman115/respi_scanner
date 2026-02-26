#!/usr/bin/env python3
"""
Test script for Absensi API
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:5000"
TOKEN = None

def print_response(response):
    """Print response nicely"""
    print(f"Status: {response.status_code}")
    try:
        pprint(response.json())
    except:
        print(response.text)
    print("-" * 50)

def login():
    """Login and get token"""
    global TOKEN
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("\n🔐 LOGIN")
    print("=" * 50)
    response = requests.post(url, json=data)
    print_response(response)
    
    if response.status_code == 200:
        TOKEN = response.json().get('token')
        return True
    return False

def test_students():
    """Test students endpoints"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n👥 STUDENTS ENDPOINTS")
    print("=" * 50)
    
    # Get all students
    print("\n1. GET /api/students")
    response = requests.get(f"{BASE_URL}/api/students", headers=headers)
    print_response(response)

    # Check students by NIS
    print("\n2. GET /api/students/626")
    response = requests.get(f"{BASE_URL}/api/students/626", headers=headers)
    print_response(response)
    
    # Get students by kelas
    print("\n2. GET /api/students/by-kelas/1")
    response = requests.get(f"{BASE_URL}/api/students/by-kelas/1", headers=headers)
    print_response(response)
    
    # Get statistics
    print("\n3. GET /api/students/statistics/by-kelas")
    response = requests.get(f"{BASE_URL}/api/students/statistics/by-kelas", headers=headers)
    print_response(response)

def test_teachers():
    """Test teachers endpoints"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n👨‍🏫 TEACHERS ENDPOINTS")
    print("=" * 50)
    
    # Get all teachers
    print("\n1. GET /api/guru")
    response = requests.get(f"{BASE_URL}/api/guru", headers=headers)
    print_response(response)
    
    # Get teachers with classes
    print("\n2. GET /api/guru/with-kelas")
    response = requests.get(f"{BASE_URL}/api/guru/with-kelas", headers=headers)
    print_response(response)

def test_classes():
    """Test classes endpoints"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n🏫 CLASSES ENDPOINTS")
    print("=" * 50)
    
    # Get all classes
    print("\n1. GET /api/kelas")
    response = requests.get(f"{BASE_URL}/api/kelas", headers=headers)
    print_response(response)
    
    # Get class statistics
    print("\n2. GET /api/kelas/statistics")
    response = requests.get(f"{BASE_URL}/api/kelas/statistics", headers=headers)
    print_response(response)
    
    # Get students in class
    print("\n3. GET /api/kelas/1/siswa")
    response = requests.get(f"{BASE_URL}/api/kelas/1/siswa", headers=headers)
    print_response(response)

def test_attendance():
    """Test attendance endpoints"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n📅 ATTENDANCE ENDPOINTS")
    print("=" * 50)
    
    # Get today's attendance
    print("\n1. GET /api/attendance/today")
    response = requests.get(f"{BASE_URL}/api/attendance/today", headers=headers)
    print_response(response)
    
    # Get attendance statistics
    print("\n2. GET /api/attendance/statistics")
    response = requests.get(f"{BASE_URL}/api/attendance/statistics", headers=headers)
    print_response(response)
    
    # Get summary by class
    print("\n3. GET /api/attendance/summary/by-class")
    response = requests.get(f"{BASE_URL}/api/attendance/summary/by-class", headers=headers)
    print_response(response)

def test_qr():
    """Test QR endpoints"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n📱 QR CODE ENDPOINTS")
    print("=" * 50)
    
    # Validate NISN
    print("\n1. POST /api/qr/validate-nisn")
    data = {"nisn": "0075787971"}
    response = requests.post(f"{BASE_URL}/api/qr/validate-nisn", headers=headers, json=data)
    print_response(response)

def test_scanner():
    """Test scanner endpoints"""
    print("\n📷 SCANNER ENDPOINTS")
    print("=" * 50)
    
    # Scan NISN (public)
    print("\n1. POST /api/scan-nisn")
    data = {
        "nisn": "0075787971",
        "location": "Test Scanner"
    }
    response = requests.post(f"{BASE_URL}/api/scan-nisn", json=data)
    print_response(response)
    
    # Check scan status (public)
    print("\n2. GET /api/scan-status/626")
    response = requests.get(f"{BASE_URL}/api/scan-status/626")
    print_response(response)

def test_system():
    """Test system endpoints"""
    print("\n⚙️ SYSTEM ENDPOINTS")
    print("=" * 50)
    
    # Health check
    print("\n1. GET /api/system/health")
    response = requests.get(f"{BASE_URL}/api/system/health")
    print_response(response)
    
    # Test endpoint
    print("\n2. GET /api/system/test")
    response = requests.get(f"{BASE_URL}/api/system/test")
    print_response(response)

def test_debug():
    """Test debug endpoints"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n🔧 DEBUG ENDPOINTS")
    print("=" * 50)
    
    # Table structure
    print("\n1. GET /api/debug/table-structure")
    response = requests.get(f"{BASE_URL}/api/debug/table-structure", headers=headers)
    print_response(response)
    
    # Performance check
    print("\n2. GET /api/debug/performance")
    response = requests.get(f"{BASE_URL}/api/debug/performance", headers=headers)
    print_response(response)

def main():
    """Main test function"""
    print("=" * 60)
    print("📋 ABSENSI API TEST SUITE")
    print("=" * 60)
    
    # Login first
    if not login():
        print("❌ Login failed, cannot proceed")
        return
    
    # Run all tests
    test_students() # ok
    #test_teachers() # ok
    #test_classes() # ok
    #test_attendance() # OK
    #test_qr() # OK
   # test_scanner() # OK
    #test_system() # OK
    #test_debug()
    
    print("\n✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
