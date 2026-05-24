"""
NaqsKAR — Synthetic Training Data Generator (Groq Version)
Uses Groq Llama 3.3 70B (or Llama 3.1 8B) to generate labeled Roman Urdu complaints
for fine-tuning XLM-R classifier. Saves incrementally to prevent data loss.

Usage:
    python scripts/generate_synthetic_data.py
"""
import json
import os
import sys
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

# Configure Groq
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_KEY:
    logger.error("❌ GROQ_API_KEY not found in .env!")
    sys.exit(1)

client = Groq(api_key=GROQ_KEY)
MODEL = "llama-3.1-8b-instant"

# ── Department definitions ─────────────────────────
DEPARTMENTS = {
    "water_supply": {
        "description": "Water outage, contamination, tanker, pipeline, leakage",
        "urdu_keywords": "pani, paani, tanker, pipeline, leakage, supply, nalkha, water, boring, tube well, filtar, contamination",
        "cities": ["Islamabad", "Lahore", "Karachi", "Peshawar", "Rawalpindi", "Faisalabad", "Multan", "Quetta"],
    },
    "electricity": {
        "description": "Load shedding, transformer, meter, billing, wiring, power outage",
        "urdu_keywords": "bijli, bijlee, light, transformer, meter, load shedding, current, wire, fuse, UPS, bill, WAPDA, IESCO, KE",
        "cities": ["Lahore", "Karachi", "Islamabad", "Faisalabad", "Multan", "Rawalpindi", "Peshawar", "Hyderabad"],
    },
    "gas_supply": {
        "description": "Gas pressure, leak, meter, SNGPL, SSGC, pipeline",
        "urdu_keywords": "gas, pressure, leak, meter, SNGPL, SSGC, cylinder, sui gas, chulha, heater, geyser",
        "cities": ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Faisalabad", "Peshawar", "Multan", "Quetta"],
    },
    "roads_infrastructure": {
        "description": "Potholes, broken road, street lights, footpath, bridge",
        "urdu_keywords": "sarak, road, gaddha, pothole, street light, footpath, bridge, signal, traffic, flyover",
        "cities": ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Faisalabad", "Multan", "Quetta"],
    },
    "sanitation_sewerage": {
        "description": "Sewage, drainage, garbage, waste, gutter, nala",
        "urdu_keywords": "gandagi, sewage, kachra, garbage, nala, gutter, drain, safai, waste, dump, kachray ka dher",
        "cities": ["Karachi", "Lahore", "Rawalpindi", "Faisalabad", "Peshawar", "Hyderabad", "Multan", "Islamabad"],
    },
    "health": {
        "description": "Hospital, clinic, medicine, doctor, ambulance, dengue, disease",
        "urdu_keywords": "hospital, doctor, dawai, medicine, ambulance, beemar, dengue, bukhar, clinic, dispensary, sehat",
        "cities": ["Karachi", "Lahore", "Islamabad", "Peshawar", "Rawalpindi", "Multan", "Faisalabad", "Quetta"],
    },
    "education": {
        "description": "School, teacher, admission, fees, building condition",
        "urdu_keywords": "school, teacher, admission, fees, college, university, class, student, exam, building, madrasa",
        "cities": ["Lahore", "Karachi", "Islamabad", "Peshawar", "Rawalpindi", "Faisalabad", "Multan", "Quetta"],
    },
    "police_security": {
        "description": "Theft, robbery, harassment, missing person, domestic violence, crime",
        "urdu_keywords": "police, chori, theft, dakaiti, harass, missing, violence, FIR, thana, daroga, SHO, crime, qatl",
        "cities": ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Peshawar", "Faisalabad", "Multan", "Quetta"],
    },
    "fire_emergency": {
        "description": "Fire, blast, explosion, building collapse",
        "urdu_keywords": "aag, fire, blast, explosion, jalaa, collapse, rescue, 1122, dhamaka, building gir",
        "cities": ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Peshawar", "Faisalabad", "Multan", "Quetta"],
    },
    "public_transport": {
        "description": "Bus, metro, rickshaw, route, fare",
        "urdu_keywords": "bus, metro, rickshaw, route, fare, kiraya, orange train, green line, wagon, speedo",
        "cities": ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Multan", "Faisalabad"],
    },
    "telecom": {
        "description": "Internet, mobile, signal, tower, PTCL, broadband",
        "urdu_keywords": "internet, mobile, signal, tower, PTCL, broadband, wifi, network, jazz, zong, telenor, ufone",
        "cities": ["Lahore", "Karachi", "Islamabad", "Rawalpindi", "Peshawar", "Faisalabad", "Multan", "Quetta"],
    },
    "revenue_land": {
        "description": "Property, land, patwari, registry, encroachment",
        "urdu_keywords": "zameen, land, patwari, registry, encroachment, qabza, plot, property, mutation, fard",
        "cities": ["Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Peshawar", "Karachi", "Quetta"],
    },
    "environment": {
        "description": "Pollution, smog, noise, deforestation, dumping",
        "urdu_keywords": "pollution, smog, noise, shor, darakhton, dumping, factory, dhuaan, aloodgi, kachra",
        "cities": ["Lahore", "Karachi", "Islamabad", "Faisalabad", "Peshawar", "Rawalpindi", "Multan", "Quetta"],
    },
}

URGENCY_LEVELS = ["critical", "high", "medium", "low"]
SENTIMENTS = ["angry", "frustrated", "neutral", "polite"]

