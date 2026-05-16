# --- Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm install
COPY dashboard/ ./
RUN npm run build

# --- Build Backend ---
FROM python:3.10-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .
# Remove the dashboard source to save space (keep the build)
RUN rm -rf dashboard

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/dashboard/dist ./static

# Expose port (Hugging Face uses 7860)
EXPOSE 7860

# Command to run the app
# We tell uvicorn to run main:app and we will update main.py to serve the /static folder
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
