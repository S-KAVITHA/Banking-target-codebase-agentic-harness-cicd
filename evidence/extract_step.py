import json, sys
t = json.load(open(sys.argv[1])); role = sys.argv[2]
ev = t["events"]
if role == "routing":
    print("path:", " ".join(e["role"] for e in ev if e.get("type") == "subagent"))
    print("escalated_to_human:", t.get("escalated_to_human"))
    sys.exit()
sub = next(e for e in ev if e.get("type") == "subagent" and e.get("role") == role)
doc = sub.get("output_document") or {}
print("role:", role)
print("tools:", " ".join(e["tool"] for e in ev if e.get("type") == "tool_call" and e.get("role") == role))
print("output_keys:", ",".join(sorted(doc)))
print("verdicts:", " ".join(f'{i["section"]}={i["verdict"]}' for i in sub.get("review_items", [])))
summary = str(doc.get("summary", "")).lower()
print("decision:", " ".join(w for w in ("approve", "reject", "pass", "fail") if w in summary))
print("summary_words:", len(summary.split()), file=sys.stderr)