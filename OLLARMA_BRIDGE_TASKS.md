# Ollarma Bridge Task List

**Task List for Byron after completed unattended BioCustody Problem #2 run**

---

### DONE  
- Reproduced the repurposing queue with `python scripts/magicstudiobox_repurposing_queue.py`.  

---

### VERIFY FIRST  
- Open **deliverables/REPURPOSING_EVIDENCE_TABLE.md**.  
- Verify that the narrative for the top candidate **desonide (BRD-K21528677-001-04-4)** aligns with the clinical-progress rows listed within.  

---

### NEXT SAFE TASKS  
1. Review the **FINAL_METRICS.json** file to confirm:  
   - `claim_ceiling` = *REPURPOSING_HYPOTHESIS*  
   - `top_candidate` = *desonide*  
   - `known_pair_rank` = 28  
2. Confirm that the **tamper_test.json** indicates a pass (`"pass": true`).  
3. Ensure all artifact statuses (e.g., custody_verified, tamper_detection) remain as reported: *yes*, *PASS*.  

---

### CUT / DO NOT DO  
- Do **not** proceed with any clinical utility claims or efficacy assessments beyond the repurposing hypothesis ceiling.  
- Avoid modifying `duplicate.fcos[2].payload.top_rows[0].restoration_score` or any other flagged artifact post‑tamper test.  

---

### FILES TO OPEN  
- **deliverables/REPURPOSING_EVIDENCE_TABLE.md** (for candidate narrative verification).  
- **runs/magicstudiobox/primary/evaluation.json** (to cross‑check evaluation metrics).  
- **runs/magicstudiobox/primary/tamper_test.json** (to reconfirm tamper test outcome).  

---

*Note:* All actions respect the **CLAIM CEILING: REPURPOSING_HYPOTHESIS** and refrain from asserting rescue or clinical utility.

## Bridge Receipt

- Host: magicstudiobox
- Endpoint: http://127.0.0.1:8484/chat
- Model: `granite4.1:8b`
- Status: `answered`
- Mode: one-shot task list, no continuous watching
