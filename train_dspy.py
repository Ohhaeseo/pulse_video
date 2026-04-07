import json
import os
import dspy
from dotenv import load_dotenv
from dspy.teleprompt import BootstrapFewShot
from services.llm_service import VeoAdPromptModule
from services.dspy_metrics import veo_prompt_metric

load_dotenv()

def load_trainset():
    reference_examples = []
    try:
        with open("reference_blueprints.json", "r", encoding="utf-8") as rf:
            rb_data = json.load(rf)
            for rb in rb_data.get("reference_videos", []):
                ex = dspy.Example(
                    target_persona=rb.get("target_persona", ""),
                    concept=rb.get("concept", ""),
                    target_vibe=rb.get("target_vibe", ""),
                    sns_marketing_hook=rb.get("sns_marketing_hook", ""),
                    camera_angle=rb.get("camera_angle", ""),
                    lens_optical_effects=rb.get("lens_optical_effects", ""),
                    visual_keywords=rb.get("visual_keywords", ""),
                    food_focus_rule=rb.get("food_focus_rule", ""),
                    negative_constraints=rb.get("negative_constraints", ""),
                    image_visual_context=rb.get("image_visual_context", ""),
                    reference_style_blueprint=rb.get("reference_style_blueprint", ""),
                    rationale=rb.get("rationale", ""),
                    final_veo_json=rb.get("final_veo_json", "")
                ).with_inputs(
                    "target_persona", "concept", "target_vibe", "sns_marketing_hook",
                    "camera_angle", "lens_optical_effects", "visual_keywords",
                    "food_focus_rule", "negative_constraints", "image_visual_context",
                    "reference_style_blueprint"
                )
                reference_examples.append(ex)
    except Exception as e:
        print(f"Failed to load reference_blueprints.json: {e}")
    return reference_examples

def train():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set.")
        return

    # Use a stronger teacher model if available, or just use the same. 
    # Since we are using gemini-2.5-flash everywhere, we will use it for both.
    lm = dspy.LM('gemini/gemini-2.5-flash', api_key=api_key)
    dspy.settings.configure(lm=lm)
    
    trainset = load_trainset()
    if not trainset:
        print("No training data found.")
        return

    print(f"Setting up BootstrapFewShot optimizer on {len(trainset)} examples...")

    # Bootstrapping optimization
    optimizer = BootstrapFewShot(
        metric=veo_prompt_metric,
        max_bootstrapped_demos=4,  # Generate up to 4 AI reasoned examples
        max_labeled_demos=min(8, len(trainset)), # Direct examples from our blueprint
        max_rounds=1
    )
    
    # 2. Compile model
    student_module = VeoAdPromptModule()
    
    print("Compiling program. This will take some time as it generates reasoning traces...")
    compiled_program = optimizer.compile(student=student_module, trainset=trainset)
    
    # 3. Save weights
    compiled_program.save("veo_optimizer.json", save_program=False)
    print("Optimization complete! Saved optimized settings to veo_optimizer.json.")

if __name__ == "__main__":
    train()
