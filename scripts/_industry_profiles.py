"""
Industry profiles used by the seed_industry_data management command.

Each profile specifies:
- name: Display name for the organization
- categories: Procurement categories with spend share, amount distribution (log-normal), and tier-1/tier-2 named suppliers
- tail_supplier_templates: Templates for synthesizing tail vendors (regional businesses)
- departments: Org units that issue PRs
- cost_centers: Budget codes
- payment_terms: Realistic terms for the industry
- seasonality: 12-element monthly multiplier (Jan..Dec), mean ~1.0
- policies: Industry-appropriate procurement policies
"""

HEALTHCARE = {
    "name": "Mercy Regional Medical Center",
    "categories": [
        {
            "name": "Pharmaceuticals",
            "spend_share": 0.32,
            "amount_mu": 8.0,
            "amount_sigma": 1.4,
            "named_suppliers": [
                "Cardinal Health Pharmaceutical", "McKesson Corporation", "AmerisourceBergen",
                "Pfizer Inc.", "Merck & Co.", "Johnson & Johnson Pharmaceutical", "AbbVie Inc.",
                "Bristol-Myers Squibb", "Eli Lilly and Company", "AstraZeneca Pharmaceuticals",
                "Novartis Pharmaceuticals", "Sanofi US", "Gilead Sciences", "Amgen Inc.",
                "Teva Pharmaceutical USA", "Viatris Inc.", "Roche Pharmaceuticals",
            ],
        },
        {
            "name": "Medical/Surgical Supplies",
            "spend_share": 0.17,
            "amount_mu": 6.7,
            "amount_sigma": 1.3,
            "named_suppliers": [
                "Medline Industries", "Owens & Minor", "Cardinal Health Medical",
                "Henry Schein Medical", "BD (Becton Dickinson)", "3M Health Care",
                "Smith & Nephew", "Halyard Health", "Mölnlycke Health Care", "B. Braun Medical",
                "Terumo Medical", "ConvaTec", "Covidien (Medtronic)",
            ],
        },
        {
            "name": "Medical Equipment",
            "spend_share": 0.10,
            "amount_mu": 10.5,
            "amount_sigma": 1.8,
            "named_suppliers": [
                "GE Healthcare", "Philips Healthcare", "Siemens Healthineers",
                "Stryker Corporation", "Hillrom (Baxter)", "Dräger Medical",
                "Mindray North America", "Welch Allyn (Hillrom)", "Masimo Corporation",
                "Nihon Kohden America",
            ],
        },
        {
            "name": "Laboratory",
            "spend_share": 0.07,
            "amount_mu": 7.6,
            "amount_sigma": 1.4,
            "named_suppliers": [
                "Thermo Fisher Scientific", "Roche Diagnostics", "Abbott Diagnostics",
                "Beckman Coulter (Danaher)", "BD Diagnostics", "Sysmex America",
                "Bio-Rad Laboratories", "Quest Diagnostics", "Siemens Healthineers Diagnostics",
                "Ortho Clinical Diagnostics",
            ],
        },
        {
            "name": "Imaging & Radiology",
            "spend_share": 0.06,
            "amount_mu": 9.6,
            "amount_sigma": 1.6,
            "named_suppliers": [
                "GE Healthcare Imaging", "Philips Imaging", "Siemens Imaging",
                "Canon Medical Systems", "Hologic Inc.", "Varian Medical Systems",
                "Fujifilm Medical Systems", "Bayer HealthCare Radiology", "Guerbet LLC",
                "Bracco Diagnostics",
            ],
        },
        {
            "name": "Implants & Prosthetics",
            "spend_share": 0.06,
            "amount_mu": 9.0,
            "amount_sigma": 1.5,
            "named_suppliers": [
                "Medtronic Cardiovascular", "Boston Scientific", "Abbott Vascular",
                "Edwards Lifesciences", "Zimmer Biomet", "Stryker Orthopaedics",
                "DePuy Synthes (J&J)", "Smith & Nephew Orthopaedics", "Arthrex Inc.",
                "Wright Medical",
            ],
        },
        {
            "name": "PPE & Infection Control",
            "spend_share": 0.04,
            "amount_mu": 6.2,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "Medline PPE", "Cardinal Health PPE", "Kimberly-Clark Professional",
                "Halyard Health PPE", "Honeywell Safety", "3M Infection Prevention",
                "Ansell Healthcare", "Ecolab Healthcare", "STERIS Corporation",
            ],
        },
        {
            "name": "IT & EMR",
            "spend_share": 0.05,
            "amount_mu": 8.5,
            "amount_sigma": 1.7,
            "named_suppliers": [
                "Epic Systems Corporation", "Oracle Health (Cerner)", "MEDITECH",
                "Allscripts Healthcare", "athenahealth", "Imprivata", "Microsoft Corporation",
                "Dell Technologies Healthcare", "HPE Healthcare", "Cisco Systems",
                "Nuance Communications",
            ],
        },
        {
            "name": "Food Service",
            "spend_share": 0.03,
            "amount_mu": 8.9,
            "amount_sigma": 0.9,
            "named_suppliers": [
                "Sysco Corporation", "US Foods", "Gordon Food Service", "Performance Food Group",
                "Aramark Healthcare Food", "Morrison Healthcare (Compass)",
            ],
        },
        {
            "name": "Linen & Laundry",
            "spend_share": 0.02,
            "amount_mu": 8.3,
            "amount_sigma": 0.7,
            "named_suppliers": [
                "Cintas Healthcare", "Crothall Healthcare", "ImageFIRST Healthcare Laundry",
                "Angelica Corporation", "ALSCO Medical",
            ],
        },
        {
            "name": "Medical Gases",
            "spend_share": 0.02,
            "amount_mu": 8.0,
            "amount_sigma": 0.8,
            "named_suppliers": [
                "Airgas Healthcare", "Air Liquide Healthcare", "Linde Healthcare (Praxair)",
                "Matheson Tri-Gas",
            ],
        },
        {
            "name": "Facilities & Maintenance",
            "spend_share": 0.03,
            "amount_mu": 7.6,
            "amount_sigma": 1.6,
            "named_suppliers": [
                "Johnson Controls", "Siemens Building Technologies", "Honeywell Building",
                "Trane Technologies", "Carrier Global", "Schneider Electric", "Grainger",
            ],
        },
        {
            "name": "Professional Services",
            "spend_share": 0.02,
            "amount_mu": 8.5,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "Deloitte Healthcare Consulting", "McKinsey & Company", "Ernst & Young Healthcare",
                "KPMG Healthcare Advisory", "Premier Inc. Advisory", "Vizient Consulting",
                "Huron Consulting Healthcare",
            ],
        },
        {
            "name": "Environmental Services",
            "spend_share": 0.01,
            "amount_mu": 7.6,
            "amount_sigma": 0.9,
            "named_suppliers": [
                "Ecolab Inc.", "Diversey Inc.", "Crothall Environmental",
                "ABM Healthcare Services", "Stericycle",
            ],
        },
        {
            "name": "Office Supplies",
            "spend_share": 0.005,
            "amount_mu": 5.3,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "Staples Business Advantage", "Office Depot Business", "Amazon Business",
                "Quill Corporation",
            ],
        },
    ],
    "tail_supplier_templates": [
        ("{city} Medical Supply Co.", 80),
        ("{city} Pharmacy Services LLC", 40),
        ("{region} Biomedical Services", 30),
        ("{city} Cleaning & Janitorial", 40),
        ("{city} Linen Services", 25),
        ("{region} Ambulance Supply", 20),
        ("{city} HVAC & Mechanical", 30),
        ("{city} Healthcare Staffing", 30),
        ("{city} Medical Waste Disposal", 20),
        ("{region} Laboratory Associates", 35),
        ("{region} Radiology Partners", 25),
        ("{region} Anesthesia Services", 20),
        ("{city} Surgical Instruments", 30),
        ("{region} Home Medical Equipment", 30),
        ("{city} Printing & Forms", 20),
    ],
    "departments": [
        "Emergency Department", "Operating Room", "Intensive Care Unit", "Laboratory",
        "Pharmacy", "Radiology", "Cardiology", "Oncology", "Maternity & NICU",
        "Orthopedics", "Facilities", "Information Technology", "Environmental Services",
        "Food & Nutrition", "Supply Chain", "Nursing Administration",
    ],
    "cost_center_prefix": "MRMC",
    "payment_terms": [("Net 30", 30), ("Net 45", 45), ("Net 60", 60), ("2/10 Net 30", 30), ("Net 15", 15)],
    "seasonality": [1.12, 1.10, 1.05, 1.00, 0.98, 0.93, 0.90, 0.92, 1.00, 1.08, 1.12, 1.15],
    "policies": [
        {
            "name": "340B Pharmaceutical Compliance",
            "description": "Pharmaceutical purchases must flow through 340B-qualified channels when eligible.",
            "rules": {"restricted_categories": ["Pharmaceuticals"], "require_contract": True,
                      "required_approval_threshold": 25000},
        },
        {
            "name": "GPO Preferred Vendor Policy",
            "description": "Med/Surg and PPE spend must prioritize Vizient, Premier, or HealthTrust GPO vendors.",
            "rules": {"restricted_categories": ["Medical/Surgical Supplies", "PPE & Infection Control"],
                      "preferred_suppliers_required": True},
        },
        {
            "name": "Capital Equipment Approval",
            "description": "Medical Equipment and Imaging capital purchases over $50K require executive approval.",
            "rules": {"max_transaction_amount": 50000, "required_approval_threshold": 50000,
                      "restricted_categories": ["Medical Equipment", "Imaging & Radiology"]},
        },
        {
            "name": "Implant Value Analysis Review",
            "description": "Implants and prosthetics must pass Value Analysis Committee review before purchase.",
            "rules": {"restricted_categories": ["Implants & Prosthetics"], "require_contract": True},
        },
    ],
    "tail_cities": [
        "Riverside", "Westfield", "Lakeside", "Oakwood", "Springfield", "Millbrook",
        "Fairview", "Northfield", "Harbor", "Summit", "Glendale", "Pinehurst",
        "Crestview", "Meridian", "Eastgate", "Ashford", "Brookline", "Valley",
    ],
    "tail_regions": ["Midwest", "Tri-State", "Regional", "Metropolitan", "Coastal", "Northern"],
}


