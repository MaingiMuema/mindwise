$env:PYTHONPATH = (Resolve-Path "$PSScriptRoot\..").Path
Set-Location "$PSScriptRoot\.."
python -m celery -A app.core.celery_app.celery_app worker --loglevel=info
