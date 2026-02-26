#!/bin/bash


# chmod +x test-app.sh
# ./test_api.sh
# Warna untuk output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BASE_URL="http://localhost:5000"
TOKEN=""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}ABSENSI API TEST SCRIPT${NC}"
echo -e "${BLUE}========================================${NC}"

# Function untuk test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local desc=$3
    local data=$4
    local auth=$5
    
    echo -e "\n${YELLOW}Testing: ${desc}${NC}"
    echo -e "${BLUE}${method} ${endpoint}${NC}"
    
    cmd="curl -s -X ${method} ${BASE_URL}${endpoint}"
    
    if [ "$auth" = "true" ] && [ -n "$TOKEN" ]; then
        cmd="$cmd -H \"Authorization: Bearer $TOKEN\""
    fi
    
    if [ -n "$data" ]; then
        cmd="$cmd -H \"Content-Type: application/json\" -d '$data'"
    fi
    
    echo -e "${YELLOW}Response:${NC}"
    eval $cmd | json_pp
}

echo -e "\n${GREEN}1. LOGIN${NC}"
echo "--------------------"
LOGIN_RESPONSE=$(curl -s -X POST ${BASE_URL}/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo -e "${GREEN}✓ Login berhasil, token didapat${NC}"
else
    echo -e "${RED}✗ Login gagal${NC}"
    exit 1
fi

# echo -e "\n${GREEN}2. TEST STUDENTS ENDPOINTS${NC}"
# echo "--------------------"
# test_endpoint "GET" "/api/students" "Get all students" "" "true"
# test_endpoint "GET" "/api/students/by-kelas/1" "Get students by kelas" "" "true"
# test_endpoint "GET" "/api/students/statistics/by-kelas" "Get student statistics" "" "true"

# echo -e "\n${GREEN}3. TEST TEACHERS ENDPOINTS${NC}"
# echo "--------------------"
# test_endpoint "GET" "/api/guru" "Get all teachers" "" "true"
# test_endpoint "GET" "/api/guru/with-kelas" "Get teachers with classes" "" "true"
# test_endpoint "GET" "/api/guru/statistics" "Get teacher statistics" "" "true"

# echo -e "\n${GREEN}4. TEST CLASSES ENDPOINTS${NC}"
# echo "--------------------"
# test_endpoint "GET" "/api/kelas" "Get all classes" "" "true"
# test_endpoint "GET" "/api/kelas/statistics" "Get class statistics" "" "true"

echo -e "\n${GREEN}5. TEST ATTENDANCE ENDPOINTS${NC}"
echo "--------------------"
test_endpoint "GET" "/api/attendance/today" "Get today attendance" "" "true"
test_endpoint "GET" "/api/attendance/statistics" "Get attendance statistics" "" "true"

echo -e "\n${GREEN}6. TEST QR ENDPOINTS${NC}"
echo "--------------------"
test_endpoint "GET" "/api/qr/validate-nisn" "Validate NISN format" '{"nisn":"0075787971"}' "true"

# echo -e "\n${GREEN}7. TEST SYSTEM ENDPOINTS${NC}"
# echo "--------------------"
# test_endpoint "GET" "/api/system/health" "Health check" "" "false"
# test_endpoint "GET" "/api/system/test" "Test endpoint" "" "false"

# echo -e "\n${GREEN}8. TEST DEBUG ENDPOINTS${NC}"
# echo "--------------------"
# test_endpoint "GET" "/api/debug/table-structure" "Table structure" "" "true"
# test_endpoint "GET" "/api/debug/performance" "Performance check" "" "true"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}TEST SELESAI${NC}"
echo -e "${BLUE}========================================${NC}"
