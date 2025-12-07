#!/bin/bash

# Test script for Phase 2 user workspace endpoints
# Run this after starting the backend with: python app.py

BASE_URL="http://localhost:5000"

echo "================================"
echo "PHASE 2 ENDPOINT TESTING"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Get all users
echo -e "${YELLOW}Test 1: GET /users${NC}"
echo "curl -X GET $BASE_URL/users"
curl -X GET "$BASE_URL/users" | jq '.'
echo ""
echo ""

# Test 2: Get specific user (linda)
echo -e "${YELLOW}Test 2: GET /users/linda${NC}"
echo "curl -X GET $BASE_URL/users/linda"
curl -X GET "$BASE_URL/users/linda" | jq '.'
echo ""
echo ""

# Test 3: Get invalid user (should return 404)
echo -e "${YELLOW}Test 3: GET /users/invalid (should fail)${NC}"
echo "curl -X GET $BASE_URL/users/invalid"
curl -X GET "$BASE_URL/users/invalid" | jq '.'
echo ""
echo ""

# Test 4: Search with user_name
echo -e "${YELLOW}Test 4: POST /search-and-rank with user_name=linda${NC}"
echo "curl -X POST $BASE_URL/search-and-rank with user_name"
curl -X POST "$BASE_URL/search-and-rank" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find Python developers in San Francisco",
    "connected_to": "all",
    "user_name": "linda"
  }' | jq '{success, id, total, user_name: .user_name}'
echo ""
echo ""

# Test 5: Get user's search history
echo -e "${YELLOW}Test 5: GET /users/linda/searches${NC}"
echo "curl -X GET $BASE_URL/users/linda/searches"
curl -X GET "$BASE_URL/users/linda/searches" | jq '.'
echo ""
echo ""

# Test 6: Add bookmark
echo -e "${YELLOW}Test 6: POST /users/linda/bookmarks${NC}"
echo "curl -X POST $BASE_URL/users/linda/bookmarks"
curl -X POST "$BASE_URL/users/linda/bookmarks" \
  -H "Content-Type: application/json" \
  -d '{
    "linkedin_url": "https://www.linkedin.com/in/test-candidate/",
    "candidate_name": "Test Candidate",
    "candidate_headline": "Software Engineer at Test Company",
    "notes": "Great candidate for our team!"
  }' | jq '.'
echo ""
echo ""

# Test 7: Check if bookmarked
echo -e "${YELLOW}Test 7: GET /users/linda/bookmarks/check/...${NC}"
ENCODED_URL=$(echo "https://www.linkedin.com/in/test-candidate/" | jq -sRr @uri)
echo "curl -X GET $BASE_URL/users/linda/bookmarks/check/$ENCODED_URL"
curl -X GET "$BASE_URL/users/linda/bookmarks/check/$ENCODED_URL" | jq '.'
echo ""
echo ""

# Test 8: Get all bookmarks
echo -e "${YELLOW}Test 8: GET /users/linda/bookmarks${NC}"
echo "curl -X GET $BASE_URL/users/linda/bookmarks"
curl -X GET "$BASE_URL/users/linda/bookmarks" | jq '.'
echo ""
echo ""

# Test 9: Remove bookmark
echo -e "${YELLOW}Test 9: DELETE /users/linda/bookmarks/...${NC}"
echo "curl -X DELETE $BASE_URL/users/linda/bookmarks/$ENCODED_URL"
curl -X DELETE "$BASE_URL/users/linda/bookmarks/$ENCODED_URL" | jq '.'
echo ""
echo ""

# Test 10: Verify bookmark was removed
echo -e "${YELLOW}Test 10: Verify bookmark removed${NC}"
echo "curl -X GET $BASE_URL/users/linda/bookmarks/check/$ENCODED_URL"
curl -X GET "$BASE_URL/users/linda/bookmarks/check/$ENCODED_URL" | jq '.'
echo ""
echo ""

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}ALL TESTS COMPLETED${NC}"
echo -e "${GREEN}================================${NC}"
