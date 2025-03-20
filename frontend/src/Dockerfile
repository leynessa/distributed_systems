# Use the official NGINX Alpine image as the base image
FROM nginx:alpine

# Copy the frontend files to the NGINX HTML directory
COPY . /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]