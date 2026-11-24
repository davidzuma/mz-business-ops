Build a working mock-data PoC from the user's description using the `poc`
skill: scaffold from `templates/poc/`, implement the core flow with
fictional data, verify locally, then deploy with `scripts/deploy_poc.py`
(private GitHub repo + Vercel). Confirm project name and visibility first;
if Vercel/GitHub auth is missing, ask the user to log in. Return the live
URL and screenshots, ready to attach to a proposal via the `proposal` skill.
