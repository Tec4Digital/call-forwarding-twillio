from fastapi import APIRouter, Query, Form, Depends
from fastapi.responses import JSONResponse, Response
from twilio.rest import Client
import os

from app.models import TwilioForwardingRequest

router = APIRouter()
HOSTED_DOMAIN = os.getenv("HOSTED_DOMAIN", "https://example.com")


@router.post("/twilio-call-forwarding")
async def twilio_call_forwarding(body: TwilioForwardingRequest):
    try:
        twilio_client = Client(body.twilio_acc_sid, body.twilio_auth_token)
        CONFERENCE_NAME = f"SupportTransfer_{body.call_sid}"

        # Move customer to conference
        twilio_client.calls(body.call_sid).update(
            twiml=f"""
            <Response>
                <Say>Transferring your call. Waiting time is 1 minutes. Please hold.</Say>
                <Dial timeout="60">
                    <Conference endConferenceOnExit="true">{CONFERENCE_NAME}</Conference>
                </Dial>
            </Response>
            """
        )

        # Call the human agent
        twilio_client.calls.create(
            to=body.twilio_human_agent_no,
            from_=body.twilio_voice_agent_no,
            url=f"{HOSTED_DOMAIN}/forward-agent-voice?conference_name={CONFERENCE_NAME}",
            status_callback=f"{HOSTED_DOMAIN}/agent-status-callback/?customer_call_sid={body.call_sid}&twilio_acc_sid={body.twilio_acc_sid}&twilio_auth_token={body.twilio_auth_token}",
            status_callback_event=["completed", "answered", "no-answer", "busy", "failed"],
            status_callback_method="POST",
            timeout=60,
        )

        return JSONResponse({"message": "Call forwarded successfully"}, status_code=200)

    except Exception as e:
        return JSONResponse({"message": f"Call forwarding failed: {str(e)}"}, status_code=400)


@router.post("/agent-status-callback")
async def agent_call_status_callback(
    customer_call_sid: str = Query(...),
    twilio_acc_sid: str = Query(...),
    twilio_auth_token: str = Query(...),
    CallStatus: str = Form(None)  # Twilio posts form-data, not JSON
):
    twilio_client = Client(twilio_acc_sid, twilio_auth_token)

    if CallStatus in ["no-answer", "busy", "failed"]:
        try:
            twilio_client.calls(customer_call_sid).update(
                twiml="""
                    <Response>
                        <Say>The line is currently busy. Please try again later.</Say>
                        <Hangup/>
                    </Response>
                """
            )
        except Exception as e:
            print(f"Failed to update customer call: {e}")

    return JSONResponse(status_code=200, content={})


@router.post("/forward-agent-voice")
async def forward_agent_voice(conference_name: str = Query(...)):
    response = f"""
        <Response>
            <Say>You are being connected to a customer.</Say>
            <Dial timeout="60">
                <Conference endConferenceOnExit="true">{conference_name}</Conference>
            </Dial>
        </Response>
    """
    return Response(content=response, media_type="text/xml")
