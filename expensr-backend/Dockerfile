FROM python:3.14-slim

WORKDIR /app

COPY pyproject.toml ./

RUN python -c "import pathlib, tomllib, subprocess, sys; deps=tomllib.loads(pathlib.Path('pyproject.toml').read_text())['project']['dependencies']; subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-cache-dir', *deps])"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
