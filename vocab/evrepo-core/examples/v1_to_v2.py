"""Mechanical evrepo-core v1 -> v2 (draft) re-mapping of a LinkedDataEnhancement.

Lossless and non-inventive: nothing is added that is not in the source.
Usage: python v1_to_v2.py in.jsonld out.jsonld
"""
import json, sys

def as_list(x): return x if isinstance(x, list) else [x]

def convert(lde):
    inv = lde["hasInvestigation"]
    nodes = {}
    def index(x):
        if isinstance(x, dict):
            if "@id" in x and len(x) > 1: nodes[x["@id"]] = x
            for v in x.values(): index(v)
        elif isinstance(x, list):
            for v in x: index(v)
    index(inv)
    cid = lambda c: c if isinstance(c, str) else c["@id"]
    arms, emitted, findings = {}, set(), []
    def ref_once(node_or_id, fallback_id=None):
        """Full node on first use, bare @id reference afterwards."""
        if isinstance(node_or_id, str): i, node = node_or_id, nodes[node_or_id]
        else:
            node = node_or_id; i = node.setdefault("@id", fallback_id)
        if i in emitted: return i
        emitted.add(i); return node
    def arm_for(c):
        i = cid(c)
        if i not in arms:
            cond = nodes[i]
            arm = {"@id": i.replace("_:", "_:arm_"), "@type": "Arm"}
            if cond["@type"] == "Intervention": arm["hasIntervention"] = cond
            else: arm.update({k: v for k, v in cond.items() if k not in ("@id", "@type")})
            arm["hasObservation"] = []
            arms[i] = arm
        return arms[i]
    for n, f in enumerate(as_list(inv["hasFinding"]), 1):
        arm_for(f["evaluates"]); arm_for(f["comparedTo"])
        by_cond = {}
        for r in f["hasArmData"]:
            o = {"@id": r["@id"], "@type": "Observation",
                 "hasOutcome": ref_once(f["hasOutcome"], f"_:outcome{n}"),
                 "hasContext": ref_once(f["hasContext"])}
            o.update({k: v for k, v in r.items() if k not in ("@id", "@type", "forCondition")})
            arm_for(r["forCondition"])["hasObservation"].append(o)
            by_cond[cid(r["forCondition"])] = r["@id"]
        nf = {"@type": "Finding",
              "compares": [by_cond[cid(f["evaluates"])], by_cond[cid(f["comparedTo"])]],
              "comparedTo": by_cond[cid(f["comparedTo"])]}
        nf.update({k: v for k, v in f.items() if k not in
                   ("@type", "evaluates", "comparedTo", "hasArmData", "hasContext", "hasOutcome")})
        findings.append(nf)
    new_inv = {k: v for k, v in inv.items() if k != "hasFinding"}
    new_inv["hasArm"] = list(arms.values()); new_inv["hasFinding"] = findings
    return {**{k: v for k, v in lde.items() if k != "hasInvestigation"}, "hasInvestigation": new_inv}

if __name__ == "__main__":
    out = convert(json.load(open(sys.argv[1])))
    json.dump(out, open(sys.argv[2], "w"), indent=2, ensure_ascii=False)
