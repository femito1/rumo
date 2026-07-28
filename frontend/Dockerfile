FROM node:20-alpine AS build
WORKDIR /app
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
COPY package*.json ./
RUN npm ci
COPY . .
# EasyPanel passes --build-arg GIT_SHA=<commit> on every deploy. Consuming it here
# makes the build layer's cache key change per commit, which (a) guarantees the SPA
# is rebuilt against the current source and (b) is our escape hatch from a poisoned
# buildkit cache: a 2026-07-28 deploy failed repeatedly with
#   "failed to commit <id> ... snapshot <id> does not exist: not found"
# because every layer resolved CACHED against a snapshot whose parent was gone, and
# the host's docker-driver cache survives stopDockerBuilder. A changing ARG sidesteps
# the bad entry without shell access to the box. Keep it ABOVE `npm run build`.
ARG GIT_SHA=dev
ENV GIT_SHA=$GIT_SHA
RUN npm run build
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
