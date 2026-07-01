FROM python:3.12-slim-bookworm

# Install app
ADD . /usr/src/ff_bot
WORKDIR /usr/src/ff_bot
RUN pip install --no-cache-dir .

# Launch app (run as a module so package imports resolve without a sys.path hack)
CMD ["python3", "-m", "ff_bot.espn.espn_bot"]
