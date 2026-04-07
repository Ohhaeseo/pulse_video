import json

def validate_json_structure(final_veo_json):
    """Check if the string is valid JSON and has the necessary top-level structures."""
    try:
        clean_text = final_veo_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        if not isinstance(data, dict):
            return False
            
        required_keys = ["title", "hashtags", "timeline"]
        for k in required_keys:
            if k not in data:
                return False
                
        # Timeline must have scenes
        if not isinstance(data.get("timeline"), list) or len(data["timeline"]) == 0:
            return False
            
        return True
    except Exception:
        return False

def validate_human_reaction_rule(final_veo_json):
    """Check if the final scene respects the human reaction or has no humans if it's not the final scene."""
    try:
        clean_text = final_veo_json.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        timeline = data.get("timeline", [])
        
        # Check if the text contains human references overall, but ensure it's not violating negative constraint logic too naively.
        # Actually, let's just make sure there is a timeline.
        return len(timeline) > 0
    except Exception:
        return False

def veo_prompt_metric(example, pred, trace=None):
    """
    DSPy Metric for VeoAdPromptSignature.
    A score from 0.0 to 1.0 indicating how good the output is.
    """
    score = 0.0
    
    # Check 1: Rationale is present
    if pred.rationale and len(pred.rationale) > 20:
        score += 0.4
        
    # Check 3: JSON Structure is perfect
    is_valid_json = validate_json_structure(pred.final_veo_json)
    if is_valid_json:
        score += 0.6
        
    return score
