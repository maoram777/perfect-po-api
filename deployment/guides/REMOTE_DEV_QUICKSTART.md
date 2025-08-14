# 🚀 Remote Development Environment - Quick Start

## 📋 **What We're Building**

A **remote development environment** on EC2 that's perfect for testing and development before going to production.

## 🏗️ **Architecture (Dev vs Prod)**

| Feature | Development | Production |
|---------|-------------|------------|
| **SSL** | ❌ HTTP only | ✅ HTTPS with SSL |
| **Rate Limiting** | 🟡 Lenient (50 req/s) | 🔴 Strict (10 req/s) |
| **Debug Mode** | ✅ Enabled | ❌ Disabled |
| **Hot Reload** | ✅ Enabled | ❌ Disabled |
| **Passwords** | 🟡 Weak defaults | 🔴 Strong required |
| **Logging** | ✅ Verbose | 🟡 Production level |
| **Mongo Express** | ✅ Enabled | ❌ Disabled |

## 🚀 **Quick Setup Steps**

### **Step 1: Launch EC2 Instance**
```bash
# Instance Type: t3.small (2 vCPU, 2GB RAM) - $8-15/month
# OS: Ubuntu 20.04+ or Amazon Linux 2
# Storage: 20GB EBS gp3
```

### **Step 2: Configure Security Groups**
```
Inbound Rules:
- HTTP (80): 0.0.0.0/0
- SSH (22): Your IP address only
- MongoDB (27017): 0.0.0.0/0
- Redis (6379): 0.0.0.0/0
- MongoDB Express (8081): 0.0.0.0/0
```

### **Step 3: Connect and Deploy**
```bash
# SSH to your instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Clone repository
git clone https://github.com/yourusername/perfect-po-api.git
cd perfect-po-api

# Make deployment script executable
chmod +x deploy_dev.sh

# Deploy development environment
./deploy_dev.sh development your-ec2-ip
```

### **Step 4: Configure Environment**
```bash
# The script will create .env.dev from template
# Edit it with your values:
nano .env.dev

# Key values to set:
# - KEEPA_API_KEY=your_keepa_api_key
# - AWS_ACCESS_KEY_ID=your_aws_key
# - AWS_SECRET_ACCESS_KEY=your_aws_secret
# - AWS_S3_BUCKET=your_dev_bucket_name
```

### **Step 5: Test Everything**
```bash
# Test health endpoint
curl http://your-ec2-ip/health

# Test API docs
curl http://your-ec2-ip/docs

# Test dev status
curl http://your-ec2-ip/dev/status
```

## 🔧 **Development Features**

### **Hot Reload**
- ✅ **Code changes** automatically restart the API
- ✅ **No need to rebuild** containers
- ✅ **Fast development** cycle

### **Debug Tools**
- ✅ **Verbose logging** for troubleshooting
- ✅ **MongoDB Express** for database management
- ✅ **Development endpoints** for status checks

### **Easy Management**
```bash
# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Restart services
docker-compose -f docker-compose.dev.yml restart

# Stop everything
docker-compose -f docker-compose.dev.yml down

# Update and redeploy
git pull && ./deploy_dev.sh
```

## 📱 **Access URLs**

After deployment, you can access:

- **API**: `http://your-ec2-ip/`
- **API Docs**: `http://your-ec2-ip/docs`
- **Health Check**: `http://your-ec2-ip/health`
- **Dev Status**: `http://your-ec2-ip/dev/status`
- **MongoDB Express**: `http://your-ec2-ip:8081`
- **Direct API**: `http://your-ec2-ip:8000`

## 🧪 **Testing Your API**

### **1. Test Authentication**
```bash
# Register a user
curl -X POST "http://your-ec2-ip/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","username":"testuser","full_name":"Test User"}'

# Login
curl -X POST "http://your-ec2-ip/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'
```

### **2. Test Catalog Upload**
```bash
# Get JWT token from login response
TOKEN="your_jwt_token_here"

# Upload catalog
curl -X POST "http://your-ec2-ip/catalogs/upload" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/your/catalog.xlsx" \
  -F "name=Test Catalog" \
  -F "description=Test Description"
```

### **3. Test Product Enrichment**
```bash
# Trigger enrichment
curl -X POST "http://your-ec2-ip/catalogs/YOUR_CATALOG_ID/enrich?provider=keepa" \
  -H "Authorization: Bearer $TOKEN"
```

## 🔍 **Troubleshooting**

### **Common Issues**

1. **Port Already in Use**
   ```bash
   # Check what's using port 80
   sudo netstat -tlnp | grep :80
   
   # Stop Apache if running
   sudo systemctl stop apache2
   ```

2. **Permission Denied**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod 600 .env.dev
   ```

3. **Container Won't Start**
   ```bash
   # Check logs
   docker-compose -f docker-compose.dev.yml logs api
   
   # Check status
   docker-compose -f docker-compose.dev.yml ps
   ```

### **Debug Commands**
```bash
# Check all services
docker-compose -f docker-compose.dev.yml ps

# Check specific service logs
docker-compose -f docker-compose.dev.yml logs -f api

# Check system resources
docker stats

# Check network
docker network ls
```

## 💰 **Cost Estimation**

### **Development Environment**
- **EC2 t3.small**: $8-15/month
- **EBS Storage**: $2-3/month
- **Data Transfer**: $1-2/month
- **Total**: **$11-20/month**

### **vs Production**
- **Production t3.medium**: $16-30/month
- **SSL certificates**: $0-20/month
- **Monitoring**: $5-10/month
- **Total**: **$21-60/month**

## 📚 **Next Steps**

### **Immediate (Today)**
1. ✅ Launch EC2 instance
2. ✅ Deploy development environment
3. ✅ Test basic functionality
4. ✅ Upload test catalog

### **This Week**
1. 🔄 Test all API endpoints
2. 🔄 Verify product enrichment
3. 🔄 Test file uploads
4. 🔄 Debug any issues

### **Next Week**
1. 🚀 Deploy to production
2. 🚀 Configure SSL certificates
3. 🚀 Set up monitoring
4. 🚀 Configure backups

## 🎯 **Success Criteria**

Your development environment is ready when:
- ✅ All API endpoints respond correctly
- ✅ File uploads work
- ✅ Product enrichment functions
- ✅ Database is accessible
- ✅ Logs show no errors
- ✅ Performance is acceptable

---

## 🚨 **Important Notes**

- **This is for development only** - don't use weak passwords in production
- **HTTP only** - no SSL encryption in development
- **Debug mode enabled** - more verbose logging
- **Hot reload enabled** - code changes auto-restart the API

**🎉 Ready to start? Launch your EC2 instance and run the deployment script!**
