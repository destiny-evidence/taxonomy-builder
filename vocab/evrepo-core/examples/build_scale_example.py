"""Builds scale-extension-v2.jsonld: a hand mapping of Ozor et al. (2026),
Sustainability 18, 8996 (doi:10.3390/su18178996, CC BY) onto evrepo-core v2,
using core terms only. `_gap` keys record where the paper had something to say
that the core model could not hold, or could only hold by forcing it.
"""
import json

NS = "https://vocab.evidence-repository.org/"
ref = lambda i: {"@id": i}
SCHEME = NS

def obs(i, name, outcome, ctx, loc, **kw):
    return {"@id": i, "@type": "Observation", "name": name, "hasOutcome": ref(outcome),
            "hasContext": ref(ctx), **kw, "sourceLocation": loc}

def est(pe, lo=None, hi=None, metric="meanDifference", loc=None, gap=None, derived=None):
    e = {"@type": "EffectEstimate", "pointEstimate": pe}
    if lo is not None: e.update(confidenceLevel=0.95, confidenceIntervalLower=lo, confidenceIntervalUpper=hi)
    if metric: e["effectSizeMetric"] = ref(SCHEME + metric)
    e["estimateSource"] = ref(NS + "extractedFromPaper")
    if derived: e["derivedFrom"] = [ref(d) for d in derived]
    if loc: e["sourceLocation"] = loc
    if gap: e["_gap"] = gap
    return e

outcomes = [{"@id": "_:o_knowledge", "@type": "Outcome", "name": "Knowledge assessment score",
             "description": "Percentage of correct responses, averaged over seven co-designed knowledge areas."},
            {"@id": "_:o_women", "@type": "Outcome", "name": "Women's share of attendances"}]
AREAS = [("A1", "ICT tools and emerging technologies", 26.2, 83.7), ("A7", "Gender equity, diversity and inclusion", 25.0, 82.2),
         ("A4", "Community mobilization and engagement", 27.4, 82.7), ("A6", "Climate financing", 22.6, 75.7),
         ("A3", "Agroecology and agroforestry", 29.0, 81.7), ("A5", "Research and policy advocacy", 25.1, 76.9),
         ("A2", "Smart agriculture and value addition", 30.4, 79.5)]
outcomes += [{"@id": f"_:o_{c}", "@type": "Outcome", "name": f"Knowledge: {n}"} for c, n, _, _ in AREAS]
outcomes += [{"@id": "_:o_other", "@type": "Outcome", "name": "Other reported results",
              "_gap": "Catch-all. hasOutcome is the only way to say what an Observation measured, so one-off results each need an Outcome node."}]

contexts = [{"@id": "_:c_pre", "@type": "Context", "timePoint": "pre-training"},
            {"@id": "_:c_post", "@type": "Context", "timePoint": "post-training"},
            {"@id": "_:c_event", "@type": "Context", "timePoint": "at workshop"},
            {"@id": "_:c_diag", "@type": "Context", "timePoint": "diagnostic needs assessment, Jan-Aug 2024"},
            {"@id": "_:c_project", "@type": "Context", "timePoint": "during project, Aug 2025-May 2026",
             "_gap": "Core Context holds only timePoint. Country, place and population have no core property, so they sit in Arm free text and five Contexts serve all 40 Observations."}]

ROUNDS = [  # id, label, description, attendances, women, pre, post, gain, lo, hi, norm
    ("ng1", "Nigeria Phase 1", "Aug 2025. 156 farmers, 91 extension agents, 60 researchers.", 307, 184, 26.4, 78.0, 51.6, 48.2, 55.0, 0.701),
    ("sn1", "Senegal Phase 1", "Podor, Oct 2025. 100 farmers, 44 extension agents, 34 researchers.", 178, 88, 23.0, 85.0, 62.0, 59.2, 64.8, 0.806),
    ("ng2", "Nigeria Phase II", "Ebonyi and Enugu, Mar 2026. 175 farmers, 113 extension agents, 84 researchers.", 372, 224, 29.0, 80.0, 51.0, 46.9, 55.0, 0.718),
    ("sn2", "Senegal Phase 2", "Podor, May 2026. 115 farmers, 46 extension agents, 24 researchers (online).", 185, 72, 27.6, 78.4, 50.8, 45.3, 56.3, 0.700)]
N_GAP = "n is the 7 knowledge areas (the paper's unit of analysis), not people. The arm had {} attendances. Core has no way to state the unit of analysis, or the unit of the score (%)."

