import asyncio
import json
import sys
from unittest.mock import patch, MagicMock, AsyncMock
from src.agents.planner import PlannerAgent

# Mock ticket data - exactly as requested
MOCK_TICKET = {
    "number": "CHG0001337",
    "sys_id": "abc123",
    "short_description": (
        "Open Port 443 inbound on Cisco ASA firewall "
        "named ASA-NYC-01 at IP 192.168.1.1 for HTTPS "
        "traffic. Business justification: New web "
        "application deployment."
    ),
    "opened_by": {"value": "john.doe"},
    "state": "new"
}

async def test_planner_live():
    print("\n🚀 Starting Live Planner Agent Test")
    print("   ServiceNow: MOCKED")
    print("   Slack: MOCKED") 
    print("   RAG (ChromaDB): LIVE")
    print("   Claude API: LIVE\n")

    # Patch paths must match where they are USED in src.agents.planner
    # PlannerAgent uses properties that instantiate the classes.
    # We patch the property returns or the methods on the classes themselves.
    
    with patch('src.integrations.servicenow.ServiceNowClient.get_ticket', new_callable=AsyncMock) as mock_get_ticket:
        mock_get_ticket.return_value = MOCK_TICKET
        
        with patch('src.integrations.slack.SlackClient.send_approval_request', new_callable=AsyncMock) as mock_send_slack:
            mock_send_slack.return_value = True
            
            # Instantiate the agent
            agent = PlannerAgent()
            
            # Build initial state
            # Note: We provide ticket_description to bypass the ServiceNow call if desired,
            # but here we'll let it call the mocked get_ticket.
            state = {
                "ticket_number": "CHG0001337",
                "ticket_sys_id": "abc123",
                "skip_slack": True, # Custom flag to avoid real Slack calls during test
                "pipeline_status": "started"
            }
            
            # Run the planner (it's async!)
            result = await agent.run(state)
            
            # Print results in requested format
            print("--- 📝 Extracted Intent ---")
            output = {
                "device_name": result.get("device_name"),
                "device_ip": result.get("device_ip"),
                "device_type": result.get("device_type"),
                "change_type": result.get("change_type"),
                "port": result.get("port"),
                "protocol": result.get("protocol"),
                "direction": result.get("direction"),
                "compliance_check_passed": result.get("compliance_check_passed"),
                "compliance_notes": result.get("compliance_notes")[:200] + "..." if result.get("compliance_notes") else ""
            }
            print(json.dumps(output, indent=4))
            
            # Assertions
            try:
                assert result.get("device_name") is not None, "FAIL: device_name is null"
                assert result.get("device_ip") == "192.168.1.1", f"FAIL: device_ip extracted as {result.get('device_ip')}"
                assert str(result.get("port")) == "443", f"FAIL: port extracted as {result.get('port')}"
                assert result.get("compliance_check_passed") is True, "FAIL: Port 443 should pass compliance"
                
                print("\n✅ All assertions passed")
                print("✅ Planner Agent is working correctly")
            except AssertionError as e:
                print(f"\n❌ Assertion Error: {e}")
                sys.exit(1)

            return result

if __name__ == "__main__":
    asyncio.run(test_planner_live())
