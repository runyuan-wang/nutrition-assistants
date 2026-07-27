# 儿童青少年肥胖治未病食养助手 🌐 International Edition

Global-ready AI nutrition科普 assistants based on the China Association of Chinese Medicine's *Guideline for Preventive Treatment of Diseases in Obesity of Children and Adolescents* (2026).

---

## Available Languages

| Language | Directory | Status | Key Files |
|----------|-----------|--------|-----------|
| 🇨🇳 **中文 (Chinese)** | `../child-obesity-tcm-prevention-skill/` | ✅ Complete v1.0.0 | SKILL.md, system_prompt.md, knowledge_base.md (13 KPK), dietary_formulas.md (11 recipes) |
| 🇬🇧 **English** | `en/` | ✅ Complete | SKILL.md, system_prompt.md, knowledge_base.md |
| 🇯🇵 **日本語 (Japanese)** | `ja/` | ✅ Complete | SKILL.md, system_prompt.md |

## Content Summary

All language versions include:
- **13 KPK knowledge points** covering: epidemiology, risk factors, TCM etiology, 7 constitution types, diagnostic criteria, 4-stage prevention, dietary/exercise/lifestyle intervention, herbal medicine, external therapies, health education
- **7 TCM constitution types**: Balanced, Qi Deficient, Yang Deficient, Phlegm-Dampness, Damp-Heat, Qi Stagnation, Yang Heat
- **4 TCM syndrome types**: Spleen Deficiency Dampness, Stomach Heat Dampness, Spleen-Kidney Deficiency, Liver Depression Spleen Deficiency
- **11 medicinal food recipes** with ingredients, preparation, and contraindications
- **3 external therapies**: Auricular acupressure (evidence level B), Tuina (level C), Acupuncture (level C)
- **4-stage preventive treatment**: Pre-disease → Sprout → Disease control → Relapse prevention
- **5-dimension health education**: Psychology, Family, Hospital, School, Society

## Anti-Hallucination Verification

All strong conclusions have been verified against the original PDF (A-level source, full text obtained):
- ✅ 47 claims checked → 44/47 directly traceable, 3/47 confirmed as PDF extraction artifacts (not content errors)
- ✅ 0 prohibited writing patterns found
- ✅ All KPK data points mapped correctly

## Usage

Load the `system_prompt.md` of your chosen language into an LLM's system prompt, then inject the knowledge_base.md and dietary_formulas.md as context.

## Author

**Wang Runyuan** (王润圆)
Registered Dietitian in China, MSc in Nutrition and Food Hygiene, Kunming Medical University
Built with WorkBuddy following the Nutrition Guideline Distillation Methodology v2.0
