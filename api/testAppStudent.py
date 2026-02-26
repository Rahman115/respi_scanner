#!/usr/bin/env python3
"""
Test script for Students API endpoints
Using NIS=626 and NISN=0096279244
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:5000"
TOKEN = None

# Test data
TEST_NIS = "626"
TEST_NISN = "0096279244"
TEST_KELAS_ID = 1  # Adjust as needed

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

def test_get_all_students():
    """Test GET /api/students - Get all students"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n📋 GET ALL STUDENTS")
    print("=" * 50)
    
    # Test without filter
    print("1. Without filter:")
    response = requests.get(f"{BASE_URL}/api/students", headers=headers)
    print_response(response)
    
    # Test with kelas_id filter
    print(f"2. With kelas_id={TEST_KELAS_ID} filter:")
    response = requests.get(f"{BASE_URL}/api/students?kelas_id={TEST_KELAS_ID}", headers=headers)
    print_response(response)

def test_get_student_detail():
    """Test GET /api/students/<nis> - Get student detail"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print(f"\n🔍 GET STUDENT DETAIL (NIS: {TEST_NIS})")
    print("=" * 50)
    
    # Test valid NIS
    print("1. Valid NIS:")
    response = requests.get(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers)
    print_response(response)
    
    # Test invalid NIS
    print("2. Invalid NIS:")
    response = requests.get(f"{BASE_URL}/api/students/999999", headers=headers)
    print_response(response)

def test_add_student():
    """Test POST /api/students/add - Add new student"""
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    
    print("\n➕ ADD NEW STUDENT")
    print("=" * 50)
    
    # Generate unique NIS to avoid conflict
    import random
    test_nis = f"999{random.randint(100, 999)}"
    test_nisn = f"88{random.randint(10000000, 99999999)}"
    
    # Test valid data
    print("1. Valid data:")
    data = {
        "nis": test_nis,
        "nisn": test_nisn,
        "nama": "Test Student",
        "kelas_id": TEST_KELAS_ID,
        "gender": "L"
    }
    response = requests.post(f"{BASE_URL}/api/students/add", headers=headers, json=data)
    print_response(response)
    
    # Test duplicate NIS
    print("2. Duplicate NIS:")
    data = {
        "nis": TEST_NIS,  # Using existing NIS
        "nisn": "1234567890",
        "nama": "Duplicate Test",
        "kelas_id": TEST_KELAS_ID,
        "gender": "P"
    }
    response = requests.post(f"{BASE_URL}/api/students/add", headers=headers, json=data)
    print_response(response)
    
    # Test invalid gender
    print("3. Invalid gender:")
    data = {
        "nis": f"998{random.randint(100, 999)}",
        "nisn": "1234567890",
        "nama": "Invalid Gender",
        "kelas_id": TEST_KELAS_ID,
        "gender": "X"
    }
    response = requests.post(f"{BASE_URL}/api/students/add", headers=headers, json=data)
    print_response(response)
    
    # Test invalid NISN format
    print("4. Invalid NISN format:")
    data = {
        "nis": f"997{random.randint(100, 999)}",
        "nisn": "12345",  # Too short
        "nama": "Invalid NISN",
        "kelas_id": TEST_KELAS_ID,
        "gender": "L"
    }
    response = requests.post(f"{BASE_URL}/api/students/add", headers=headers, json=data)
    print_response(response)
    
    # Test missing required field
    print("5. Missing required field:")
    data = {
        "nis": f"996{random.randint(100, 999)}",
        "nisn": "1234567890",
        # "nama" is missing
        "kelas_id": TEST_KELAS_ID,
        "gender": "L"
    }
    response = requests.post(f"{BASE_URL}/api/students/add", headers=headers, json=data)
    print_response(response)

def test_update_student():
    """Test PUT /api/students/<nis> - Update student"""
    headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    
    print(f"\n✏️ UPDATE STUDENT (NIS: {TEST_NIS})")
    print("=" * 50)
    
    # Test update nama only
    print("1. Update nama only:")
    data = {
        "nama": "Updated Name Test"
    }
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)
    
    # Test update multiple fields
    print("2. Update multiple fields:")
    data = {
        "nama": "Student Updated",
        "gender": "P",
        "nisn": "0096279244"  # Back to original
    }
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)
    
    # Test update kelas
    print("3. Update kelas:")
    data = {
        "kelas_id": 2  # Assuming kelas_id 2 exists
    }
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)
    
    # Test invalid gender
    print("4. Invalid gender:")
    data = {
        "gender": "X"
    }
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)
    
    # Test invalid kelas_id
    print("5. Invalid kelas_id:")
    data = {
        "kelas_id": 99999
    }
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)
    
    # Test invalid NISN format
    print("6. Invalid NISN format:")
    data = {
        "nisn": "123"
    }
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)
    
    # Test empty data
    print("7. Empty data:")
    data = {}
    response = requests.put(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers, json=data)
    print_response(response)

def test_get_students_by_kelas():
    """Test GET /api/students/by-kelas/<kelas_id> - Get students by class"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print(f"\n🏫 GET STUDENTS BY KELAS (Kelas ID: {TEST_KELAS_ID})")
    print("=" * 50)
    
    # Test valid kelas_id
    print("1. Valid kelas_id:")
    response = requests.get(f"{BASE_URL}/api/students/by-kelas/{TEST_KELAS_ID}", headers=headers)
    print_response(response)
    
    # Test invalid kelas_id
    print("2. Invalid kelas_id:")
    response = requests.get(f"{BASE_URL}/api/students/by-kelas/99999", headers=headers)
    print_response(response)

