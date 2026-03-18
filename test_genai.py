import os
import inspect
from google import genai
from google.genai import types

def test():
    client = genai.Client()
    print("generate_videos arguments:")
    print(inspect.signature(client.models.generate_videos))
    
    print("\nVideoPrompt attributes:")
    if hasattr(types, "VideoPrompt"):
        print(dir(types.VideoPrompt))
    else:
        print("No VideoPrompt in types")
        
    print("\nGenerateVideosConfig attributes:")
    if hasattr(types, "GenerateVideosConfig"):
        print(dir(types.GenerateVideosConfig))
    
if __name__ == "__main__":
    test()