HIGHER_ED = {
    "name": "Pacific State University",
    "categories": [
        {
            "name": "Research Lab Equipment",
            "spend_share": 0.13,
            "amount_mu": 10.0,
            "amount_sigma": 1.8,
            "named_suppliers": [
                "Thermo Fisher Scientific", "Agilent Technologies", "Waters Corporation",
                "PerkinElmer", "Bruker Corporation", "Zeiss Research Microscopy",
                "Leica Microsystems", "Olympus Life Science", "Nikon Instruments",
                "Bio-Rad Laboratories", "Beckman Coulter Life Sciences", "Illumina Inc.",
            ],
        },
        {
            "name": "Lab Supplies & Consumables",
            "spend_share": 0.11,
            "amount_mu": 6.5,
            "amount_sigma": 1.4,
            "named_suppliers": [
                "MilliporeSigma (Sigma-Aldrich)", "Thermo Fisher Scientific",
                "VWR International (Avantor)", "Fisher Scientific", "Carolina Biological Supply",
                "New England Biolabs", "Qiagen", "Promega Corporation", "Takara Bio",
                "Cell Signaling Technology", "Corning Incorporated", "Eppendorf",
            ],
        },
        {
            "name": "IT Equipment & Software",
            "spend_share": 0.13,
            "amount_mu": 7.5,
            "amount_sigma": 1.7,
            "named_suppliers": [
                "Apple Inc.", "Dell Technologies", "Lenovo Group", "HP Inc.",
                "CDW Government (CDW-G)", "Insight Enterprises", "Microsoft Corporation",
                "Adobe Systems", "Autodesk Inc.", "MathWorks", "SAS Institute",
                "Ellucian Company", "Workday Inc.", "Instructure (Canvas)",
                "Oracle Higher Education", "Zones Inc.", "SHI International",
            ],
        },
        {
            "name": "Library Resources",
            "spend_share": 0.05,
            "amount_mu": 9.5,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "Elsevier Science", "Wiley Publishing", "Springer Nature", "EBSCO Information Services",
                "JSTOR / ITHAKA", "ProQuest LLC", "Taylor & Francis Group", "SAGE Publications",
                "OCLC Inc.", "Clarivate Analytics",
            ],
        },
        {
            "name": "Facilities & Construction",
            "spend_share": 0.25,
            "amount_mu": 10.5,
            "amount_sigma": 2.0,
            "named_suppliers": [
                "Skanska USA", "Turner Construction", "Whiting-Turner", "Gilbane Building",
                "Clark Construction", "Johnson Controls", "Trane Technologies", "Schneider Electric",
                "Grainger", "Ferguson Enterprises", "HD Supply", "Siemens Building Technologies",
                "Carrier Global",
            ],
        },
        {
            "name": "Dining Services",
            "spend_share": 0.07,
            "amount_mu": 9.0,
            "amount_sigma": 0.9,
            "named_suppliers": [
                "Sodexo Education", "Aramark Campus Dining", "Chartwells Higher Education (Compass)",
                "Bon Appétit Management", "Sysco Corporation", "US Foods Education",
            ],
        },
        {
            "name": "Athletics",
            "spend_share": 0.04,
            "amount_mu": 7.5,
            "amount_sigma": 1.5,
            "named_suppliers": [
                "Nike Team Sports", "Under Armour Athletics", "Adidas Team", "Rawlings Sporting Goods",
                "Riddell Sports", "BSN Sports", "Wilson Sporting Goods", "Spalding",
                "Gatorade (PepsiCo)",
            ],
        },
        {
            "name": "Instructional Materials",
            "spend_share": 0.03,
            "amount_mu": 6.5,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "Pearson Education", "Cengage Learning", "McGraw-Hill Education",
                "Follett Higher Education", "Barnes & Noble College", "Macmillan Learning",
                "W.W. Norton & Company",
            ],
        },
        {
            "name": "Professional Services",
            "spend_share": 0.07,
            "amount_mu": 8.5,
            "amount_sigma": 1.3,
            "named_suppliers": [
                "Deloitte Higher Education", "Ernst & Young Academic Services", "KPMG Advisory",
                "Huron Consulting Group", "Accenture Higher Education", "Gartner Research",
                "Alvarez & Marsal",
            ],
        },
        {
            "name": "Utilities",
            "spend_share": 0.05,
            "amount_mu": 9.5,
            "amount_sigma": 0.6,
            "named_suppliers": [
                "Pacific Gas & Electric", "Southern California Edison", "AT&T Business",
                "Verizon Business", "Comcast Business", "Waste Management Inc.",
            ],
        },
        {
            "name": "Travel & Conferences",
            "spend_share": 0.02,
            "amount_mu": 6.0,
            "amount_sigma": 0.8,
            "named_suppliers": [
                "Concur (SAP)", "American Express Global Business Travel", "BCD Travel",
                "Delta Air Lines", "United Airlines", "Marriott Hotels",
                "Hilton Hotels & Resorts", "Enterprise Rent-A-Car",
            ],
        },
        {
            "name": "Student Life & Activities",
            "spend_share": 0.015,
            "amount_mu": 6.5,
            "amount_sigma": 1.1,
            "named_suppliers": [
                "Herff Jones", "Jostens Inc.", "Oak Hall Cap & Gown",
                "Campus Labs", "ModoLabs", "Presence (Student Engagement)",
            ],
        },
        {
            "name": "Marketing & Communications",
            "spend_share": 0.015,
            "amount_mu": 7.0,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "RR Donnelley", "Vistaprint", "Carnegie Dartlet (Carnegie Communications)",
                "EAB Marketing", "Ruffalo Noel Levitz",
            ],
        },
        {
            "name": "Office Supplies",
            "spend_share": 0.005,
            "amount_mu": 5.0,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "Staples Business Advantage", "Office Depot Business", "Amazon Business",
                "Quill Corporation",
            ],
        },
        {
            "name": "Transportation",
            "spend_share": 0.01,
            "amount_mu": 7.5,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "Enterprise Fleet Management", "First Transit", "National Express Transit",
                "Cummins Inc.", "Bridgestone Fleet",
            ],
        },
        {
            "name": "Student Health Services",
            "spend_share": 0.015,
            "amount_mu": 7.0,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "Henry Schein Medical", "McKesson Medical-Surgical", "Medline Industries",
                "Walgreens Boots Alliance", "CVS Health Corporation",
            ],
        },
    ],
    "tail_supplier_templates": [
        ("{city} Scientific Supply Co.", 60),
        ("{region} Research Services LLC", 35),
        ("{city} Print & Design", 35),
        ("{city} Office Services", 30),
        ("{region} Construction & Development", 30),
        ("{city} Landscaping & Grounds", 20),
        ("{city} Audio Visual Services", 25),
        ("{region} Academic Publishing", 20),
        ("{city} Catering Group", 30),
        ("{region} Security Services", 25),
        ("{city} IT Consulting Partners", 25),
        ("{region} Educational Technology", 20),
        ("{city} Moving & Storage", 20),
        ("{region} Law Firm Associates", 15),
        ("{city} Athletic Apparel Co.", 20),
    ],
    "departments": [
        "Biology", "Chemistry", "Physics", "Engineering", "Computer Science",
        "Business School", "School of Medicine", "School of Law",
        "Arts & Humanities", "Mathematics", "Library", "Information Technology",
        "Facilities Management", "Athletics", "Student Affairs", "Dining Services",
        "Registrar", "Admissions", "Research Administration",
    ],
    "cost_center_prefix": "PSU",
    "payment_terms": [("Net 30", 30), ("Net 45", 45), ("Net 60", 60), ("Net 15", 15)],
    "seasonality": [1.00, 0.90, 0.95, 0.90, 0.75, 1.55, 1.15, 1.65, 1.25, 1.05, 1.00, 0.75],
    "policies": [
        {
            "name": "Federal Grant Compliance (Uniform Guidance)",
            "description": "Purchases funded by NSF/NIH/DOE grants must follow 2 CFR 200 Uniform Guidance thresholds and documentation.",
            "rules": {"required_approval_threshold": 10000, "require_contract": True,
                      "restricted_categories": ["Research Lab Equipment", "Lab Supplies & Consumables"]},
        },
        {
            "name": "Consortium Preferred Vendor (E&I / NASPO)",
            "description": "IT and office category spend should use E&I Cooperative or NASPO ValuePoint contracts.",
            "rules": {"restricted_categories": ["IT Equipment & Software", "Office Supplies"],
                      "preferred_suppliers_required": True},
        },
        {
            "name": "PI Direct Purchase Limit",
            "description": "Principal Investigators may approve direct purchases up to $5,000 without additional review.",
            "rules": {"max_transaction_amount": 5000, "required_approval_threshold": 5000},
        },
        {
            "name": "Capital Construction Authorization",
            "description": "Facilities & Construction projects over $250K require Board of Trustees authorization.",
            "rules": {"max_transaction_amount": 250000, "required_approval_threshold": 250000,
                      "restricted_categories": ["Facilities & Construction"]},
        },
    ],
    "tail_cities": [
        "Berkeley", "Davis", "Palo Alto", "Westwood", "Irvine", "Long Beach",
        "San Diego", "Sacramento", "Monterey", "Santa Barbara", "Humboldt",
        "Chico", "Fresno", "Oakland", "Pomona", "Stanislaus",
    ],
    "tail_regions": ["West Coast", "Pacific", "Bay Area", "Southern California", "Coastal"],
}


