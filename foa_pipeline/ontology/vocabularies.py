"""
Controlled Ontology Vocabularies for FOA Semantic Tagging.

Four taxonomy dimensions:
  1. Research Domains — broad disciplinary areas
  2. Methods/Approaches — research methodologies
  3. Populations — target groups / demographics
  4. Sponsor Themes — cross-cutting funder priorities

Each vocabulary maps a canonical tag slug to:
  - label: Human-readable name
  - keywords: List of matching phrases for rule-based tagging
  - description: Brief description (used for embedding-based tagging)

Design principles:
  - Start small, extend later
  - Each tag has a unique slug
  - Keywords are lowercase for case-insensitive matching
"""

from typing import Dict, List


# 1. RESEARCH DOMAINS
RESEARCH_DOMAINS: Dict[str, dict] = {
    "artificial-intelligence": {
        "label": "Artificial Intelligence",
        "keywords": [
            "artificial intelligence",
            "ai systems",
            "ai research",
            "intelligent systems",
            "autonomous systems",
        ],
        "description": "Research on artificial intelligence, intelligent agents, and AI systems.",
    },
    "machine-learning": {
        "label": "Machine Learning",
        "keywords": [
            "machine learning",
            "statistical learning",
            "supervised learning",
            "unsupervised learning",
            "reinforcement learning",
            "neural network",
        ],
        "description": "Machine learning algorithms, models, and applications.",
    },
    "deep-learning": {
        "label": "Deep Learning",
        "keywords": [
            "deep learning",
            "deep neural",
            "convolutional neural",
            "recurrent neural",
            "transformer model",
        ],
        "description": "Deep learning architectures and training methods.",
    },
    "natural-language-processing": {
        "label": "Natural Language Processing",
        "keywords": [
            "natural language processing",
            "nlp",
            "text mining",
            "language model",
            "computational linguistics",
            "text analysis",
        ],
        "description": "Processing, understanding, and generating human language.",
    },
    "computer-vision": {
        "label": "Computer Vision",
        "keywords": [
            "computer vision",
            "image recognition",
            "object detection",
            "image processing",
            "visual computing",
        ],
        "description": "Visual perception and image understanding by computers.",
    },
    "data-science": {
        "label": "Data Science",
        "keywords": [
            "data science",
            "data analytics",
            "big data",
            "data-driven",
            "data mining",
        ],
        "description": "Data analysis, modeling, and insight extraction from large datasets.",
    },
    "cybersecurity": {
        "label": "Cybersecurity",
        "keywords": [
            "cybersecurity",
            "information security",
            "network security",
            "cyber defense",
            "security research",
        ],
        "description": "Protection of systems, networks, and data from cyber threats.",
    },
    "public-health": {
        "label": "Public Health",
        "keywords": [
            "public health",
            "population health",
            "epidemiology",
            "health disparities",
            "disease prevention",
            "health outcomes",
        ],
        "description": "Health of populations and communities.",
    },
    "biomedical-research": {
        "label": "Biomedical Research",
        "keywords": [
            "biomedical",
            "biomedicine",
            "biomedical research",
            "translational research",
            "clinical research",
            "life sciences",
        ],
        "description": "Biological and medical research for understanding and treating disease.",
    },
    "climate-science": {
        "label": "Climate Science",
        "keywords": [
            "climate change",
            "climate science",
            "global warming",
            "carbon emissions",
            "greenhouse gas",
            "climate adaptation",
        ],
        "description": "Study of climate systems, change, and mitigation strategies.",
    },
    "environmental-science": {
        "label": "Environmental Science",
        "keywords": [
            "environmental science",
            "ecology",
            "biodiversity",
            "conservation",
            "environmental sustainability",
            "pollution",
        ],
        "description": "Study of the environment, ecosystems, and sustainability.",
    },
    "education-research": {
        "label": "Education Research",
        "keywords": [
            "education research",
            "stem education",
            "educational technology",
            "learning outcomes",
            "curriculum",
            "pedagogy",
        ],
        "description": "Research on teaching, learning, and educational systems.",
    },
    "social-science": {
        "label": "Social Science",
        "keywords": [
            "social science",
            "sociology",
            "psychology",
            "behavioral science",
            "political science",
            "economics",
        ],
        "description": "Study of human society, behavior, and social institutions.",
    },
    "engineering": {
        "label": "Engineering",
        "keywords": [
            "engineering research",
            "civil engineering",
            "mechanical engineering",
            "electrical engineering",
            "chemical engineering",
            "systems engineering",
        ],
        "description": "Application of scientific principles to design and build systems.",
    },
    "quantum-computing": {
        "label": "Quantum Computing",
        "keywords": [
            "quantum computing",
            "quantum information",
            "quantum algorithms",
            "quantum simulation",
            "qubits",
        ],
        "description": "Computation using quantum-mechanical phenomena.",
    },
    "robotics": {
        "label": "Robotics",
        "keywords": [
            "robotics",
            "robotic systems",
            "autonomous robots",
            "human-robot interaction",
        ],
        "description": "Design, construction, and operation of robots.",
    },
    "materials-science": {
        "label": "Materials Science",
        "keywords": [
            "materials science",
            "advanced materials",
            "nanomaterials",
            "polymers",
            "composites",
        ],
        "description": "Study and development of materials with novel properties.",
    },
    "mathematics": {
        "label": "Mathematics",
        "keywords": [
            "mathematics",
            "mathematical foundations",
            "applied mathematics",
            "statistics",
            "mathematical modeling",
        ],
        "description": "Mathematical theory, foundations, and applications.",
    },
}


