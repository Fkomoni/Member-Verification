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
        "common_brand_names": "Wellman, Pregnacare",
        "therapeutic_class": "vitamin supplement",
        "aliases": ["Wellman", "Pregnacare", "Centrum"],
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
]


def get_seed_drugs() -> list[dict]:
    """Return the seed drug list. Each entry has keys:
    generic_name, category, common_brand_names, therapeutic_class,
    requires_review (optional), aliases (optional).
    """
    return SEED_DRUGS
