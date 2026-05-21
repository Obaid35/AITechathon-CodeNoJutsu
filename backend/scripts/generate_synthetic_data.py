"""
NaqsKAR — Synthetic Training Data Generator
Uses Groq (Llama 3.1) to generate labeled Roman Urdu complaints
for fine-tuning XLM-R classifier.

Usage:
    python scripts/generate_synthetic_data.py

Output:
    data/synthetic_training_data.json
"""
import json
import os
import sys
import time
import logging
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from groq import Groq
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Department definitions with context ────────────────
DEPARTMENTS = {
    "water_supply": {
        "description": "Water outage, contamination, tanker, pipeline, leakage",
        "urdu_keywords": "pani, paani, tanker, pipeline, leakage, supply, nalkha, nala, water, boring, tube well, filtar, contamination",
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
        "urdu_keywords": "sarak, road, gaddha, pothole, street light, footpath, bridge, signal, traffic, flyover, gutter",
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


def generate_batch(department: str, dept_info: dict, batch_num: int, samples_per_batch: int = 25) -> list[dict]:
    """Generate a batch of synthetic complaints for one department."""
    
    prompt = f"""Generate exactly {samples_per_batch} realistic Pakistani citizen complaints for the "{department}" department.

DEPARTMENT: {department}
DESCRIPTION: {dept_info['description']}
RELEVANT KEYWORDS: {dept_info['urdu_keywords']}
CITIES TO USE: {', '.join(dept_info['cities'])}

RULES:
1. Write complaints in ROMAN URDU (transliterated Urdu using English alphabet)
2. Mix in some English words naturally (code-mixing is common in Pakistan)
3. Include realistic spelling variations (e.g., "pani"/"paani", "nahi"/"nhi"/"ni")
4. Include specific locations (sectors, mohallas, areas) from the cities
5. Vary urgency: some critical (life-threatening), some high, some medium, some low
6. Vary sentiment: some angry, some frustrated, some neutral, some polite
7. Make complaints 1-3 sentences long
8. Include realistic Pakistani phone/reference numbers occasionally
9. Batch {batch_num} — make these DIFFERENT from typical examples

OUTPUT FORMAT (strict JSON array):
[
  {{
    "text": "<Roman Urdu complaint>",
    "department": "{department}",
    "urgency": "<critical|high|medium|low>",
    "sentiment": "<angry|frustrated|neutral|polite>"
  }},
  ...
]

IMPORTANT: Return ONLY valid JSON array, no extra text.
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a data generator. Output ONLY valid JSON arrays. No markdown, no explanation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,  # High temperature for variety
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result_text = response.choices[0].message.content
        parsed = json.loads(result_text)
        
        # Handle both {"complaints": [...]} and direct [...] format
        if isinstance(parsed, dict):
            data = parsed.get("complaints", parsed.get("data", parsed.get("samples", [])))
            if isinstance(data, list):
                return data
            # If no known key, get the first list value
            for v in parsed.values():
                if isinstance(v, list):
                    return v
            return []
        elif isinstance(parsed, list):
            return parsed
        return []
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error for {department} batch {batch_num}: {e}")
        return []
    except Exception as e:
        logger.error(f"Groq error for {department} batch {batch_num}: {e}")
        return []


def main():
    output_path = Path(__file__).parent.parent / "data" / "synthetic_training_data.json"
    
    all_data = []
    samples_per_dept = 100  # 100 per department × 13 = 1300 total
    batch_size = 25         # Groq handles 25 per call well
    batches_per_dept = samples_per_dept // batch_size
    
    total_depts = len(DEPARTMENTS)
    
    logger.info(f"🚀 Generating {samples_per_dept} samples × {total_depts} departments = {samples_per_dept * total_depts} total")
    logger.info(f"   {batches_per_dept} batches per department, {batch_size} samples per batch")
    logger.info(f"   Total API calls: {batches_per_dept * total_depts}")
    logger.info("")
    
    for dept_idx, (dept, info) in enumerate(DEPARTMENTS.items(), 1):
        dept_samples = []
        logger.info(f"[{dept_idx}/{total_depts}] 📦 Generating for: {dept}")
        
        for batch in range(1, batches_per_dept + 1):
            logger.info(f"  Batch {batch}/{batches_per_dept}...")
            samples = generate_batch(dept, info, batch, batch_size)
            
            # Validate each sample
            for s in samples:
                if isinstance(s, dict) and "text" in s and len(s["text"]) > 10:
                    # Ensure correct department label
                    s["department"] = dept
                    # Validate urgency
                    if s.get("urgency") not in URGENCY_LEVELS:
                        s["urgency"] = "medium"
                    # Validate sentiment
                    if s.get("sentiment") not in SENTIMENTS:
                        s["sentiment"] = "neutral"
                    dept_samples.append(s)
            
            # Rate limiting — Groq free tier: 30 RPM
            time.sleep(2.5)
        
        logger.info(f"  ✅ Got {len(dept_samples)} valid samples for {dept}")
        all_data.extend(dept_samples)
    
    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ DONE! Generated {len(all_data)} total samples")
    logger.info(f"📁 Saved to: {output_path}")
    
    # Print distribution
    dept_counts = {}
    urgency_counts = {}
    sentiment_counts = {}
    for s in all_data:
        dept_counts[s["department"]] = dept_counts.get(s["department"], 0) + 1
        urgency_counts[s.get("urgency", "?")] = urgency_counts.get(s.get("urgency", "?"), 0) + 1
        sentiment_counts[s.get("sentiment", "?")] = sentiment_counts.get(s.get("sentiment", "?"), 0) + 1
    
    logger.info(f"\n📊 Department distribution:")
    for d, c in sorted(dept_counts.items()):
        logger.info(f"   {d}: {c}")
    
    logger.info(f"\n📊 Urgency distribution:")
    for u, c in sorted(urgency_counts.items()):
        logger.info(f"   {u}: {c}")
    
    logger.info(f"\n📊 Sentiment distribution:")
    for s, c in sorted(sentiment_counts.items()):
        logger.info(f"   {s}: {c}")


if __name__ == "__main__":
    main()
