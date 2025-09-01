from pydantic import BaseModel
from typing import Optional


class TwilioForwardingRequest(BaseModel):
    twilio_acc_sid: str
    twilio_auth_token: str
    twilio_voice_agent_no: str
    twilio_human_agent_no: str
    call_sid: str


class AgentStatusCallbackQuery(BaseModel):
    customer_call_sid: str
    twilio_acc_sid: str
    twilio_auth_token: str


class ForwardAgentVoiceQuery(BaseModel):
    conference_name: str