# 2. METHODS / APPROACHES
METHODS: Dict[str, dict] = {
    "simulation": {
        "label": "Simulation",
        "keywords": [
            "simulation",
            "computational modeling",
            "agent-based model",
            "monte carlo",
            "numerical simulation",
        ],
        "description": "Computer-based modeling and simulation methods.",
    },
    "clinical-trial": {
        "label": "Clinical Trial",
        "keywords": [
            "clinical trial",
            "randomized controlled",
            "phase i",
            "phase ii",
            "phase iii",
            "clinical study",
        ],
        "description": "Controlled experimental studies in clinical settings.",
    },
    "qualitative-research": {
        "label": "Qualitative Research",
        "keywords": [
            "qualitative research",
            "ethnography",
            "interviews",
            "focus groups",
            "case study",
            "grounded theory",
        ],
        "description": "Non-numerical data collection and analysis methods.",
    },
    "survey-research": {
        "label": "Survey Research",
        "keywords": [
            "survey",
            "questionnaire",
            "longitudinal study",
            "cross-sectional",
            "cohort study",
        ],
        "description": "Data collection via structured surveys and questionnaires.",
    },
    "experimental-research": {
        "label": "Experimental Research",
        "keywords": [
            "experimental",
            "controlled experiment",
            "laboratory study",
            "field experiment",
        ],
        "description": "Hypothesis testing through controlled experiments.",
    },
    "meta-analysis": {
        "label": "Meta-Analysis",
        "keywords": [
            "meta-analysis",
            "systematic review",
            "literature review",
            "evidence synthesis",
        ],
        "description": "Statistical synthesis of findings from multiple studies.",
    },
    "mixed-methods": {
        "label": "Mixed Methods",
        "keywords": [
            "mixed methods",
            "mixed-method",
            "convergent design",
            "sequential design",
        ],
        "description": "Combination of quantitative and qualitative approaches.",
    },
    "participatory-research": {
        "label": "Participatory Research",
        "keywords": [
            "participatory research",
            "community-based participatory",
            "action research",
            "co-design",
        ],
        "description": "Research conducted with active community participation.",
    },
    "machine-learning-method": {
        "label": "Machine Learning Methods",
        "keywords": [
            "machine learning method",
            "predictive modeling",
            "classification",
            "regression analysis",
            "clustering",
        ],
        "description": "Application of ML techniques as research methodology.",
    },
    "genomics": {
        "label": "Genomics / Bioinformatics",
        "keywords": [
            "genomics",
            "bioinformatics",
            "genome sequencing",
            "proteomics",
            "transcriptomics",
        ],
        "description": "Computational analysis of biological sequence data.",
    },
}


# 3. POPULATIONS
POPULATIONS: Dict[str, dict] = {
    "children-youth": {
        "label": "Children & Youth",
        "keywords": [
            "children",
            "youth",
            "adolescents",
            "pediatric",
            "k-12",
            "minors",
        ],
        "description": "Individuals under 18 years of age.",
    },
    "older-adults": {
        "label": "Older Adults",
        "keywords": [
            "older adults",
            "elderly",
            "aging",
            "geriatric",
            "seniors",
            "age-related",
        ],
        "description": "Individuals aged 65 and older.",
    },
    "underserved-communities": {
        "label": "Underserved Communities",
        "keywords": [
            "underserved",
            "underrepresented",
            "marginalized",
            "disadvantaged",
            "low-income",
            "rural communities",
        ],
        "description": "Communities with limited access to resources or services.",
    },
    "veterans": {
        "label": "Veterans",
        "keywords": [
            "veterans",
            "military",
            "service members",
            "armed forces",
        ],
        "description": "Current or former military service members.",
    },
    "persons-with-disabilities": {
        "label": "Persons with Disabilities",
        "keywords": [
            "disabilities",
            "disabled",
            "accessibility",
            "assistive technology",
            "special needs",
        ],
        "description": "Individuals with physical, cognitive, or developmental disabilities.",
    },
    "indigenous-populations": {
        "label": "Indigenous Populations",
        "keywords": [
            "indigenous",
            "tribal",
            "native american",
            "alaska native",
            "first nations",
        ],
        "description": "Indigenous and native peoples.",
    },
    "women-girls": {
        "label": "Women & Girls",
        "keywords": [
            "women",
            "girls",
            "female",
            "gender equity",
            "maternal",
            "women in stem",
        ],
        "description": "Women and girls as specific focus populations.",
    },
    "immigrants-refugees": {
        "label": "Immigrants & Refugees",
        "keywords": [
            "immigrants",
            "refugees",
            "asylum",
            "migrant",
            "displaced populations",
        ],
        "description": "Immigrant and refugee populations.",
    },
}


