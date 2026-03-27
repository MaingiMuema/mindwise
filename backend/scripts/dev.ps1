$env:PYTHONPATH = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location "$PSScriptRoot\.."
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
