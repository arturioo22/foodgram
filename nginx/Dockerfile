FROM nginx:1.22.1-alpine

RUN rm /etc/nginx/conf.d/default.conf

RUN mkdir -p /static /media

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]