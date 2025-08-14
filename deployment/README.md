# 🚀 Perfect PO API - Deployment Guide

This directory contains all deployment configurations and guides for the Perfect PO API.

## 📁 **Directory Structure**

```
deployment/
├── README.md                 # This file - main deployment guide
├── dev/                      # Development environments
│   ├── docker-compose.dev.yml      # Remote dev (MongoDB Atlas)
│   ├── docker-compose.local.yml    # Local dev (localhost MongoDB)
│   ├── Dockerfile.dev
│   ├── nginx.dev.conf
│   ├── env.dev.template            # Remote dev template
│   ├── env.local.template          # Local dev template
│   ├── deploy_dev.sh               # Remote dev deployment
│   └── deploy_local.sh             # Local dev deployment
├── prod/                     # Production environment
│   ├── docker-compose.prod.yml
│   ├── Dockerfile.prod
│   ├── nginx.conf
│   ├── env.prod.template
│   └── deploy_ec2.sh
├── lambda/                   # AWS Lambda & SQS setup
│   ├── lambda_enrichment_function.py
│   ├── sqs_enrichment_service.py
│   ├── template.yaml
│   ├── lambda_requirements.txt
│   ├── deploy_lambda.sh
│   └── setup_secrets.sh
└── guides/                   # Documentation & guides
    ├── REMOTE_DEV_QUICKSTART.md
    ├── EC2_DEPLOYMENT_GUIDE.md
    ├── DEPLOYMENT_CHECKLIST.md
    ├── SQS_LAMBDA_ARCHITECTURE.md
    └── LAMBDA_CONFIGURATION.md
```

## 🎯 **Deployment Options**

### **1. 🏠 Local Development** (`dev/` with localhost)
- **Purpose**: Development on your local machine
- **Features**: Hot reload, debug mode, local MongoDB, MongoDB Express
- **Database**: Local MongoDB (localhost:27017)
- **Cost**: Free (local resources)
- **Security**: Local only, weak passwords, permissive CORS
- **Use Case**: Local development, testing, debugging

**Quick Start:**
```bash
cd deployment/dev
chmod +x deploy_local.sh
./deploy_local.sh
```

### **2. 🧪 Remote Development** (`dev/` with MongoDB Atlas)
- **Purpose**: Testing and development on EC2
- **Features**: Hot reload, debug mode, remote MongoDB Atlas
- **Database**: MongoDB Atlas cluster (AllShoes-Dev)
- **Cost**: $11-20/month (t3.small + Atlas)
- **Security**: HTTP only, weak passwords, permissive CORS
- **Use Case**: Remote development, testing, team collaboration

**Quick Start:**
```bash
cd deployment/dev
chmod +x deploy_dev.sh
./deploy_dev.sh development your-ec2-ip
```

### **3. 🚀 Production Environment** (`prod/`)
- **Purpose**: Live production deployment
- **Features**: SSL, strict security, monitoring, backups
- **Database**: MongoDB Atlas or dedicated MongoDB
- **Cost**: $21-60/month (t3.medium + SSL + monitoring)
- **Security**: HTTPS, strong passwords, strict CORS
- **Use Case**: Live production application

**Quick Start:**
```bash
cd deployment/prod
chmod +x deploy_ec2.sh
./deploy_ec2.sh production your-domain.com
```

### **4. ⚡ AWS Lambda & SQS** (`lambda/`)
- **Purpose**: Asynchronous product enrichment
- **Features**: Scalable, serverless, cost-effective
- **Cost**: Pay-per-use (typically $5-20/month)
- **Security**: IAM roles, Secrets Manager
- **Use Case**: Background processing, scaling

**Quick Start:**
```bash
cd deployment/lambda
chmod +x deploy_lambda.sh
./deploy_lambda.sh
```

## 🚀 **Recommended Deployment Path**

### **Phase 1: Local Development (Week 1)**
1. ✅ Deploy local development environment
2. ✅ Test all functionality locally
3. ✅ Debug any issues
4. ✅ Verify everything works

### **Phase 2: Remote Development (Week 2)**
1. 🧪 Launch EC2 t3.small instance
2. 🧪 Deploy remote development environment
3. 🧪 Test with MongoDB Atlas
4. 🧪 Verify remote functionality

