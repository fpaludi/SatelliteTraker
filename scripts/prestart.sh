#!/bin/bash
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}Creating Database tables...${NC}"
cd /app/app/
python create_tables.py
