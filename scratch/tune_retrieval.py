import math
import numpy as np

def calculate_energy(E0, distance, dist_penalty, degree, deg_penalty):
    """The new exponential decay formula."""
    return E0 * math.exp(-distance * dist_penalty) * math.exp(-degree * deg_penalty)

def run_sweep():
    print("Starting Hyperparameter Sweep...")
    print("-" * 60)

    # Define the search space
    distance_penalties = np.arange(0.1, 1.0, 0.05)
    degree_penalties = np.arange(0.05, 0.5, 0.02)
    cutoffs = np.arange(0.1, 0.6, 0.05)

    valid_configs = []

    for dp in distance_penalties:
        for deg_p in degree_penalties:
            for cutoff in cutoffs:
                
                # Scenario A: Vanguard Project (Dist 1, Degree ~3) -> MUST SURVIVE
                hop1_normal = calculate_energy(1.0, 1, dp, 3, deg_p)
                
                # Scenario B: Xenon (Dist 2, Degree ~2) -> MUST SURVIVE
                hop2_target = calculate_energy(1.0, 2, dp, 2, deg_p)
                
                # Scenario C: Titanium / Python Hub (Dist 1, Degree ~25) -> MUST DIE
                hop1_hub = calculate_energy(1.0, 1, dp, 25, deg_p)
                
                # The Logic Gate: Find the sweet spot
                if hop1_normal >= cutoff and hop2_target >= cutoff and hop1_hub < cutoff:
                    # Calculate a "Margin of Safety" (how far the target is from death)
                    safety_margin = hop2_target - cutoff
                    
                    valid_configs.append({
                        "dist_p": round(dp, 2),
                        "deg_p": round(deg_p, 2),
                        "cutoff": round(cutoff, 2),
                        "hop2_energy": round(hop2_target, 3),
                        "hub_energy": round(hop1_hub, 3),
                        "safety": round(safety_margin, 3)
                    })

    # Sort by the highest safety margin (most robust configurations)
    valid_configs.sort(key=lambda x: x["safety"], reverse=True)

    print(f"Found {len(valid_configs)} viable configurations.")
    if valid_configs:
        print("\nTop 3 Sweet Spots:")
        for idx, config in enumerate(valid_configs[:3]):
            print(f"Rank {idx+1}: Cutoff={config['cutoff']} | Dist Penalty={config['dist_p']} | Deg Penalty={config['deg_p']}")
            print(f"      -> Target Energy: {config['hop2_energy']} (Hub Energy: {config['hub_energy']})")
    
    return valid_configs

if __name__ == "__main__":
    run_sweep()
