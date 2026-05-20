import asyncio
import json
import time
from app.classifier import classify_complaint
from app.geo_extractor import resolve_location

# Synthetic Gold Dataset for FYS Techathon Evaluation
# Mix of Roman Urdu, Urdu, and English
EVAL_DATASET = [
    {
        "text": "bhai 4 din se G-9 mein pani nahi aa raha, bache beemar ho rahe hain jaldi kuch karo",
        "expected_dept": "water_supply",
        "expected_urgency": "high"
    },
    {
        "text": "Transformer blast ho gaya F-11 markaz ke pas, aag lag gayi hai!",
        "expected_dept": "electricity", # or fire_emergency, both acceptable
        "expected_urgency": "critical"
    },
    {
        "text": "Gutter ubal raha hai I-8/4 main sarak par, bohat badboo hai.",
        "expected_dept": "sanitation_sewerage",
        "expected_urgency": "medium"
    },
    {
        "text": "My PTCL broadband is down since yesterday in DHA Phase 2.",
        "expected_dept": "telecom",
        "expected_urgency": "low"
    },
    {
        "text": "hospital me dawai nahi mil rahi, emergency me patient hai!",
        "expected_dept": "health",
        "expected_urgency": "critical"
    },
    {
        "text": "Police station G-11 waly FIR nahi kaat rahay mobile chori ki",
        "expected_dept": "police_security",
        "expected_urgency": "high"
    },
    {
        "text": "Sui gas ka pressure boht kam hai subha se PWD society me",
        "expected_dept": "gas_supply",
        "expected_urgency": "medium"
    },
    {
        "text": "School ki chhat toot gai hai sector F-7 me, bachon ke liye khatarnak hai",
        "expected_dept": "education",
        "expected_urgency": "high"
    },
    {
        "text": "Sarak mein itna bara gaddha hai G-10 markaz, accident ho sakta hai",
        "expected_dept": "roads_infrastructure",
        "expected_urgency": "medium"
    },
    {
        "text": "Kachra uthane koi nahi aya 3 hafte se Blue Area me",
        "expected_dept": "sanitation_sewerage",
        "expected_urgency": "medium"
    }
]

async def run_evaluation():
    print("=" * 60)
    print("🚀 NaqsKAR Evaluation Suite")
    print("Evaluating Multi-Label Classifier & Geo-Extractor")
    print("=" * 60)
    
    correct_dept = 0
    correct_urgency = 0
    geo_extractions = 0
    total = len(EVAL_DATASET)
    
    start_time = time.time()
    
    for i, item in enumerate(EVAL_DATASET):
        print(f"\nProcessing [{i+1}/{total}]: {item['text'][:40]}...")
        
        # Run classification
        res = await classify_complaint(item["text"])
        
        dept_match = res["department"] == item["expected_dept"]
        # Allow fire_emergency or electricity for transformer blast
        if item["expected_dept"] == "electricity" and res["department"] == "fire_emergency":
            dept_match = True
            
        urg_match = res["urgency"] == item["expected_urgency"]
        
        if dept_match:
            correct_dept += 1
        if urg_match:
            correct_urgency += 1
            
        # Run Geo
        loc = resolve_location(res.get("extracted_location"))
        if loc:
            geo_extractions += 1
            
        print(f"  Predicted Dept: {res['department']} {'✅' if dept_match else '❌'} (Expected: {item['expected_dept']})")
        print(f"  Predicted Urg:  {res['urgency']} {'✅' if urg_match else '❌'} (Expected: {item['expected_urgency']})")
        print(f"  Geo Extracted:  {loc.resolved_name if loc else 'None'}")
        
    duration = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Samples:         {total}")
    print(f"Department Accuracy:   {(correct_dept/total)*100:.1f}%")
    print(f"Urgency Accuracy:      {(correct_urgency/total)*100:.1f}%")
    print(f"Geo-Extraction Yield:  {(geo_extractions/total)*100:.1f}%")
    print(f"Average latency:       {(duration/total)*1000:.0f} ms / request")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_evaluation())
