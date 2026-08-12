FROM python:3.13-slim

ENV PORT=8000 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

RUN useradd --create-home --uid 10001 wizard \
    && chown -R wizard:wizard /app \
    && python3 -c "import sys; from pathlib import Path; sys.path.insert(0, 'scripts'); from setup_wizard.engine import _tracked_files; _tracked_files(Path('.'))"

USER wizard

EXPOSE 8000

CMD ["python3", "scripts/setup-project.py", "--serve"]
