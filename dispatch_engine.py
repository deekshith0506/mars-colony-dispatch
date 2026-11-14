import csv
import io

CREW_SPECIALTY = {
    "STRUCTURAL": "E",
    "MEDICAL": "M",
    "LIFE_SUPPORT": "L"
}
ALL_CREWS = ["E", "M", "L"]


def calculate_points(severity: int, arrival: int, start: int) -> float:
    wait = start - arrival
    window = 60 - 4 * severity
    if wait >= window:
        return 0.0
    return severity * max(0.0, 1.0 - (wait / window))


def solve_dispatch(csv_text: str) -> tuple[dict, float, list[str]]:
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    unscheduled = []
    for row in reader:
        unscheduled.append({
            "id": int(row["id"].strip()),
            "arrival": int(row["arrival"].strip()),
            "category": row["category"].strip(),
            "severity": int(row["severity"].strip()),
            "duration": int(row["duration"].strip())
        })

    # Sort initially by arrival time, then highest severity
    unscheduled.sort(key=lambda x: (x["arrival"], -x["severity"], x["id"]))

    crew_free_time = {"E": 0, "M": 0, "L": 0}
    schedule = []
    total_score = 0.0

    while unscheduled:
        earliest_arrival = min(inc["arrival"] for inc in unscheduled)
        earliest_crew_free = min(crew_free_time.values())
        current_time = max(earliest_arrival, earliest_crew_free)

        # Find all crews available at or before current_time
        available_crews = [c for c in ALL_CREWS if crew_free_time[c] <= current_time]
        # Find all incidents that have arrived by current_time
        arrived_incidents = [inc for inc in unscheduled if inc["arrival"] <= current_time]

        best_choice = None
        best_priority_score = -1e9

        for crew in available_crews:
            for inc in arrived_incidents:
                is_match = (CREW_SPECIALTY[inc["category"]] == crew)
                actual_duration = inc["duration"] if is_match else (2 * inc["duration"])
                start_time = max(current_time, inc["arrival"])
                end_time = start_time + actual_duration

                # Immediate points earned if scheduled now
                pts_now = calculate_points(inc["severity"], inc["arrival"], start_time)

                # Urgency factor: critical incidents lose points much faster per minute
                window = 60 - 4 * inc["severity"]
                decay_per_min = inc["severity"] / window

                # Compare against waiting for the matching specialist crew
                specialist = CREW_SPECIALTY[inc["category"]]
                specialist_start = max(crew_free_time[specialist], inc["arrival"])
                pts_if_wait_for_specialist = calculate_points(
                    inc["severity"], inc["arrival"], specialist_start
                )

                # Penalty if a non-specialist takes a long job and blocks their own specialty
                cross_crew_penalty = 0.0
                if not is_match:
                    # Check if specialist will be free soon enough to get almost the same score
                    gain_over_specialist = pts_now - pts_if_wait_for_specialist
                    if gain_over_specialist <= 0.25 * inc["severity"]:
                        cross_crew_penalty = 1000.0  # Prefer keeping crew free for own specialty
                    else:
                        # Penalize extra busy duration proportionally
                        cross_crew_penalty = 0.15 * inc["duration"] * decay_per_min

                # Combined heuristic score: reward high points saved & fast decay rate
                priority = (pts_now * 2.0) + (decay_per_min * 15.0) - cross_crew_penalty

                if priority > best_priority_score:
                    best_priority_score = priority
                    best_choice = (crew, inc, start_time, end_time, pts_now)

        chosen_crew, chosen_inc, start_t, end_t, earned_pts = best_choice

        crew_free_time[chosen_crew] = end_t
        total_score += earned_pts
        unscheduled.remove(chosen_inc)

        schedule.append({
            "id": int(chosen_inc["id"]),
            "crew": chosen_crew,
            "start": int(start_t),
            "end": int(end_t)
        })

    # Rule 2.6: The list MUST be sorted by start time (ties in any order)
    schedule.sort(key=lambda x: (x["start"], x["id"]))

    submission_json = {"schedule": schedule}
    errors = validate_submission(csv_text, submission_json)
    return submission_json, round(total_score, 4), errors


def validate_submission(csv_text: str, submission_json: dict) -> list[str]:
    """Checks all 7 Judge Validity Rules from AlgoX Rules Section 2."""
    errors = []
    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    incidents = {
        int(r["id"]): {
            "arrival": int(r["arrival"]),
            "category": r["category"].strip(),
            "duration": int(r["duration"])
        }
        for r in reader
    }

    schedule = submission_json.get("schedule", [])

    # Rule 1: Every incident appears exactly once
    seen_ids = [item["id"] for item in schedule]
    if len(seen_ids) != len(incidents) or set(seen_ids) != set(incidents.keys()):
        errors.append("Rule 1 Failed: Missing, duplicate, or unknown incident IDs.")

    crew_last_end = {"E": 0, "M": 0, "L": 0}
    prev_start = -1

    for item in schedule:
        inc_id = item.get("id")
        crew = item.get("crew")
        start = item.get("start")
        end = item.get("end")

        # Rule 7: Whole numbers
        if not (isinstance(inc_id, int) and isinstance(start, int) and isinstance(end, int)):
            errors.append(f"Rule 7 Failed on ID {inc_id}: id, start, and end must be integers.")

        # Rule 2: Valid crew
        if crew not in ALL_CREWS:
            errors.append(f"Rule 2 Failed on ID {inc_id}: Invalid crew '{crew}'.")
            continue

        # Rule 6: Sorted by start time
        if start < prev_start:
            errors.append(f"Rule 6 Failed on ID {inc_id}: Schedule not sorted by start time.")
        prev_start = start

        if inc_id in incidents:
            inc = incidents[inc_id]
            # Rule 3: No start before arrival
            if start < inc["arrival"]:
                errors.append(f"Rule 3 Failed on ID {inc_id}: Started at {start} before arrival {inc['arrival']}.")

            # Rule 4: Exact duration check (1x match, 2x non-match)
            expected_dur = inc["duration"] if CREW_SPECIALTY[inc["category"]] == crew else 2 * inc["duration"]
            if end != start + expected_dur:
                errors.append(f"Rule 4 Failed on ID {inc_id}: Expected end {start + expected_dur}, got {end}.")

        # Rule 5: No overlapping tasks per crew
        if start < crew_last_end[crew]:
            errors.append(f"Rule 5 Failed on ID {inc_id}: Crew {crew} overlap at minute {start}.")
        crew_last_end[crew] = end

    return errors