def save_data(data, filepath):
    """Save data incrementally to avoid loss on crash."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def generate_batch(department: str, dept_info: dict, batch_num: int, samples_per_batch: int = 15) -> list[dict]:
    """Generate a batch of synthetic complaints using Groq with retry."""

    prompt = f"""You are an expert data generator.
Generate exactly {samples_per_batch} realistic Pakistani citizen complaints for the "{department}" department.

DEPARTMENT: {department}
DESCRIPTION: {dept_info['description']}
KEYWORDS: {dept_info['urdu_keywords']}
CITIES: {', '.join(dept_info['cities'][:4])}

RULES (Follow strictly to avoid noise in dataset):
1. Write ONLY in ROMAN URDU (transliterated Urdu using English alphabet). Do NOT use Urdu script.
2. Ensure HIGH DIVERSITY in sentence structures, complaint types, and lengths (short 1-liners and 3-sentence detailed ones).
3. Mix some English words naturally like real citizens (e.g., "meter ka bill bohat zyada hai", "pipeline leak ho gayi").
4. Include spelling variations like pani/paani, nahi/nhi/nai, bohat/bohut/bahut.
5. Use specific locations from the cities listed (e.g., G-9 Markaz, DHA Phase 5, Saddar).
6. Vary urgency precisely: 'critical' (life/death/disaster), 'high' (serious disruption), 'medium' (annoyance), 'low' (query/minor).
7. Vary sentiment: 'angry' (using aggressive tone), 'frustrated' (helpless tone), 'neutral' (factual reporting), 'polite' (respectful request).
8. Batch {batch_num} — Make sure these are completely unique from common textbook examples.

Return a strict JSON array of {samples_per_batch} objects. Each object must have these exact keys:
"text", "department", "urgency", "sentiment"
Ensure the labels for urgency and sentiment exactly match the lists above. 
Output ONLY valid JSON, starting with [ and ending with ]. No markdown, no introductory text."""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Groq's json_object requires dict, so wrap array in a dict if needed, 
            # or try to parse if it gave us an array inside a wrapper.
            try:
                parsed = json.loads(result_text)
            except:
                # Fallback to direct text if JSON mode messed up
                start = result_text.find("[")
                end = result_text.rfind("]") + 1
                parsed = json.loads(result_text[start:end])

            if isinstance(parsed, dict):
                # Groq might return {"complaints": [...]}
                for k, v in parsed.items():
                    if isinstance(v, list):
                        return v
                return []
            elif isinstance(parsed, list):
                return parsed
            return []

        except Exception as e:
            logger.warning(f"Groq API/Parse error {department} batch {batch_num} attempt {attempt+1}: {e}")
            try:
                # Direct retry without json mode if it fails
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                    max_tokens=4000,
                )
                text = response.choices[0].message.content.strip()
                start = text.find("[")
                end = text.rfind("]") + 1
                if start != -1 and end > start:
                    items = json.loads(text[start:end])
                    if items:
                        logger.info(f"  Salvaged {len(items)} items from raw text")
                        return items
            except:
                pass
            time.sleep(2)

    return []


def main():
    output_path = Path(__file__).parent.parent / "data" / "synthetic_training_data.json"
    
    # Load existing data if resuming
    all_data = []
    if output_path.exists():
        try:
            with open(output_path, "r", encoding="utf-8") as f:
                all_data = json.load(f)
            logger.info(f"♻️ Resuming with {len(all_data)} existing samples")
        except:
            pass

    samples_per_dept = 100
    batch_size = 15 # Optimal for Groq max tokens
    batches_per_dept = samples_per_dept // batch_size

    total_depts = len(DEPARTMENTS)

    logger.info(f"🚀 Generating highly diverse synthetic data with Groq Llama 3.3 70B")
    
    for dept_idx, (dept, info) in enumerate(DEPARTMENTS.items(), 1):
        # Check how many we already have for this department
        existing_dept_samples = len([s for s in all_data if s.get("department") == dept])
        if existing_dept_samples >= samples_per_dept:
            logger.info(f"[{dept_idx}/{total_depts}] ✅ Skipping {dept} (already has {existing_dept_samples} samples)")
            continue
            
        logger.info(f"[{dept_idx}/{total_depts}] 📦 Generating: {dept} (Need {samples_per_dept - existing_dept_samples} more)")
        
        dept_samples = []
        for batch in range(1, batches_per_dept + 1):
            logger.info(f"  Batch {batch}/{batches_per_dept}...")
            samples = generate_batch(dept, info, batch, batch_size)

            for s in samples:
                if isinstance(s, dict) and "text" in s and len(s.get("text", "")) > 10:
                    s["department"] = dept
                    if s.get("urgency") not in URGENCY_LEVELS:
                        s["urgency"] = "medium"
                    if s.get("sentiment") not in SENTIMENTS:
                        s["sentiment"] = "neutral"
                    dept_samples.append(s)

            # Save incrementally after every batch
            all_data.extend(dept_samples)
            save_data(all_data, output_path)
            dept_samples = [] # Reset for next batch
            
            time.sleep(1) # Groq rate limit protection

        logger.info(f"  ✅ Saved data for {dept}")

    logger.info(f"\n{'='*60}")
    logger.info(f"✅ DONE! Generated {len(all_data)} total samples")

if __name__ == "__main__":
    main()
