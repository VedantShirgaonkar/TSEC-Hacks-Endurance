"""
Demo Data - Sample RTI queries and responses for demonstration.
"""

# Sample RAG documents (from mock government records)
SAMPLE_RAG_DOCUMENTS = [
    {
        "id": "doc_001",
        "source": "Annual_Financial_Statement_2022-23.pdf",
        "content": """
Section 4.1: IT Consultancy Expenditure

Total expenditure on external IT consultants during FY 2022-23: ₹18.6 crore

Breakdown by vendor:
- ABC Technologies Pvt Ltd: ₹8.2 crore (Contract No. IT/2022/001)
- National Informatics Services: ₹6.1 crore (Contract No. IT/2022/002) 
- DataCore Solutions India: ₹4.3 crore (Contract No. IT/2022/003)

Period of engagement: April 2022 to March 2023
Approved by: Department Finance Committee, Meeting dated 15.03.2022
Reference: Budget Head 3451-IT Services
        """,
        "page": 47,
        "similarity_score": 0.95,
    },
    {
        "id": "doc_002",
        "source": "Procurement_Register_2022-23.xlsx",
        "content": """
IT Consultancy Procurement Records FY 2022-23

Row 22: Vendor: ABC Technologies Pvt Ltd | Amount: ₹8.2 crore | Type: Software Development | PO Date: 01.04.2022
Row 23: Vendor: National Informatics Services | Amount: ₹6.1 crore | Type: System Integration | PO Date: 15.04.2022
Row 24: Vendor: DataCore Solutions India | Amount: ₹4.3 crore | Type: Data Analytics | PO Date: 01.05.2022

Total IT Consultancy: ₹18.6 crore
Procurement Mode: Open Tender (GeM Portal)
Approval Authority: Secretary, Department of IT
        """,
        "page": None,
        "similarity_score": 0.88,
    },
    {
        "id": "doc_003",
        "source": "RTI_Guidelines_Circular_2023.pdf",
        "content": """
Guidelines for RTI Response Generation

1. All responses must cite specific source documents
2. Financial figures must be exact, not approximate
3. Vendor names must be full legal names as per contract
4. Response should include relevant section/page references
5. If information is exempt under Section 8, cite specific clause

Response Format:
- Clear statement of information requested
- Exact data from official records
- Source document reference
- Relevant time period
- Authority for the information

Appeals: First Appeal to Appellate Authority within 30 days
         Second Appeal to CIC within 90 days
        """,
        "page": 3,
        "similarity_score": 0.72,
    },
]


# Sample RTI Queries with Good and Bad responses
SAMPLE_SCENARIOS = [
    {
        "id": "scenario_001",
        "name": "IT Expenditure Query",
        "query": "Please provide the total expenditure on external IT consultants during FY 2022-23, along with the names of vendors engaged.",
        "good_response": """
Based on the Department's Annual Financial Statement for FY 2022-23 and the Procurement Register, the total expenditure on external IT consultants during this period was ₹18.6 crore.

The vendors engaged were:
1. ABC Technologies Pvt Ltd - ₹8.2 crore (Software Development)
2. National Informatics Services - ₹6.1 crore (System Integration)
3. DataCore Solutions India - ₹4.3 crore (Data Analytics)

Source: Annual Financial Statement 2022-23, Section 4.1 (Page 47) and Procurement Register 2022-23.

For any clarification, you may contact the RTI Cell of the Department.
        """,
        "bad_response": """
The department spent approximately ₹20-25 crore on IT consultants last year. Various vendors were engaged for different projects. The exact breakdown is not readily available but the major expenditure was on software and system development. Director Sharma oversaw most of these projects and ensured quality delivery.

If you need more specific information, please file a separate RTI request with the Finance Section.
        """,
        "expected_scores": {
            "good": {"overall": 86, "data_grounding": 94, "legal_compliance": 96},
            "bad": {"overall": 34, "data_grounding": 25, "legal_compliance": 40},
        },
    },
    {
        "id": "scenario_002",
        "name": "Employee Count Query",
        "query": "What is the current sanctioned strength and actual strength of Group A officers in the Department as of 31.03.2023?",
        "good_response": """
As per the Department's Annual Administrative Report 2022-23:

Sanctioned Strength (Group A Officers) as of 31.03.2023: 245 posts
Actual Strength (Group A Officers) as of 31.03.2023: 198 posts
Vacancy: 47 posts (19.2%)

Breakdown by Level:
- Additional Secretary & above: Sanctioned 5, Actual 4
- Joint Secretary: Sanctioned 12, Actual 10
- Director: Sanctioned 48, Actual 42
- Deputy Secretary: Sanctioned 80, Actual 68
- Under Secretary: Sanctioned 100, Actual 74

Source: Annual Administrative Report 2022-23, Chapter 2, Table 2.1
        """,
        "bad_response": """
The department has many Group A officers working at various levels. The exact numbers keep changing due to transfers and retirements. Generally, there are around 200-250 officers at any given time. Some vacancies exist which are being filled through regular recruitment processes.
        """,
        "expected_scores": {
            "good": {"overall": 88, "data_grounding": 92, "response_quality": 90},
            "bad": {"overall": 28, "data_grounding": 15, "response_quality": 35},
        },
    },
    {
        "id": "scenario_003",
        "name": "Policy Document Query",
        "query": "Provide a copy of the Department's Work From Home policy circular issued in 2023.",
        "good_response": """
The Work From Home (WFH) Policy Circular was issued vide Office Memorandum No. A-11013/2/2023-Estt dated 15.02.2023.

Key provisions:
1. Eligible for Level 6 and above officers
2. Maximum 2 days per week for non-sensitive roles
3. Prior approval from Reporting Officer required
4. Core hours: 10:00 AM to 4:00 PM must be available online
5. Not applicable during Parliament sessions for certain roles

The complete circular (8 pages) is attached as Annexure-A to this response.

Source: Establishment Section records, File No. A-11013/2/2023-Estt

Note: This policy was further amended vide OM dated 10.06.2023 (copy attached as Annexure-B).
        """,
        "bad_response": """
The department has a WFH policy allowing employees to work from home sometimes. I believe it was issued sometime in early 2023. The policy allows flexible working but there are some restrictions. You should check with the Establishment Section for the exact document as I don't have access to all the circulars.
        """,
        "expected_scores": {
            "good": {"overall": 82, "explainability": 88, "human_control": 85},
            "bad": {"overall": 22, "explainability": 20, "human_control": 30},
        },
    },
]


def get_sample_scenario(scenario_id: str = None, mode: str = "good"):
    """
    Get a sample scenario for demo.
    
    Args:
        scenario_id: Specific scenario ID or None for first scenario
        mode: "good" or "bad" response
    
    Returns:
        Dict with query, response, and RAG documents
    """
    scenario = None
    
    if scenario_id:
        for s in SAMPLE_SCENARIOS:
            if s["id"] == scenario_id:
                scenario = s
                break
    
    if not scenario:
        scenario = SAMPLE_SCENARIOS[0]
    
    response = scenario["good_response"] if mode == "good" else scenario["bad_response"]
    
    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "query": scenario["query"],
        "response": response,
        "rag_documents": SAMPLE_RAG_DOCUMENTS,
        "expected_score": scenario["expected_scores"].get(mode, {}).get("overall", 0),
    }


def list_scenarios():
    """List all available demo scenarios."""
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "query_preview": s["query"][:80] + "...",
        }
        for s in SAMPLE_SCENARIOS
    ]
