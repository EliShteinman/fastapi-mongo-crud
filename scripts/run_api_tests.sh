#!/bin/bash

# ================================================================================
#  End-to-End API Test Script for the FastAPI Soldiers DB Service
# ================================================================================

# --- Step 0: Configuration and Validation ---

# Validate input parameter (API Base URL)
if [ -z "$1" ]; then
    echo "ERROR: API Base URL must be provided as the first argument."
    echo "Usage: ./run_api_tests.sh <your-application-url>"
    exit 1
fi

API_URL="$1"
BASE_PATH="/soldiersdb"
FULL_URL="${API_URL}${BASE_PATH}"

# Soldier data for testing
SOLDIER_1_ID=301 # Using a different range to avoid conflicts with manual tests
SOLDIER_2_ID=302
NON_EXISTENT_ID=999

JSON_SOLDIER_1="{\"ID\": $SOLDIER_1_ID, \"first_name\": \"Yitzhak\", \"last_name\": \"Rabin\", \"phone_number\": 5551922, \"rank\": \"Chief of Staff\"}"
JSON_SOLDIER_2="{\"ID\": $SOLDIER_2_ID, \"first_name\": \"Ariel\", \"last_name\": \"Sharon\", \"phone_number\": 5551928, \"rank\": \"Major General\"}"
JSON_UPDATE="{\"rank\": \"Prime Minister\", \"phone_number\": 5552001}"
JSON_INVALID="{\"ID\": 404, \"first_name\": \"Missing\", \"last_name\": \"Fields\"}" # Missing rank and phone_number

# --- Helper Functions ---
function print_header() {
  echo ""
  echo "================================================================="
  echo "   $1"
  echo "================================================================="
}

# --- Test Execution ---
echo "### Starting API Test Suite ###"
echo "API Endpoint: $FULL_URL"

# --- Phase 0: Cleanup ---
print_header "Phase 0: Cleanup Previous Test Data (if any)"
# We don't check the status code here, as the soldiers might not exist.
curl -s -o /dev/null -X DELETE "${FULL_URL}/${SOLDIER_1_ID}"
curl -s -o /dev/null -X DELETE "${FULL_URL}/${SOLDIER_2_ID}"
echo "Cleanup requests sent."

# --- Phase 1: Creation ---
print_header "Phase 1: Initial State and Creation"

echo "Test 1: Check initial state is empty"
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')
echo "  - Received Status: $STATUS_CODE. Expected: 200"
if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 0 ]; then
    echo "  - ✅ PASSED: Received 200 and body is an empty array."
else
    echo "  - ❌ FAILED: Status was $STATUS_CODE or body was not empty: $BODY"
    exit 1
fi

echo -e "\nTest 2: Create Soldier 1 (ID $SOLDIER_1_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FULL_URL}/" -H "Content-Type: application/json" -d "$JSON_SOLDIER_1")
echo "  - Received Status: $STATUS_CODE. Expected: 201"
if [ "$STATUS_CODE" = "201" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 3: Create Soldier 2 (ID $SOLDIER_2_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FULL_URL}/" -H "Content-Type: application/json" -d "$JSON_SOLDIER_2")
echo "  - Received Status: $STATUS_CODE. Expected: 201"
if [ "$STATUS_CODE" = "201" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

# --- Phase 2: Reading and Error Handling ---
print_header "Phase 2: Reading and Error Handling"

echo -e "\nTest 4: Read all soldiers"
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')
echo "  - Received Status: $STATUS_CODE. Expected: 200"
if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 2 ]; then
    echo "  - ✅ PASSED: Received 200 and found 2 soldiers."
else
    echo "  - ❌ FAILED: Status was $STATUS_CODE or incorrect number of soldiers found."
    exit 1
fi

echo -e "\nTest 5: Read a single, existing soldier (ID $SOLDIER_1_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${FULL_URL}/${SOLDIER_1_ID}")
echo "  - Received Status: $STATUS_CODE. Expected: 200"
if [ "$STATUS_CODE" = "200" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 6: Attempt to create a duplicate soldier (ID $SOLDIER_1_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FULL_URL}/" -H "Content-Type: application/json" -d "$JSON_SOLDIER_1")
echo "  - Received Status: $STATUS_CODE. Expected: 409"
if [ "$STATUS_CODE" = "409" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 7: Attempt to create an invalid soldier (Missing fields)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${FULL_URL}/" -H "Content-Type: application/json" -d "$JSON_INVALID")
echo "  - Received Status: $STATUS_CODE. Expected: 422"
if [ "$STATUS_CODE" = "422" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

# --- Phase 3: Update and Deletion ---
print_header "Phase 3: Update and Deletion"

echo -e "\nTest 8: Update an existing soldier (ID $SOLDIER_2_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT "${FULL_URL}/${SOLDIER_2_ID}" -H "Content-Type: application/json" -d "$JSON_UPDATE")
echo "  - Received Status: $STATUS_CODE. Expected: 200"
if [ "$STATUS_CODE" = "200" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 9: Try to fetch a non-existent soldier (ID $NON_EXISTENT_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${FULL_URL}/${NON_EXISTENT_ID}")
echo "  - Received Status: $STATUS_CODE. Expected: 404"
if [ "$STATUS_CODE" = "404" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 10: Delete a soldier (ID $SOLDIER_1_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${FULL_URL}/${SOLDIER_1_ID}")
echo "  - Received Status: $STATUS_CODE. Expected: 204"
if [ "$STATUS_CODE" = "204" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 11: Verify the soldier was actually deleted (ID $SOLDIER_1_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${FULL_URL}/${SOLDIER_1_ID}")
echo "  - Received Status: $STATUS_CODE. Expected: 404"
if [ "$STATUS_CODE" = "404" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

# --- Phase 4: Final Cleanup ---
print_header "Phase 4: Final Cleanup"

echo -e "\nTest 12: Clean up the remaining soldier (ID $SOLDIER_2_ID)"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE "${FULL_URL}/${SOLDIER_2_ID}")
echo "  - Received Status: $STATUS_CODE. Expected: 204"
if [ "$STATUS_CODE" = "204" ]; then echo "  - ✅ PASSED"; else echo "  - ❌ FAILED"; exit 1; fi

echo -e "\nTest 13: Ensure the database is empty again"
RESPONSE_BODY=$(curl -s -w "\n%{http_code}" "${FULL_URL}/")
STATUS_CODE=$(echo "$RESPONSE_BODY" | tail -n1)
BODY=$(echo "$RESPONSE_BODY" | sed '$d')
echo "  - Received Status: $STATUS_CODE. Expected: 200"
if [ "$STATUS_CODE" = "200" ] && [ "$(echo "$BODY" | jq 'length')" -eq 0 ]; then
    echo "  - ✅ PASSED: Final state is empty."
else
    echo "  - ❌ FAILED: Final state is not empty."
    exit 1
fi

print_header "🎉 All tests completed successfully! 🎉"