# 🚀 DEPLOYMENT CHECKLIST

Use this checklist when deploying GAX Banking Platform to production.

## Pre-Deployment

### ⚙️ Configuration
- [ ] Copy `.env.example` to `.env`
- [ ] Set `DEBUG=False`
- [ ] Generate strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Set up PostgreSQL database
- [ ] Configure Redis connection
- [ ] Add Moniepoint LIVE credentials
- [ ] Add bill payment API credentials
- [ ] Configure email settings (SMTP)
- [ ] Set `FRONTEND_URL` to your domain
- [ ] Configure CORS allowed origins

### 🔐 Security
- [ ] Enable `SECURE_SSL_REDIRECT=True`
- [ ] Set `SESSION_COOKIE_SECURE=True`
- [ ] Set `CSRF_COOKIE_SECURE=True`
- [ ] Configure security headers
- [ ] Set up Sentry for error tracking
- [ ] Review and update rate limits
- [ ] Rotate API keys and secrets
- [ ] Set up SSL certificate (Let's Encrypt)

### 🗄️ Database
- [ ] Create production database
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Set up database backups (daily)
- [ ] Configure connection pooling
- [ ] Enable query logging (for optimization)

### 📦 Dependencies
- [ ] Install all requirements: `pip install -r requirements.txt`
- [ ] Install production server (Gunicorn/uWSGI)
- [ ] Set up virtual environment
- [ ] Verify all packages are compatible

### 📁 Static Files
- [ ] Run `python manage.py collectstatic`
- [ ] Configure S3 or CDN for media files
- [ ] Set up proper media file permissions
- [ ] Test file uploads (KYC documents, profile pictures)

### 🔄 Celery (Background Tasks)
- [ ] Install Celery workers
- [ ] Configure Celery beat for scheduled tasks
- [ ] Set up task monitoring (Flower)
- [ ] Test task execution

## Deployment

### 🌐 Server Setup
- [ ] Provision server (DigitalOcean, AWS, etc.)
- [ ] Install Python 3.10+
- [ ] Install PostgreSQL 13+
- [ ] Install Redis
- [ ] Install Nginx
- [ ] Configure firewall (UFW/iptables)
- [ ] Set up SSH key authentication
- [ ] Disable root login

### 🔧 Application Deployment
- [ ] Clone repository to server
- [ ] Set up virtual environment
- [ ] Install dependencies
- [ ] Configure environment variables
- [ ] Run migrations
- [ ] Collect static files
- [ ] Test application startup

### 🔀 Web Server (Nginx)
- [ ] Install Nginx
- [ ] Configure reverse proxy
- [ ] Set up SSL/TLS
- [ ] Configure rate limiting
- [ ] Set up logging
- [ ] Test configuration: `nginx -t`
- [ ] Restart Nginx

Example Nginx config:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

### 📊 Process Management (Systemd)
- [ ] Create systemd service file
- [ ] Enable service on boot
- [ ] Start service
- [ ] Verify service status

Example systemd service (`/etc/systemd/system/gax.service`):
```ini
[Unit]
Description=GAX Banking API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/gax
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:8000 gax.wsgi:application

[Install]
WantedBy=multi-user.target
```

Commands:
```bash
sudo systemctl daemon-reload
sudo systemctl enable gax
sudo systemctl start gax
sudo systemctl status gax
```

## Post-Deployment

### ✅ Testing
- [ ] Test user registration
- [ ] Test login/authentication
- [ ] Test wallet creation
- [ ] Test deposit
- [ ] Test transfer
- [ ] Test withdrawal
- [ ] Test all bill payments (airtime, data, TV, electricity)
- [ ] Test payment gateway
- [ ] Test webhooks
- [ ] Test admin panel
- [ ] Load testing with Apache Bench or Locust
- [ ] Security scan (OWASP ZAP)

### 📈 Monitoring
- [ ] Set up application monitoring (Sentry)
- [ ] Configure server monitoring (New Relic, DataDog)
- [ ] Set up uptime monitoring (UptimeRobot)
- [ ] Configure log aggregation (ELK, Papertrail)
- [ ] Set up alerts for errors
- [ ] Monitor database performance
- [ ] Monitor API response times
- [ ] Set up webhook failure alerts

### 🔐 API Keys
- [ ] Generate production API keys
- [ ] Test merchant integration
- [ ] Document API for merchants
- [ ] Set up API key rotation policy

### 💾 Backups
- [ ] Set up automated database backups
- [ ] Test backup restoration
- [ ] Configure backup retention policy
- [ ] Set up media files backup
- [ ] Document backup procedures

### 🔄 Maintenance
- [ ] Schedule regular security updates
- [ ] Plan for Django upgrades
- [ ] Set up staging environment
- [ ] Document deployment procedures
- [ ] Create rollback plan

### 📞 Support
- [ ] Set up support email
- [ ] Create support documentation
- [ ] Train support team
- [ ] Set up ticketing system

### ⚖️ Compliance
- [ ] Review data protection policies
- [ ] Ensure PCI compliance (if applicable)
- [ ] Review terms of service
- [ ] Privacy policy
- [ ] Cookie policy
- [ ] KYC/AML compliance

## Moniepoint Integration Checklist

### Sandbox Testing
- [ ] Create sandbox account
- [ ] Get sandbox API credentials
- [ ] Test virtual account creation
- [ ] Test transaction verification
- [ ] Test bank transfer
- [ ] Test webhook reception
- [ ] Verify signature verification

### Live Integration
- [ ] Complete Moniepoint KYC
- [ ] Get live API credentials
- [ ] Update environment variables
- [ ] Test small transactions
- [ ] Verify webhook handling
- [ ] Monitor settlement timing

## Performance Optimization

### Database
- [ ] Add database indexes
- [ ] Optimize queries (use select_related, prefetch_related)
- [ ] Enable query caching
- [ ] Set up connection pooling
- [ ] Regular VACUUM (PostgreSQL)

### Caching
- [ ] Configure Redis caching
- [ ] Cache frequently accessed data
- [ ] Set appropriate TTLs
- [ ] Monitor cache hit rates

### Application
- [ ] Enable gzip compression
- [ ] Optimize static files
- [ ] Use CDN for static assets
- [ ] Implement pagination
- [ ] Add rate limiting

## Management Commands Schedule

Set up cron jobs or Celery beat:

```bash
# Reconcile transactions every hour
0 * * * * cd /path/to/gax && /path/to/venv/bin/python manage.py reconcile_transactions --hours 1

# Process settlements every 6 hours
0 */6 * * * cd /path/to/gax && /path/to/venv/bin/python manage.py process_settlements

# Database backup daily at 2 AM
0 2 * * * /path/to/backup-script.sh
```

## Emergency Procedures

### Rollback Plan
1. Stop application
2. Restore database from backup
3. Revert to previous code version
4. Run migrations if needed
5. Restart application
6. Verify functionality

### High Traffic
- [ ] Scale horizontally (add more app servers)
- [ ] Increase database connections
- [ ] Enable caching aggressively
- [ ] Use load balancer

### Security Breach
1. Immediately rotate all API keys
2. Change SECRET_KEY
3. Force password reset for all users
4. Review logs for unauthorized access
5. Patch vulnerability
6. Notify affected users

## Launch Day

- [ ] All tests passing
- [ ] Staging environment matches production
- [ ] Backups verified
- [ ] Monitoring active
- [ ] Support team ready
- [ ] Announcement prepared
- [ ] Gradual rollout plan
- [ ] Rollback plan ready

## Post-Launch (First Week)

- [ ] Monitor error rates
- [ ] Check API response times
- [ ] Review user feedback
- [ ] Monitor transaction volumes
- [ ] Check webhook success rates
- [ ] Review security logs
- [ ] Optimize slow queries
- [ ] Update documentation based on feedback

---

## 🎯 Success Criteria

Your deployment is successful when:
- ✅ All API endpoints respond correctly
- ✅ Transactions process successfully
- ✅ Bill payments work for all providers
- ✅ Payment gateway accepts payments
- ✅ Webhooks are received and processed
- ✅ No critical errors in logs
- ✅ Response times < 200ms for most endpoints
- ✅ Database queries optimized
- ✅ SSL certificate valid
- ✅ Monitoring shows 99.9% uptime

---

**Good luck with your deployment! 🚀**
