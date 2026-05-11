```yaml
version: '3'
services:
  server:
    image: ghcr.io/zx419d2o0/ipyaz4:latest
    container_name: ipyaz4
    restart: unless-stopped
    volumes:
      - ./download:/home/download
    ports:
      - 4190:80
    environment:
      - proxy_http=http://127.0.0.1:7890
```
