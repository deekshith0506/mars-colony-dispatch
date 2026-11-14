import csv
import io
import heapq

def process_csv_to_json(csv_text: str) -> dict:
    reader = csv.DictReader(io.StringIO(csv_text))
    
    # Load and sort incoming events chronologically
    incoming = []
    for row in reader:
        incoming.append({
            "incident_id": row["incident_id"].strip(),
            "arrival": int(row["timestamp_mins"]),
            "type": row["type"].strip(),
            "severity": int(row["severity"]),
            "duration": int(row["duration_mins"])
        })
    incoming.sort(key=lambda x: (x["arrival"], x["severity"]))

    # Track the 3 crews: (available_at_minute, crew_name)
    crews = [(0, "Crew Alpha"), (0, "Crew Beta"), (0, "Crew Gamma")]
    heapq.heapify(crews)

    waiting_queue = []  # Priority queue: (severity, arrival, index, incident_dict)
    schedule = []
    idx = 0
    n = len(incoming)

    while idx < n or waiting_queue:
        # Advance time to the next arrival if no incidents are waiting
        if not waiting_queue and idx < n:
            next_arrival = incoming[idx]["arrival"]
            while idx < n and incoming[idx]["arrival"] <= next_arrival:
                inc = incoming[idx]
                heapq.heappush(waiting_queue, (inc["severity"], inc["arrival"], idx, inc))
                idx += 1

        # Pick the crew that finishes earliest
        free_time, crew_name = heapq.heappop(crews)

        # Collect any new emergencies that arrived while that crew was busy
        while idx < n and incoming[idx]["arrival"] <= free_time:
            inc = incoming[idx]
            heapq.heappush(waiting_queue, (inc["severity"], inc["arrival"], idx, inc))
            idx += 1

        # Dispatch the highest-priority waiting incident (1 = Critical)
        _, _, _, current_inc = heapq.heappop(waiting_queue)

        start_time = max(current_inc["arrival"], free_time)
        end_time = start_time + current_inc["duration"]
        wait_time = start_time - current_inc["arrival"]

        # Update when this crew becomes available again
        heapq.heappush(crews, (end_time, crew_name))

        schedule.append({
            "incident_id": current_inc["incident_id"],
            "type": current_inc["type"],
            "severity": current_inc["severity"],
            "assigned_crew": crew_name,
            "arrival_time_mins": current_inc["arrival"],
            "start_time_mins": start_time,
            "end_time_mins": end_time,
            "wait_time_mins": wait_time
        })

    return {
        "colony": "Ares Prime",
        "active_crews": 3,
        "total_incidents_resolved": len(schedule),
        "dispatch_schedule": schedule
    }
