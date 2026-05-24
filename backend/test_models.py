import asyncio
import json
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from app.classifier_v2 import classify_complaint

async def test():
    result = await classify_complaint("tanker mafia ne pani band kar diya hai, 3 din se pani nahi aa rha Lahore mein")
    print(json.dumps(result, indent=2, ensure_ascii=False))

asyncio.run(test())