arms, findings = [], []
for i, (rid, label, desc, att, women, pre, post, gain, lo, hi, norm) in enumerate(ROUNDS):
    arm = {"@id": f"_:arm_{rid}", "@type": "Arm", "name": label, "description": desc + " Attendances, not unique individuals.",
           "hasIntervention": ({"@id": "_:int_workshop", "@type": "Intervention", "name": "Brokered capacity-strengthening workshop",
                                "description": "Participatory workshop for farmers, extension agents and researchers on seven co-designed modules.",
                                "_gap": "One Intervention shared by four arms, although Phase 2 curricula differed. Sharing or splitting is the coder's call."}
                               if i == 0 else ref("_:int_workshop")),
           "hasObservation": [
               obs(f"_:{rid}_pre", "Pre-training score", "_:o_knowledge", "_:c_pre", "Table 3", n=7, mean=pre, _gap=N_GAP.format(att)),
               obs(f"_:{rid}_post", "Post-training score", "_:o_knowledge", "_:c_post", "Table 3", n=7, mean=post),
               obs(f"_:{rid}_women", "Women attending", "_:o_women", "_:c_event", "Table 1", n=att, events=women)]}
    if rid == "sn2":
        arm["hasObservation"].append(obs("_:sn2_gesi", "Reported better understanding of gender equality and social inclusion", "_:o_other", "_:c_post",
            "Section 4.3", description="97% of participants.", _gap="A bare percentage with no denominator. No core property holds it: mean and events/n both misstate it."))
    arms.append(arm)
    findings.append({"@type": "Finding", "compares": [ref(f"_:{rid}_post"), ref(f"_:{rid}_pre")], "comparedTo": ref(f"_:{rid}_pre"),
        "hasEffectEstimate": [
            est(gain, lo, hi, loc="Table 3", derived=[f"_:{rid}_post", f"_:{rid}_pre"],
                gap="Paired t(6) and p < 0.001 have no home: core has no test statistic, degrees of freedom or p-value. Nothing marks the comparison as paired."),
            est(norm, metric=None, loc="Table 3", gap="Normalized (Hake) gain. Not in EffectSizeMetricScheme, and EffectEstimate has no name, so this number is unlabelled.")]})

pooled = {"@id": "_:arm_pooled", "@type": "Arm", "name": "All rounds pooled", "description": "1042 attendances across the four rounds.",
          "_gap": "A union of the four round arms. Core cannot say an Arm is made of other Arms, so the pooled results look like a fifth independent group.",
          "hasObservation": [obs("_:all_pre", "Pre-training score", "_:o_knowledge", "_:c_pre", "Table 3", n=28, mean=26.5),
                             obs("_:all_post", "Post-training score", "_:o_knowledge", "_:c_post", "Table 3", n=28, mean=80.3),
                             obs("_:all_women", "Women attending", "_:o_women", "_:c_event", "Table 1", n=1042, events=568)]}
for c, n, pre, post in AREAS:
    pooled["hasObservation"] += [obs(f"_:{c}_pre", f"{c} pre-training", f"_:o_{c}", "_:c_pre", "Table 6", n=4, mean=pre),
                                 obs(f"_:{c}_post", f"{c} post-training", f"_:o_{c}", "_:c_post", "Table 6", n=4, mean=post)]
    findings.append({"@type": "Finding", "compares": [ref(f"_:{c}_post"), ref(f"_:{c}_pre")], "comparedTo": ref(f"_:{c}_pre"),
                     "hasEffectEstimate": [est(round(post - pre, 1), loc="Table 6", derived=[f"_:{c}_post", f"_:{c}_pre"])]})
findings.append({"@type": "Finding", "compares": [ref("_:all_post"), ref("_:all_pre")], "comparedTo": ref("_:all_pre"),
                 "hasEffectEstimate": [est(53.8, 51.4, 56.3, loc="Table 3", derived=["_:all_post", "_:all_pre"])]})
arms.append(pooled)

PAIR_GAP = ("A difference between two gains. compares lists four Observations but one comparedTo cannot say which arm is the reference "
            "or that pre is subtracted from post, so the sign of the estimate is not recoverable from the graph.")
for a, b, d, lo, hi in [("sn1", "ng1", 10.44, 7.26, 13.62), ("ng2", "sn1", -11.06, -14.69, -7.42), ("sn2", "sn1", -11.26, -16.18, -6.34),
                        ("ng2", "ng1", -0.61, -6.41, 5.18), ("sn2", "ng1", -0.81, -6.24, 4.61), ("sn2", "ng2", -0.20, -5.40, 5.00)]:
    findings.append({"@type": "Finding", "compares": [ref(f"_:{a}_post"), ref(f"_:{a}_pre"), ref(f"_:{b}_post"), ref(f"_:{b}_pre")],
                     "hasEffectEstimate": [est(d, lo, hi, loc="Table 5")], "_gap": PAIR_GAP})
all8 = [ref(f"_:{r[0]}_{t}") for r in ROUNDS for t in ("post", "pre")]
findings.append({"@type": "Finding", "compares": all8, "hasEffectEstimate": [est(0.72, metric=None, loc="Table 4",
    gap="Partial eta-squared for the round effect, F(3,18) = 15.63, p < 0.001. Metric not in the scheme; F and p have no home.")],
    "_gap": "Omnibus ANOVA across four arms. The n-ary compares fits this."})
