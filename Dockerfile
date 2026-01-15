FROM python:3.11-alpine
RUN apk add --no-cache ffmpeg
WORKDIR /app
RUN pip install --no-cache-dir pyTelegramBotAPI
COPY . .
CMD ["python", "logo_bot.py"]
