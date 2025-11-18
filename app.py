# from __future__ import annotations

# import os
# import json
# from typing import Any, Dict
# from neo4j import GraphDatabase
# from dotenv import load_dotenv
# from mcp.server.fastmcp import FastMCP

# load_dotenv()

# # ----------------------------------------------------------
# #  MCP SERVER
# # ----------------------------------------------------------

# mcp = FastMCP("memgraph_query")

# def _to_json_safe(obj: Any) -> str:
#     return json.dumps(obj, ensure_ascii=False, default=str)

# # ----------------------------------------------------------
# #  INTERNAL DB EXECUTION
# # ----------------------------------------------------------

# def run_cypher_query(uri: str, username: str, password: str, query: str):
#     """
#     Internal wrapper to connect & execute Cypher against Memgraph/Neo4j.
#     """
#     try:
#         driver = GraphDatabase.driver(uri, auth=(username, password))
#         with driver.session() as session:
#             result = session.run(query)
#             data = [record.data() for record in result]
#         driver.close()
#         return {"status": "success", "data": data}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# # ----------------------------------------------------------
# #  MCP TOOL — fetch_customer_data
# # ----------------------------------------------------------

# @mcp.tool()
# def fetch_customer_data(
#     uri: str,
#     username: str,
#     password: str,
#     mtcn: str,
# ) -> str:
#     """
#     Fetch customer + risk + receiver data based on MTCN.
#     Required:
#       - uri: bolt://host:port
#       - username: DB username
#       - password: DB password
#       - mtcn: transaction number
#     """

#     # ----------------------------
#     # Prepare derived MTCN attempt
#     # ----------------------------
#     mtcn_attempt = str(mtcn)[-10:]

#     # ----------------------------
#     # Receiver Query
#     # ----------------------------
#     receiver_query = f"""
#     MATCH (a:AttemptTxn {{MTCN: "{mtcn_attempt}"}})
#     RETURN a.RCVRFIRSTNAME AS ReceiverFirstName,
#            a.RCVRLASTNAME  AS ReceiverLastName;
#     """

#     receiver_result = run_cypher_query(uri, username, password, receiver_query)

#     # ----------------------------
#     # Customer + Risk Query
#     # ----------------------------
#     customer_query = f"""
#     MATCH (r:RiskXML {{MTCN: "{mtcn}"}})-[:INITIATED_BY]->(c:Customer)
#     RETURN 
#         c.SENDER_CUSTOMERNUMBER AS SenderCustomerNumber,
#         c.FIRST_NAME AS FirstName,
#         c.LAST_NAME AS LastName,
#         c.GALACTIC_ID AS GalacticID,
#         c.OCCUPATION AS Occupation,
#         c.INDUSTRY AS Industry,
#         c.COUNTRY_OF_BIRTH AS CountryOfBirth,
#         c.EMPLOYMENT_STATUS AS EmploymentStatus,
#         c.cn_sum_tran_filter_trandatedur_90d_dispoeq_a AS TranSum90d,
#         c.rfn_rln_rcc_sum_amt_dispoeq_a_365d AS TranSum365d,
#         r.grossAmount AS GrossAmount,
#         r.KYCResult AS KYCResult,
#         r.ReceiverCity AS ReceiverCity,
#         c.COMPANY AS Company;
#     """

#     customer_result = run_cypher_query(uri, username, password, customer_query)

#     # If DB query failed
#     if receiver_result.get("status") == "error":
#         return _to_json_safe(receiver_result)

#     if customer_result.get("status") == "error":
#         return _to_json_safe(customer_result)

#     receiver = receiver_result.get("data", [])
#     customer = customer_result.get("data", [])

#     def first_valid(lst, key):
#         for item in lst:
#             if key in item and item[key] not in (None, ""):
#                 return item[key]
#         return None

#     # -----------------------------------------
#     # Build EXACT SAME combined_output structure
#     # -----------------------------------------
#     combined_output = {
#         "ReceiverFirstName": first_valid(receiver, "ReceiverFirstName"),
#         "ReceiverLastName": first_valid(receiver, "ReceiverLastName"),
#         "ReceiverCity": first_valid(customer, "ReceiverCity"),
#         "c.SENDER_CUSTOMERNUMBER": first_valid(customer, "SenderCustomerNumber"),
#         "c.FIRST_NAME": first_valid(customer, "FirstName"),
#         "c.LAST_NAME": first_valid(customer, "LastName"),
#         "GalacticID": first_valid(customer, "GalacticID"),
#         "c.OCCUPATION": first_valid(customer, "Occupation"),
#         "c.INDUSTRY": first_valid(customer, "Industry"),
#         "c.COUNTRY_OF_BIRTH": first_valid(customer, "CountryOfBirth"),
#         "c.EMPLOYMENT_STATUS": first_valid(customer, "EmploymentStatus"),
#         "c.cn_sum_tran_filter_trandatedur_90d_dispoeq_a": first_valid(customer, "TranSum90d"),
#         "c.rfn_rln_rcc_sum_amt_dispoeq_a_365d": first_valid(customer, "TranSum365d"),
#         "r.grossAmount": first_valid(customer, "GrossAmount"),
#         "r.KYCResult": first_valid(customer, "KYCResult"),
#         "c.COMPANY": first_valid(customer, "Company"),
#     }

#     return _to_json_safe({"status": "success", "data": combined_output})


# # ----------------------------------------------------------
# #  MCP RUNNER
# # ----------------------------------------------------------

# if __name__ == "__main__":
#     host = os.getenv("FASTMCP_HOST", "0.0.0.0")
#     port = int(os.getenv("FASTMCP_PORT") or os.getenv("PORT") or 9000)
#     print(f"Memgraph MCP server running at http://{host}:{port}")
#     mcp.settings.host = host
#     mcp.settings.port = port
#     mcp.run(transport="streamable-http")


from __future__ import annotations

import os
import json
from typing import Any, Dict
from neo4j import GraphDatabase
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# ----------------------------------------------------------
#  MCP SERVER
# ----------------------------------------------------------

mcp = FastMCP("memgraph_query")


def _to_json_safe(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


# ----------------------------------------------------------
#  INTERNAL DB EXECUTION
# ----------------------------------------------------------

def run_cypher_query(uri: str, username: str, password: str, query: str):
    """Internal wrapper to connect & execute Cypher against Memgraph/Neo4j."""
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run(query)
            data = [record.data() for record in result]
        driver.close()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------------------------------------------------
#  MCP TOOL — generic_cypher_query
# ----------------------------------------------------------

@mcp.tool()
def generic_cypher_query(
    uri: str,
    username: str,
    password: str,
    query: str,
) -> str:
    """
    Execute ANY Cypher query that the user sends.

    Parameters:
      - uri: bolt://host:port
      - username: DB username
      - password: DB password
      - query: FULL cypher query string

    Returns JSON:
      {
        "status": "...",
        "data": [...]
      }
    """

    result = run_cypher_query(uri, username, password, query)
    return _to_json_safe(result)


# ----------------------------------------------------------
#  MCP RUNNER
# ----------------------------------------------------------

if __name__ == "__main__":
    host = os.getenv("FASTMCP_HOST", "0.0.0.0")
    port = int(os.getenv("FASTMCP_PORT") or os.getenv("PORT") or 9000)
    print(f"Memgraph MCP server running at http://{host}:{port}")
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.run(transport="streamable-http")

