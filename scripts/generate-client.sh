#! /usr/bin/env bash

set -e
set -x

cd backend
python -c "import src.app.entrypoints.fastapi_app; import json; print(json.dumps(src.app.entrypoints.fastapi_app.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json frontend/
cd frontend
npm run generate-client
npx biome format --write ./src/client
