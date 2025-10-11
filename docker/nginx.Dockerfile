FROM nginx:alpine

# Copy custom config
COPY ./docker/nginx/nginx.conf /etc/nginx/conf.d/default.conf