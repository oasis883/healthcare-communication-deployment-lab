# Healthcare Communication Deployment Lab

A one-day Streamlit project demonstrating:

- HL7 ADT message generation
- patient admission workflow
- nurse-call alert simulation
- wireless signal assessment
- go-live checks
- optional Claude API implementation review

## Run

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Claude API

Set your API key before starting Streamlit:

```powershell
$env:ANTHROPIC_API_KEY="your-key-here"
```

Use fictional data only. This is a learning simulation, not a clinical system.
