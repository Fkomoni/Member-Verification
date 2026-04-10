"""
Drug Master Seed Data — common Nigerian medications pre-classified.

Categories:
  - acute:   short-term treatment (antibiotics, antimalarials, analgesics, etc.)
  - chronic: long-term/ongoing treatment (antihypertensives, diabetes, etc.)
  - either:  can be prescribed as either acute or chronic depending on context
  - unknown: not yet classified — triggers review

Source: curated from common Nigerian HMO formularies.
When WellaHealth drug list API is available, this seed can be supplemented.
"""

SEED_DRUGS: list[dict] = [
    # ── Chronic: Cardiovascular / Antihypertensives ──────────────
    {
        "generic_name": "Amlodipine",
        "category": "chronic",
        "common_brand_names": "Norvasc, Amlovar",
        "therapeutic_class": "antihypertensive",
        "aliases": ["Norvasc", "Amlovar", "Amlod"],
    },
    {
        "generic_name": "Lisinopril",
        "category": "chronic",
        "common_brand_names": "Zestril, Prinivil",
        "therapeutic_class": "antihypertensive",
        "aliases": ["Zestril", "Prinivil"],
    },
    {
        "generic_name": "Losartan",
        "category": "chronic",
        "common_brand_names": "Cozaar, Losacar",
        "therapeutic_class": "antihypertensive",
        "aliases": ["Cozaar", "Losacar"],
    },
    {
        "generic_name": "Atenolol",
        "category": "chronic",
        "common_brand_names": "Tenormin",
        "therapeutic_class": "antihypertensive",
        "aliases": ["Tenormin"],
    },
    {
        "generic_name": "Nifedipine",
        "category": "chronic",
        "common_brand_names": "Adalat, Procardia",
        "therapeutic_class": "antihypertensive",
        "aliases": ["Adalat", "Procardia"],
    },
    {
        "generic_name": "Hydrochlorothiazide",
        "category": "chronic",
        "common_brand_names": "Esidrex, HCTZ",
        "therapeutic_class": "diuretic",
        "aliases": ["HCTZ", "Esidrex", "Hydrochlorothiazide"],
    },
    {
        "generic_name": "Furosemide",
        "category": "chronic",
        "common_brand_names": "Lasix",
        "therapeutic_class": "diuretic",
        "aliases": ["Lasix"],
    },
    {
        "generic_name": "Aspirin (Low-dose)",
        "category": "chronic",
        "common_brand_names": "Vasoprin, Disprin CV",
        "therapeutic_class": "antiplatelet",
        "aliases": ["Vasoprin", "Disprin CV", "Low-dose Aspirin", "Baby Aspirin"],
    },
    {
        "generic_name": "Atorvastatin",
        "category": "chronic",
        "common_brand_names": "Lipitor, Atorva",
        "therapeutic_class": "statin",
        "aliases": ["Lipitor", "Atorva"],
    },
    {
        "generic_name": "Rosuvastatin",
        "category": "chronic",
        "common_brand_names": "Crestor",
        "therapeutic_class": "statin",
        "aliases": ["Crestor"],
    },
    {
        "generic_name": "Warfarin",
        "category": "chronic",
        "common_brand_names": "Coumadin, Marevan",
        "therapeutic_class": "anticoagulant",
        "requires_review": True,
        "aliases": ["Coumadin", "Marevan"],
    },
    {
        "generic_name": "Digoxin",
        "category": "chronic",
        "common_brand_names": "Lanoxin",
        "therapeutic_class": "cardiac glycoside",
        "requires_review": True,
        "aliases": ["Lanoxin"],
    },

    # ── Chronic: Diabetes ────────────────────────────────────────
    {
        "generic_name": "Metformin",
        "category": "chronic",
        "common_brand_names": "Glucophage, Metforal",
        "therapeutic_class": "antidiabetic",
        "aliases": ["Glucophage", "Metforal", "Metformin HCl"],
    },
    {
        "generic_name": "Glibenclamide",
        "category": "chronic",
        "common_brand_names": "Daonil, Glyburide",
        "therapeutic_class": "antidiabetic",
        "aliases": ["Daonil", "Glyburide"],
    },
    {
        "generic_name": "Glimepiride",
        "category": "chronic",
        "common_brand_names": "Amaryl",
        "therapeutic_class": "antidiabetic",
        "aliases": ["Amaryl"],
    },
    {
        "generic_name": "Insulin (Soluble)",
        "category": "chronic",
        "common_brand_names": "Actrapid, Humulin R",
        "therapeutic_class": "insulin",
        "requires_review": True,
        "aliases": ["Actrapid", "Humulin R", "Regular Insulin"],
    },
    {
        "generic_name": "Insulin (NPH/Isophane)",
        "category": "chronic",
        "common_brand_names": "Insulatard, Humulin N",
        "therapeutic_class": "insulin",
        "requires_review": True,
        "aliases": ["Insulatard", "Humulin N", "NPH Insulin"],
    },
    {
        "generic_name": "Insulin Glargine",
        "category": "chronic",
        "common_brand_names": "Lantus, Basaglar",
        "therapeutic_class": "insulin",
        "requires_review": True,
        "aliases": ["Lantus", "Basaglar"],
    },
    {
        "generic_name": "Pioglitazone",
        "category": "chronic",
        "common_brand_names": "Actos",
        "therapeutic_class": "antidiabetic",
        "aliases": ["Actos"],
    },
    {
        "generic_name": "Sitagliptin",
        "category": "chronic",
        "common_brand_names": "Januvia",
        "therapeutic_class": "antidiabetic",
        "aliases": ["Januvia"],
    },

    # ── Chronic: Respiratory ─────────────────────────────────────
    {
        "generic_name": "Salbutamol Inhaler",
        "category": "chronic",
        "common_brand_names": "Ventolin",
        "therapeutic_class": "bronchodilator",
        "aliases": ["Ventolin Inhaler", "Albuterol"],
    },
    {
        "generic_name": "Beclometasone Inhaler",
        "category": "chronic",
        "common_brand_names": "Becotide, Clenil",
        "therapeutic_class": "inhaled corticosteroid",
        "aliases": ["Becotide", "Clenil"],
    },
    {
        "generic_name": "Montelukast",
        "category": "chronic",
        "common_brand_names": "Singulair",
        "therapeutic_class": "leukotriene antagonist",
        "aliases": ["Singulair"],
    },

    # ── Chronic: CNS / Psychiatry ────────────────────────────────
    {
        "generic_name": "Carbamazepine",
        "category": "chronic",
        "common_brand_names": "Tegretol",
        "therapeutic_class": "anticonvulsant",
        "aliases": ["Tegretol"],
    },
    {
        "generic_name": "Phenytoin",
        "category": "chronic",
        "common_brand_names": "Dilantin, Epanutin",
        "therapeutic_class": "anticonvulsant",
        "requires_review": True,
        "aliases": ["Dilantin", "Epanutin"],
    },
    {
        "generic_name": "Sodium Valproate",
        "category": "chronic",
        "common_brand_names": "Epilim, Depakote",
        "therapeutic_class": "anticonvulsant",
        "aliases": ["Epilim", "Depakote", "Valproic Acid"],
    },
    {
        "generic_name": "Amitriptyline",
        "category": "chronic",
        "common_brand_names": "Elavil, Tryptanol",
        "therapeutic_class": "antidepressant",
        "aliases": ["Elavil", "Tryptanol"],
    },
    {
        "generic_name": "Fluoxetine",
        "category": "chronic",
        "common_brand_names": "Prozac",
        "therapeutic_class": "antidepressant",
        "aliases": ["Prozac"],
    },
    {
        "generic_name": "Haloperidol",
        "category": "chronic",
        "common_brand_names": "Haldol",
        "therapeutic_class": "antipsychotic",
        "aliases": ["Haldol"],
    },

    # ── Chronic: Thyroid ─────────────────────────────────────────
    {
        "generic_name": "Levothyroxine",
        "category": "chronic",
        "common_brand_names": "Eltroxin, Synthroid",
        "therapeutic_class": "thyroid hormone",
        "aliases": ["Eltroxin", "Synthroid", "Thyroxine"],
    },
    {
        "generic_name": "Carbimazole",
        "category": "chronic",
        "common_brand_names": "Neo-Mercazole",
        "therapeutic_class": "antithyroid",
        "aliases": ["Neo-Mercazole"],
    },

    # ── Chronic: GI ──────────────────────────────────────────────
    {
        "generic_name": "Omeprazole",
        "category": "either",
        "common_brand_names": "Losec, Omez",
        "therapeutic_class": "proton pump inhibitor",
        "aliases": ["Losec", "Omez"],
    },
    {
        "generic_name": "Esomeprazole",
        "category": "either",
        "common_brand_names": "Nexium",
        "therapeutic_class": "proton pump inhibitor",
        "aliases": ["Nexium"],
    },
    {
        "generic_name": "Ranitidine",
        "category": "either",
        "common_brand_names": "Zantac",
        "therapeutic_class": "H2 blocker",
        "aliases": ["Zantac"],
    },

    # ── Acute: Antibiotics ───────────────────────────────────────
    {
        "generic_name": "Amoxicillin",
        "category": "acute",
        "common_brand_names": "Amoxil, Ospamox",
        "therapeutic_class": "antibiotic",
        "aliases": ["Amoxil", "Ospamox"],
    },
    {
        "generic_name": "Amoxicillin/Clavulanate",
        "category": "acute",
        "common_brand_names": "Augmentin, Clavamox",
        "therapeutic_class": "antibiotic",
        "aliases": ["Augmentin", "Clavamox", "Amoxiclav", "Augmentin 625"],
    },
    {
        "generic_name": "Azithromycin",
        "category": "acute",
        "common_brand_names": "Zithromax, Azee",
        "therapeutic_class": "antibiotic",
        "aliases": ["Zithromax", "Azee", "Z-pack"],
    },
    {
        "generic_name": "Ciprofloxacin",
        "category": "acute",
        "common_brand_names": "Cipro, Ciproxin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Cipro", "Ciproxin"],
    },
    {
        "generic_name": "Metronidazole",
        "category": "acute",
        "common_brand_names": "Flagyl",
        "therapeutic_class": "antibiotic/antiprotozoal",
        "aliases": ["Flagyl"],
    },
    {
        "generic_name": "Ceftriaxone",
        "category": "acute",
        "common_brand_names": "Rocephin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Rocephin"],
    },
    {
        "generic_name": "Cefuroxime",
        "category": "acute",
        "common_brand_names": "Zinnat, Zinacef",
        "therapeutic_class": "antibiotic",
        "aliases": ["Zinnat", "Zinacef"],
    },
    {
        "generic_name": "Erythromycin",
        "category": "acute",
        "common_brand_names": "Erythrocin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Erythrocin", "E-Mycin"],
    },
    {
        "generic_name": "Doxycycline",
        "category": "acute",
        "common_brand_names": "Vibramycin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Vibramycin"],
    },
    {
        "generic_name": "Levofloxacin",
        "category": "acute",
        "common_brand_names": "Tavanic, Levaquin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Tavanic", "Levaquin"],
    },
    {
        "generic_name": "Nitrofurantoin",
        "category": "acute",
        "common_brand_names": "Macrodantin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Macrodantin"],
    },

    # ── Acute: Antimalarials ─────────────────────────────────────
    {
        "generic_name": "Artemether/Lumefantrine",
        "category": "acute",
        "common_brand_names": "Coartem, Lonart",
        "therapeutic_class": "antimalarial",
        "aliases": ["Coartem", "Lonart", "AL"],
    },
    {
        "generic_name": "Artesunate/Amodiaquine",
        "category": "acute",
        "common_brand_names": "Camosunate, Larimal",
        "therapeutic_class": "antimalarial",
        "aliases": ["Camosunate", "Larimal"],
    },
    {
        "generic_name": "Artesunate (Injectable)",
        "category": "acute",
        "common_brand_names": "Artesunat",
        "therapeutic_class": "antimalarial",
        "aliases": ["IV Artesunate"],
    },
    {
        "generic_name": "Quinine",
        "category": "acute",
        "common_brand_names": "Quinine Sulphate",
        "therapeutic_class": "antimalarial",
        "aliases": ["Quinine Sulphate", "Quinine Dihydrochloride"],
    },

    # ── Acute: Analgesics / Anti-inflammatory ────────────────────
    {
        "generic_name": "Paracetamol",
        "category": "acute",
        "common_brand_names": "Panadol, Tylenol, Emzor Paracetamol",
        "therapeutic_class": "analgesic",
        "aliases": ["Panadol", "Tylenol", "Acetaminophen", "PCM"],
    },
    {
        "generic_name": "Ibuprofen",
        "category": "acute",
        "common_brand_names": "Brufen, Advil",
        "therapeutic_class": "NSAID",
        "aliases": ["Brufen", "Advil", "Nurofen"],
    },
    {
        "generic_name": "Diclofenac",
        "category": "acute",
        "common_brand_names": "Voltaren, Cataflam",
        "therapeutic_class": "NSAID",
        "aliases": ["Voltaren", "Cataflam", "Olfen"],
    },
    {
        "generic_name": "Piroxicam",
        "category": "acute",
        "common_brand_names": "Feldene",
        "therapeutic_class": "NSAID",
        "aliases": ["Feldene"],
    },
    {
        "generic_name": "Tramadol",
        "category": "acute",
        "common_brand_names": "Tramol, Ultram",
        "therapeutic_class": "opioid analgesic",
        "requires_review": True,
        "aliases": ["Tramol", "Ultram"],
    },
    {
        "generic_name": "Aspirin (Analgesic dose)",
        "category": "acute",
        "common_brand_names": "Disprin, Aspro",
        "therapeutic_class": "analgesic/NSAID",
        "aliases": ["Disprin", "Aspro"],
    },

    # ── Acute: Antihistamines / Allergy ──────────────────────────
    {
        "generic_name": "Cetirizine",
        "category": "acute",
        "common_brand_names": "Zyrtec",
        "therapeutic_class": "antihistamine",
        "aliases": ["Zyrtec"],
    },
    {
        "generic_name": "Loratadine",
        "category": "acute",
        "common_brand_names": "Clarityn, Loratyn",
        "therapeutic_class": "antihistamine",
        "aliases": ["Clarityn", "Loratyn"],
    },
    {
        "generic_name": "Chlorpheniramine",
        "category": "acute",
        "common_brand_names": "Piriton",
        "therapeutic_class": "antihistamine",
        "aliases": ["Piriton"],
    },
    {
        "generic_name": "Prednisolone",
        "category": "either",
        "common_brand_names": "Prelone",
        "therapeutic_class": "corticosteroid",
        "aliases": ["Prelone", "Pred"],
    },

    # ── Acute: GI / Anti-emetics ─────────────────────────────────
    {
        "generic_name": "Metoclopramide",
        "category": "acute",
        "common_brand_names": "Plasil, Maxolon",
        "therapeutic_class": "antiemetic",
        "aliases": ["Plasil", "Maxolon"],
    },
    {
        "generic_name": "Loperamide",
        "category": "acute",
        "common_brand_names": "Imodium",
        "therapeutic_class": "antidiarrhoeal",
        "aliases": ["Imodium"],
    },
    {
        "generic_name": "Oral Rehydration Salts",
        "category": "acute",
        "common_brand_names": "ORS",
        "therapeutic_class": "rehydration",
        "aliases": ["ORS"],
    },
    {
        "generic_name": "Hyoscine Butylbromide",
        "category": "acute",
        "common_brand_names": "Buscopan",
        "therapeutic_class": "antispasmodic",
        "aliases": ["Buscopan"],
    },

    # ── Acute: Cough / Cold ──────────────────────────────────────
    {
        "generic_name": "Cough Syrup (Expectorant)",
        "category": "acute",
        "common_brand_names": "Benylin Expectorant",
        "therapeutic_class": "expectorant",
        "aliases": ["Benylin", "Guaifenesin"],
    },
    {
        "generic_name": "Cough Syrup (Suppressant)",
        "category": "acute",
        "common_brand_names": "Benylin DM",
        "therapeutic_class": "antitussive",
        "aliases": ["Benylin DM", "Dextromethorphan"],
    },

    # ── Acute: Antifungals ───────────────────────────────────────
    {
        "generic_name": "Fluconazole",
        "category": "acute",
        "common_brand_names": "Diflucan",
        "therapeutic_class": "antifungal",
        "aliases": ["Diflucan"],
    },
    {
        "generic_name": "Clotrimazole (Topical)",
        "category": "acute",
        "common_brand_names": "Canesten",
        "therapeutic_class": "antifungal",
        "aliases": ["Canesten"],
    },

    # ── Acute: Anthelmintics ─────────────────────────────────────
    {
        "generic_name": "Albendazole",
        "category": "acute",
        "common_brand_names": "Zentel",
        "therapeutic_class": "anthelmintic",
        "aliases": ["Zentel"],
    },
    {
        "generic_name": "Mebendazole",
        "category": "acute",
        "common_brand_names": "Vermox",
        "therapeutic_class": "anthelmintic",
        "aliases": ["Vermox"],
    },

    # ── Acute: Muscle Relaxant ───────────────────────────────────
    {
        "generic_name": "Tizanidine",
        "category": "acute",
        "common_brand_names": "Zanaflex, Sirdalud",
        "therapeutic_class": "muscle relaxant",
        "aliases": ["Zanaflex", "Sirdalud"],
    },

    # ── Acute: Eye/Ear ───────────────────────────────────────────
    {
        "generic_name": "Chloramphenicol Eye Drops",
        "category": "acute",
        "common_brand_names": "Chlorsig",
        "therapeutic_class": "ophthalmic antibiotic",
        "aliases": ["Chlorsig"],
    },
    {
        "generic_name": "Ciprofloxacin Eye Drops",
        "category": "acute",
        "common_brand_names": "Ciloxan",
        "therapeutic_class": "ophthalmic antibiotic",
        "aliases": ["Ciloxan"],
    },

    # ── Chronic: Miscellaneous ───────────────────────────────────
    {
        "generic_name": "Allopurinol",
        "category": "chronic",
        "common_brand_names": "Zyloprim",
        "therapeutic_class": "urate-lowering",
        "aliases": ["Zyloprim"],
    },
    {
        "generic_name": "Folic Acid",
        "category": "either",
        "common_brand_names": "Folate",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Folate", "Folvite"],
    },
    {
        "generic_name": "Ferrous Sulphate",
        "category": "either",
        "common_brand_names": "Ferograd, Fersolate",
        "therapeutic_class": "iron supplement",
        "aliases": ["Ferograd", "Fersolate", "Iron Tablets"],
    },
    {
        "generic_name": "Calcium + Vitamin D",
        "category": "either",
        "common_brand_names": "Calcichew D3, Caltrate",
        "therapeutic_class": "calcium supplement",
        "aliases": ["Calcichew", "Caltrate"],
    },

    # ── Chronic: HIV / ARVs (requires review) ───────────────────
    {
        "generic_name": "Tenofovir/Lamivudine/Dolutegravir",
        "category": "chronic",
        "common_brand_names": "TLD",
        "therapeutic_class": "antiretroviral",
        "requires_review": True,
        "aliases": ["TLD"],
    },
    {
        "generic_name": "Tenofovir/Emtricitabine",
        "category": "chronic",
        "common_brand_names": "Truvada",
        "therapeutic_class": "antiretroviral",
        "requires_review": True,
        "aliases": ["Truvada"],
    },

    # ── Vitamins / Supplements (either) ──────────────────────────
    {
        "generic_name": "Multivitamin",
        "category": "either",
        "common_brand_names": "Wellman, Pregnacare, Dayamineral",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Wellman", "Pregnacare", "Centrum", "Dayamineral"],
    },
    {
        "generic_name": "Vitamin C",
        "category": "acute",
        "common_brand_names": "Ascorbic Acid",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Ascorbic Acid", "Vit C"],
    },
    {
        "generic_name": "Vitamin B Complex",
        "category": "either",
        "common_brand_names": "Neurobion, Becosules",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Neurobion", "Becosules", "Vit B"],
    },

    # ── Acute: More Antimalarials ─────────────────────────────────
    {
        "generic_name": "Chloroquine",
        "category": "acute",
        "common_brand_names": "Chloroquine Phosphate, Resochin",
        "therapeutic_class": "antimalarial",
        "aliases": ["Resochin", "Chloroquine Phosphate", "CQ"],
    },
    {
        "generic_name": "Dihydroartemisinin/Piperaquine",
        "category": "acute",
        "common_brand_names": "Cotecxin, Eurartesim",
        "therapeutic_class": "antimalarial",
        "aliases": ["Cotecxin", "Eurartesim", "DHA-PQP"],
    },
    {
        "generic_name": "Sulphadoxine/Pyrimethamine",
        "category": "acute",
        "common_brand_names": "Fansidar",
        "therapeutic_class": "antimalarial",
        "aliases": ["Fansidar", "SP"],
    },
    {
        "generic_name": "Primaquine",
        "category": "acute",
        "common_brand_names": "Primaquine Phosphate",
        "therapeutic_class": "antimalarial",
        "requires_review": True,
        "aliases": ["Primaquine Phosphate"],
    },

    # ── Acute: More Antibiotics ───────────────────────────────────
    {
        "generic_name": "Cefixime",
        "category": "acute",
        "common_brand_names": "Suprax, Cefspan",
        "therapeutic_class": "antibiotic",
        "aliases": ["Suprax", "Cefspan"],
    },
    {
        "generic_name": "Cloxacillin",
        "category": "acute",
        "common_brand_names": "Cloxapen, Orbenin",
        "therapeutic_class": "antibiotic",
        "aliases": ["Cloxapen", "Orbenin"],
    },
    {
        "generic_name": "Clarithromycin",
        "category": "acute",
        "common_brand_names": "Klacid, Klaricid",
        "therapeutic_class": "antibiotic",
        "aliases": ["Klacid", "Klaricid"],
    },
    {
        "generic_name": "Cephalexin",
        "category": "acute",
        "common_brand_names": "Keflex, Cephadex",
        "therapeutic_class": "antibiotic",
        "aliases": ["Keflex", "Cephadex"],
    },
    {
        "generic_name": "Co-trimoxazole",
        "category": "acute",
        "common_brand_names": "Septrin, Bactrim",
        "therapeutic_class": "antibiotic",
        "aliases": ["Septrin", "Bactrim", "Trimethoprim/Sulfamethoxazole", "TMP-SMX"],
    },
    {
        "generic_name": "Ceftazidime",
        "category": "acute",
        "common_brand_names": "Fortum, Fortaz",
        "therapeutic_class": "antibiotic",
        "aliases": ["Fortum", "Fortaz"],
    },
    {
        "generic_name": "Gentamicin",
        "category": "acute",
        "common_brand_names": "Garamycin",
        "therapeutic_class": "antibiotic",
        "requires_review": True,
        "aliases": ["Garamycin"],
    },
    {
        "generic_name": "Amikacin",
        "category": "acute",
        "common_brand_names": "Amikin",
        "therapeutic_class": "antibiotic",
        "requires_review": True,
        "aliases": ["Amikin"],
    },
    {
        "generic_name": "Vancomycin",
        "category": "acute",
        "common_brand_names": "Vancocin",
        "therapeutic_class": "antibiotic",
        "requires_review": True,
        "aliases": ["Vancocin"],
    },
    {
        "generic_name": "Meropenem",
        "category": "acute",
        "common_brand_names": "Meronem",
        "therapeutic_class": "antibiotic",
        "requires_review": True,
        "aliases": ["Meronem"],
    },
    {
        "generic_name": "Piperacillin/Tazobactam",
        "category": "acute",
        "common_brand_names": "Tazocin, Zosyn",
        "therapeutic_class": "antibiotic",
        "aliases": ["Tazocin", "Zosyn"],
    },

    # ── Acute: More Analgesics / Anti-inflammatory ───────────────
    {
        "generic_name": "Naproxen",
        "category": "acute",
        "common_brand_names": "Naprosyn, Aleve",
        "therapeutic_class": "NSAID",
        "aliases": ["Naprosyn", "Aleve"],
    },
    {
        "generic_name": "Meloxicam",
        "category": "either",
        "common_brand_names": "Mobic, Movel",
        "therapeutic_class": "NSAID",
        "aliases": ["Mobic", "Movel"],
    },
    {
        "generic_name": "Celecoxib",
        "category": "either",
        "common_brand_names": "Celebrex",
        "therapeutic_class": "NSAID",
        "aliases": ["Celebrex"],
    },
    {
        "generic_name": "Codeine",
        "category": "acute",
        "common_brand_names": "Codeine Phosphate",
        "therapeutic_class": "opioid analgesic",
        "requires_review": True,
        "aliases": ["Codeine Phosphate", "Codeine Linctus"],
    },
    {
        "generic_name": "Morphine",
        "category": "acute",
        "common_brand_names": "MST Continus, Sevredol",
        "therapeutic_class": "opioid analgesic",
        "requires_review": True,
        "aliases": ["MST", "Oramorph"],
    },
    {
        "generic_name": "Gabapentin",
        "category": "either",
        "common_brand_names": "Neurontin",
        "therapeutic_class": "neuropathic pain / anticonvulsant",
        "aliases": ["Neurontin"],
    },
    {
        "generic_name": "Pregabalin",
        "category": "either",
        "common_brand_names": "Lyrica",
        "therapeutic_class": "neuropathic pain / anticonvulsant",
        "aliases": ["Lyrica"],
    },

    # ── Acute: Anti-emetics / GI ─────────────────────────────────
    {
        "generic_name": "Ondansetron",
        "category": "acute",
        "common_brand_names": "Zofran, Emetrol",
        "therapeutic_class": "antiemetic",
        "aliases": ["Zofran", "Emetrol"],
    },
    {
        "generic_name": "Domperidone",
        "category": "acute",
        "common_brand_names": "Motilium",
        "therapeutic_class": "antiemetic / prokinetic",
        "aliases": ["Motilium"],
    },
    {
        "generic_name": "Promethazine",
        "category": "acute",
        "common_brand_names": "Phenergan",
        "therapeutic_class": "antihistamine / antiemetic",
        "aliases": ["Phenergan"],
    },
    {
        "generic_name": "Pantoprazole",
        "category": "either",
        "common_brand_names": "Pantoloc, Protonix",
        "therapeutic_class": "proton pump inhibitor",
        "aliases": ["Pantoloc", "Protonix"],
    },
    {
        "generic_name": "Lansoprazole",
        "category": "either",
        "common_brand_names": "Prevacid, Lanzo",
        "therapeutic_class": "proton pump inhibitor",
        "aliases": ["Prevacid", "Lanzo"],
    },
    {
        "generic_name": "Aluminum Hydroxide/Magnesium Hydroxide",
        "category": "acute",
        "common_brand_names": "Maalox, Gelusil, Ulgel",
        "therapeutic_class": "antacid",
        "aliases": ["Maalox", "Gelusil", "Ulgel", "Aluminium Hydroxide"],
    },
    {
        "generic_name": "Sucralfate",
        "category": "acute",
        "common_brand_names": "Carafate, Ulcyte",
        "therapeutic_class": "antiulcer",
        "aliases": ["Carafate", "Ulcyte"],
    },

    # ── Acute: Antifungals (more) ─────────────────────────────────
    {
        "generic_name": "Ketoconazole",
        "category": "acute",
        "common_brand_names": "Nizoral",
        "therapeutic_class": "antifungal",
        "aliases": ["Nizoral"],
    },
    {
        "generic_name": "Itraconazole",
        "category": "acute",
        "common_brand_names": "Sporanox, Itraco",
        "therapeutic_class": "antifungal",
        "aliases": ["Sporanox", "Itraco"],
    },
    {
        "generic_name": "Nystatin",
        "category": "acute",
        "common_brand_names": "Mycostatin, Nystan",
        "therapeutic_class": "antifungal",
        "aliases": ["Mycostatin", "Nystan"],
    },
    {
        "generic_name": "Miconazole Cream",
        "category": "acute",
        "common_brand_names": "Daktarin",
        "therapeutic_class": "antifungal (topical)",
        "aliases": ["Daktarin"],
    },

    # ── Acute: Antivirals ────────────────────────────────────────
    {
        "generic_name": "Acyclovir",
        "category": "acute",
        "common_brand_names": "Zovirax",
        "therapeutic_class": "antiviral",
        "aliases": ["Zovirax", "Aciclovir"],
    },
    {
        "generic_name": "Oseltamivir",
        "category": "acute",
        "common_brand_names": "Tamiflu",
        "therapeutic_class": "antiviral (influenza)",
        "aliases": ["Tamiflu"],
    },

    # ── Corticosteroids ──────────────────────────────────────────
    {
        "generic_name": "Dexamethasone",
        "category": "either",
        "common_brand_names": "Decadron, Dexona",
        "therapeutic_class": "corticosteroid",
        "aliases": ["Decadron", "Dexona", "Dex"],
    },
    {
        "generic_name": "Betamethasone Cream",
        "category": "either",
        "common_brand_names": "Betnovate, Diprosone",
        "therapeutic_class": "topical corticosteroid",
        "aliases": ["Betnovate", "Diprosone"],
    },
    {
        "generic_name": "Hydrocortisone Cream",
        "category": "acute",
        "common_brand_names": "Cortisone, Hydrocort",
        "therapeutic_class": "topical corticosteroid",
        "aliases": ["Cortisone Cream", "HC Cream"],
    },

    # ── Chronic: More Cardiovascular ─────────────────────────────
    {
        "generic_name": "Bisoprolol",
        "category": "chronic",
        "common_brand_names": "Concor, Bisol",
        "therapeutic_class": "beta-blocker",
        "aliases": ["Concor", "Bisol"],
    },
    {
        "generic_name": "Spironolactone",
        "category": "chronic",
        "common_brand_names": "Aldactone",
        "therapeutic_class": "potassium-sparing diuretic",
        "aliases": ["Aldactone"],
    },
    {
        "generic_name": "Ramipril",
        "category": "chronic",
        "common_brand_names": "Tritace, Altace",
        "therapeutic_class": "antihypertensive (ACE inhibitor)",
        "aliases": ["Tritace", "Altace"],
    },
    {
        "generic_name": "Enalapril",
        "category": "chronic",
        "common_brand_names": "Vasotec, Enacard",
        "therapeutic_class": "antihypertensive (ACE inhibitor)",
        "aliases": ["Vasotec", "Enacard"],
    },
    {
        "generic_name": "Propranolol",
        "category": "chronic",
        "common_brand_names": "Inderal",
        "therapeutic_class": "beta-blocker",
        "aliases": ["Inderal"],
    },
    {
        "generic_name": "Verapamil",
        "category": "chronic",
        "common_brand_names": "Isoptin, Verelan",
        "therapeutic_class": "calcium channel blocker",
        "aliases": ["Isoptin", "Verelan"],
    },
    {
        "generic_name": "Isosorbide Dinitrate",
        "category": "chronic",
        "common_brand_names": "Isordil, Sorbitrate",
        "therapeutic_class": "nitrate",
        "aliases": ["Isordil", "Sorbitrate"],
    },

    # ── Chronic: Psychiatry / Neurology (more) ───────────────────
    {
        "generic_name": "Risperidone",
        "category": "chronic",
        "common_brand_names": "Risperdal",
        "therapeutic_class": "antipsychotic",
        "aliases": ["Risperdal"],
    },
    {
        "generic_name": "Olanzapine",
        "category": "chronic",
        "common_brand_names": "Zyprexa",
        "therapeutic_class": "antipsychotic",
        "aliases": ["Zyprexa"],
    },
    {
        "generic_name": "Quetiapine",
        "category": "chronic",
        "common_brand_names": "Seroquel",
        "therapeutic_class": "antipsychotic",
        "aliases": ["Seroquel"],
    },
    {
        "generic_name": "Sertraline",
        "category": "chronic",
        "common_brand_names": "Zoloft",
        "therapeutic_class": "antidepressant (SSRI)",
        "aliases": ["Zoloft"],
    },
    {
        "generic_name": "Escitalopram",
        "category": "chronic",
        "common_brand_names": "Lexapro, Cipralex",
        "therapeutic_class": "antidepressant (SSRI)",
        "aliases": ["Lexapro", "Cipralex"],
    },
    {
        "generic_name": "Lamotrigine",
        "category": "chronic",
        "common_brand_names": "Lamictal",
        "therapeutic_class": "anticonvulsant",
        "aliases": ["Lamictal"],
    },
    {
        "generic_name": "Levetiracetam",
        "category": "chronic",
        "common_brand_names": "Keppra",
        "therapeutic_class": "anticonvulsant",
        "aliases": ["Keppra"],
    },
    {
        "generic_name": "Diazepam",
        "category": "either",
        "common_brand_names": "Valium",
        "therapeutic_class": "benzodiazepine",
        "requires_review": True,
        "aliases": ["Valium"],
    },
    {
        "generic_name": "Baclofen",
        "category": "either",
        "common_brand_names": "Lioresal",
        "therapeutic_class": "muscle relaxant",
        "aliases": ["Lioresal"],
    },

    # ── Antituberculosis ─────────────────────────────────────────
    {
        "generic_name": "Rifampicin",
        "category": "acute",
        "common_brand_names": "Rifadin, Rimactane",
        "therapeutic_class": "antituberculosis",
        "requires_review": True,
        "aliases": ["Rifadin", "Rimactane", "Rifampin"],
    },
    {
        "generic_name": "Isoniazid",
        "category": "acute",
        "common_brand_names": "INH, Rimifon",
        "therapeutic_class": "antituberculosis",
        "requires_review": True,
        "aliases": ["INH", "Rimifon"],
    },
    {
        "generic_name": "Pyrazinamide",
        "category": "acute",
        "common_brand_names": "Zinamide",
        "therapeutic_class": "antituberculosis",
        "requires_review": True,
        "aliases": ["Zinamide", "PZA"],
    },
    {
        "generic_name": "Ethambutol",
        "category": "acute",
        "common_brand_names": "Myambutol",
        "therapeutic_class": "antituberculosis",
        "requires_review": True,
        "aliases": ["Myambutol", "EMB"],
    },

    # ── Chronic: Diabetes (more) ─────────────────────────────────
    {
        "generic_name": "Empagliflozin",
        "category": "chronic",
        "common_brand_names": "Jardiance",
        "therapeutic_class": "antidiabetic (SGLT2 inhibitor)",
        "aliases": ["Jardiance"],
    },
    {
        "generic_name": "Dapagliflozin",
        "category": "chronic",
        "common_brand_names": "Farxiga, Forxiga",
        "therapeutic_class": "antidiabetic (SGLT2 inhibitor)",
        "aliases": ["Farxiga", "Forxiga"],
    },
    {
        "generic_name": "Liraglutide",
        "category": "chronic",
        "common_brand_names": "Victoza",
        "therapeutic_class": "antidiabetic (GLP-1)",
        "aliases": ["Victoza"],
    },

    # ── Vitamins / Minerals (more) ────────────────────────────────
    {
        "generic_name": "Zinc Sulphate",
        "category": "acute",
        "common_brand_names": "Zincovit, Zn Tabs",
        "therapeutic_class": "zinc supplement",
        "aliases": ["Zincovit", "Zinc Tablets"],
    },
    {
        "generic_name": "Vitamin A",
        "category": "acute",
        "common_brand_names": "Aquasol A, Retinol",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Retinol", "Aquasol A"],
    },
    {
        "generic_name": "Vitamin D3",
        "category": "either",
        "common_brand_names": "Cholecalciferol",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Cholecalciferol", "Vit D3"],
    },
    {
        "generic_name": "Ferrous Gluconate",
        "category": "either",
        "common_brand_names": "Fergon",
        "therapeutic_class": "iron supplement",
        "aliases": ["Fergon"],
    },
    {
        "generic_name": "Calcium Gluconate",
        "category": "either",
        "common_brand_names": "Calcium-Sandoz",
        "therapeutic_class": "calcium supplement",
        "aliases": ["Calcium-Sandoz"],
    },
    {
        "generic_name": "Magnesium Sulphate",
        "category": "acute",
        "common_brand_names": "Epsom Salt (IV)",
        "therapeutic_class": "electrolyte / anticonvulsant",
        "requires_review": True,
        "aliases": ["MgSO4", "Epsom Salt"],
    },

    # ── Respiratory (more) ───────────────────────────────────────
    {
        "generic_name": "Ipratropium Bromide Inhaler",
        "category": "chronic",
        "common_brand_names": "Atrovent",
        "therapeutic_class": "bronchodilator (anticholinergic)",
        "aliases": ["Atrovent"],
    },
    {
        "generic_name": "Salbutamol Nebuliser Solution",
        "category": "acute",
        "common_brand_names": "Ventolin Nebules",
        "therapeutic_class": "bronchodilator",
        "aliases": ["Ventolin Nebules", "Salbutamol Neb"],
    },
    {
        "generic_name": "Theophylline",
        "category": "chronic",
        "common_brand_names": "Uniphyllin, Nuelin",
        "therapeutic_class": "bronchodilator (xanthine)",
        "aliases": ["Uniphyllin", "Nuelin"],
    },

    # ── Reproductive / Hormones ──────────────────────────────────
    {
        "generic_name": "Levonorgestrel (Emergency)",
        "category": "acute",
        "common_brand_names": "Postinor-2, Escapelle",
        "therapeutic_class": "emergency contraceptive",
        "aliases": ["Postinor-2", "Postinor", "Escapelle"],
    },
    {
        "generic_name": "Norethisterone",
        "category": "either",
        "common_brand_names": "Primolut-N",
        "therapeutic_class": "progestogen",
        "aliases": ["Primolut-N", "Primolut"],
    },
    {
        "generic_name": "Misoprostol",
        "category": "acute",
        "common_brand_names": "Cytotec",
        "therapeutic_class": "prostaglandin",
        "requires_review": True,
        "aliases": ["Cytotec"],
    },

    # ── Antiparasitics / Dermatology ─────────────────────────────
    {
        "generic_name": "Ivermectin",
        "category": "acute",
        "common_brand_names": "Mectizan, Stromectol",
        "therapeutic_class": "antiparasitic",
        "aliases": ["Mectizan", "Stromectol"],
    },
    {
        "generic_name": "Praziquantel",
        "category": "acute",
        "common_brand_names": "Biltricide",
        "therapeutic_class": "anthelmintic",
        "aliases": ["Biltricide"],
    },
    {
        "generic_name": "Permethrin Cream",
        "category": "acute",
        "common_brand_names": "Lyclear",
        "therapeutic_class": "antiparasitic (topical)",
        "aliases": ["Lyclear"],
    },
    {
        "generic_name": "Benzyl Benzoate",
        "category": "acute",
        "common_brand_names": "Ascabiol",
        "therapeutic_class": "antiparasitic (topical)",
        "aliases": ["Ascabiol"],
    },

    # ── Ophthalmics (more) ───────────────────────────────────────
    {
        "generic_name": "Tobramycin Eye Drops",
        "category": "acute",
        "common_brand_names": "Tobrex",
        "therapeutic_class": "ophthalmic antibiotic",
        "aliases": ["Tobrex"],
    },
    {
        "generic_name": "Prednisolone Eye Drops",
        "category": "acute",
        "common_brand_names": "Pred Forte",
        "therapeutic_class": "ophthalmic corticosteroid",
        "aliases": ["Pred Forte"],
    },
    {
        "generic_name": "Timolol Eye Drops",
        "category": "chronic",
        "common_brand_names": "Timoptol",
        "therapeutic_class": "ophthalmic beta-blocker (glaucoma)",
        "aliases": ["Timoptol"],
    },
]


def get_seed_drugs() -> list[dict]:
    """Return the seed drug list. Each entry has keys:
    generic_name, category, common_brand_names, therapeutic_class,
    requires_review (optional), aliases (optional).
    """
    return SEED_DRUGS
