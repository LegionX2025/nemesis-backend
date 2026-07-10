from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class IntelligenceEntity:
    entity_id: str
    entity_type: str
    value: str

    aliases: List[str] = field(default_factory=list)

    confidence: float = 0.0

    first_seen: str = ""
    last_seen: str = ""

    source_count: int = 0

    tags: List[str] = field(default_factory=list)

    attributes: Dict[str, Any] = field(default_factory=dict)

    relationships: List[Dict] = field(default_factory=list)

    risk_score: int = 0

    sanctions: List[str] = field(default_factory=list)

    evidence: List[Dict] = field(default_factory=list)


# 1. PERSON ENTITIES
PERSON_ENTITIES = {
    "Executive", "Director", "Officer", "Shareholder", "Beneficial Owner", 
    "Founder", "Co-Founder", "Investor", "Advisor", "Employee", "Contractor", 
    "Consultant", "Trustee", "Nominee Director", "Nominee Shareholder", "Attorney", 
    "Accountant", "Auditor", "Registered Agent", "Lobbyist", "Promoter", "Broker", 
    "Politician", "Government Official", "Regulator", "Judge", "Prosecutor", 
    "Witness", "Informant", "Suspect", "Defendant", "Plaintiff", "Convicted Individual", 
    "Fugitive", "Sanctioned Individual", "Politically Exposed Person (PEP)"
}

# 2. CORPORATE ENTITIES
CORPORATE_ENTITIES = {
    "Corporation", "LLC", "LLP", "LP", "Sole Proprietorship", "Partnership", 
    "Foundation", "Trust", "Cooperative", "Nonprofit", "NGO", "Charity", 
    "Holding Company", "Shell Company", "SPV", "Joint Venture", "Consortium", 
    "Public Company", "Private Company", "Government Corporation", "State-Owned Enterprise"
}

# 3. OWNERSHIP ENTITIES
OWNERSHIP_ENTITIES = {
    "Shareholding", "Beneficial Ownership", "Voting Rights", "Equity Interest", 
    "Partnership Interest", "Trustee Relationship", "Nominee Ownership", 
    "Ultimate Beneficial Ownership (UBO)", "Control Relationship"
}

# 4. GOVERNMENT ENTITIES
GOVERNMENT_ENTITIES = {
    "Ministry", "Department", "Agency", "Commission", "Regulatory Authority", 
    "Tax Authority", "Intelligence Service", "Military Branch", "Police Agency", 
    "Prosecutor Office", "Court", "Legislature", "Municipality", "Embassy", "Consulate"
}

# 5. REGULATORY ENTITIES
REGULATORY_ENTITIES = {
    "Securities Regulator", "Banking Regulator", "Insurance Regulator", 
    "Financial Intelligence Unit", "AML Authority", "Competition Authority", 
    "Privacy Authority", "Telecommunications Regulator"
}

# 6. FINANCIAL ENTITIES
FINANCIAL_ENTITIES = {
    "Commercial Bank", "Investment Bank", "Credit Union", "Broker Dealer", 
    "Hedge Fund", "Mutual Fund", "ETF", "Pension Fund", "Sovereign Wealth Fund", 
    "Venture Capital Firm", "Private Equity Firm", "Family Office", "Asset Manager", 
    "Custodian", "Payment Processor"
}

# 7. DIGITAL ASSET ENTITIES
DIGITAL_ASSET_ENTITIES = {
    "Exchange", "DEX", "OTC Desk", "Wallet Provider", "Stablecoin Issuer", 
    "Validator", "Mining Pool", "Staking Provider", "DAO", "Token Issuer", 
    "NFT Marketplace", "Bridge Operator"
}

# 8. BLOCKCHAIN ENTITIES
BLOCKCHAIN_ENTITIES = {
    "Wallet", "Address", "Smart Contract", "Token", "NFT", "Transaction", "Block", 
    "Validator", "Node", "Bridge", "Liquidity Pool", "Treasury Wallet", "Cold Wallet", "Hot Wallet"
}

# 9. LEGAL ENTITIES
LEGAL_ENTITIES = {
    "Civil Case", "Criminal Case", "Arbitration", "Regulatory Action", 
    "Enforcement Action", "Bankruptcy", "Receivership", "Settlement", 
    "Consent Order", "Injunction"
}

# 10. EVENT ENTITIES
EVENT_ENTITIES = {
    "Merger", "Acquisition", "IPO", "Funding Round", "Bankruptcy Filing", 
    "Product Launch", "Security Incident", "Data Breach", "Regulatory Filing", 
    "Court Hearing", "Shareholder Meeting"
}

# 11. DOCUMENT ENTITIES
DOCUMENT_ENTITIES = {
    "SEC Filing", "Prospectus", "Annual Report", "Quarterly Report", "Audit Report", 
    "Court Filing", "Contract", "Invoice", "License", "Permit", "Registration Certificate", 
    "Press Release", "Intelligence Report"
}

