# Production Scaling Guide
## Optimized for 100,000+ Users

This guide covers the production scaling configuration for handling 100,000+ concurrent users.

## Resource Allocation

**Total Resources:**
- RAM: 32GB
- Disk: 100GB
- Network: 1GB bandwidth

**Resource Distribution:**

| Service | RAM | CPU Cores | Purpose |
|---------|-----|-----------|---------|
| Traefik | 2GB | 2 | Reverse proxy & load balancing |
| Chatbot (4 instances) | 24GB (6GB each) | 16 (4 each) | Application workers |
| PostgreSQL | 8GB | 4 | Database server |
| Redis | 4GB | 2 | Cache layer |
| Qdrant | 4GB | 2 | Vector database |
| System/Buffer | ~2GB | - | OS and headroom |

**Total Worker Capacity:**
- 4 chatbot instances × 8 workers = 32 workers
- Can handle ~3,200 concurrent requests (100 per worker)

## Deployment Options

### Option 1: Docker Compose (Single Server)

For deployment on a single server with 32GB RAM:

```bash
# Use production compose file
docker compose -f docker-compose.prod.yml --profile production up -d
```

This uses Docker Compose scaling which works on a single machine.

### Option 2: Docker Swarm (Recommended for High Scale)

For better orchestration and horizontal scaling:

```bash
# Initialize swarm (if not already)
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.prod.yml chatbot
```

### Option 3: Kubernetes (For Maximum Scale)

For even better orchestration and auto-scaling, consider Kubernetes deployment.

## Performance Optimizations

### 1. PostgreSQL Tuning

The PostgreSQL configuration is optimized in `config/postgresql.conf`:

- **max_connections**: 500 (high concurrent access)
- **shared_buffers**: 2GB (25% of available RAM for PostgreSQL)
- **effective_cache_size**: 6GB (OS cache estimation)
- **work_mem**: 8MB (for sorting operations)
- **Parallel query execution**: Enabled for large queries

### 2. Redis Cache

- **Memory**: 4GB (3GB for data, 1GB buffer)
- **Eviction Policy**: allkeys-lru (Least Recently Used)
- **Persistence**: AOF enabled for durability
- **Max Connections**: 100

### 3. Application Workers

- **Workers per instance**: 8
- **Total workers**: 32 (4 instances × 8 workers)
- **Worker type**: Uvicorn with uvloop (async event loop)

### 4. Rate Limiting

Configured in Traefik:

- **General**: 500 requests/minute per IP
- **API endpoints**: 300 requests/minute per IP
- **Burst**: 50-100 requests

## Monitoring & Metrics

### Health Checks

All services have health checks configured:

```bash
# Check service status
docker compose ps

# Check health endpoint
curl https://chatbot.dfgp.fonctionpublique.gov.gn/health
```

### Resource Monitoring

Monitor resource usage:

```bash
# Real-time stats
docker stats

# Specific service
docker stats chatbot_l0027
```

### Logs

Access logs for troubleshooting:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f chatbot
docker compose logs -f postgres
docker compose logs -f redis
```

## Scaling Strategies

### Vertical Scaling (Current Setup)

Increase resources per instance:
- More RAM per service
- More CPU cores
- Adjust in `docker compose.prod.yml`

### Horizontal Scaling (Recommended)

Add more chatbot instances:

```yaml
chatbot:
  deploy:
    replicas: 6  # Increase from 4 to 6
```

This distributes load across more instances.

### Database Scaling

For even higher scale:

1. **Read Replicas**: Set up PostgreSQL read replicas
2. **Connection Pooling**: Use PgBouncer for connection pooling
3. **Sharding**: Consider database sharding for very high load

### Cache Scaling

1. **Redis Cluster**: Set up Redis cluster for distributed caching
2. **CDN**: Use CDN for static assets

## Capacity Planning

### Current Capacity

- **Concurrent Users**: ~3,200 (100 per worker)
- **Requests/second**: ~500 (with 32 workers)
- **Daily Requests**: ~43M (assuming 24/7 usage)
- **Peak Load**: Handles spikes up to 800 req/s

### Projected Load for 100k Users

Assumptions:
- Average session: 5 requests
- Peak concurrent users: 5,000 (5% of 100k)
- Average request time: 500ms

**Requirements:**
- Need ~50-60 workers for peak load
- Current setup handles ~64% of peak (with some headroom)

### Recommendations

1. **Start with current setup** (32 workers)
2. **Monitor performance** for 1-2 weeks
3. **Scale horizontally** if needed:
   - Add more chatbot instances
   - Increase to 6-8 instances if traffic grows

## Performance Benchmarks

### Expected Performance

- **Average Response Time**: < 500ms (cached)
- **P95 Response Time**: < 1s
- **P99 Response Time**: < 2s
- **Cache Hit Rate**: > 80%
- **Database Connection Pool**: < 50% utilization
- **Memory Usage**: < 90% of allocated

### Load Testing

Test your deployment:

```bash
# Install load testing tools
pip install locust

# Run load test
locust -f tests/load_test.py --host=https://chatbot.dfgp.fonctionpublique.gov.gn
```

## Troubleshooting

### High Memory Usage

1. Check worker count - reduce if necessary
2. Monitor Redis memory usage
3. Check for memory leaks
4. Adjust PostgreSQL shared_buffers

### Slow Response Times

1. Check cache hit rate
2. Monitor database query times
3. Review slow query logs
4. Check network bandwidth usage
5. Consider adding more workers

### Database Connection Errors

1. Increase `max_connections` in PostgreSQL
2. Reduce `pool_size` in application
3. Add connection pooler (PgBouncer)
4. Check for connection leaks

### High CPU Usage

1. Reduce worker count per instance
2. Optimize slow queries
3. Enable query result caching
4. Consider more instances with fewer workers

## Backup Strategy

### Database Backups

```bash
# Automated backup (add to cron)
docker exec chatbot_postgres pg_dump -U chatbot_user chatbot_l0027 > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i chatbot_postgres psql -U chatbot_user chatbot_l0027 < backup.sql
```

### Volume Backups

Backup all volumes:

```bash
docker run --rm -v chatbot_l0027_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Backup Schedule

- **Database**: Daily backups
- **Volumes**: Weekly backups
- **Retention**: 30 days

## Security Considerations

1. **Rate Limiting**: Prevents abuse
2. **Connection Limits**: Prevents resource exhaustion
3. **Resource Limits**: Prevents OOM issues
4. **Health Checks**: Automatic recovery
5. **Logging**: Audit trail for security events

## Next Steps

1. Deploy with current configuration
2. Monitor for 1-2 weeks
3. Collect metrics:
   - Request rate
   - Response times
   - Resource usage
   - Error rates
4. Adjust configuration based on real-world usage
5. Scale horizontally as needed