# 4. SPONSOR THEMES (cross-cutting funder priorities)
SPONSOR_THEMES: Dict[str, dict] = {
    "equity-diversity-inclusion": {
        "label": "Equity, Diversity & Inclusion",
        "keywords": [
            "equity",
            "diversity",
            "inclusion",
            "dei",
            "broadening participation",
            "inclusive",
        ],
        "description": "Promoting equity, diversity, and inclusion in research and outcomes.",
    },
    "workforce-development": {
        "label": "Workforce Development",
        "keywords": [
            "workforce development",
            "training",
            "capacity building",
            "career development",
            "professional development",
        ],
        "description": "Building human capital and workforce capacity.",
    },
    "innovation-commercialization": {
        "label": "Innovation & Commercialization",
        "keywords": [
            "innovation",
            "commercialization",
            "technology transfer",
            "startup",
            "entrepreneurship",
            "sbir",
            "sttr",
        ],
        "description": "Moving research to market and supporting innovation ecosystems.",
    },
    "national-security": {
        "label": "National Security",
        "keywords": [
            "national security",
            "defense",
            "homeland security",
            "critical infrastructure",
            "national defense",
        ],
        "description": "Research supporting national security objectives.",
    },
    "sustainability": {
        "label": "Sustainability",
        "keywords": [
            "sustainability",
            "sustainable development",
            "clean energy",
            "renewable",
            "green technology",
            "net zero",
        ],
        "description": "Long-term environmental and societal sustainability.",
    },
    "international-collaboration": {
        "label": "International Collaboration",
        "keywords": [
            "international collaboration",
            "global partnership",
            "bilateral",
            "multilateral",
            "international cooperation",
        ],
        "description": "Cross-national research partnerships and cooperation.",
    },
    "convergence-research": {
        "label": "Convergence Research",
        "keywords": [
            "convergence research",
            "interdisciplinary",
            "transdisciplinary",
            "multidisciplinary",
            "cross-disciplinary",
        ],
        "description": "Integration of knowledge across disciplines.",
    },
    "responsible-ai": {
        "label": "Responsible AI",
        "keywords": [
            "responsible ai",
            "trustworthy ai",
            "ethical ai",
            "ai safety",
            "ai governance",
            "explainable ai",
            "fairness in ai",
            "socially responsible",
        ],
        "description": "Ensuring AI systems are safe, fair, and transparent.",
    },
    "pandemic-preparedness": {
        "label": "Pandemic Preparedness",
        "keywords": [
            "pandemic preparedness",
            "infectious disease",
            "epidemic",
            "outbreak",
            "public health emergency",
        ],
        "description": "Readiness and response to pandemic threats.",
    },
    "digital-infrastructure": {
        "label": "Digital Infrastructure",
        "keywords": [
            "digital infrastructure",
            "broadband",
            "cyberinfrastructure",
            "high-performance computing",
            "cloud computing",
        ],
        "description": "Building and maintaining digital systems and networks.",
    },
}


# Utility functions
ALL_VOCABULARIES = {
    "research_domains": RESEARCH_DOMAINS,
    "methods": METHODS,
    "populations": POPULATIONS,
    "sponsor_themes": SPONSOR_THEMES,
}


def get_all_labels() -> Dict[str, List[str]]:
    """Return all tag labels organized by category.

    Returns:
        Dict mapping category name → list of tag labels.
    """
    return {
        category: [entry["label"] for entry in vocab.values()]
        for category, vocab in ALL_VOCABULARIES.items()
    }


def get_labels_for_category(category: str) -> List[str]:
    """Return tag labels for a single category.

    Args:
        category: One of "research_domains", "methods", "populations", "sponsor_themes".

    Returns:
        List of human-readable label strings.
    """
    vocab = ALL_VOCABULARIES.get(category, {})
    return [entry["label"] for entry in vocab.values()]


def get_descriptions_for_category(category: str) -> Dict[str, str]:
    """Return tag slug → description mapping for a category.

    Useful for embedding-based tagging where descriptions are encoded.
    """
    vocab = ALL_VOCABULARIES.get(category, {})
    return {slug: entry["description"] for slug, entry in vocab.items()}


def get_keywords_for_category(category: str) -> Dict[str, List[str]]:
    """Return tag slug → keywords mapping for a category.

    Useful for rule-based tagging.
    """
    vocab = ALL_VOCABULARIES.get(category, {})
    return {slug: entry["keywords"] for slug, entry in vocab.items()}