# 12. LOCATION ENTITIES
LOCATION_ENTITIES = {
    "Country", "Territory", "State", "Province", "Region", "City", "Municipality", 
    "Postal Address", "Office", "Facility", "Warehouse", "Port", "Airport"
}

# 13. PROPERTY ENTITIES
PROPERTY_ENTITIES = {
    "Real Estate", "Land", "Building", "Data Center", "Manufacturing Facility", 
    "Vehicle", "Aircraft", "Vessel", "Equipment"
}

# 14. COMMUNICATION ENTITIES
COMMUNICATION_ENTITIES = {
    "Email Address", "Domain", "Website", "IP Address", "Phone Number", 
    "Mobile Number", "Social Media Account", "Messaging Account"
}

# 15. INTERNET INFRASTRUCTURE ENTITIES
INTERNET_INFRASTRUCTURE_ENTITIES = {
    "ASN", "DNS Record", "Name Server", "SSL Certificate", "Cloud Instance", 
    "Hosting Provider", "CDN", "VPN Endpoint"
}

# 16. INTELLECTUAL PROPERTY ENTITIES
INTELLECTUAL_PROPERTY_ENTITIES = {
    "Patent", "Trademark", "Copyright", "Trade Secret", "Design Patent"
}

# 17. SANCTIONS ENTITIES
SANCTIONS_ENTITIES = {
    "OFAC Subject", "UN Subject", "EU Subject", "UK Subject", "Secondary Sanctions Target"
}

# 18. AML ENTITIES
AML_ENTITIES = {
    "Money Laundering Network", "Smurfing Network", "Trade-Based Laundering Scheme", 
    "Shell Network", "Terror Finance Network", "Fraud Network", "Ponzi Scheme"
}

# 19. THREAT ENTITIES
THREAT_ENTITIES = {
    "Cybercriminal", "Ransomware Group", "Nation State Actor", "Insider Threat", 
    "Fraud Ring", "Organized Crime Group"
}

# 20. MEDIA ENTITIES
MEDIA_ENTITIES = {
    "News Article", "Blog", "Podcast", "Video", "Social Media Post", "Forum Post", "Research Paper"
}

# 21. RELATIONSHIPS
RELATIONSHIPS = {
    "Owns", "Controls", "Subsidiary Of", "Parent Of", "Affiliate Of", "Partner Of", 
    "Invested In", "Funded By", "Acquired", "Merged With", "Director Of", "Officer Of", 
    "Employee Of", "Advisor To", "Trustee Of", "Nominee For", "Relative Of", "Sent Funds To", 
    "Received Funds From", "Custodian For", "Banked By", "Invested By", "Controls Wallet", 
    "Interacted With", "Sent Transaction To", "Received Transaction From", "Deployed Contract", 
    "Owns Token", "Plaintiff In", "Defendant In", "Prosecuted By", "Investigated By", 
    "Regulated By", "Associated With", "Linked To", "Mentioned With", "Co-Located With", 
    "Shared Address", "Shared Phone", "Shared Email", "Shared Director", "Shared Beneficial Owner"
}

# 22. RISK ENTITIES
RISK_ENTITIES = {
    "Regulatory Risk", "AML Risk", "Sanctions Risk", "Litigation Risk", 
    "Reputational Risk", "Political Risk", "Financial Risk", "Operational Risk", 
    "Cyber Risk", "Fraud Risk"
}

# Master aggregation
ENTITY_TYPES = (
    PERSON_ENTITIES | CORPORATE_ENTITIES | OWNERSHIP_ENTITIES | GOVERNMENT_ENTITIES |
    REGULATORY_ENTITIES | FINANCIAL_ENTITIES | DIGITAL_ASSET_ENTITIES | BLOCKCHAIN_ENTITIES |
    LEGAL_ENTITIES | EVENT_ENTITIES | DOCUMENT_ENTITIES | LOCATION_ENTITIES |
    PROPERTY_ENTITIES | COMMUNICATION_ENTITIES | INTERNET_INFRASTRUCTURE_ENTITIES |
    INTELLECTUAL_PROPERTY_ENTITIES | SANCTIONS_ENTITIES | AML_ENTITIES |
    THREAT_ENTITIES | MEDIA_ENTITIES | RISK_ENTITIES
)

ENTITY_RESOLUTION = {
    "wallet_to_ens", "wallet_to_exchange", "wallet_to_protocol", "wallet_to_organization",
    "wallet_to_person", "email_to_person", "email_to_domain", "domain_to_company",
    "domain_to_asn", "domain_to_ssl", "company_to_cik", "company_to_lei",
    "company_to_sanctions", "person_to_pep", "person_to_sanctions", "person_to_corporate_role"
}

CONFIDENCE = {
    "SEC": 100, "DOJ": 100, "OFAC": 100, "CFTC": 95, "INTERPOL": 95, "GLEIF": 95,
    "WHOIS": 80, "BLOCKCHAIN": 90, "SOCIAL_MEDIA": 60, "OSINT": 50, "AI_INFERENCE": 30
}
