# Frontend service — static HTML/CSS/JS served via Nginx.
#
# No build step (no bundler/framework) is required per the project's
# technology decision (plain HTML/CSS/JS + Leaflet.js loaded via CDN in a
# later milestone), so this is a minimal static-file image.

FROM nginx:1.27-alpine

COPY . /usr/share/nginx/html

EXPOSE 80