def test_check_nisn_validity():
    """Test GET /api/students/check-nisn - Check NISN validity"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n✅ CHECK NISN VALIDITY")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/students/check-nisn", headers=headers)
    print_response(response)

def test_get_statistics_by_kelas():
    """Test GET /api/students/statistics/by-kelas - Get statistics by class"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n📊 GET STATISTICS BY KELAS")
    print("=" * 50)
    
    response = requests.get(f"{BASE_URL}/api/students/statistics/by-kelas", headers=headers)
    print_response(response)

def test_delete_student():
    """Test DELETE /api/students/<nis> - Delete student"""
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    print("\n🗑️ DELETE STUDENT")
    print("=" * 50)
    
    # First, create a temporary student to delete
    print("1. Creating temporary student...")
    temp_nis = f"888{random.randint(100, 999)}"
    temp_nisn = f"77{random.randint(10000000, 99999999)}"
    
    create_headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
    create_data = {
        "nis": temp_nis,
        "nisn": temp_nisn,
        "nama": "Temporary Student",
        "kelas_id": TEST_KELAS_ID,
        "gender": "L"
    }
    create_response = requests.post(f"{BASE_URL}/api/students/add", headers=create_headers, json=create_data)
    print_response(create_response)
    
    # Test delete temporary student
    print(f"2. Deleting temporary student with NIS: {temp_nis}")
    response = requests.delete(f"{BASE_URL}/api/students/{temp_nis}", headers=headers)
    print_response(response)
    
    # Test delete non-existent student
    print("3. Deleting non-existent student:")
    response = requests.delete(f"{BASE_URL}/api/students/999999", headers=headers)
    print_response(response)
    
    # Test delete student with attendance records
    print(f"4. Attempting to delete student with attendance records (NIS: {TEST_NIS})")
    response = requests.delete(f"{BASE_URL}/api/students/{TEST_NIS}", headers=headers)
    print_response(response)

def test_all_students_endpoints():
    """Run all students endpoint tests"""
    print("=" * 60)
    print("📋 STUDENTS API TEST SUITE")
    print(f"Using NIS: {TEST_NIS}, NISN: {TEST_NISN}")
    print("=" * 60)
    
    # Login first
    if not login():
        print("❌ Login failed, cannot proceed")
        return
    
    # Run all tests in sequence
    test_get_all_students()
    test_get_student_detail()
    test_get_students_by_kelas()
    test_check_nisn_validity()
    test_get_statistics_by_kelas()
    test_add_student()
    test_update_student()
    test_delete_student()
    
    print("\n✅ All students endpoint tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    import random
    test_all_students_endpoints()
