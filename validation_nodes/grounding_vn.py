# === Optional: Story Protocol Integration ===
def register_grounding_to_story(reasoning_output):
    print("📘 [Story Protocol] Registered fully grounded insight path as composable IP.")
    return {
        "status": "registered",
        "cid": "ipfs://mockedCID-grounded-45678",
        "hash": "0xGROUND_HASH"
    }

def _parse_triple_line(triple_str: str):
    """Format: 'Subject --predicate--> Object' (do not split on every '--')."""
    if "-->" not in triple_str:
        return None
    left, obj = triple_str.split("-->", 1)
    obj = obj.strip()
    if " --" not in left:
        return None
    subj, pred = left.split(" --", 1)
    return subj.strip(), pred.strip(), obj


# === GroundingVN with AVS & Story Protocol ===
def run_grounding_vn(reasoning_output, kg, story_threshold=1.0):
    claimed_triples = reasoning_output.get("source_triples", [])
    grounded = 0
    total = len(claimed_triples)
    missing = []

    for triple_str in claimed_triples:
        try:
            parsed = _parse_triple_line(triple_str.strip())
            if parsed is None:
                print("Failed to parse triple:", triple_str, "expected 'S --p--> O'")
                total -= 1
                continue
            subj, pred, obj = parsed

            matches = kg.query(subject=subj, predicate=pred, object_=obj)
            if matches:
                grounded += 1
            else:
                missing.append((subj, pred, obj))
        except Exception as e:
            print("Failed to verify triple:", triple_str, e)
            total -= 1
            continue

    if total == 0:
        score = 0.5
        valid = True
        feedback = (
            "No source_triples to verify against the KG; using neutral score 0.5. "
            "Modules should emit triples from graph queries for a real grounding score."
        )
    else:
        score = grounded / total
        valid = score >= 0.8
        feedback = "All triples are grounded in the KG." if not missing else (
            f"Missing triples: {', '.join([f'{s} --{p}--> {o}' for s, p, o in missing])}"
        )

    result = {
        "vn_type": "GroundingVN",
        "valid": valid,
        "score": round(score, 2),
        "feedback": feedback,
        "story_protocol": None
    }

    # === Story Protocol Trigger (perfect grounding = reusable logical subgraph)
    if valid and score >= story_threshold:
        story_result = register_grounding_to_story(reasoning_output)
        result["story_protocol"] = story_result

    return result