for label, d, lo, hi in [("country (Senegal - Nigeria)", 5.12, 2.21, 8.03), ("phase (Phase 2 - Phase 1)", -5.94, -8.84, -3.03),
                         ("country x phase interaction", -5.32, -8.23, -2.41)]:
    findings.append({"@type": "Finding", "compares": all8, "hasEffectEstimate": [est(d, lo, hi, loc="Section 4.3.1")],
        "_gap": f"Orthogonal contrast: {label}. Identical in the graph to the omnibus Finding and the other two contrasts: "
                "Finding has no name or description and compares carries no weights or roles. This note is the only thing telling them apart."})

arms.append({"@id": "_:arm_sn_diag", "@type": "Arm", "name": "Senegal diagnostic sample",
    "description": "Podor needs assessment: key informant interviews with farmers, extension agents and researchers.",
    "_gap": "Each Observation below is about a different subgroup (extension agents, researchers, farmers). Subgroup belongs to neither Arm nor core Context, so it is only in the Observation name.",
    "hasObservation": [
        obs("_:sn_fin_unaware", "Extension agents unaware of climate finance opportunities", "_:o_other", "_:c_diag", "Section 4.2", description="92%"),
        obs("_:sn_fin_access", "Extension agents with access to financial resources for adaptation", "_:o_other", "_:c_diag", "Section 4.2", description="16.67%"),
        obs("_:sn_women_agents", "Women among surveyed extension agents", "_:o_other", "_:c_diag", "Section 4.2", description="8.33%"),
        obs("_:sn_heard", "Farmers reporting that advisers listen to them", "_:o_other", "_:c_diag", "Section 4.6", description="70%")]})
findings.append({"@type": "Finding", "compares": [ref("_:sn_heard")],
    "_gap": "The paper reports that gender significantly influenced whether a farmer was heard, with no figures by gender. A Finding needs two or more Observations to compare; the paper gives none, so this Finding is invalid as written and the result itself has nowhere to be stated."})
arms.append({"@id": "_:arm_ng_diag", "@type": "Arm", "name": "Nigeria diagnostic sample", "description": "Enugu and Ebonyi needs assessment and validation workshops.",
    "hasObservation": [
        obs("_:ng_fin_barrier", "Farmers citing poor awareness of climate finance as primary barrier", "_:o_other", "_:c_diag", "Section 4.2", description="65.1%"),
        obs("_:ng_prio_women", "Training priorities of female farmers", "_:o_other", "_:c_diag", "Section 4.2",
            description="Financial literacy and organic, chemical-free pest and disease management to reduce input costs."),
        obs("_:ng_prio_men", "Training priorities of male farmers", "_:o_other", "_:c_diag", "Section 4.2",
            description="Advanced agro-technologies such as push-pull systems, and ICT tools for real-time weather forecasts.")]})
findings.append({"@type": "Finding", "compares": [ref("_:ng_prio_women"), ref("_:ng_prio_men")],
    "_gap": "A qualitative comparison with no effect estimate. This fits the model well."})
arms.append({"@id": "_:arm_ng_adopt", "@type": "Arm", "name": "Nigeria participants and partner bodies",
    "_gap": "Overlaps the two Nigeria round arms to an unknown degree. The MoU is a result about an institution, not a measurement on a group of units; it is here because an Observation must belong to an Arm.",
    "hasObservation": [
        obs("_:ng_bottles", "Upcycled-bottle crop protection, Nwanyi Bu Ihe cooperative, Nsukka", "_:o_other", "_:c_project", "Section 4.3.2",
            description="Deployed on 15 farms with 2000 devices; 100% crop protection reported; spontaneous adoption by neighbouring non-participants."),
        obs("_:ng_digital", "Participants trained on and adopting digital agricultural tools", "_:o_other", "_:c_project", "Section 4.3.2", n=207),
        obs("_:ng_mou", "Five-year MoU with Enugu State Ministry of Agriculture", "_:o_other", "_:c_project", "Section 4.5",
            description="Institutionalizes the project's locally led adaptation strategies and sets up a Joint Technical Working Group.")]})

doc = {"@context": {"@vocab": NS, "_gap": None, "_comment": None, "_outcomes": "@nest", "_contexts": "@nest"},
       "_comment": "Hand mapping of Ozor et al. (2026), Sustainability 18, 8996, doi:10.3390/su18178996, onto evrepo-core v2 (draft), core terms only. _gap keys mark where the model could not hold what the paper reports.",
       "@type": "LinkedDataEnhancement",
       "hasInvestigation": {"@type": "Investigation", "hasArm": arms, "hasFinding": findings},
       "@included": outcomes + contexts}
json.dump(doc, open("scale-extension-v2.jsonld", "w"), indent=2, ensure_ascii=False)