MANUFACTURING = {
    "name": "Apex Manufacturing Co.",
    "categories": [
        {
            "name": "Raw Materials",
            "spend_share": 0.28,
            "amount_mu": 8.5,
            "amount_sigma": 1.5,
            "named_suppliers": [
                "Nucor Corporation", "Steel Dynamics Inc.", "Cleveland-Cliffs",
                "ArcelorMittal USA", "U.S. Steel", "Alcoa Corporation",
                "Novelis Inc.", "Reliance Steel & Aluminum", "Ryerson Holding",
                "Dow Chemical Company", "BASF Corporation", "LyondellBasell Industries",
                "Eastman Chemical Company", "Covestro LLC", "DuPont de Nemours",
                "Olin Corporation", "Weyerhaeuser Company",
            ],
        },
        {
            "name": "Components & Parts",
            "spend_share": 0.16,
            "amount_mu": 7.0,
            "amount_sigma": 1.3,
            "named_suppliers": [
                "Rockwell Automation", "ABB Motors & Generators", "Siemens Industry",
                "Schneider Electric", "Eaton Electrical", "Mitsubishi Electric Automation",
                "Omron Automation", "Phoenix Contact", "Parker Hannifin Corporation",
                "SKF USA", "Timken Company", "Bosch Rexroth", "Dana Incorporated",
                "Fastenal Industrial Supply", "Würth Industry North America",
                "Bossard North America",
            ],
        },
        {
            "name": "MRO Supplies",
            "spend_share": 0.10,
            "amount_mu": 5.8,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "W.W. Grainger", "MSC Industrial Direct", "Fastenal Company",
                "McMaster-Carr Supply", "HD Supply Industrial", "Global Industrial",
                "Motion Industries", "Applied Industrial Technologies",
                "Kaman Industrial Technologies",
            ],
        },
        {
            "name": "Industrial Equipment (Capital)",
            "spend_share": 0.08,
            "amount_mu": 11.0,
            "amount_sigma": 1.8,
            "named_suppliers": [
                "DMG Mori USA", "Haas Automation", "Makino Inc.", "Mazak Corporation",
                "Okuma America", "Fanuc America Robotics", "ABB Robotics",
                "KUKA Robotics", "Yaskawa Motoman", "Atlas Copco Industrial",
            ],
        },
        {
            "name": "Contract Manufacturing",
            "spend_share": 0.06,
            "amount_mu": 10.0,
            "amount_sigma": 1.4,
            "named_suppliers": [
                "Jabil Inc.", "Flex Ltd.", "Celestica Inc.", "Plexus Corp",
                "Benchmark Electronics", "Sanmina Corporation",
            ],
        },
        {
            "name": "Logistics & Freight",
            "spend_share": 0.06,
            "amount_mu": 6.8,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "C.H. Robinson Worldwide", "J.B. Hunt Transport", "FedEx Freight",
                "UPS Supply Chain Solutions", "XPO Logistics", "Old Dominion Freight Line",
                "Schneider National", "Landstar System", "Expeditors International",
            ],
        },
        {
            "name": "Facilities & Utilities",
            "spend_share": 0.05,
            "amount_mu": 8.5,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "Johnson Controls", "Trane Technologies", "Carrier Global",
                "Honeywell Building Technologies", "Siemens Building Technologies",
                "Schneider Electric Buildings", "NRG Energy", "Constellation Energy",
            ],
        },
        {
            "name": "IT/OT Systems",
            "spend_share": 0.04,
            "amount_mu": 8.5,
            "amount_sigma": 1.6,
            "named_suppliers": [
                "Rockwell Automation (PLC)", "Siemens Digital Industries",
                "AVEVA (Wonderware)", "GE Digital", "PTC Inc.", "Dassault Systèmes",
                "SAP Industry Cloud", "Oracle Manufacturing Cloud", "Microsoft Corporation",
                "Dell Technologies Industrial", "Cisco Systems", "Hexagon Manufacturing Intelligence",
            ],
        },
        {
            "name": "Professional Services",
            "spend_share": 0.04,
            "amount_mu": 8.8,
            "amount_sigma": 1.2,
            "named_suppliers": [
                "Deloitte Manufacturing Consulting", "McKinsey & Company",
                "Accenture Industry X", "KPMG Manufacturing Advisory",
                "Ernst & Young Manufacturing", "PwC Industrial Services",
                "Boston Consulting Group", "Kearney Operations",
            ],
        },
        {
            "name": "Packaging",
            "spend_share": 0.03,
            "amount_mu": 7.0,
            "amount_sigma": 1.1,
            "named_suppliers": [
                "Packaging Corporation of America", "International Paper",
                "WestRock Company", "Sealed Air Corporation", "Sonoco Products",
                "Berry Global", "Graphic Packaging International", "Pratt Industries",
            ],
        },
        {
            "name": "Tooling & Dies",
            "spend_share": 0.03,
            "amount_mu": 8.0,
            "amount_sigma": 1.5,
            "named_suppliers": [
                "Sandvik Coromant", "Kennametal Inc.", "Iscar Metals",
                "Walter Tools USA", "Mitsubishi Materials USA", "Seco Tools",
                "OSG Corporation", "Dormer Pramet",
            ],
        },
        {
            "name": "Quality & Metrology",
            "spend_share": 0.02,
            "amount_mu": 8.5,
            "amount_sigma": 1.4,
            "named_suppliers": [
                "Hexagon Metrology", "Keyence Corporation", "Mitutoyo America",
                "Zeiss Industrial Metrology", "FARO Technologies", "Renishaw",
                "The L.S. Starrett Company",
            ],
        },
        {
            "name": "Safety & PPE",
            "spend_share": 0.02,
            "amount_mu": 6.2,
            "amount_sigma": 1.1,
            "named_suppliers": [
                "3M Safety Division", "Honeywell Safety Products", "MSA Safety",
                "Ansell Industrial", "Kimberly-Clark Professional", "DuPont Personal Protection",
                "Bullard", "Uvex Safety",
            ],
        },
        {
            "name": "Lubricants & Chemicals",
            "spend_share": 0.02,
            "amount_mu": 6.8,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "ExxonMobil Industrial Lubricants", "Shell Lubricants",
                "Chevron Industrial Lubricants", "Castrol Industrial",
                "Quaker Houghton", "Total Energies Industrial",
            ],
        },
        {
            "name": "Office Supplies",
            "spend_share": 0.01,
            "amount_mu": 5.0,
            "amount_sigma": 1.0,
            "named_suppliers": [
                "Staples Business Advantage", "Office Depot Business",
                "Amazon Business", "Quill Corporation",
            ],
        },
    ],
    "tail_supplier_templates": [
        ("{city} Industrial Supply Co.", 60),
        ("{region} Tooling & Machine Shop", 35),
        ("{city} Metal Fabricators", 40),
        ("{city} Hydraulic & Pneumatic Services", 30),
        ("{region} Welding Services", 25),
        ("{city} Electrical Contractors", 30),
        ("{city} Freight Services", 35),
        ("{region} Safety Equipment", 20),
        ("{city} Industrial Cleaning", 25),
        ("{city} Packaging Materials", 25),
        ("{region} Transport & Logistics", 30),
        ("{city} Instrumentation & Calibration", 20),
        ("{city} Industrial Gases", 20),
        ("{region} Machine Tool Repair", 25),
        ("{city} Conveyor Systems", 20),
    ],
    "departments": [
        "Production", "Maintenance", "Quality", "Engineering", "Supply Chain",
        "Logistics", "R&D", "Operations", "EHS", "Plant Management",
        "Tooling", "Information Technology", "Finance", "Human Resources", "Procurement",
    ],
    "cost_center_prefix": "MFG",
    "payment_terms": [("Net 30", 30), ("Net 45", 45), ("Net 60", 60), ("2/10 Net 30", 30)],
    "seasonality": [1.05, 1.00, 1.10, 1.15, 1.20, 1.20, 0.75, 0.95, 1.15, 1.20, 1.05, 1.35],
    "policies": [
        {
            "name": "Supplier Quality Qualification (PPAP / ISO 9001)",
            "description": "Raw Materials and Components suppliers must hold current PPAP or ISO 9001 qualification and active quality agreement.",
            "rules": {"require_contract": True,
                      "restricted_categories": ["Raw Materials", "Components & Parts"],
                      "preferred_suppliers_required": True},
        },
        {
            "name": "Capital Equipment Authorization",
            "description": "Industrial Equipment purchases over $100K require executive CapEx committee approval.",
            "rules": {"max_transaction_amount": 100000,
                      "required_approval_threshold": 100000,
                      "restricted_categories": ["Industrial Equipment (Capital)"]},
        },
        {
            "name": "Conflict Minerals & Materials Compliance",
            "description": "Raw material sourcing requires documented conflict-minerals and trade compliance disclosures.",
            "rules": {"require_contract": True,
                      "restricted_categories": ["Raw Materials"]},
        },
        {
            "name": "MRO Single-PO Cap",
            "description": "Maintenance/Repair/Operations purchases capped at $25K per PO to prevent unplanned shutdown overruns.",
            "rules": {"max_transaction_amount": 25000,
                      "restricted_categories": ["MRO Supplies"]},
        },
    ],
    "tail_cities": [
        "Detroit", "Cleveland", "Akron", "Toledo", "Pittsburgh", "Youngstown",
        "Dayton", "Wichita", "Milwaukee", "Charlotte", "Greenville",
        "Chattanooga", "Birmingham", "Tulsa", "Columbus",
    ],
    "tail_regions": ["Rust Belt", "Midwest", "Southeast", "Great Lakes", "Mid-Atlantic", "Tri-State"],
}


PROFILES = {
    "healthcare": HEALTHCARE,
    "higher-ed": HIGHER_ED,
    "manufacturing": MANUFACTURING,
}
