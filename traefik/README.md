# Traefik Configuration

This directory contains the Traefik reverse proxy configuration for the production deployment.

## Files

- `traefik.yml` - Main Traefik configuration file
- `dynamic.yml` - Dynamic configuration for middlewares
- `.gitignore` - Prevents committing sensitive files (like acme.json)

## Configuration

### Domain Setup

The configuration is set up for:
- **Domain**: `chatbot.dfgp.fonctionpublique.gov.gn`
- **SSL/TLS**: Automatic via Let's Encrypt
- **Email**: Update in `traefik.yml` line 49

### Key Features

- ✅ Automatic HTTPS/SSL certificate management
- ✅ HTTP to HTTPS redirect
- ✅ Security headers middleware
- ✅ CORS middleware
- ✅ Rate limiting (100 req/min)
- ✅ Compression middleware
- ✅ Request/response logging

## SSL Certificate

Certificates are stored in the Docker volume `letsencrypt` and will be automatically renewed by Traefik.

The `acme.json` file contains the certificate data and should **NEVER** be committed to git (already in `.gitignore`).

## Customization

### Update Email for Let's Encrypt

Edit `traefik.yml`:
```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@domain.com  # Change this
```

### Update CORS Origins

Edit `dynamic.yml`:
```yaml
cors-headers:
  headers:
    accessControlAllowOriginList:
      - "https://chatbot.dfgp.fonctionpublique.gov.gn"
      - "https://your-other-domain.com"
```

### Update Rate Limits

Edit `dynamic.yml`:
```yaml
rate-limit:
  rateLimit:
    average: 100  # Requests per period
    period: 1m    # Time period
    burst: 50     # Burst allowance
```

## Dashboard Access

The Traefik dashboard can be accessed at:
- `https://traefik.laufane.com` (if DNS configured)

To secure the dashboard with basic auth:

1. Generate password hash:
   ```bash
   echo $(htpasswd -nb admin your_password) | sed -e s/\\$/\\$\\$/g
   ```

2. Update `dynamic.yml`:
   ```yaml
   dashboard-auth:
     basicAuth:
       users:
         - "admin:$2y$05$your_hash_here"
   ```

## Troubleshooting

### Certificate Issues

Check Traefik logs:
```bash
docker compose logs traefik | grep -i acme
```

Common issues:
- DNS not pointing correctly
- Ports 80/443 not accessible
- Email format incorrect

### Service Not Discovered

Verify Docker socket access:
```bash
docker compose logs traefik | grep -i docker
```

Check that services have correct labels:
```bash
docker inspect chatbot_l0027 | grep -i traefik
```

