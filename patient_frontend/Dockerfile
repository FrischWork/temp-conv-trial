# Dockerfile
FROM node:14-alpine as build

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./
RUN npm install

COPY . ./

# Add environment variable for API URL
ARG REACT_APP_BFF_URL
ENV REACT_APP_BFF_URL=$REACT_APP_BFF_URL

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
