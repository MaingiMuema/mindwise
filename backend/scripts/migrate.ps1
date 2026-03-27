$env:PYTHONPATH = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location "$PSScriptRoot\.."
python -m alembic upgrade head
