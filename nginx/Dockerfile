FROM nginx:1.22.1-alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/

RUN mkdir -p /static /media

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]