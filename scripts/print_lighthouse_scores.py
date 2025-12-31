import json
import glob
import os

def load_thresholds():
    """Load minScore assertions from lighthouserc.json"""
    try:
        # Assuming script is in scripts/, config is in root
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'lighthouserc.json')
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assertions = config.get('ci', {}).get('assert', {}).get('assertions', {})
        thresholds = {}
        
        # Map category keys to simple names
        category_map = {
            'categories:performance': 'performance',
            'categories:accessibility': 'accessibility',
            'categories:best-practices': 'best-practices',
            'categories:seo': 'seo',
            'categories:pwa': 'pwa'
        }

        for key, limits in assertions.items():
            if key in category_map:
                # Handle ["warn", {"minScore": 0.9}] or ["error", {"minScore": 0.9}]
                if isinstance(limits, list) and len(limits) > 1 and isinstance(limits[1], dict):
                    min_score = limits[1].get('minScore')
                    if min_score:
                        thresholds[category_map[key]] = min_score
        
        return thresholds
    except Exception as e:
        print(f"⚠️  Could not load thresholds from lighthouserc.json: {e}")
        return {}

def main():
    # Find the most recent lhr-*.json file
    # We are usually running from frontend/ directory when invoked by full_salvo, 
    # but the script is in scripts/. We need to look in ../.lighthouseci relative to where we run?
    # full_salvo.sh runs `../venv/bin/python3 ../scripts/print_lighthouse_scores.py` from `frontend/`
    # So CWD is `frontend/`. .lighthouseci is in root, so `../.lighthouseci`
    
    # Try different paths to find the report
    possible_paths = [
        '.lighthouseci/lhr-*.json',       # If run from root
        '../.lighthouseci/lhr-*.json'     # If run from frontend/
    ]
    
    list_of_files = []
    for pattern in possible_paths:
        list_of_files.extend(glob.glob(pattern))

    if not list_of_files:
        print("No Lighthouse reports found.")
        return

    latest_file = max(list_of_files, key=os.path.getmtime)
    
    thresholds = load_thresholds()
    # Default threshold if not found
    DEFAULT_THRESHOLD = 0.9

    try:
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        print(f"\n📊 Lighthouse Scores ({os.path.basename(latest_file)}):")
        print("---------------------------------------------")
        categories = data.get('categories', {})
        
        for key, category in categories.items():
            score = category.get('score')
            category_id = category.get('id')
            
            if score is not None:
                # Determine threshold
                required = thresholds.get(category_id, DEFAULT_THRESHOLD)
                
                score_val = score  # 0 to 1
                score_pct = int(score * 100)
                required_pct = int(required * 100)
                
                # Strict Red/Green based on threshold
                if score_val >= required:
                    emoji = "🟢"
                    status = "PASS"
                else:
                    emoji = "🔴"
                    status = f"FAIL (<{required_pct})"
                
                print(f"{emoji} {category.get('title', key):<20}: {score_pct:<3} (Req: {required_pct})")
                
        print("---------------------------------------------\n")

    except Exception as e:
        # print error but don't fail the build just for the print script
        print(f"Error reading Lighthouse report: {e}")

if __name__ == "__main__":
    main()