### **Phase 3: Production (Week 3)**
1. 🚀 Launch EC2 t3.medium instance
2. 🚀 Deploy production environment
3. 🚀 Configure SSL certificates
4. 🚀 Set up monitoring

### **Phase 4: Scaling (Week 4)**
1. ⚡ Deploy Lambda & SQS
2. ⚡ Configure async enrichment
3. ⚡ Set up monitoring & alerts
4. ⚡ Configure backups

## 🔧 **Prerequisites**

### **For Local Development**
- Docker and Docker Compose
- Local machine resources
- Keepa API key
- AWS S3 bucket

### **For Remote Development**
- AWS account with EC2 access
- SSH key pair for EC2
- MongoDB Atlas cluster (provided)
- Keepa API key
- AWS S3 bucket

### **For Production**
- SSL certificate (Let's Encrypt or custom)
- Strong passwords
- Monitoring tools
- Backup strategy

### **For Lambda**
- AWS CLI configured
- SAM CLI installed
- IAM permissions

## 📚 **Documentation**

### **Quick Start Guides**
- **`guides/REMOTE_DEV_QUICKSTART.md`**: Remote development setup
- **`guides/EC2_DEPLOYMENT_GUIDE.md`**: Production deployment guide
- **`guides/DEPLOYMENT_CHECKLIST.md`**: Production readiness checklist

### **Architecture Guides**
- **`guides/SQS_LAMBDA_ARCHITECTURE.md`**: Lambda & SQS setup
- **`guides/LAMBDA_CONFIGURATION.md`**: Lambda configuration details

## 🎯 **Choose Your Path**

### **🏠 Start Local (Recommended)**
```bash
# 1. Deploy local development environment
cd deployment/dev
./deploy_local.sh

# 2. Test everything works locally
# 3. Move to remote when ready
```

### **🧪 Go Remote (Team Development)**
```bash
# 1. Read the remote development guide
cat deployment/guides/REMOTE_DEV_QUICKSTART.md

# 2. Deploy remote development environment
cd deployment/dev
./deploy_dev.sh

# 3. Uses your MongoDB Atlas cluster
```

### **🚀 Go Straight to Production**
```bash
# 1. Read the production guide
cat deployment/guides/EC2_DEPLOYMENT_GUIDE.md

# 2. Deploy production environment
cd deployment/prod
./deploy_ec2.sh

# 3. Configure SSL and monitoring
```

### **⚡ Add Lambda Scaling**
```bash
# 1. Read the Lambda architecture guide
cat deployment/guides/SQS_LAMBDA_ARCHITECTURE.md

# 2. Deploy Lambda infrastructure
cd deployment/lambda
./deploy_lambda.sh

# 3. Configure async enrichment
```

## 🔍 **Troubleshooting**

### **Common Issues**
1. **Port conflicts**: Check if ports 80, 8000, 27017, 6379 are free
2. **Permission errors**: Ensure scripts are executable (`chmod +x`)
3. **Environment variables**: Check `.env` files are properly configured
4. **Docker issues**: Ensure Docker and Docker Compose are installed
5. **MongoDB connection**: Verify connection strings and network access

### **Debug Commands**
```bash
# Check service status
docker-compose -f docker-compose.local.yml ps      # Local
docker-compose -f docker-compose.dev.yml ps        # Remote

# View logs
docker-compose -f docker-compose.local.yml logs -f # Local
docker-compose -f docker-compose.dev.yml logs -f   # Remote

# Check system resources
docker stats
```

## 💰 **Cost Estimation**

| Environment | Instance | Database | Monthly Cost | Use Case |
|-------------|----------|----------|--------------|----------|
| **Local** | Local machine | Local MongoDB | Free | Local development |
| **Remote Dev** | t3.small | MongoDB Atlas | $11-20 | Remote development |
| **Production** | t3.medium | MongoDB Atlas | $21-60 | Live application |
| **Lambda** | Pay-per-use | - | $5-20 | Background processing |

## 🎉 **Get Started**

1. **Choose your deployment path** (local → remote → prod → lambda)
2. **Read the relevant guide** in `guides/`
3. **Deploy with the appropriate script**
4. **Test and verify functionality**
5. **Scale up when ready**

---

**🚀 Ready to deploy? Choose your path and let's get started!**
