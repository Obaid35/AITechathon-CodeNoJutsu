import httpx
import asyncio
import time

API_URL = "http://127.0.0.1:8000/api/submit"

SEED_COMPLAINTS = [
    {"text": "Mera pani pichle 3 din se nahi aa raha DHA phase 6 me. Tameerati kaam ki wajah se line toot gai hai.", "source": "web"},
    {"text": "WAPDA walon ne light band ki hui hai subah 8 baje se Johar Town me. Garmi bohot hai aur bachay ro rahay hain.", "source": "whatsapp"},
    {"text": "There is a massive pothole on Main Boulevard Gulberg near the signal. It caused two major accidents just today. Fix this immediately!", "source": "web"},
    {"text": "Kachra uthane wali gaadi 2 hafte se nahi aayi Sector F-11 Islamabad me. Bohat badboo hai aur beemari phailne ka khadsha hai.", "source": "ivr"},
    {"text": "Hospital bed is not available at Jinnah Hospital emergency ward. My father is in critical condition.", "source": "whatsapp"},
    {"text": "Meter reader ne galat reading likh di hai. Humara bill 50 hazar aya hai jabke pichle mahine 5 hazar tha.", "source": "web"},
    {"text": "Police is asking for bribe at the checkpost near Liberty Market Lahore. They stopped my car without reason.", "source": "whatsapp"},
    {"text": "Gas pressure is extremely low in Bahria Town Phase 8 Rawalpindi since winter started. Khana pakana namumkin ho gaya hai.", "source": "ivr"},
    {"text": "Trees are being cut down illegally in Margalla Hills near trail 3. The timber mafia is active.", "source": "web"},
    {"text": "Johar town block G me light nahi aa rahi pichle 12 ghantay se. Please solve this issue ASAP.", "source": "web"}, # This should cluster with the 2nd one
    {"text": "Peshawar BRT bus station 4 pe escalator pichle ek mahine se kharab hai.", "source": "web"},
    {"text": "The government school in Orangi Town Karachi has no drinking water for children.", "source": "whatsapp"}
]

async def submit_complaint(client, complaint):
    print(f"Submitting: '{complaint['text'][:50]}...'")
    try:
        response = await client.post(API_URL, json=complaint, timeout=30.0)
        if response.status_code == 200:
            data = response.json()
            print(f"Success | Dept: {data['classification']['department']} | Urgency: {data['classification']['urgency']}")
        else:
            print(f"Failed: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

async def main():
    print("Starting Seed Generation...")
    print(f"Total complaints to process: {len(SEED_COMPLAINTS)}")
    print("This will take a few moments as the AI processes each one (extraction, local classification, pgvector deduplication)...\n")
    
    start_time = time.time()
    
    # We will submit them sequentially to avoid rate-limiting the Groq API or overwhelming the local HuggingFace model
    async with httpx.AsyncClient() as client:
        for complaint in SEED_COMPLAINTS:
            await submit_complaint(client, complaint)
            # Short sleep to be safe with rate limits
            await asyncio.sleep(1)
            
    print(f"\nSeeding complete in {time.time() - start_time:.2f} seconds!")
    print("Check the NaqsKAR dashboard Live Feed to see the results.")

if __name__ == "__main__":
    asyncio.run(main())
